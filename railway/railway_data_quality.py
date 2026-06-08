"""
railway_data_quality.py
=======================
Data Quality Normalization Layer (additive -- NEVER overwrites originals).

A few cable SKUs carry a per-km / per-drum `Rate` while their stock and
consumption are recorded in metres. This inflates Inventory_Value,
Inventory_Investment_Required and Procurement_Priority_Score ~1000x.

This layer:
  * detects the mismatch (Unit in metre-family AND Unit_Cost > Rs 1,00,000),
  * produces *parallel* Normalized_* fields (originals untouched),
  * appends 4 normalized columns to railway_inventory_policy.csv,
  * writes an audit trail + a Power BI "Data Quality" page,
  * re-ranks procurement priority on the normalized score.

The `Unit` is derived from the strategic workbook's free-text 'UDM STOCK'
column (the only unit signal in railways.xlsx) -- real data, not fabricated.
"""

from __future__ import annotations

import openpyxl
import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway import railway_data_preparation as dp
from railway import railway_inventory_optimization as opt

UDM_COL = 20                      # 0-indexed 'UDM STOCK' column in the strategic sheet
UNIT_COST_THRESHOLD = cfg.UNIT_COST_MISMATCH_THRESHOLD   # centralized in config
METRE_TOKENS = cfg.METRE_UNIT_TOKENS


def _safe(x):
    return 0.0 if (x is None or pd.isna(x)) else float(x)


# ----------------------------------------------------------------------
# Derive a Unit token per PL from the workbook 'UDM STOCK' free text
# ----------------------------------------------------------------------
def load_units() -> pd.DataFrame:
    wb = openpyxl.load_workbook(cfg.STRATEGIC_WORKBOOK, read_only=True, data_only=True)
    ws = wb[cfg.STRATEGIC_STOCK_SHEET]
    rows = list(ws.iter_rows(values_only=True))
    recs = []
    for r in rows[cfg.STRATEGIC_DATA_START_ROW - 1:]:
        pl = dp._norm_pl(r[cfg.STRATEGIC_COLS["PL_Code"]]
                         if len(r) > cfg.STRATEGIC_COLS["PL_Code"] else None)
        if pl is None:
            continue
        udm = str(r[UDM_COL]) if (len(r) > UDM_COL and r[UDM_COL] is not None) else ""
        u = udm.upper()
        if any(t in u for t in METRE_TOKENS):
            unit = "MTR"
        elif "NOS" in u:
            unit = "Nos"
        elif "SET" in u:
            unit = "Set"
        elif "PAIR" in u:
            unit = "Pairs"
        elif "KG" in u:
            unit = "Kgs"
        else:
            unit = ""
        recs.append({"PL_Code": pl, "Unit": unit, "UDM_Text": udm.strip()})
    wb.close()
    return pd.DataFrame.from_records(recs).drop_duplicates(subset="PL_Code")


# ----------------------------------------------------------------------
# Detection + normalization rules (locked)
# ----------------------------------------------------------------------
def detect_mismatch(unit, unit_cost) -> str:
    u = str(unit or "").upper()
    has_metre = any(t in u for t in METRE_TOKENS)
    return "Yes" if (has_metre and _safe(unit_cost) > UNIT_COST_THRESHOLD) else "No"


def build_quality_layer(write: bool = True):
    """Rebuild Step-5 policy fresh, attach normalized parallel metrics."""
    # fresh policy (idempotent) -- has Current_Stock, Inventory_Gap,
    # Criticality_Weight, Procurement_Priority_Score, _Inventory_Value
    pol = opt.build_inventory_policy(write=True)
    hist = dp.build_demand_history(write=False)[["PL_Code", "Unit_Cost"]]
    units = load_units()[["PL_Code", "Unit", "UDM_Text"]]

    df = pol.merge(hist, on="PL_Code", how="left").merge(units, on="PL_Code", how="left")

    df["Potential_Unit_Mismatch"] = [detect_mismatch(u, c)
                                     for u, c in zip(df["Unit"], df["Unit_Cost"])]
    flagged = df["Potential_Unit_Mismatch"] == "Yes"

    df["Normalized_Unit_Cost"] = np.where(
        flagged, df["Unit_Cost"] / cfg.UNIT_MISMATCH_DIVISOR, df["Unit_Cost"])
    gap_pos = df["Inventory_Gap"].clip(lower=0)
    df["Normalized_Inventory_Value"] = (df["Current_Stock"] * df["Normalized_Unit_Cost"]).round(2)
    df["Normalized_Investment_Required"] = (gap_pos * df["Normalized_Unit_Cost"]).round(2)
    df["Normalized_Procurement_Priority_Score"] = (
        df["Criticality_Weight"] * gap_pos * df["Normalized_Unit_Cost"]).round(2)
    df["Normalized_Unit_Cost"] = df["Normalized_Unit_Cost"].round(2)

    # ---------- recompute priority CLASS from the NORMALIZED score (Fix Group B) ----------
    # Same positional thresholds as the original class (Top 10/20/30/rest).
    ranked = df.sort_values("Normalized_Procurement_Priority_Score",
                            ascending=False).reset_index(drop=True)
    n = len(ranked)
    ranked["Normalized_Procurement_Priority_Class"] = [
        opt.priority_class_for_position(i, n) for i in range(n)]
    df = df.merge(ranked[["PL_Code", "Normalized_Procurement_Priority_Class"]],
                  on="PL_Code", how="left")

    # ---------- append normalized cols to the policy CSV (originals kept) ----------
    policy_csv = pd.read_csv(cfg.INVENTORY_POLICY_CSV, dtype={"PL_Code": str})
    append_cols = ["Potential_Unit_Mismatch", "Normalized_Unit_Cost",
                   "Normalized_Investment_Required", "Normalized_Procurement_Priority_Score",
                   "Normalized_Procurement_Priority_Class"]
    policy_csv = policy_csv.merge(df[["PL_Code"] + append_cols], on="PL_Code", how="left")
    if write:
        policy_csv.to_csv(cfg.INVENTORY_POLICY_CSV, index=False)

        # ---------- audit trail ----------
        audit = df[["PL_Code", "Description", "Unit", "UDM_Text", "Unit_Cost",
                    "Normalized_Unit_Cost", "Potential_Unit_Mismatch",
                    "_Inventory_Value", "Normalized_Inventory_Value",
                    "Inventory_Investment_Required", "Normalized_Investment_Required",
                    "Procurement_Priority_Score", "Normalized_Procurement_Priority_Score"]] \
            .rename(columns={"_Inventory_Value": "Inventory_Value"})
        audit.to_csv(cfg.OUTPUT_DIR / "railway_data_quality.csv", index=False)

    return df


# ----------------------------------------------------------------------
# Concentration helpers
# ----------------------------------------------------------------------
def _concentration(value_series, top=10):
    s = value_series.sort_values(ascending=False)
    total = float(s.sum())
    return (float(s.head(top).sum()) / total * 100.0) if total > 0 else 0.0


def _level(pct):
    return "Low" if pct < 40 else ("Medium" if pct < 70 else "High")


# ----------------------------------------------------------------------
# Power BI Data Quality page
# ----------------------------------------------------------------------
def write_powerbi_page(df: pd.DataFrame, orig_conc, norm_conc, orig_inv, norm_inv):
    cfg.ensure_output_dirs()
    kpis = pd.DataFrame([
        {"KPI": "Flagged SKUs", "Value": int((df["Potential_Unit_Mismatch"] == "Yes").sum())},
        {"KPI": "Original Investment Required (Rs)", "Value": round(orig_inv, 2)},
        {"KPI": "Normalized Investment Required (Rs)", "Value": round(norm_inv, 2)},
        {"KPI": "Original Concentration Index (%)", "Value": round(orig_conc, 2)},
        {"KPI": "Normalized Concentration Index (%)", "Value": round(norm_conc, 2)},
    ])
    kpis.to_csv(cfg.POWERBI_DIR / "page6_data_quality.csv", index=False)


# ----------------------------------------------------------------------
# Validation + re-run
# ----------------------------------------------------------------------
def run():
    df = build_quality_layer(write=True)

    flagged = df[df["Potential_Unit_Mismatch"] == "Yes"]
    orig_conc = _concentration(df["_Inventory_Value"])
    norm_conc = _concentration(df["Normalized_Inventory_Value"])
    orig_inv = float(df["Inventory_Investment_Required"].sum())
    norm_inv = float(df["Normalized_Investment_Required"].sum())
    write_powerbi_page(df, orig_conc, norm_conc, orig_inv, norm_inv)

    print("=" * 80)
    print("DATA QUALITY NORMALIZATION LAYER -- validation")
    print("=" * 80)
    print(f"Flagged SKUs (Potential_Unit_Mismatch = Yes): {len(flagged)}")
    print(flagged[["PL_Code", "Description", "Unit", "Unit_Cost",
                   "Normalized_Unit_Cost"]].to_string(index=False))

    print("\n--- Concentration Index (Top 10 SKUs / Total Inventory Value) ---")
    print(f"   Original   : {orig_conc:5.1f}%  -> {_level(orig_conc)}")
    print(f"   Normalized : {norm_conc:5.1f}%  -> {_level(norm_conc)}")

    print("\n--- Total Investment Required ---")
    print(f"   Original   : Rs {orig_inv:,.0f}")
    print(f"   Normalized : Rs {norm_inv:,.0f}")

    # re-run Step-5 validation gate on the (now extended) policy CSV
    pol = pd.read_csv(cfg.INVENTORY_POLICY_CSV, dtype={"PL_Code": str})
    gate = {
        "no_negative_safety_stock": bool((pol["Safety_Stock"] >= 0).all()),
        "no_negative_rop": bool((pol["ROP"] >= 0).all()),
        "no_duplicate_pl": bool(pol["PL_Code"].is_unique),
        "no_nan_normalized_investment": bool(pol["Normalized_Investment_Required"].notna().all()),
        "no_negative_normalized_priority": bool((pol["Normalized_Procurement_Priority_Score"] >= 0).all()),
        "originals_preserved": all(c in pol.columns for c in
                                   ["Inventory_Investment_Required", "Procurement_Priority_Score"]),
        "four_columns_appended": all(c in pol.columns for c in
                                     ["Potential_Unit_Mismatch", "Normalized_Unit_Cost",
                                      "Normalized_Investment_Required",
                                      "Normalized_Procurement_Priority_Score"]),
    }
    print("\n--- Re-run Step 5 validation gate (with normalized fields) ---")
    for k, v in gate.items():
        print(f"   {k:32s}: {v}")
    print(f"   ALL PASS: {all(gate.values())}")

    # re-ranked Top 20 by Normalized_Procurement_Priority_Score
    print("\n--- Updated Top 20 Procurement Items (by Normalized_Procurement_Priority_Score) ---")
    show = df[df["Inventory_Status"] == "Procurement Required"] \
        .sort_values("Normalized_Procurement_Priority_Score", ascending=False).head(20)
    cols = ["PL_Code", "Description", "ABC_Class", "Criticality", "Current_Stock",
            "Inventory_Gap", "Normalized_Investment_Required",
            "Normalized_Procurement_Priority_Score", "Potential_Unit_Mismatch"]
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(show[cols].to_string(index=False))

    print(f"\nWrote: {cfg.INVENTORY_POLICY_CSV} (4 columns appended)")
    print(f"Wrote: {cfg.OUTPUT_DIR / 'railway_data_quality.csv'} (audit trail)")
    print(f"Wrote: {cfg.POWERBI_DIR / 'page6_data_quality.csv'} (Power BI Data Quality page)")
    return df, gate


if __name__ == "__main__":
    run()
