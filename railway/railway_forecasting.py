"""
railway_forecasting.py
======================
Railway demand forecasting for INVENTORY PLANNING (not statistical research).
Priorities: stability > explainability > inventory usefulness > robustness.

PRIMARY ENGINE  (official forecast -- always used downstream):
    Forecast_2026_27 = 0.40*AAC + 0.30*EAR_Qty + 0.20*MA + 0.10*CAGR
    Stored components: AAC_Forecast, EAR_Forecast, MA_Forecast, CAGR_Forecast

SECONDARY BENCHMARK ENGINE  (report only, never overrides primary):
    Croston, SBA, TSB  -> reused VERBATIM from notebooks/04_demand_forecasting.ipynb
    Holt               -> statsmodels, with safe fallback

DEMAND-CLASS DRIVEN RECOMMENDATION:
    Smooth->Weighted Blend, Intermittent->Croston, Erratic->SBA,
    Lumpy->TSB, Dead->Zero Forecast

Plus planning KPIs: Forecast_Confidence, Forecast_to_Stock_Ratio/Class, and a
4->1 hold-out backtest (MAE/MAPE/Bias) on the Recommended_Model.

Output: railway/outputs/railway_forecast.csv
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway import railway_data_preparation as dp
from railway import railway_classification as rc

# Primary blend weights (locked) -- centralized in railway_config
BLEND_WEIGHTS = cfg.FORECAST_BLEND_WEIGHTS

FORECAST_FIELDS = [
    "PL_Code", "Description",
    "Demand_Class",
    "AAC_Forecast", "EAR_Forecast", "MA_Forecast", "CAGR_Forecast",
    "Forecast_2026_27",
    "Croston_Forecast", "SBA_Forecast", "TSB_Forecast", "Holt_Forecast",
    "Recommended_Model", "Recommended_Forecast",
    "Forecast_Confidence",
    "Forecast_to_Stock_Ratio", "Forecast_to_Stock_Class",
    "MAE", "MAPE", "Bias",
]


# ======================================================================
# Reused VERBATIM from notebooks/04_demand_forecasting.ipynb
# ======================================================================
def croston_forecast(demand, alpha=0.1):
    demand = np.array(demand, dtype=float)
    n = len(demand)
    z = 0; p = 0; q = 1; first = True
    forecast = np.zeros(n)
    for t in range(n):
        if demand[t] > 0:
            if first:
                z = demand[t]; p = q; first = False
            else:
                z = alpha * demand[t] + (1 - alpha) * z
                p = alpha * q + (1 - alpha) * p
            q = 1
        else:
            q += 1
        forecast[t] = z / p if p > 0 else 0
    return forecast


def sba_forecast(demand, alpha=0.1):
    return 0.95 * croston_forecast(demand, alpha)


def tsb_forecast(demand, alpha=0.1, beta=0.1):
    demand = np.array(demand, dtype=float)
    n = len(demand)
    z = 0; p = 0; first = True
    forecast = np.zeros(n)
    for t in range(n):
        if demand[t] > 0:
            if first:
                z = demand[t]; p = 1; first = False
            else:
                z = alpha * demand[t] + (1 - alpha) * z
                p = beta + (1 - beta) * p
        else:
            p = (1 - beta) * p
        forecast[t] = z * p
    return forecast


def _last(arr):
    """Steady-state point forecast = last value of an intermittent-model series."""
    arr = np.asarray(arr, dtype=float)
    return float(arr[-1]) if arr.size else 0.0


def holt_forecast(series):
    """Holt linear trend (statsmodels) with safe fallback to the mean.

    Adapted for very short railway series (4-5 annual points). On any failure
    or degenerate input, falls back to the series mean for stability.
    """
    s = np.asarray(series, dtype=float)
    if s.size < 3 or np.allclose(s, 0):
        return float(np.nanmean(s)) if s.size else 0.0
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = ExponentialSmoothing(s, trend="add",
                                       initialization_method="estimated").fit()
            return max(float(fit.forecast(1)[0]), 0.0)
    except Exception:
        return float(np.nanmean(s))


# ======================================================================
# Primary engine helpers
# ======================================================================
def _safe(x):
    return 0.0 if (x is None or pd.isna(x)) else float(x)


def ma_forecast(series):
    s = np.array([_safe(v) for v in series], dtype=float)
    return float(s.mean()) if s.size else 0.0


def cagr_forecast(series):
    """Project one period ahead via CAGR; stable fallback to MA when undefined."""
    s = [_safe(v) for v in series]
    if len(s) < 2:
        return ma_forecast(series)
    first, last, periods = s[0], s[-1], len(s) - 1
    if first > 0 and last > 0:
        cagr = (last / first) ** (1.0 / periods) - 1.0
        return max(last * (1.0 + cagr), 0.0)
    return ma_forecast(series)          # endpoints not both positive -> MA


def weighted_blend(aac, ear, ma, cagr):
    return (BLEND_WEIGHTS["AAC"] * _safe(aac) + BLEND_WEIGHTS["EAR"] * _safe(ear)
            + BLEND_WEIGHTS["MA"] * _safe(ma) + BLEND_WEIGHTS["CAGR"] * _safe(cagr))


# ======================================================================
# Recommendation, confidence, KPI
# ======================================================================
RECO_BY_CLASS = {
    "Smooth": "Weighted Blend",
    "Intermittent": "Croston",
    "Erratic": "SBA",
    "Lumpy": "TSB",
    "Dead": "Zero Forecast",
}


def forecast_confidence(demand_class, cv2):
    if demand_class == "Smooth":
        return "High" if (cv2 is not None and not pd.isna(cv2) and cv2 < 0.25) else "Medium"
    if demand_class == "Intermittent":
        return "Medium"
    if demand_class in ("Erratic", "Lumpy"):
        return "Low"
    if demand_class == "Dead":
        return "Very Low"
    return "Medium"


def forecast_to_stock(forecast, current_stock):
    """Ratio = Forecast / Current_Stock, divide-by-zero safe."""
    cs = _safe(current_stock)
    if cs <= 0:
        ratio = np.inf if forecast > 0 else 0.0
    else:
        ratio = forecast / cs
    if ratio < 0.25:
        cls = "Excess Inventory"
    elif ratio < 1.0:
        cls = "Adequate"
    elif ratio < 2.0:
        cls = "Monitor"
    else:
        cls = "Procurement Risk"
    ratio_out = round(ratio, 4) if np.isfinite(ratio) else np.inf
    return ratio_out, cls


# ======================================================================
# Backtest  (train 4 years -> predict 2025-26)
# ======================================================================
def _metrics(pred, actual):
    err = pred - actual
    mae = abs(err)
    bias = err
    mape = (abs(err) / actual * 100.0) if actual > 0 else np.nan
    return mae, mape, bias


def backtest_all(train, actual, aac, ear):
    """Return {model: (mae, mape, bias)} for the 4->1 hold-out."""
    preds = {
        "Weighted Blend": weighted_blend(aac, ear, ma_forecast(train), cagr_forecast(train)),
        "Croston": _last(croston_forecast(train)),
        "SBA": _last(sba_forecast(train)),
        "TSB": _last(tsb_forecast(train)),
        "Holt": holt_forecast(train),
        "Zero Forecast": 0.0,
    }
    return {m: _metrics(p, actual) for m, p in preds.items()}


# ======================================================================
# Main build
# ======================================================================
def build_forecast(write: bool = True):
    hist = dp.build_demand_history(write=False)
    master = rc.build_sku_master(write=False)[["PL_Code", "Demand_Class", "CV2"]]
    df = hist.merge(master, on="PL_Code", how="left")

    rows = []
    per_model_err = {}      # model -> list of (mae,mape,bias) for validation aggregate
    for _, r in df.iterrows():
        series = [r[y] for y in cfg.CONSUMPTION_YEARS]
        train = [_safe(r[y]) for y in cfg.BACKTEST_TRAIN_YEARS]
        actual = _safe(r[cfg.BACKTEST_TEST_YEAR])
        aac, ear, cs = r["AAC"], r["EAR_Qty"], r["Current_Stock"]
        dclass = r["Demand_Class"] if pd.notna(r["Demand_Class"]) else "Smooth"
        cv2 = r["CV2"]

        # primary
        ma = ma_forecast(series)
        cagr = cagr_forecast(series)
        f2627 = weighted_blend(aac, ear, ma, cagr)

        # benchmarks
        croston = _last(croston_forecast(series))
        sba = _last(sba_forecast(series))
        tsb = _last(tsb_forecast(series))
        holt = holt_forecast(series)

        # recommendation
        reco_model = RECO_BY_CLASS.get(dclass, "Weighted Blend")
        reco_val = {"Weighted Blend": f2627, "Croston": croston, "SBA": sba,
                    "TSB": tsb, "Zero Forecast": 0.0}[reco_model]

        conf = forecast_confidence(dclass, cv2)
        fts_ratio, fts_class = forecast_to_stock(f2627, cs)

        # backtest -> store recommended model's error
        bt = backtest_all(train, actual, aac, ear)
        for m, mv in bt.items():
            per_model_err.setdefault(m, []).append(mv)
        bt_key = reco_model if reco_model in bt else "Weighted Blend"
        mae, mape, bias = bt[bt_key]

        rows.append({
            "PL_Code": r["PL_Code"], "Description": r["Description"],
            "Demand_Class": dclass,
            "AAC_Forecast": round(_safe(aac), 2), "EAR_Forecast": round(_safe(ear), 2),
            "MA_Forecast": round(ma, 2), "CAGR_Forecast": round(cagr, 2),
            "Forecast_2026_27": round(f2627, 2),
            "Croston_Forecast": round(croston, 2), "SBA_Forecast": round(sba, 2),
            "TSB_Forecast": round(tsb, 2), "Holt_Forecast": round(holt, 2),
            "Recommended_Model": reco_model, "Recommended_Forecast": round(reco_val, 2),
            "Forecast_Confidence": conf,
            "Forecast_to_Stock_Ratio": fts_ratio, "Forecast_to_Stock_Class": fts_class,
            "MAE": round(mae, 3),
            "MAPE": (round(mape, 2) if not pd.isna(mape) else np.nan),
            "Bias": round(bias, 3),
        })

    out = pd.DataFrame(rows)[FORECAST_FIELDS]
    if write:
        cfg.ensure_output_dirs()
        out.to_csv(cfg.FORECAST_CSV, index=False)
    return out, per_model_err


# ======================================================================
# Validation
# ======================================================================
def _agg_model_errors(per_model_err):
    agg = {}
    for m, vals in per_model_err.items():
        arr = np.array(vals, dtype=float)        # columns: mae, mape, bias
        agg[m] = {
            "MAE": round(np.nanmean(arr[:, 0]), 2),
            "MAPE": round(np.nanmean(arr[:, 1]), 2),
            "Bias": round(np.nanmean(arr[:, 2]), 2),
        }
    return agg


def run():
    df, per_model_err = build_forecast(write=True)
    print("=" * 72)
    print("STEP 4 VALIDATION REPORT  -- railway_forecast.csv")
    print("=" * 72)
    print(f"Rows: {len(df)}")
    print("\nRecommended_Model distribution :", df["Recommended_Model"].value_counts().to_dict())
    print("Forecast_Confidence distribution:", df["Forecast_Confidence"].value_counts().to_dict())
    print("Forecast_to_Stock_Class dist.  :", df["Forecast_to_Stock_Class"].value_counts().to_dict())

    print("\nPer-model backtest (4->1 hold-out) average MAE / MAPE / Bias:")
    for m, v in _agg_model_errors(per_model_err).items():
        print(f"   {m:16s} MAE={v['MAE']:>10}  MAPE={v['MAPE']:>8}  Bias={v['Bias']:>10}")

    cols = ["PL_Code", "Description", "Forecast_2026_27", "Current_Stock",
            "Forecast_to_Stock_Ratio", "Forecast_to_Stock_Class"]
    hist = dp.build_demand_history(write=False)[["PL_Code", "Current_Stock"]]
    show = df.merge(hist, on="PL_Code", how="left")

    risk = show[show["Forecast_to_Stock_Class"] == "Procurement Risk"] \
        .sort_values("Forecast_to_Stock_Ratio", ascending=False).head(10)
    print("\nTop 10 PROCUREMENT RISK (highest Forecast/Stock):")
    print(risk[cols].to_string(index=False))

    excess = show[show["Forecast_to_Stock_Class"] == "Excess Inventory"] \
        .sort_values("Forecast_to_Stock_Ratio", ascending=True).head(10)
    print("\nTop 10 EXCESS INVENTORY (lowest Forecast/Stock):")
    print(excess[cols].to_string(index=False))

    print(f"\nWrote: {cfg.FORECAST_CSV}")
    return df


if __name__ == "__main__":
    run()
