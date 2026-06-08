# STEP 22 — Demand Analytics & Forecast-Method Selection: Implementation Report

**Type:** Additive analytics. **No forecasting, SRRS, procurement, optimization, Power BI, KPI or existing-output logic changed. No forecasting model executed.**
**Date:** 2026-06-08
**Scope:** MAS division (the only division with reconstructed monthly history).

---

## 1. Objective
Use the STEP21A 54-month demand history to classify every PL Code by demand behaviour (Syntetos–Boylan) and assign a forecasting method — analytics + assignment only, no model runs.

## 2. Inputs
`outputs/MAS/history/monthly_demand_history.csv` (39,148 rows · 1,083 PLs · 54 continuous months, Jan 2022–Jun 2026).

## 3. Module added (additive)
`railway/railway_demand_classification.py` — reads the monthly history, computes per-PL demand metrics, applies the SBC matrix + XYZ + method assignment, writes three new CSVs. **No existing module modified.** Cutoffs reused read-only from `railway_config` (`ADI_CUTOFF=1.32`, `CV2_CUTOFF=0.49`).

## 4. Methodology (as agreed)

Per PL, over its gap-filled monthly `Issues_Qty` series (first-observed → 2026-06):

| Metric | Definition |
|--------|------------|
| Active Months / Months_Observed | length of the PL's continuous monthly span |
| Months With / Without Demand | count of months with `Issues_Qty` > 0 / = 0 |
| Mean Monthly Demand | mean of `Issues_Qty` (full series) |
| Demand Variance / Std Deviation | sample variance / std (full series) |
| CV | std/mean (full series) → **XYZ** |
| **CV²** | (std/mean)² of the **non-zero** demand sizes (population variance) → **SBC** |
| **ADI** | Months_Observed / Months_With_Demand |
| Intermittency % | Months_Without_Demand / Months_Observed × 100 |

**Syntetos–Boylan matrix:** Dead (no positive demand) · Smooth (ADI<1.32, CV²<0.49) · Erratic (ADI<1.32, CV²≥0.49) · Intermittent (ADI≥1.32, CV²<0.49) · Lumpy (ADI≥1.32, CV²≥0.49).

**Forecast-method assignment (STEP22 spec):** Smooth→SES/Holt · Erratic→Croston · Intermittent→SBA · Lumpy→TSB · Dead→No Forecast.
> This mapping intentionally differs from the existing engine's `RECO_BY_CLASS`; STEP22 produces a *new* monthly-based assignment for a future STEP23. `railway_forecasting.py` is untouched.

**XYZ (full-series CV):** X ≤ 0.5 · Y ≤ 1.0 · Z > 1.0 · Dead → N/A.

## 5. Outputs (new, `outputs/MAS/history/`)

| File | Rows | Columns |
|------|-----:|---------|
| `demand_classification.csv` | 1,083 | PL_Code, Description, Active_Months, Months_With_Demand, Months_Without_Demand, Mean_Monthly_Demand, Demand_Variance, Std_Deviation, CV, CV2, ADI, Intermittency_Pct, Demand_Class |
| `xyz_classification.csv` | 1,083 | PL_Code, Description, Mean_Monthly_Demand, Std_Deviation, CV, XYZ_Class |
| `forecast_method_assignment.csv` | 1,083 | PL_Code, Description, Demand_Class, XYZ_Class, Forecast_Method |

## 6. Headline results

| Demand Class | PLs | % PLs | Demand volume | % volume | Method |
|--------------|----:|------:|--------------:|---------:|--------|
| Intermittent | 654 | 60.4% | 75,747 | 2.8% | SBA |
| Lumpy | 276 | 25.5% | 1,192,630 | 43.7% | TSB |
| Dead | 122 | 11.3% | 0 | 0.0% | No Forecast |
| Erratic | 26 | 2.4% | 1,204,210 | 44.1% | Croston |
| Smooth | 5 | 0.5% | 255,097 | 9.4% | SES/Holt |

**XYZ:** Z 950 · Y 10 · X 1 · N/A 122. **Forecastable (non-Dead): 961** (769 with ≥24 months).

## 7. Data-quality note
One PL_Code is the literal string **`NA`** (uncoded transactions in the DMTR; 47 months, **0 issues** → classified **Dead/No Forecast**). It is preserved for completeness (read with `keep_default_na=False`) but flagged as non-genuine — exclude from planning. No other anomalies.

## 8. Files
| Path | Action |
|------|--------|
| `railway/railway_demand_classification.py` | new module |
| `railway/outputs/MAS/history/{demand_classification,xyz_classification,forecast_method_assignment}.csv` | new outputs |
| `_step22_run.py` | one-off driver (backward-compat + validation), retained |
| all existing outputs (498 files) | **untouched (SHA-256 verified)** |

See `STEP22_VALIDATION_REPORT.md` and `STEP22_DEMAND_ANALYTICS_REPORT.md`.
