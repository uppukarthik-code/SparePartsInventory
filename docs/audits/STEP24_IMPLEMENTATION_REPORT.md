# STEP 24 — Safety-Stock Recalibration (MAS): Implementation Report

**Type:** Additive analytics. **No forecasting / classification / lead-time / procurement / ROP / SRRS / enterprise logic modified. Existing SS formula reused.**
**Date:** 2026-06-08 · **Scope:** MAS.

---

## 1. Objective
Compute a calibrated safety-stock layer per MAS PL from the now-complete internal inputs (demand variability + forecast + lead time + criticality), reusing the repository's inventory-theory formula.

## 2. Method (reused, not invented)
`Safety_Stock = z · σ_LT` — the existing `railway_inventory_optimization` form (`z = stats.norm.ppf(SL)`).
- **σ_LT = σ_monthly · √(Lead_Time_Days / 30.4375)** — dimensionally consistent (per-month σ × √months). `σ_monthly` = STEP22 `demand_classification.Std_Deviation` (std of monthly Issues).
- **Service levels (agreed):** Critical = 95% (z=1.645) · Non-Critical = 85% (z=1.036). The existing `cfg.SERVICE_LEVEL_TABLE` (ABC×S1–S4) was inapplicable (3% coverage, defaults 0.90); the binary mapping aligns with the STEP23.8 criticality signal (99.6%).
- **Lead time:** `lead_time_master.csv` only — **no synthetic/default values**; PLs without a derived lead time are flagged, not computed.
- **Criticality (binary):** SUMMARY col4 Type — Safety/Vital → Critical, NA → Non-Critical (STEP23.8 validated, recall 0.95).
- **Forecast:** `forecast_results.Forecast_2026_27`.

## 3. Module added (additive)
`railway/railway_safety_stock.py` — reads existing artifacts + SUMMARY, reuses `norm.ppf` + `z·σ·√LT`; writes two new files. No existing module modified.

## 4. Outputs (new, `outputs/MAS/history/`)
| File | Rows | Columns |
|------|-----:|---------|
| `safety_stock_results.csv` | 626 | PL_Code, Description, Business_Unit, Criticality_Class, Forecast_Method, Forecast_Annual, Lead_Time_Days, Demand_STD, Service_Level, Z_Value, Safety_Stock |
| `safety_stock_summary.csv` | 1 | PL count, coverage, volume coverage, Critical/Non-Critical, SS totals, uncovered counts |

## 5. Results

| Metric | Value |
|--------|------:|
| PLs with safety stock | **626** (65.1% of 961 forecastable) |
| **Forecast-volume coverage** | **96.0%** |
| Critical / Non-Critical PLs | 360 / 266 |
| Total safety stock | 301,558 units (Critical 264,221 · Non-Critical 37,337) |
| Flagged — no derived lead time | 335 forecastable PLs (≈4% of volume) |
| Flagged — no criticality | 0 |

### Highest safety-stock items (high σ × long lead time, all Critical)
| PL_Code | SS (units) | LT (d) | σ (monthly) | Description |
|---------|-----------:|-------:|------------:|-------------|
| 56501006 | 40,743 | 120 | 12,475 | PVC insulated armoured cable |
| 509000396559 | 28,784 | 82 | 10,694 | 48-fibre OFC (armoured) |
| 56501018 | 28,080 | 79 | 10,597 | PVC insulated cable |
| 56509959 | 27,559 | 124 | 8,301 | PVC insulating cable |
| 561183521801 | 21,716 | 111 | 6,913 | PVC cable unsheathed |
| 539804752183 | 17,067 | 333 | 3,137 | OFC 24-fibre armoured |

These are the high-volume signalling cables/OFC with long lead times — exactly the items where buffer matters most.

## 6. Constraint compliance
No synthetic demand / lead time / criticality. No modification of forecasting, procurement, SRRS, or enterprise outputs. All calculations trace to `demand_classification.csv`, `lead_time_master.csv`, `forecast_results.csv`, and SUMMARY OF STOCK HELD.

## 7. Files
| Path | Action |
|------|--------|
| `railway/railway_safety_stock.py` | new module |
| `railway/outputs/MAS/history/safety_stock_{results,summary}.csv` | new |
| `_step24_run.py` | one-off validation driver, retained |
| all existing outputs (516 files) | **untouched (SHA-256 verified)** |

See `STEP24_VALIDATION_REPORT.md` and `STEP24_IMPACT_ANALYSIS.md`.
