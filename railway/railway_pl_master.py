"""
railway_pl_master.py
====================
STEP 23.7 -- Enterprise PL Master Reconciliation (DATA RECONCILIATION ONLY).

Builds a canonical enterprise PL entity by linking the four planning universes
(DMTR demand / Operational stock / Strategic / Criticality) plus the derived
Forecasting and Lead-Time layers. Modifies NO forecasting/safety-stock/ROP/SRRS/
procurement/optimization logic and NO existing output. Writes three new files to
outputs/MAS/history/.

PL codes are NEVER silently modified: a documented `PL_Code_Normalized` is derived
(digits-only, leading zeros stripped) and every normalization is reported. Fuzzy /
prefix matches are FLAGGED as review candidates only -- never auto-merged.
"""

from __future__ import annotations

import re
from collections import defaultdict

import pandas as pd

from railway import railway_config as cfg
from railway.ingestion import pl_normalization   # consolidated I/O (Phase A)
from railway.governance import config as gcfg    # centralized config (Phase B)

H = gcfg.HISTORY_DIR
MAS = gcfg.DIVISION_OUTPUT_DIR
ROLL = cfg.OUTPUT_DIR / "_enterprise_rollup"

MASTER_COLS = ["PL_Code", "PL_Code_Normalized", "Description", "Business_Unit",
               "Demand_Present", "Inventory_Present", "Strategic_Present",
               "Criticality_Present", "Forecast_Present", "Lead_Time_Present",
               "Demand_Records", "Inventory_Records", "Strategic_Records",
               "Forecast_Method", "Forecastability_Class",
               "Lead_Time_Days", "Lead_Time_Source",
               "Criticality", "ABC_Class", "XYZ_Class", "Master_Status"]


def _rd(p, cols=None):
    df = pd.read_csv(p, dtype=str, keep_default_na=False)
    return df[cols] if cols else df


# ----------------------------------------------------------------------
# PL normalization (documented; never overwrites the source code)
# ----------------------------------------------------------------------
def normalize_pl(pl: str):
    """Return (normalized, issue_type, changed). Delegates to the consolidated
    ``railway.ingestion.pl_normalization.normalize_pl`` (behaviour unchanged, Phase A)."""
    return pl_normalization.normalize_pl(pl)


# ----------------------------------------------------------------------
# universe loaders
# ----------------------------------------------------------------------
def load_universes():
    dc = _rd(H / "demand_classification.csv")
    dc_desc = dict(zip(dc["PL_Code"], dc["Description"]))
    dmd_records = dict(zip(dc["PL_Code"], dc["Months_With_Demand"]))
    xyz = dict(zip(dc["PL_Code"], dc["Demand_Class"]))  # placeholder; xyz below

    fma = _rd(H / "forecast_method_assignment.csv")
    method = dict(zip(fma["PL_Code"], fma["Forecast_Method"]))
    xyz = dict(zip(fma["PL_Code"], fma["XYZ_Class"]))

    fr = set(_rd(H / "forecast_results.csv")["PL_Code"])
    fa = _rd(H / "forecast_accuracy.csv")
    fclass = dict(zip(fa["PL_Code"], fa["Forecastability_Class"]))

    op = _rd(MAS / "railway_operational_inventory.csv")
    op_desc = dict(zip(op["PL_Code"], op["Description"]))
    inv_records = op["PL_Code"].value_counts().to_dict()

    alloc = _rd(ROLL / "strategic_inventory_allocation.csv")
    alloc = alloc[alloc["Business_Unit"] == gcfg.DIVISION]
    strat_records = alloc["PL_Code"].value_counts().to_dict()

    skum = _rd(MAS / "railway_sku_master.csv")
    crit = {p: c for p, c in zip(skum["PL_Code"], skum["Criticality"]) if c.strip()}
    abc = dict(zip(skum["PL_Code"], skum["ABC_Class"]))
    sk_desc = dict(zip(skum["PL_Code"], skum["Description"]))

    lt = _rd(H / "lead_time_master.csv")
    lt_days = dict(zip(lt["PL_Code"], lt["Lead_Time_Days"]))
    lt_src = dict(zip(lt["PL_Code"], lt["Lead_Time_Source"]))

    return dict(dc_desc=dc_desc, dmd_records=dmd_records, method=method, xyz=xyz,
                forecastable=fr, fclass=fclass, op_desc=op_desc, inv_records=inv_records,
                strat_records=strat_records, crit=crit, abc=abc, sk_desc=sk_desc,
                lt_days=lt_days, lt_src=lt_src)


def _status(D, I, S, C, LT):
    if D and I and C:
        return "Fully_Reconciled"
    if D and LT and C:
        return "Planning_Ready"
    if D and LT:
        return "Forecast_Ready"
    if I and not D and not C and not S:
        return "Inventory_Only"
    if D and not I and not C and not S:
        return "Demand_Only"
    if C and not D and not I and not S:
        return "Criticality_Only"
    return "Partial"


def build_master(write: bool = True):
    u = load_universes()
    dmd = set(u["dmd_records"]); inv = set(u["inv_records"])
    strat = set(u["strat_records"]); crit = set(u["crit"])
    universe = sorted(dmd | inv | strat | crit)

    rows = []
    for pl in universe:
        D, I, S, C = pl in dmd, pl in inv, pl in strat, pl in crit
        LT = pl in u["lt_days"]
        F = pl in u["forecastable"]
        desc = u["dc_desc"].get(pl) or u["op_desc"].get(pl) or u["sk_desc"].get(pl, "")
        norm, _, _ = normalize_pl(pl)
        rows.append({
            "PL_Code": pl, "PL_Code_Normalized": norm, "Description": desc,
            "Business_Unit": gcfg.DIVISION,
            "Demand_Present": int(D), "Inventory_Present": int(I),
            "Strategic_Present": int(S), "Criticality_Present": int(C),
            "Forecast_Present": int(F), "Lead_Time_Present": int(LT),
            "Demand_Records": u["dmd_records"].get(pl, 0),
            "Inventory_Records": u["inv_records"].get(pl, 0),
            "Strategic_Records": u["strat_records"].get(pl, 0),
            "Forecast_Method": u["method"].get(pl, ""),
            "Forecastability_Class": u["fclass"].get(pl, ""),
            "Lead_Time_Days": u["lt_days"].get(pl, ""),
            "Lead_Time_Source": u["lt_src"].get(pl, ""),
            "Criticality": u["crit"].get(pl, ""),
            "ABC_Class": u["abc"].get(pl, ""),
            "XYZ_Class": u["xyz"].get(pl, ""),
            "Master_Status": _status(D, I, S, C, LT),
        })
    df = pd.DataFrame(rows)[MASTER_COLS]
    if write:
        H.mkdir(parents=True, exist_ok=True)
        df.to_csv(H / "enterprise_pl_master.csv", index=False)
    return df, u


def build_normalization_report(universe_pls, write: bool = True):
    rows = []
    for pl in sorted(universe_pls):
        norm, issue, changed = normalize_pl(pl)
        rows.append({"PL_Code": pl, "PL_Code_Normalized": norm,
                     "Length": len(str(pl)), "Issue_Type": issue,
                     "Changed": "Yes" if changed else "No"})
    df = pd.DataFrame(rows)
    if write:
        df.to_csv(H / "pl_code_normalization_report.csv", index=False)
    return df


def _tokens(s):
    return set(re.sub(r"[^A-Z0-9 ]", " ", str(s).upper()).split())


def _jaccard(a, b):
    A, B = _tokens(a), _tokens(b)
    return round(len(A & B) / len(A | B), 3) if (A | B) else 0.0


def build_match_candidates(u, write: bool = True):
    """Phase 3: review candidates only (never merged). Prefix-8 + description-exact."""
    dmd_desc = u["dc_desc"]; op_desc = u["op_desc"]; sk_desc = u["sk_desc"]
    dmd = set(dmd_desc); op = set(op_desc); sk = set(sk_desc)
    exact = dmd & op

    def f8(s):
        d = "".join(c for c in str(s) if c.isdigit())
        return d[:8] if len(d) >= 8 else None

    rows = []
    # Description-exact (different code) DMTR<->Operational and DMTR<->Strategic
    def nd(s):
        return re.sub(r"[^A-Z0-9]", "", str(s).upper())
    for other, odesc, label in [(op, op_desc, "OP"), (sk, sk_desc, "SK")]:
        ndmap = defaultdict(list)
        for p, d in odesc.items():
            if nd(d):
                ndmap[nd(d)].append(p)
        for pa, da in dmd_desc.items():
            key = nd(da)
            if key and key in ndmap:
                for pb in ndmap[key]:
                    if pb != pa:
                        rows.append((pa, pb, da, odesc[pb], 1.0, f"Description-{label}"))
    # Prefix-8 (8<->12 digit) DMTR<->Operational, exclude exact
    op_by8 = defaultdict(list)
    for p in op:
        k = f8(p)
        if k:
            op_by8[k].append(p)
    for pa in dmd:
        k = f8(pa)
        if not k:
            continue
        for pb in op_by8.get(k, []):
            if pb != pa and pa not in exact:
                rows.append((pa, pb, dmd_desc.get(pa, ""), op_desc.get(pb, ""),
                             _jaccard(dmd_desc.get(pa, ""), op_desc.get(pb, "")), "Prefix8-OP"))
    df = pd.DataFrame(rows, columns=["PL_Code_A", "PL_Code_B", "Description_A",
                                     "Description_B", "Match_Score", "Match_Type"])
    df = df.drop_duplicates().sort_values(["Match_Type", "Match_Score"], ascending=[True, False]).reset_index(drop=True)
    if write:
        df.to_csv(H / "pl_match_candidates.csv", index=False)
    return df


def run():
    master, u = build_master(write=True)
    norm = build_normalization_report(master["PL_Code"], write=True)
    cand = build_match_candidates(u, write=True)
    print("STEP 23.7 -- enterprise PL master reconciliation (MAS)")
    print(f"  enterprise_pl_master rows : {len(master)} (union of 4 universes)")
    print(f"  Master_Status             : {master['Master_Status'].value_counts().to_dict()}")
    print(f"  normalization changed     : {(norm['Changed']=='Yes').sum()} / {len(norm)}")
    print(f"  match candidates          : {len(cand)}  ({cand['Match_Type'].value_counts().to_dict()})")
    return master, norm, cand


if __name__ == "__main__":
    run()
