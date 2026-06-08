# STEP 23 — Forecast Generation, Validation & Forecastability: Implementation Report

**Type:** Additive. **No change to the forecasting engine logic, SRRS, procurement, inventory/budget optimization, Power BI, executive dashboards or KPIs.** Forecast generation + validation + forecastability assessment only.
**Date:** 2026-06-08 · **Scope:** MAS (only division with monthly history).

---

## 1. Objective
Generate 12-month forecasts (Jul 2026 → Jun 2027) for every forecastable MAS PL using the STEP22 method assignment (no overrides), validate via rolling-origin backtesting, and score forecastability.

## 2. Engine reuse (no new algorithms)
`railway/railway_forecast_generation.py` **imports** `railway_forecasting` and calls its existing estimators verbatim:
`SBA→sba_forecast` · `Croston→croston_forecast` · `TSB→tsb_forecast` · `Smooth→holt_forecast (SES/Holt)`. Method comes **exclusively** from `forecast_method_assignment.csv`.

## 3. Forecast profile
Croston/SBA/TSB estimate a per-period **rate** → the 12 monthly columns are the rate repeated (flat); `Forecast_2026_27 = 12 × rate`. A `Seasonality_Modeled = "No"` column is emitted (insufficient regular history for monthly seasonality). Smooth items use Holt's level.

## 4. Rolling-origin validation (authoritative)
Expanding window, **min train = 24 months, 1-step-ahead, monthly origin**, evaluated at every feasible origin (≤30 per PL). **760 of 961** PLs were backtestable (≥25 months); the rest (newer items) carry NaN error metrics and are capped at lower forecastability.

Per-PL metrics: **MAE, RMSE, MAPE** (non-zero actuals), **sMAPE** (zero-safe), **Mean_Forecast_Error** (signed units), **Bias** (MFE normalized by mean demand), **Tracking_Signal** (RSFE/MAD), plus **Forecast_CV** (RMSE/mean).

## 5. Forecastability framework (agreed accuracy-weighted blend)
`Score = 100 × (0.35·Accuracy + 0.25·Frequency + 0.15·Stability + 0.15·History + 0.10·Bias-control)`
where Accuracy = 1−sMAPE/200, Frequency = 1−intermittency, Stability = 1−min(CV/2,1), History = min(months/36,1), Bias-control = 1−min(|TS|/4,1). Unbacktested items take an accuracy/bias penalty and are capped at **Low**.

**Classes & routing:** High ≥70 → *Forecast-driven* · Medium 50–69 → *Forecast-assisted* · Low 30–49 → *Policy-driven* · Very Low <30 → *Risk-driven*.

## 6. Outputs (new, `outputs/MAS/history/`)

| File | Rows | Notes |
|------|-----:|-------|
| `forecast_results.csv` | 961 | required schema + trailing `Seasonality_Modeled` |
| `forecast_accuracy.csv` | 961 | required schema + trailing special-analysis cols (Forecast_Volume, Forecast_CV, Demand_Intermittency, Forecast_Confidence, Planning_Strategy, Backtest_Origins) |
| `forecast_method_results.csv` | 961 | PL_Code, Demand_Pattern, XYZ_Class, Forecast_Method, Forecastability_Class |
| `forecast_summary.csv` | 4 | per method: PL_Count, Forecast_Volume, Mean_MAE, Mean_Bias, Forecastability_Distribution |

(Required columns appear first and unchanged; extra columns are additive and trailing.)

## 7. Headline results

| Method | PLs | 12-mo volume | Mean MAE |
|--------|----:|-------------:|---------:|
| SBA | 654 | 171,157 | 10.3 |
| TSB | 276 | 382,353 | 116.4 |
| Croston | 26 | 275,115 | 845.1 |
| SES/Holt | 5 | 53,127 | 854.8 |
| **Total** | **961** | **881,752** | — |

Forecastability: **High 2 · Medium 40 · Low 90 · Very Low 829.** 122 Dead excluded.

## 8. Determinism & known caveats
- Engines use fixed α/β (0.1), no randomness → forecasts and errors **fully reproducible** (verified byte-identical on re-run).
- **Positive forecast bias** (Croston-family over-forecast on intermittent demand; SBA partially corrects). The summary `Mean_Bias` (mean of per-PL *normalized* bias) is inflated by near-zero-demand items — directional, not magnitude-precise; see Forecastability report §10.
- Criticality coverage is limited: most DMTR PLs are not in the strategic criticality master (different key universe).

## 9. Files
| Path | Action |
|------|--------|
| `railway/railway_forecast_generation.py` | new module (imports existing engine) |
| `railway/outputs/MAS/history/forecast_*.csv` (4) | new outputs |
| `_step23_run.py` | one-off SHA-256 + validation driver, retained |
| all existing outputs (501 files) | **untouched (SHA-256 verified)** |

See `STEP23_VALIDATION_REPORT.md` and `STEP23_FORECASTABILITY_REPORT.md`.
