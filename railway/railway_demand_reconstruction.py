"""
railway_demand_reconstruction.py
================================
STEP 21A -- Monthly Demand History Reconstruction (DATA FOUNDATION ONLY).

Reconstructs a normalized monthly demand history for the MAS division from the
54 monthly DMTR (Material Transaction Register) workbooks in
raw_data/Railway_Operations/MAS/. This is ADDITIVE: no forecasting, SRRS,
procurement, optimization, Power BI or KPI logic is touched, and nothing under
the existing outputs tree is modified -- all writes land in a NEW directory
outputs/MAS/history/.

Source schema (verified, STEP21A discovery -- single sheet 'Sheet1', header row 1):
    col 2  DMTR No. + date   ('...dt. DD-MM-YYYY HH:MM:SSby NAME')
    col 3  Transaction type  ('Issue-...', 'Receipt-...', 'Initial Stock', ...)
    col 6  PL No. / Code
    col 7  Item description
    col 9  Quantity + UOM    ('10.000Number')

Reconstruction rules (agreed STEP21A):
  * Issues_Qty (demand)  = TRUE CONSUMPTION only:
        Issue-To User Depot + Issue-For End Use + Issue-To Contractor.
    (Issue-Book Transfer and Write-Back Issue are EXCLUDED from demand; they are
     still counted in the physical running balance and reported in QA.)
  * Receipts_Qty         = all 'Receipt-*' inflows.
  * Closing_Stock        = RECONSTRUCTED running balance (derived, NOT a source
    field): opening from 'Initial Stock' + cumulative (inflows - outflows).
    Reconciled against stock_history.xlsx in validation.
  * Gap filling          = per PL, first-observed month -> 2026-06, missing months
    zero-filled (continuous monthly timeline).

Output: outputs/MAS/history/{monthly_demand_history,monthly_demand_summary,
        demand_history_quality_report}.csv
"""

from __future__ import annotations

import glob
import re
import zipfile
from collections import defaultdict
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway.ingestion import excel_reader, shared_io   # consolidated I/O (Phase A)
from railway.governance import config as gcfg           # centralized config (Phase B)

BUSINESS_UNIT = gcfg.DIVISION
DMTR_DIR = shared_io.DMTR_DIR                            # single source (was: cfg.RAW_DATA_DIR/...)
HISTORY_DIR = gcfg.HISTORY_DIR

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# Column indices (0-based) in the DMTR sheet.
C_DMTR_DATE, C_TYPE, C_PL, C_DESC, C_QTY = 2, 3, 6, 7, 9

# --- transaction classification ---------------------------------------------
DEMAND_ISSUE_PREFIXES = ("Issue-To User Depot", "Issue-For End Use", "Issue-To Contractor")

def _is_demand_issue(t: str) -> bool:
    return any(t.startswith(p) for p in DEMAND_ISSUE_PREFIXES)

def _is_receipt(t: str) -> bool:
    return t.startswith("Receipt")

def _balance_sign(t: str) -> int:
    """Physical effect on stock for the reconstructed running balance."""
    if t.startswith("Receipt") or t.startswith("Initial Stock") or t.startswith("Write-Back"):
        return +1
    if t.startswith("Issue") or t.startswith("Return of Initial Rejected"):
        return -1
    return 0   # 'No discrepancy found during Stock Verification', etc.

_DATE_RE = re.compile(r"dt\.?\s*([0-9]{1,2})[.\-/]([0-9]{1,2})[.\-/]([0-9]{2,4})")
_QTY_RE = re.compile(r"^\s*(-?[0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)")


# ----------------------------------------------------------------------
# raw OOXML reader — now delegates to the consolidated ingestion layer
# (railway.ingestion.excel_reader.read_sheet_rows). Name/return kept for the
# module's internal callers; behaviour is byte-identical (Phase A).
# ----------------------------------------------------------------------
def _sheet_rows(path):
    return excel_reader.read_sheet_rows(path)


def _parse_qty(raw):
    m = _QTY_RE.match(str(raw or ""))
    if not m:
        return 0.0, ""
    return float(m.group(1)), m.group(2)


def _parse_month(raw):
    m = _DATE_RE.search(str(raw or ""))
    if not m:
        return None
    dd, mm, yy = m.groups()
    yy = int(yy); yy = yy + 2000 if yy < 100 else yy
    return (yy, int(mm))


def _month_str(ym):
    return f"{ym[0]:04d}-{ym[1]:02d}"


def _month_range(start, end):
    """Inclusive list of (y,m) from start to end."""
    y, m = start; out = []
    while (y, m) <= end:
        out.append((y, m))
        m += 1
        if m > 12:
            y += 1; m = 1
    return out


# ----------------------------------------------------------------------
# Extraction
# ----------------------------------------------------------------------
def extract_transactions():
    """Return (records, qa) where records = list of dicts per transaction."""
    files = sorted(glob.glob(str(DMTR_DIR / "DMTR_*.xlsx")))
    recs = []
    qa = {"files": len(files), "rows": 0, "null_pl": 0, "null_date": 0,
          "qty_fail": 0, "excluded_booktransfer_writeback_qty": 0.0}
    for fp in files:
        for row in _sheet_rows(fp)[1:]:            # skip header
            qa["rows"] += 1
            pl = str(row.get(C_PL) or "").strip()
            if not pl:
                qa["null_pl"] += 1
                continue
            ym = _parse_month(row.get(C_DMTR_DATE))
            if ym is None:
                qa["null_date"] += 1
                continue
            t = str(row.get(C_TYPE) or "").strip()
            qraw = row.get(C_QTY)
            if not _QTY_RE.match(str(qraw or "")):
                qa["qty_fail"] += 1
            q, uom = _parse_qty(qraw)
            demand = q if _is_demand_issue(t) else 0.0
            receipt = q if _is_receipt(t) else 0.0
            if (t.startswith("Issue-Book Transfer") or t.startswith("Write-Back")):
                qa["excluded_booktransfer_writeback_qty"] += q
            recs.append({
                "PL_Code": pl, "Month": ym, "Type": t,
                "Description": str(row.get(C_DESC) or "").strip(),
                "Demand": demand, "Receipt": receipt,
                "BalanceDelta": _balance_sign(t) * q, "UOM": uom,
            })
    return recs, qa


# ----------------------------------------------------------------------
# Aggregation + gap fill + running balance
# ----------------------------------------------------------------------
def build_history(recs):
    global_end = max(r["Month"] for r in recs)               # (2026, 6)
    # per-PL aggregation
    agg = defaultdict(lambda: {"Demand": 0.0, "Receipt": 0.0, "Delta": 0.0})
    desc = {}; uom_count = defaultdict(lambda: defaultdict(int))
    first_month = {}
    for r in recs:
        key = (r["PL_Code"], r["Month"])
        agg[key]["Demand"] += r["Demand"]
        agg[key]["Receipt"] += r["Receipt"]
        agg[key]["Delta"] += r["BalanceDelta"]
        pl = r["PL_Code"]
        if r["Description"] and pl not in desc:
            desc[pl] = r["Description"]
        if r["UOM"]:
            uom_count[pl][r["UOM"]] += 1
        first_month[pl] = min(first_month.get(pl, r["Month"]), r["Month"])

    rows = []
    for pl in sorted(first_month):
        months = _month_range(first_month[pl], global_end)
        running = 0.0
        for ym in months:
            a = agg.get((pl, ym), {"Demand": 0.0, "Receipt": 0.0, "Delta": 0.0})
            running += a["Delta"]
            rows.append({
                "Business_Unit": BUSINESS_UNIT,
                "PL_Code": pl,
                "Description": desc.get(pl, ""),
                "Month": _month_str(ym),
                "Issues_Qty": round(a["Demand"], 3),
                "Receipts_Qty": round(a["Receipt"], 3),
                "Closing_Stock": round(running, 3),
            })
    hist = pd.DataFrame(rows)
    mixed_uom = {pl: dict(c) for pl, c in uom_count.items() if len(c) > 1}
    return hist, global_end, mixed_uom


def build_summary(hist):
    rows = []
    for pl, g in hist.groupby("PL_Code", sort=True):
        issues = g["Issues_Qty"].to_numpy(dtype=float)
        n = len(issues)
        total = float(issues.sum())
        mean = float(issues.mean()) if n else 0.0
        std = float(issues.std(ddof=1)) if n > 1 else 0.0
        cv = (std / mean) if mean > 0 else np.nan
        rows.append({
            "PL_Code": pl,
            "Description": g["Description"].iloc[0],
            "Months_Observed": n,
            "Total_Issues": round(total, 3),
            "Average_Monthly_Demand": round(mean, 4),
            "Std_Deviation": round(std, 4),
            "CV": (round(cv, 4) if not np.isnan(cv) else np.nan),
        })
    return pd.DataFrame(rows)


def _load_stock_history_snapshot():
    """PL_Code -> Current_Stock from stock_history.xlsx (end snapshot anchor)."""
    p = DMTR_DIR / "stock_history.xlsx"
    if not p.exists():
        return {}
    out = {}
    for row in _sheet_rows(p)[1:]:
        plraw = row.get(4)          # 'PL-Code/Type/Usage'
        if not plraw:
            continue
        pl = str(plraw).split("/")[0].strip()
        q, _ = _parse_qty(str(row.get(8)) + "x")   # stock col; ensure regex match
        try:
            out[pl] = float(str(row.get(8)).replace(",", ""))
        except Exception:
            out[pl] = q
    return out


def build_quality(hist, recs, qa, global_end, mixed_uom):
    total_pl = hist["PL_Code"].nunique()
    source_months = sorted({r["Month"] for r in recs})
    total_months = len(source_months)
    # gap (zero-filled) PL-months = rows where no transaction existed
    txn_keys = {(r["PL_Code"], _month_str(r["Month"])) for r in recs}
    hist_keys = set(zip(hist["PL_Code"], hist["Month"]))
    missing_months = len(hist_keys - txn_keys)
    dup = int(hist.duplicated(subset=["PL_Code", "Month"]).sum())
    coverage = round(100.0 * len(hist_keys & txn_keys) / len(hist_keys), 2) if len(hist_keys) else 0.0
    q = pd.DataFrame([{
        "Total_PL_Codes": total_pl,
        "Total_Months": total_months,
        "Missing_Months": missing_months,
        "Duplicate_Rows": dup,
        "Null_PL_Codes": qa["null_pl"],
        "Null_Dates": qa["null_date"],
        "Coverage_Percent": coverage,
    }])
    return q


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def run(write: bool = True):
    recs, qa = extract_transactions()
    hist, global_end, mixed_uom = build_history(recs)
    summary = build_summary(hist)
    quality = build_quality(hist, recs, qa, global_end, mixed_uom)

    if write:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        hist.to_csv(HISTORY_DIR / "monthly_demand_history.csv", index=False)
        summary.to_csv(HISTORY_DIR / "monthly_demand_summary.csv", index=False)
        quality.to_csv(HISTORY_DIR / "demand_history_quality_report.csv", index=False)

    print("STEP 21A -- MAS monthly demand history reconstruction")
    print(f"  DMTR files processed : {qa['files']}")
    print(f"  transactions         : {qa['rows']}")
    print(f"  PL codes             : {hist['PL_Code'].nunique()}")
    print(f"  monthly rows         : {len(hist)}")
    print(f"  source months        : {quality['Total_Months'].iloc[0]}")
    print(f"  zero-filled PL-months: {quality['Missing_Months'].iloc[0]}")
    print(f"  coverage %           : {quality['Coverage_Percent'].iloc[0]}")
    print(f"  mixed-UOM PLs        : {len(mixed_uom)}")
    print(f"  -> {HISTORY_DIR}")
    return {"history": hist, "summary": summary, "quality": quality,
            "qa": qa, "mixed_uom": mixed_uom, "global_end": global_end}


if __name__ == "__main__":
    run()
