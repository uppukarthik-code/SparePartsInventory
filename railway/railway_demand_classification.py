"""
railway_demand_classification.py
================================
STEP 22 -- Demand Analytics & Forecast-Method Selection (ANALYTICS ONLY).

Consumes the STEP21A reconstructed monthly demand history (MAS, 54 months) and
classifies every PL Code by demand behaviour (Syntetos-Boylan), assigns an XYZ
predictability class, and recommends a forecasting method per PL.

NO forecasting model is executed here. This phase is additive: it does not modify
forecasting, SRRS, procurement, optimization, Power BI, KPI or any existing output.
It only reads outputs/MAS/history/monthly_demand_history.csv and writes three new
CSVs alongside it.

Conventions (agreed STEP22):
  * ADI   = Months_Observed / Months_With_Demand            (avg demand interval)
  * CV2   = (std/mean)^2 of the NON-ZERO monthly demand sizes  (Syntetos-Boylan;
            population variance -- identical convention to railway_classification.py)
  * CV    = std/mean of the FULL monthly series (incl. zeros) -> XYZ predictability
  * Cutoffs reused from railway_config: ADI_CUTOFF=1.32, CV2_CUTOFF=0.49

Syntetos-Boylan matrix:
  Dead         : no positive demand in any observed month
  Smooth       : ADI <  1.32 and CV2 <  0.49
  Erratic      : ADI <  1.32 and CV2 >= 0.49
  Intermittent : ADI >= 1.32 and CV2 <  0.49
  Lumpy        : ADI >= 1.32 and CV2 >= 0.49

Forecast-method assignment (STEP22 spec):
  Smooth -> SES/Holt   Erratic -> Croston   Intermittent -> SBA
  Lumpy  -> TSB        Dead -> No Forecast

XYZ (full-series CV):  X: CV<=0.5   Y: 0.5<CV<=1.0   Z: CV>1.0   (Dead -> N/A)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway.governance import config as gcfg           # centralized config (Phase B)

BUSINESS_UNIT = gcfg.DIVISION
HISTORY_DIR = gcfg.HISTORY_DIR
HISTORY_CSV = HISTORY_DIR / "monthly_demand_history.csv"

FORECAST_METHOD = {
    "Smooth": "SES/Holt",
    "Erratic": "Croston",
    "Intermittent": "SBA",
    "Lumpy": "TSB",
    "Dead": "No Forecast",
}


# ----------------------------------------------------------------------
# per-PL metrics + classification
# ----------------------------------------------------------------------
def _sbc_class(adi, cv2):
    if adi < cfg.ADI_CUTOFF and cv2 < cfg.CV2_CUTOFF:
        return "Smooth"
    if adi < cfg.ADI_CUTOFF and cv2 >= cfg.CV2_CUTOFF:
        return "Erratic"
    if adi >= cfg.ADI_CUTOFF and cv2 < cfg.CV2_CUTOFF:
        return "Intermittent"
    return "Lumpy"


def _xyz_class(cv):
    if cv is None or np.isnan(cv):
        return "N/A"
    if cv <= 0.5:
        return "X"
    if cv <= 1.0:
        return "Y"
    return "Z"


def classify_pl(issues: np.ndarray) -> dict:
    """Compute demand metrics + classes for one PL's monthly Issues series."""
    n = int(issues.size)                       # Months_Observed / Active_Months
    nz = issues[issues > 0]
    months_with = int(nz.size)
    months_without = n - months_with

    mean_full = float(issues.mean()) if n else 0.0
    var_full = float(issues.var(ddof=1)) if n > 1 else 0.0
    std_full = float(issues.std(ddof=1)) if n > 1 else 0.0
    cv_full = (std_full / mean_full) if mean_full > 0 else np.nan
    intermittency = (100.0 * months_without / n) if n else 0.0

    if months_with == 0:                       # Dead
        return {
            "Months_Observed": n, "Active_Months": n,
            "Months_With_Demand": 0, "Months_Without_Demand": months_without,
            "Mean_Monthly_Demand": 0.0, "Demand_Variance": 0.0,
            "Std_Deviation": 0.0, "CV": np.nan, "CV2": np.nan,
            "ADI": np.nan, "Intermittency_Pct": round(intermittency, 2),
            "Demand_Class": "Dead", "XYZ_Class": "N/A",
            "Forecast_Method": FORECAST_METHOD["Dead"],
        }

    adi = n / months_with
    sz_mean = float(nz.mean())
    cv2 = float(((nz - sz_mean) ** 2).mean() / (sz_mean ** 2)) if sz_mean > 0 else 0.0
    dclass = _sbc_class(adi, cv2)
    xyz = _xyz_class(cv_full)
    return {
        "Months_Observed": n, "Active_Months": n,
        "Months_With_Demand": months_with, "Months_Without_Demand": months_without,
        "Mean_Monthly_Demand": round(mean_full, 4), "Demand_Variance": round(var_full, 4),
        "Std_Deviation": round(std_full, 4),
        "CV": (round(cv_full, 4) if not np.isnan(cv_full) else np.nan),
        "CV2": round(cv2, 4), "ADI": round(adi, 4),
        "Intermittency_Pct": round(intermittency, 2),
        "Demand_Class": dclass, "XYZ_Class": xyz,
        "Forecast_Method": FORECAST_METHOD[dclass],
    }


# ----------------------------------------------------------------------
# build
# ----------------------------------------------------------------------
def build(write: bool = True):
    # keep_default_na=False so a literal PL_Code 'NA' (an uncoded-transaction item
    # present in the DMTR data) is preserved as the string "NA" and not dropped.
    hist = pd.read_csv(HISTORY_CSV, dtype={"PL_Code": str, "Description": str},
                       keep_default_na=False)
    hist["Issues_Qty"] = pd.to_numeric(hist["Issues_Qty"], errors="coerce").fillna(0.0)
    desc = hist.groupby("PL_Code")["Description"].first()

    rows = []
    for pl, g in hist.groupby("PL_Code", sort=True):
        issues = g.sort_values("Month")["Issues_Qty"].to_numpy(dtype=float)
        m = classify_pl(issues)
        m["PL_Code"] = pl
        m["Description"] = desc.loc[pl]
        rows.append(m)
    df = pd.DataFrame(rows)

    demand_cols = ["PL_Code", "Description", "Active_Months", "Months_With_Demand",
                   "Months_Without_Demand", "Mean_Monthly_Demand", "Demand_Variance",
                   "Std_Deviation", "CV", "CV2", "ADI", "Intermittency_Pct", "Demand_Class"]
    xyz_cols = ["PL_Code", "Description", "Mean_Monthly_Demand", "Std_Deviation", "CV", "XYZ_Class"]
    method_cols = ["PL_Code", "Description", "Demand_Class", "XYZ_Class", "Forecast_Method"]

    demand_df = df[demand_cols].sort_values("PL_Code").reset_index(drop=True)
    xyz_df = df[xyz_cols].sort_values("PL_Code").reset_index(drop=True)
    method_df = df[method_cols].sort_values("PL_Code").reset_index(drop=True)

    if write:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        demand_df.to_csv(HISTORY_DIR / "demand_classification.csv", index=False)
        xyz_df.to_csv(HISTORY_DIR / "xyz_classification.csv", index=False)
        method_df.to_csv(HISTORY_DIR / "forecast_method_assignment.csv", index=False)
    return {"demand": demand_df, "xyz": xyz_df, "method": method_df, "full": df}


def run():
    art = build(write=True)
    d = art["demand"]
    print("STEP 22 -- Demand analytics & forecast-method selection (MAS)")
    print(f"  PL codes classified : {len(d)}")
    print(f"  Demand pattern dist : {d['Demand_Class'].value_counts().to_dict()}")
    print(f"  XYZ distribution    : {art['xyz']['XYZ_Class'].value_counts().to_dict()}")
    print(f"  Method distribution : {art['method']['Forecast_Method'].value_counts().to_dict()}")
    print(f"  -> {HISTORY_DIR}")
    return art


if __name__ == "__main__":
    run()
