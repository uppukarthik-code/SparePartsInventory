"""
railway_lead_time_derivation.py
===============================
STEP 23.6B -- Internal Lead-Time Derivation + Planning-Universe Reconciliation
(ADDITIVE; data foundation only; reuses the DMTR raw-XML reader).

A. Derives a REAL per-PL planning lead time from DMTR procurement dates only:
     Priority 1  PO Date  -> Receipt Date   (vendor procurement lead time)
     Priority 2  Reqn Date-> Receipt Date   (internal fulfilment lead time)
   Rules (agreed STEP23.6B): real dates only; reject negative intervals; GLOBAL
   per-source P5/P95 winsorization; strict source hierarchy per PL (PO if any PO
   observation, else Reqn); Median_LT is the planning lead time. NO synthetic
   values, NO industry averages, NO defaults.

B. Reconciles the four planning universes (DMTR demand / Operational stock /
   Strategic / Criticality) and classifies each PL.

Writes outputs/MAS/history/{lead_time_master.csv, pl_universe_reconciliation.csv}.
Modifies nothing existing.
"""

from __future__ import annotations

import glob
import re
from collections import defaultdict
from datetime import date

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway.ingestion import excel_reader, csv_reader, shared_io   # consolidated I/O (Phase A)
from railway.governance import config as gcfg                       # centralized config (Phase B)

H = gcfg.HISTORY_DIR
MAS = gcfg.DIVISION_OUTPUT_DIR
ROLL = cfg.OUTPUT_DIR / "_enterprise_rollup"

_TXN = re.compile(r"dt\.?\s*([0-3]?\d)[.\-/]([01]?\d)[.\-/]((?:20)?\d\d)")
_REQN = re.compile(r"Reqn\s*No\.?\s*([A-Za-z0-9\-/ ]*?)\s*dt\.?\s*([0-3]?\d)[.\-/]([01]?\d)[.\-/]((?:20)?\d\d)", re.I)
_PO = re.compile(r"(?:PO|Contract)\s*/?\s*(?:PO|Contract)?\s*No\.?\s*([A-Za-z0-9\-/]+).{0,60}?dt\.?\s*([0-3]?\d)[.\-/]([01]?\d)[.\-/]((?:20)?\d\d)", re.I)


def _mk(d, m, y):
    y = int(y); y = y + 2000 if y < 100 else y
    try:
        return date(y, int(m), int(d))
    except Exception:
        return None


# ----------------------------------------------------------------------
# A. lead-time derivation
# ----------------------------------------------------------------------
def _collect_intervals():
    """Return {pl: [days]} for PO and Reqn paths (non-negative only)."""
    po = defaultdict(list); reqn = defaultdict(list)
    for fp in sorted(glob.glob(str(shared_io.DMTR_DIR / "DMTR_*.xlsx"))):
        for row in excel_reader.read_sheet_rows(fp)[1:]:
            t = str(row.get(3) or "")
            if not t.startswith("Receipt"):
                continue
            pl = str(row.get(6) or "").strip()
            if not pl:
                continue
            mt = _TXN.search(str(row.get(2) or ""))
            rcv = _mk(*mt.groups()) if mt else None
            if rcv is None:
                continue
            detail = str(row.get(8) or "")
            mp = _PO.search(detail)
            if mp:
                od = _mk(mp.group(2), mp.group(3), mp.group(4))
                if od:
                    d = (rcv - od).days
                    if d >= 0:
                        po[pl].append(d)
            mr = _REQN.search(detail)
            if mr and mr.group(2):
                rq = _mk(mr.group(2), mr.group(3), mr.group(4))
                if rq:
                    d = (rcv - rq).days
                    if d >= 0:
                        reqn[pl].append(d)
    return po, reqn


def _winsor_bounds(per_pl):
    allv = [v for lst in per_pl.values() for v in lst]
    if not allv:
        return None, None
    return float(np.percentile(allv, 5)), float(np.percentile(allv, 95))


def _clip(lst, lo, hi):
    return [min(max(v, lo), hi) for v in lst]


def build_lead_time_master(write: bool = True):
    po, reqn = _collect_intervals()
    po_lo, po_hi = _winsor_bounds(po)
    rq_lo, rq_hi = _winsor_bounds(reqn)

    pls = set(po) | set(reqn)
    rows = []
    for pl in sorted(pls):
        if pl in po and po[pl]:                       # Priority 1: PO
            vals = _clip(po[pl], po_lo, po_hi); src = "PO_Date"
        else:                                          # Priority 2: Requisition
            vals = _clip(reqn[pl], rq_lo, rq_hi); src = "Requisition_Date"
        arr = np.array(vals, float)
        n = len(arr)
        median = float(np.median(arr))
        p90 = float(np.percentile(arr, 90)) if n > 1 else float(arr[0])
        std = float(np.std(arr, ddof=1)) if n > 1 else 0.0
        conf = "High" if n >= 20 else ("Medium" if n >= 5 else "Low")
        rows.append({
            "PL_Code": pl,
            "Lead_Time_Days": round(median, 1),        # planning LT = median
            "Lead_Time_Source": src,
            "Observations": n,
            "Median_LT": round(median, 1),
            "P90_LT": round(p90, 1),
            "Std_LT": round(std, 2),
            "Confidence": conf,
        })
    df = pd.DataFrame(rows, columns=["PL_Code", "Lead_Time_Days", "Lead_Time_Source",
                                     "Observations", "Median_LT", "P90_LT", "Std_LT", "Confidence"])
    if write:
        H.mkdir(parents=True, exist_ok=True)
        df.to_csv(H / "lead_time_master.csv", index=False)
    return df, {"po_bounds": (po_lo, po_hi), "reqn_bounds": (rq_lo, rq_hi)}


# ----------------------------------------------------------------------
# B. universe reconciliation
# ----------------------------------------------------------------------
def _rd(p):
    return csv_reader.read_pl_csv(p)


def build_universe_reconciliation(write: bool = True):
    dmtr = set(_rd(H / "demand_classification.csv")["PL_Code"])
    oper = set(_rd(MAS / "railway_operational_inventory.csv")["PL_Code"])
    alloc = _rd(ROLL / "strategic_inventory_allocation.csv")
    strat = set(alloc[alloc["Business_Unit"] == gcfg.DIVISION]["PL_Code"])
    skum = _rd(MAS / "railway_sku_master.csv")
    crit = set(skum[skum["Criticality"].str.strip() != ""]["PL_Code"])

    def status(d, o, s, c):
        if d and o and s and c:
            return "Fully_Reconciled"
        present = [d, o, s, c]
        if sum(present) == 1:
            if d: return "Demand_Only"
            if o: return "Inventory_Only"
            if c: return "Criticality_Only"
            return "Partial_Match"          # strategic-only (no dedicated class)
        return "Partial_Match"

    rows = []
    for pl in sorted(dmtr | oper | strat | crit):
        d, o, s, c = pl in dmtr, pl in oper, pl in strat, pl in crit
        rows.append({"PL_Code": pl, "In_DMTR": int(d), "In_Operational": int(o),
                     "In_Strategic": int(s), "In_Criticality": int(c),
                     "Universe_Status": status(d, o, s, c)})
    df = pd.DataFrame(rows)
    if write:
        df.to_csv(H / "pl_universe_reconciliation.csv", index=False)
    return df, {"dmtr": dmtr, "oper": oper, "strat": strat, "crit": crit}


def run():
    lt, win = build_lead_time_master(write=True)
    uni, sets = build_universe_reconciliation(write=True)
    dmtr = sets["dmtr"]
    covered = set(lt["PL_Code"]) & dmtr
    print("STEP 23.6B -- internal lead-time derivation + universe reconciliation (MAS)")
    print(f"  PLs with derived lead time : {len(lt)}  (in DMTR universe: {len(covered)} = {100*len(covered)/len(dmtr):.1f}%)")
    print(f"  source split               : {lt['Lead_Time_Source'].value_counts().to_dict()}")
    print(f"  confidence                 : {lt['Confidence'].value_counts().to_dict()}")
    print(f"  PO winsor bounds (d)       : {tuple(round(x,1) for x in win['po_bounds'])}")
    print(f"  Reqn winsor bounds (d)     : {tuple(round(x,1) for x in win['reqn_bounds'])}")
    print(f"  universe status            : {uni['Universe_Status'].value_counts().to_dict()}")
    return lt, uni


if __name__ == "__main__":
    run()
