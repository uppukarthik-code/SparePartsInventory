"""
railway_classification.py
=========================
Strategic-domain classification engine. Consumes the Step-2 demand history
(railways.xlsx) and the Safety/Vital flag, and produces railway_sku_master.csv
with every dimension Power BI needs pre-computed (no recomputation downstream):

  * ABC               -> Annual_Issue_Value (AAC x Unit_Cost), ABC_Class, ABC_Rank
  * Criticality       -> Criticality (S1..S4), Criticality_Weight (10/5/2/1), Safety_Flag
  * Coverage KPI      -> Inventory_Coverage_Ratio, Coverage_Class
  * Demand pattern    -> Demand_Class, ADI, CV2   (Syntetos-Boylan / ADI-CV^2)
  * Valuation         -> Inventory_Value (Current_Stock x Unit_Cost)

All thresholds/mappings come from railway_config (single source of truth).
Reuses the repository's ADI/CV^2 demand-typing framework (notebook 04) adapted
to the 5 annual observations available for railway items.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway import railway_data_preparation as dp

# Final column order for railway_sku_master.csv (locked spec, Step-3 refinement)
SKU_MASTER_FIELDS = [
    "PL_Code", "Description",
    "ABC_Class", "ABC_Rank",
    "Annual_Issue_Value",
    "Criticality", "Criticality_Weight",
    "Safety_Flag",
    "Demand_Class", "ADI", "CV2",
    "Inventory_Coverage_Ratio", "Coverage_Class",
    "Current_Stock", "Pending_Supply",
    "AAC", "EAR_Qty",
    "Unit_Cost", "Inventory_Value",
]


# ----------------------------------------------------------------------
# Demand pattern (ADI / CV^2 -- Syntetos-Boylan)
# ----------------------------------------------------------------------
def compute_demand_metrics(series) -> tuple[float, float, str]:
    """Return (ADI, CV2, Demand_Class) for an annual consumption series.

    ADI  = n_periods / n_positive_periods   (avg interval between demands)
    CV2  = (std/mean)^2 of the *non-zero* demand sizes
    Class (Syntetos-Boylan):
        Dead         : no positive demand in any period
        Smooth       : ADI <  1.32 and CV2 <  0.49
        Erratic      : ADI <  1.32 and CV2 >= 0.49
        Intermittent : ADI >= 1.32 and CV2 <  0.49
        Lumpy        : ADI >= 1.32 and CV2 >= 0.49
    """
    vals = np.array([0.0 if (v is None or pd.isna(v)) else float(v) for v in series])
    n = len(vals)
    nz = vals[vals > 0]
    if nz.size == 0:
        return (np.nan, np.nan, "Dead")

    adi = n / nz.size
    mean = nz.mean()
    # population variance of non-zero demand sizes
    cv2 = float(((nz - mean) ** 2).mean() / (mean ** 2)) if mean > 0 else 0.0

    if adi < cfg.ADI_CUTOFF and cv2 < cfg.CV2_CUTOFF:
        cls = "Smooth"
    elif adi < cfg.ADI_CUTOFF and cv2 >= cfg.CV2_CUTOFF:
        cls = "Erratic"
    elif adi >= cfg.ADI_CUTOFF and cv2 < cfg.CV2_CUTOFF:
        cls = "Intermittent"
    else:
        cls = "Lumpy"
    return (round(adi, 4), round(cv2, 4), cls)


# ----------------------------------------------------------------------
# Coverage KPI
# ----------------------------------------------------------------------
def compute_coverage(current_stock, pending_supply, ear_qty):
    """Inventory_Coverage_Ratio = (Current_Stock + Pending_Supply) / EAR_Qty."""
    cs = 0.0 if pd.isna(current_stock) else float(current_stock)
    ps = 0.0 if pd.isna(pending_supply) else float(pending_supply)
    if ear_qty is None or pd.isna(ear_qty) or float(ear_qty) <= 0:
        # EAR undefined: ratio meaningless. If anything on hand/incoming -> excess.
        ratio = np.inf if (cs + ps) > 0 else np.nan
    else:
        ratio = (cs + ps) / float(ear_qty)
    cov_class = cfg.classify_coverage(ratio) if not pd.isna(ratio) else "Unknown"
    ratio_out = round(ratio, 4) if np.isfinite(ratio) else (np.inf if ratio == np.inf else np.nan)
    return ratio_out, cov_class


# ----------------------------------------------------------------------
# Main build
# ----------------------------------------------------------------------
def build_sku_master(write: bool = True) -> pd.DataFrame:
    """Assemble railway_sku_master.csv from demand history + Safety/Vital flag."""
    hist = dp.build_demand_history(write=False)
    safety = dp.load_safety_vital().set_index("PL_Code")["Safety_Vital"].to_dict()

    rows = []
    for _, r in hist.iterrows():
        aac = r["AAC"]
        unit_cost = r["Unit_Cost"]
        ear = r["EAR_Qty"]

        # --- ABC (consumption-based) ---
        aiv = (0.0 if pd.isna(aac) else float(aac)) * (0.0 if pd.isna(unit_cost) else float(unit_cost))
        abc = cfg.classify_abc(aiv)

        # --- Criticality from Safety/Vital ---
        raw_flag = safety.get(r["PL_Code"])
        crit = cfg.map_criticality(raw_flag)
        crit_weight = cfg.CRITICALITY_STOCKOUT_WEIGHT[crit]
        safety_flag = "Yes" if (raw_flag in cfg.SAFETY_FLAG_POSITIVE) else "No"

        # --- Demand pattern ---
        adi, cv2, dclass = compute_demand_metrics([r[y] for y in cfg.CONSUMPTION_YEARS])

        # --- Coverage ---
        cov_ratio, cov_class = compute_coverage(r["Current_Stock"], r["Pending_Supply"], ear)

        # --- Valuation ---
        inv_value = (0.0 if pd.isna(r["Current_Stock"]) else float(r["Current_Stock"])) * \
                    (0.0 if pd.isna(unit_cost) else float(unit_cost))

        rows.append({
            "PL_Code": r["PL_Code"],
            "Description": r["Description"],
            "ABC_Class": abc,
            "Annual_Issue_Value": round(aiv, 2),
            "Criticality": crit,
            "Criticality_Weight": crit_weight,
            "Safety_Flag": safety_flag,
            "Demand_Class": dclass,
            "ADI": adi,
            "CV2": cv2,
            "Inventory_Coverage_Ratio": cov_ratio,
            "Coverage_Class": cov_class,
            "Current_Stock": r["Current_Stock"],
            "Pending_Supply": r["Pending_Supply"],
            "AAC": aac,
            "EAR_Qty": ear,
            "Unit_Cost": unit_cost,
            "Inventory_Value": round(inv_value, 2),
        })

    df = pd.DataFrame(rows)
    # --- ABC_Rank: 1 = highest Annual Issue Value ---
    df["ABC_Rank"] = (df["Annual_Issue_Value"].rank(ascending=False, method="first").astype(int))
    df = df[SKU_MASTER_FIELDS].sort_values("ABC_Rank").reset_index(drop=True)

    if write:
        cfg.ensure_output_dirs()
        df.to_csv(cfg.SKU_MASTER_CSV, index=False)
    return df


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------
def validate_sku_master(df: pd.DataFrame) -> dict:
    return {
        "row_count": len(df),
        "abc_distribution": df["ABC_Class"].value_counts().reindex(cfg.ABC_ORDER, fill_value=0).to_dict(),
        "criticality_distribution": df["Criticality"].value_counts().reindex(cfg.CRITICALITY_ORDER, fill_value=0).to_dict(),
        "coverage_distribution": df["Coverage_Class"].value_counts().to_dict(),
        "demand_distribution": df["Demand_Class"].value_counts().reindex(cfg.DEMAND_CLASSES, fill_value=0).to_dict(),
        "safety_flag_yes": int((df["Safety_Flag"] == "Yes").sum()),
        "abc_rank_unique": bool(df["ABC_Rank"].is_unique),
        "total_annual_issue_value": float(df["Annual_Issue_Value"].sum()),
        "total_inventory_value": float(df["Inventory_Value"].sum()),
    }


def _print_report(rep: dict):
    print("=" * 72)
    print("STEP 3 VALIDATION REPORT  -- railway_sku_master.csv")
    print("=" * 72)
    print(f"Rows: {rep['row_count']}   ABC_Rank unique: {rep['abc_rank_unique']}")
    print(f"Total Annual Issue Value : Rs {rep['total_annual_issue_value']:,.0f}")
    print(f"Total Inventory Value    : Rs {rep['total_inventory_value']:,.0f}")
    print(f"Safety_Flag = Yes        : {rep['safety_flag_yes']}")
    print("-" * 72)
    print("ABC distribution        :", rep["abc_distribution"])
    print("Criticality distribution:", rep["criticality_distribution"])
    print("Coverage distribution   :", rep["coverage_distribution"])
    print("Demand distribution     :", rep["demand_distribution"])
    print("=" * 72)


def run():
    df = build_sku_master(write=True)
    rep = validate_sku_master(df)
    _print_report(rep)
    print(f"\nWrote: {cfg.SKU_MASTER_CSV}")
    return df, rep


if __name__ == "__main__":
    run()
