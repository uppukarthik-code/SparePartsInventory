# STEP 23 — Validation Report

**Date:** 2026-06-08 · **Subject:** MAS forecast generation + rolling-origin validation + forecastability.
**Method:** Independent re-computation, deterministic re-run, SHA-256 backward-compatibility guard.

---

## 1. Validation checklist (15 checks)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Every forecastable PL processed | ✅ PASS | 961 / 961 (1,083 − 122 Dead) |
| 2 | Every PL assigned exactly one method | ✅ PASS | unique PLs; method from assignment only; {SBA, TSB, Croston, SES/Holt} |
| 3 | Dead items excluded | ✅ PASS | 0 `No Forecast` rows in forecast_results (122 excluded) |
| 4 | No duplicate PL codes | ✅ PASS | unique in results & accuracy |
| 5 | Forecast horizon = 12 months | ✅ PASS | 12 monthly columns Jul 2026→Jun 2027 |
| 6 | Rolling-origin validation completed | ✅ PASS | 760 PLs backtested, up to 30 origins each (expanding, min-train 24, 1-step) |
| 7 | Forecast totals reproducible | ✅ PASS | byte-identical on re-run (SHA-256) |
| 8 | Forecast errors reproducible | ✅ PASS | byte-identical on re-run (SHA-256) |
| 9 | Existing forecasting engine unchanged | ✅ PASS | `railway_forecasting.py` imported, not modified |
| 10 | Existing SRRS unchanged | ✅ PASS | within unchanged 501 files |
| 11 | Existing procurement unchanged | ✅ PASS | within unchanged 501 files |
| 12 | Existing inventory optimisation unchanged | ✅ PASS | within unchanged 501 files |
| 13 | Existing Power BI unchanged | ✅ PASS | within unchanged 501 files |
| 14 | Existing KPIs unchanged | ✅ PASS | within unchanged 501 files |
| 15 | Existing outputs byte-identical | ✅ PASS | 501 files fingerprinted, **0 changed / 0 removed / 0 added** |

**All 15 checks PASS.**

## 2. Backward-compatibility (SHA-256)
```
Existing files fingerprinted (outputs/, excl. 4 new forecast CSVs) : 501
Changed : 0     Removed : 0     Added : 0     UNCHANGED : True
```
The module writes only the four new forecast files; all STEP1–22 outputs (incl. the STEP21A/22 history & classification files), forecasting engine, SRRS, procurement, optimization, enterprise, Power BI and KPI outputs are byte-for-byte identical.

## 3. Coverage & method integrity
- Forecastable processed: **961** (SBA 654, TSB 276, Croston 26, SES/Holt 5) — matches the assignment exactly.
- Dead excluded: 122. No method substitution, no manual override (method read verbatim from `forecast_method_assignment.csv`).
- Horizon: 12 monthly columns + `Forecast_2026_27` (= 12 × monthly rate).

## 4. Rolling-origin validation
- Expanding window, min train 24, 1-step-ahead, monthly origin.
- **760 PLs** had ≥25 months → backtested (max 30 origins). **201** newer PLs lacked sufficient history → NaN error metrics, capped at ≤ Low forecastability (validation penalty applied transparently).
- Errors aggregated across all origins per PL → MAE/RMSE/MAPE/sMAPE/Bias/MFE/Tracking_Signal.

## 5. Reproducibility
Deterministic estimators (fixed α/β = 0.1, no randomness, no run-time dependence). Re-running `build()` produced **byte-identical** `forecast_results.csv`, `forecast_accuracy.csv`, `forecast_method_results.csv`, `forecast_summary.csv` (SHA-256 match) → forecast totals and errors are reproducible.

## 6. Verdict
**STEP 23 validation PASSED (15/15).** 961 MAS PLs forecast and validated via rolling-origin backtesting, with reproducible results and full byte-for-byte backward compatibility. Forecast accuracy is honestly characterised (intermittent demand → high sMAPE, mild positive bias) and drives the forecastability routing in `STEP23_FORECASTABILITY_REPORT.md`.
