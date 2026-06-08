# STEP 25 — Division ROP & Reorder-Gap Analysis (MAS): Implementation Report

**Type:** Additive analytics. **Existing ROP formula reused. No forecasting / lead-time / safety-stock / procurement / SRRS / enterprise logic modified.**
**Date:** 2026-06-08 · **Scope:** MAS.

---

## 1. Objective
Convert planning parameters into actionable replenishment signals: compute ROP and the reorder gap vs depot-027534 actual stock.

## 2. ROP architecture & flow
```
forecast_results.Forecast_2026_27 (annual) ─┐
lead_time_master.Lead_Time_Days  ───────────┤→ Demand_During_LT = Forecast_Annual × (LT_months / 12)
                                             │                                   │
safety_stock_results.Safety_Stock (STEP24) ──┼──────────────────────────────────►├→ ROP = DDLT + SS
                                             │                                   │
SUMMARY OF STOCK HELD (depot 027534) ────────┴── Current_Stock ──────────────────┴→ Reorder_Gap = ROP − Stock → Stock_Status
```

## 3. Formula reuse (not invented)
The repository's single existing ROP implementation (`railway_inventory_optimization`):
`edlt = forecast * lt/12.0 ; rop = edlt + safety_stock ; gap = rop − cur_stock` — **reused exactly**.
- **Demand_During_LT** = `Forecast_Annual × (LT_months/12)`, LT_months = `Lead_Time_Days/30.4375`.
- **Safety_Stock** read **verbatim** from STEP24 `safety_stock_results.csv` (validated identical).
- **Current_Stock** from `SUMMARY OF STOCK HELD` (depot **027534** only; per-PL sum of col8). No synthetic/inferred/back-calculated stock; no 027029 substitution.

## 4. Stock-status thresholds (agreed)
Critical Shortage `Current < 0.5×ROP` · Shortage `0.5×ROP ≤ Current < ROP` · Healthy `ROP ≤ Current ≤ 2×ROP` · Excess `Current > 2×ROP`. ROP=0 → `Excess` if stock>0 else `No_Demand`.

## 5. Outputs (new, `outputs/MAS/history/`)
| File | Rows | Columns |
|------|-----:|---------|
| `rop_results.csv` | 626 | PL_Code, Description, Business_Unit, Criticality_Class, Forecast_Method, Forecast_Annual, Forecast_Monthly, Lead_Time_Days, Demand_During_LT, Safety_Stock, ROP, Current_Stock, Reorder_Gap, Stock_Status |
| `rop_summary.csv` | 1 | counts, coverage, totals, status distribution |

## 6. Results

| Metric | Value |
|--------|------:|
| PLs with ROP | **626** |
| Forecast-volume coverage | **96.0%** |
| Critical / Non-Critical | 360 / 266 |
| Total ROP | 601,481 units |
| Total positive reorder gap | **502,668 units** |
| Status: Critical Shortage / Shortage / Healthy / Excess / No_Demand | 465 / 45 / 43 / 60 / 13 |

### Largest shortages (Critical, by reorder gap)
| PL_Code | Gap | ROP | Stock | Description |
|---------|----:|----:|------:|-------------|
| 56501006 | 86,474 | 86,474 | 0 | PVC insulated armoured cable |
| 56509959 | 47,378 | 47,378 | 0 | PVC insulating cable |
| 56501018 | 41,291 | 41,527 | 236 | PVC insulated cable |
| 561196180021 | 41,205 | 47,178 | 5,973 | Cable jelly-filled underground |
| 509000396559 | 39,065 | 42,178 | 3,113 | 48-fibre OFC (armoured) |

### Largest excesses
| PL_Code | Gap | ROP | Stock | Description |
|---------|----:|----:|------:|-------------|
| 539802804167 | −70,266 | 8,534 | 78,800 | HDPE pipe |
| 56507641 | −35,664 | 20,746 | 56,410 | Channel bond pin |
| 56509376 | −5,183 | 12,540 | 17,723 | ARA terminal block |

## 7. Interpretation caveat (honest)
465 of 626 PLs (74%) show **Critical Shortage** — concentrated in high-volume cables held at ~0 at depot **027534**. Depot 027534 is an **issuing depot** (high-throughput, low-holding) rather than a consignee buffer store, so a forecast-based ROP naturally exceeds its on-hand for fast-moving items. The ROP/gap is computed **correctly per the formula**; it flags replenishment *signal*, but procurement decisions (downstream) should weigh the issuing-depot operating model and any in-transit/pipeline (NS_DM_CONS shows active POs). The numbers are evidence; the depot role is context.

## 8. Files
| Path | Action |
|------|--------|
| `railway/railway_rop.py` | new module |
| `railway/outputs/MAS/history/rop_{results,summary}.csv` | new |
| `_step25_run.py` | one-off validation driver, retained |
| all existing outputs (518 files) | **untouched (SHA-256 verified)** |

See `STEP25_VALIDATION_REPORT.md` and `STEP25_IMPACT_ANALYSIS.md`.
