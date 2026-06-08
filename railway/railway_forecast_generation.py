"""
railway_forecast_generation.py
==============================
STEP 23 -- Automated Forecast Generation, Rolling-Origin Validation &
Forecastability Assessment (ADDITIVE; reuses the existing forecasting engine).

For every FORECASTABLE MAS PL (non-Dead) this module:
  * generates a 12-month forecast (Jul 2026 -> Jun 2027) using the method assigned
    in STEP22 (forecast_method_assignment.csv) -- NO manual override;
  * measures accuracy via expanding-window rolling-origin backtesting
    (min train 24 months, 1-step-ahead, monthly origin);
  * derives a Forecastability_Score / Class and a planning-strategy routing.

NO new forecasting algorithm is introduced: the point estimators are imported
verbatim from railway_forecasting (croston/sba/tsb/holt). NOTHING existing is
modified -- all four outputs are NEW files under outputs/MAS/history/.

Intermittent estimators (Croston/SBA/TSB) produce a per-period RATE, so the
12-month profile is flat (rate repeated); a Seasonality_Modeled='No' flag is
emitted for transparency (insufficient regular history for monthly seasonality).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway import railway_forecasting as fc          # REUSE existing engine
from railway.governance import config as gcfg          # centralized config (Phase B)

BUSINESS_UNIT = gcfg.DIVISION
HISTORY_DIR = gcfg.HISTORY_DIR
MIN_TRAIN = 24                                          # rolling-origin min window

HORIZON = gcfg.HORIZON

ROUTING = {"High": "Forecast-driven", "Medium": "Forecast-assisted",
           "Low": "Policy-driven", "Very Low": "Risk-driven"}


# ----------------------------------------------------------------------
# point forecast -- assigned method only (reuse existing functions)
# ----------------------------------------------------------------------
def point_forecast(method: str, series) -> float:
    s = list(series)
    if method == "SBA":
        return max(fc._last(fc.sba_forecast(s)), 0.0)
    if method == "Croston":
        return max(fc._last(fc.croston_forecast(s)), 0.0)
    if method == "TSB":
        return max(fc._last(fc.tsb_forecast(s)), 0.0)
    if method == "SES/Holt":
        return max(fc.holt_forecast(s), 0.0)
    return 0.0                                           # No Forecast / Dead


# ----------------------------------------------------------------------
# rolling-origin backtest (expanding window, 1-step-ahead)
# ----------------------------------------------------------------------
def backtest(method: str, series) -> list:
    n = len(series)
    pairs = []
    for t in range(MIN_TRAIN, n):                        # train series[:t] -> predict series[t]
        pred = point_forecast(method, series[:t])
        pairs.append((pred, float(series[t])))
    return pairs


def error_metrics(pairs) -> dict:
    if not pairs:
        return {k: np.nan for k in ("MAE", "RMSE", "MAPE", "sMAPE", "Bias",
                                    "Mean_Forecast_Error", "Tracking_Signal",
                                    "Forecast_CV", "n_origins")} | {"n_origins": 0}
    pred = np.array([p for p, _ in pairs], float)
    act = np.array([a for _, a in pairs], float)
    err = pred - act
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mfe = float(np.mean(err))
    nz = act > 0
    mape = float(np.mean(np.abs(err[nz]) / act[nz]) * 100) if nz.any() else np.nan
    denom = (np.abs(pred) + np.abs(act)) / 2.0
    smape_terms = np.where(denom == 0, 0.0, np.abs(err) / np.where(denom == 0, 1, denom))
    smape = float(np.mean(smape_terms) * 100)
    rsfe = float(np.sum(err))
    ts = (rsfe / mae) if mae > 0 else 0.0
    mean_act = float(np.mean(act))
    bias = (mfe / mean_act) if mean_act > 0 else 0.0     # normalized signed bias
    fcv = (rmse / mean_act) if mean_act > 0 else np.nan  # forecast-error CV
    return {"MAE": round(mae, 4), "RMSE": round(rmse, 4),
            "MAPE": (round(mape, 2) if not np.isnan(mape) else np.nan),
            "sMAPE": round(smape, 2), "Bias": round(bias, 4),
            "Mean_Forecast_Error": round(mfe, 4),
            "Tracking_Signal": round(ts, 4),
            "Forecast_CV": (round(fcv, 4) if not np.isnan(fcv) else np.nan),
            "n_origins": len(pairs)}


# ----------------------------------------------------------------------
# forecastability score (accuracy-weighted blend; agreed STEP23)
# ----------------------------------------------------------------------
def forecastability(m, intermittency_pct, cv, active_months, backtested) -> tuple:
    freq = max(0.0, 1.0 - intermittency_pct / 100.0)            # demand frequency
    stab = (1.0 - min((cv if not (cv is None or np.isnan(cv)) else 2.0) / 2.0, 1.0))
    hist = min(active_months / 36.0, 1.0)
    if backtested:
        acc = 1.0 - min((m["sMAPE"] if not np.isnan(m["sMAPE"]) else 200) / 200.0, 1.0)
        bias_ctrl = 1.0 - min(abs(m["Tracking_Signal"]) / 4.0, 1.0)
    else:
        acc, bias_ctrl = 0.30, 0.30                             # validation penalty
    score = 100.0 * (0.35 * acc + 0.25 * freq + 0.15 * stab + 0.15 * hist + 0.10 * bias_ctrl)
    score = round(score, 2)
    if score >= 70:
        cls = "High"
    elif score >= 50:
        cls = "Medium"
    elif score >= 30:
        cls = "Low"
    else:
        cls = "Very Low"
    if not backtested and cls in ("High", "Medium"):            # cap unvalidated items
        cls = "Low"
    return score, cls


# ----------------------------------------------------------------------
# build
# ----------------------------------------------------------------------
def _load():
    hist = pd.read_csv(HISTORY_DIR / "monthly_demand_history.csv",
                       dtype={"PL_Code": str, "Description": str}, keep_default_na=False)
    hist["Issues_Qty"] = pd.to_numeric(hist["Issues_Qty"], errors="coerce").fillna(0.0)
    assign = pd.read_csv(HISTORY_DIR / "forecast_method_assignment.csv",
                         dtype={"PL_Code": str}, keep_default_na=False)
    clas = pd.read_csv(HISTORY_DIR / "demand_classification.csv",
                       dtype={"PL_Code": str}, keep_default_na=False)
    return hist, assign, clas


def build(write: bool = True):
    hist, assign, clas = _load()
    series_by_pl = {pl: g.sort_values("Month")["Issues_Qty"].to_numpy(float)
                    for pl, g in hist.groupby("PL_Code")}
    cl = clas.set_index("PL_Code")
    am = assign.set_index("PL_Code")

    res_rows, acc_rows = [], []
    for _, a in assign.iterrows():
        pl = a["PL_Code"]
        method = a["Forecast_Method"]
        pattern = a["Demand_Class"]
        xyz = a["XYZ_Class"]
        if method == "No Forecast":                      # Dead -> excluded
            continue
        series = series_by_pl[pl]
        ci = cl.loc[pl]
        intermittency = float(ci["Intermittency_Pct"])
        cv = float(ci["CV"]) if str(ci["CV"]) not in ("", "nan") else np.nan
        cv2 = float(ci["CV2"]) if str(ci["CV2"]) not in ("", "nan") else 0.0
        active_months = int(ci["Active_Months"])

        rate = point_forecast(method, series)
        monthly = round(rate, 4)
        annual = round(rate * 12.0, 4)

        pairs = backtest(method, list(series))
        backtested = len(pairs) > 0
        m = error_metrics(pairs)
        score, fclass = forecastability(m, intermittency, cv, active_months, backtested)
        confidence = fc.forecast_confidence(pattern, cv2)

        row = {"PL_Code": pl, "Description": a["Description"],
               "Demand_Pattern": pattern, "XYZ_Class": xyz, "Forecast_Method": method,
               "Forecast_2026_27": annual}
        for mo in HORIZON:
            row[f"Forecast_{mo}"] = monthly
        row["Seasonality_Modeled"] = "No"
        res_rows.append(row)

        acc_rows.append({
            "PL_Code": pl, "Forecast_Method": method,
            "MAE": m["MAE"], "RMSE": m["RMSE"], "MAPE": m["MAPE"], "sMAPE": m["sMAPE"],
            "Bias": m["Bias"], "Mean_Forecast_Error": m["Mean_Forecast_Error"],
            "Tracking_Signal": m["Tracking_Signal"],
            "Forecastability_Score": score, "Forecastability_Class": fclass,
            # --- additive special-analysis columns (after required schema) ---
            "Forecast_Volume": annual, "Forecast_CV": m["Forecast_CV"],
            "Demand_Intermittency": round(intermittency, 2),
            "Forecast_Confidence": confidence,
            "Planning_Strategy": ROUTING[fclass],
            "Backtest_Origins": m["n_origins"],
        })

    results = pd.DataFrame(res_rows)
    accuracy = pd.DataFrame(acc_rows)

    res_cols = (["PL_Code", "Description", "Demand_Pattern", "XYZ_Class",
                 "Forecast_Method", "Forecast_2026_27"]
                + [f"Forecast_{mo}" for mo in HORIZON] + ["Seasonality_Modeled"])
    results = results[res_cols].sort_values("PL_Code").reset_index(drop=True)

    acc_cols = ["PL_Code", "Forecast_Method", "MAE", "RMSE", "MAPE", "sMAPE", "Bias",
                "Mean_Forecast_Error", "Tracking_Signal", "Forecastability_Score",
                "Forecastability_Class", "Forecast_Volume", "Forecast_CV",
                "Demand_Intermittency", "Forecast_Confidence", "Planning_Strategy",
                "Backtest_Origins"]
    accuracy = accuracy[acc_cols].sort_values("PL_Code").reset_index(drop=True)

    method_results = accuracy.merge(
        results[["PL_Code", "Demand_Pattern", "XYZ_Class"]], on="PL_Code")[
        ["PL_Code", "Demand_Pattern", "XYZ_Class", "Forecast_Method",
         "Forecastability_Class"]].sort_values("PL_Code").reset_index(drop=True)

    # summary per method
    srows = []
    for method, g in accuracy.groupby("Forecast_Method"):
        dist = g["Forecastability_Class"].value_counts().to_dict()
        dist_str = ";".join(f"{k}:{dist.get(k,0)}" for k in ["High", "Medium", "Low", "Very Low"])
        srows.append({
            "Forecast_Method": method, "PL_Count": len(g),
            "Forecast_Volume": round(g["Forecast_Volume"].sum(), 2),
            "Mean_MAE": round(g["MAE"].mean(skipna=True), 4),
            "Mean_Bias": round(g["Bias"].mean(skipna=True), 4),
            "Forecastability_Distribution": dist_str,
        })
    summary = pd.DataFrame(srows).sort_values("PL_Count", ascending=False).reset_index(drop=True)

    if write:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        results.to_csv(HISTORY_DIR / "forecast_results.csv", index=False)
        accuracy.to_csv(HISTORY_DIR / "forecast_accuracy.csv", index=False)
        method_results.to_csv(HISTORY_DIR / "forecast_method_results.csv", index=False)
        summary.to_csv(HISTORY_DIR / "forecast_summary.csv", index=False)
    return {"results": results, "accuracy": accuracy,
            "method_results": method_results, "summary": summary}


def run():
    art = build(write=True)
    a = art["accuracy"]
    print("STEP 23 -- forecast generation + rolling-origin validation (MAS)")
    print(f"  forecastable PLs        : {len(art['results'])}")
    print(f"  method distribution     : {art['results']['Forecast_Method'].value_counts().to_dict()}")
    print(f"  forecastability dist    : {a['Forecastability_Class'].value_counts().to_dict()}")
    print(f"  backtested PLs          : {int((a['Backtest_Origins']>0).sum())}")
    print(f"  total forecast volume   : {art['results']['Forecast_2026_27'].sum():,.0f}")
    print(f"  -> {HISTORY_DIR}")
    return art


if __name__ == "__main__":
    run()
