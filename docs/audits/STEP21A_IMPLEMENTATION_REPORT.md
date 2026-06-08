# STEP 21A — Monthly Demand History Reconstruction: Implementation Report

**Type:** Additive data-foundation build. **No forecasting, SRRS, procurement, optimization, Power BI, KPI or existing-output logic changed.**
**Date:** 2026-06-08
**Scope:** MAS division only (per spec).

---

## 1. Objective

Convert the 54 monthly MAS DMTR registers into a normalized monthly demand history — the foundation STEP 20 identified as the primary blocker to business-unit strategic planning (forecasting, XYZ, safety stock, ROP, SRRS).

## 2. Architecture

```
54 DMTR_*.xlsx  (raw_data/Railway_Operations/MAS/)
        │
        ▼  raw-OOXML reader (handles shared + inlineStr cells)
Schema discovery & validation  (col 2 date · col 3 type · col 6 PL · col 9 qty)
        │
        ▼  classify: demand-issue / receipt / balance-sign
Transaction extraction  (19,618 rows → typed records)
        │
        ▼  group by (PL_Code, Month)
Monthly aggregation  (Issues_Qty, Receipts_Qty)
        │
        ▼  per PL: first-observed month → 2026-06
Gap filling  (missing months → zero demand; continuous timeline)
        │
        ▼  per PL chronological cumulative (Initial + inflows − outflows)
Closing_Stock running balance (reconstructed)
        │
        ▼  conservation + integrity + backward-compat checks
Quality validation
        │
        ▼
outputs/MAS/history/monthly_demand_history.csv
        │
        ▼
Future forecasting / XYZ / SS / ROP / SRRS foundation
```

## 3. Module added (additive only)

`railway/railway_demand_reconstruction.py` — self-contained, reuses the repository's raw-OOXML reading technique (no openpyxl dependency, robust to the workbooks' styling). Reads `cfg.RAW_DATA_DIR/Railway_Operations/MAS`, writes to `cfg.OUTPUT_DIR/MAS/history/`. **No existing module imported for mutation; no existing module modified.**

### 3.1 Reconstruction rules implemented (as agreed)
- **Issues_Qty** = `Issue-To User Depot` + `Issue-For End Use` + `Issue-To Contractor` only. `Issue-Book Transfer` and `Write-Back Issue` excluded from demand (tracked in the running balance + QA).
- **Receipts_Qty** = all `Receipt-*`.
- **Closing_Stock** = reconstructed running balance: opening from `Initial Stock`, then cumulative (`Receipt-*`, `Write-Back`, `Initial` as +; `Issue-*`, `Return-to-Vendor` as −; stock-verification neutral).
- **Gap-fill** = per PL from first-observed month to 2026-06; absent months → `Issues_Qty=0, Receipts_Qty=0`, `Closing_Stock` carried forward.

## 4. Outputs produced (all new, under `outputs/MAS/history/`)

| File | Rows | Columns |
|------|-----:|---------|
| `monthly_demand_history.csv` | **39,148** | Business_Unit, PL_Code, Description, Month, Issues_Qty, Receipts_Qty, Closing_Stock |
| `monthly_demand_summary.csv` | 1,083 | PL_Code, Description, Months_Observed, Total_Issues, Average_Monthly_Demand, Std_Deviation, CV |
| `demand_history_quality_report.csv` | 1 | Total_PL_Codes, Total_Months, Missing_Months, Duplicate_Rows, Null_PL_Codes, Null_Dates, Coverage_Percent |

## 5. Headline reconstruction metrics

| Metric | Value |
|--------|------:|
| DMTR files processed | 54 / 54 |
| Transactions parsed | 19,618 |
| PL codes reconstructed | 1,083 |
| Months reconstructed | 54 (2022-01 → 2026-06, continuous) |
| Monthly history rows | 39,148 |
| Avg months/PL | 36.1 (min 1, max 54) |
| PLs with computable CV (≥2 mo) | 961 |
| PLs with ≥24 months | 834 |
| Zero-issue PL-months (intermittency) | 83.7% |
| Total issues conserved | 2,727,683.618 (exact) |
| Total receipts conserved | 2,726,423.483 (exact) |

## 6. Notes / honest limitations
- **Closing_Stock is derived**, not a source field; external reconciliation vs `stock_history.xlsx` is limited by low PL-key overlap (20/1083). Treat as a relative running balance; the demand signals (Issues/Receipts) are the verified deliverable.
- **6 PLs have mixed UOM** across their history — quantities are summed numerically; flagged in QA. Negligible (0.55%).
- **83.7% intermittency** is a finding, not a defect — it confirms MAS spares demand is intermittent and **must** be forecast with Croston/SBA/TSB rather than simple averages.

## 7. Files
| Path | Action |
|------|--------|
| `railway/railway_demand_reconstruction.py` | new module |
| `railway/outputs/MAS/history/*.csv` (3) | new outputs |
| `_step21a_run.py` | one-off driver (backward-compat guard + validation), retained for provenance |
| all existing outputs (495 files) | **untouched (SHA-256 verified)** |

See `STEP21A_VALIDATION_REPORT.md` for the full validation gate.
