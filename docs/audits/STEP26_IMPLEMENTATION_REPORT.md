# STEP 26 — Division SRRS Prioritization Engine (MAS): Implementation Report

**Type:** Additive analytics. **SRRS mathematics reused verbatim; no cost injected into SRRS; no forecasting / safety-stock / ROP / procurement / enterprise logic or output modified.**
**Date:** 2026-06-08 · **Scope:** MAS.

---

## 1. Objective
Prioritise the STEP 25 shortages by **service risk** (reusing the repo's SRRS objective) and, as a **separate** lens, by **capital exposure**.

## 2. SRRS objective (reused exactly)
From `railway_inventory_optimization` (Step-15 calibrated):
```
SRRS = Criticality_Weight × Service_Factor × Positive_Gap
```
- **Service_Factor** = `opt.service_factor(SL)` reused verbatim → Critical (SL 0.95) = 2.0, Non-Critical (SL 0.85) = 1.0.
- **Positive_Gap** = `max(ROP − Current_Stock, 0)` from STEP 25 `rop_results.csv`.
- **Criticality_Weight** = the existing S1/S2/S4 values via the native STEP 23.8 Type signal: **Safety Item → 10, Vital Item → 5, NA → 1**. (Criticality_Class reported as the binary Critical/Non-Critical view.)

Demand-/Lead-Time-factors remain *excluded* from the objective (per the repo's STEP14 audit) — no change.

## 3. Value lens (separate; NOT in SRRS)
```
Reorder_Gap_Value_Rs = Positive_Gap × Average_Rate_Rs
```
Unit rate from SUMMARY OF STOCK HELD (STEP 25.5, 100% coverage). Service risk and capital exposure are maintained **independently** (`SRRS_Rank` vs `Value_Rank`).

## 4. Module added (additive)
`railway/railway_srrs_mas.py` — imports `opt.service_factor`, reads STEP 25 + SUMMARY; writes two new files. No existing module modified.

## 5. Outputs (new, `outputs/MAS/history/`)
| File | Rows | Columns |
|------|-----:|---------|
| `srss_results.csv` | 626 | PL_Code, Description, Criticality_Class, Forecast_Annual, Lead_Time_Days, Current_Stock, ROP, Positive_Gap, SRRS, SRRS_Rank, Average_Rate_Rs, Reorder_Gap_Value_Rs, Value_Rank |
| `srss_summary.csv` | 1 | PL_Count, Total_SRRS, Total_Positive_Gap, Total_Reorder_Gap_Value_Rs, Top10/20/50 SRRS & Value % |

## 6. Headline results

| Metric | Value |
|--------|------:|
| PLs prioritised | 626 |
| Total SRRS | 8,217,897 |
| Total Positive Gap | 502,668 units |
| Total Reorder-Gap Value | **₹3,367,367,459** |
| SRRS concentration (Top 10 / 20 / 50) | **84.5% / 94.6% / 97.8%** |
| Value concentration (Top 10 / 20 / 50) | **74.1% / 79.6% / 88.4%** |
| Critical contribution (PLs / SRRS / Value) | 360 / 99.0% / 92.1% |

## 7. Two independent views
- **Top SRRS (service risk):** high-gap **Critical PVC cables / OFC** (56501006, 56509959, 56501018, 509000396559).
- **Top Value (capital):** expensive **fire-alarm / EI systems** (567912550075 ₹1.23B, 569003030023 ₹795M, 567919640033 ₹132M).
- **6 PLs appear in both Top-20 lists** → unambiguous procure-first.

## 8. Constraint compliance
SRRS math unchanged; no cost in SRRS (value kept separate); no existing output altered; all prioritisation traces to `rop_results.csv` + SUMMARY. Issuing-depot caveat (STEP 25) carries forward into interpretation.

## 9. Files
| Path | Action |
|------|--------|
| `railway/railway_srrs_mas.py` | new module |
| `railway/outputs/MAS/history/srss_{results,summary}.csv` | new |
| `_step26_run.py` | one-off validation driver, retained |
| all existing outputs (523 files) | **untouched (SHA-256 verified)** |

See `STEP26_VALIDATION_REPORT.md` and `STEP26_SRRS_ANALYSIS_REPORT.md`.
