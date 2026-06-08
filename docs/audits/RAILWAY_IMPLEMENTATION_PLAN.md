# Railway Platform — Implementation Review Package

**Generated:** 2026-06-07 · Planning only — **no code generated yet.**
**Architecture (LOCKED):** two independent pipelines, no merged source, full source traceability.
**Strategic source:** `raw_data/railways.xlsx` (59 vital items). **Operational source:** `raw_data/railway_stock_summary.xlsx` (907 depot items).
**Hard rules:** Walmart workflow untouched · notebooks 01–06 unedited · railway outputs isolated · reuse repo logic · minimize new deps.

---

## 1. Repository impact assessment

| Area | Impact | Detail |
|---|---|---|
| Walmart notebooks 01–06 | **None** | Read-only extraction of functions; files never edited. |
| Walmart CSV outputs (`notebooks/`) | **None** | Railway writes only under `railway/outputs/`. No filename overlap. |
| `requirements.txt` | **None (target)** | Primary engine: numpy/pandas/scipy/openpyxl (present). Secondary: `statsmodels` Holt + `pulp` (both present). No new dependency. |
| `raw_data/` | **Read-only** | Both workbooks already there. |
| New code | **Additive** | New `railway/` package + 1 new notebook + docs. |
| Two-pipeline isolation | **Enforced** | Strategic and Operational modules never join source workbooks; only the Power BI export reads both *outputs* side-by-side with a `source` lineage column. |
| Scalability (59→907→all) | **By design** | Loaders are schema-driven and row-count agnostic; classification/forecast/optimization operate per-SKU, so growing the item set needs no redesign — only pointing the loader at more rows/sheets. |

---

## 2. Updated repository tree (additive)

```
SparePartsInventory/
├── railway/                                  ★ NEW package
│   ├── __init__.py                           ★ NEW
│   ├── railway_config.py                     ★ NEW  constants (thresholds, weights, sheet names)
│   │
│   │   ── STRATEGIC PIPELINE (railways.xlsx) ──
│   ├── railway_data_preparation.py           ★ NEW  load → demand history
│   ├── railway_classification.py             ★ NEW  ABC + Criticality + Demand class + Coverage
│   ├── railway_forecasting.py                ★ NEW  primary + secondary + backtest selection
│   ├── railway_inventory_optimization.py     ★ NEW  lead time + safety stock + ROP + PuLP
│   │
│   │   ── OPERATIONAL PIPELINE (stock_summary)──
│   ├── railway_operational_analysis.py       ★ NEW  aging + dead/slow stock + valuation
│   │
│   │   ── SHARED EXPORTS ──
│   ├── railway_powerbi_export.py             ★ NEW  consumes BOTH pipeline outputs
│   ├── railway_anylogistix_export.py         ★ NEW  railways.xlsx only (6 divisions)
│   │
│   └── outputs/                              ★ NEW
│       ├── railway_demand_history.csv
│       ├── railway_sku_master.csv
│       ├── railway_forecast.csv
│       ├── railway_inventory_policy.csv
│       ├── powerbi/   (page1_executive … page5_optimization .csv)
│       └── anylogistix/ (locations, products, demand, inventory_policy .csv)
│
├── notebooks/
│   └── 07_railway_inventory_analysis.ipynb   ★ NEW  orchestrates railway/ package
│
├── railway_schema_report.md                  ✓ written
├── RAILWAY_DATA_QUALITY_REPORT.md            ✓ written
├── railways_discovery_report.md              ✓ written
├── RAILWAY_IMPLEMENTATION_PLAN.md            ← this review package
└── README_RAILWAYS.md                        ★ NEW

UNCHANGED: notebooks 01–06 · all Walmart CSVs · Anylogistix/ · Optimization_models_CPLEX/
           · Power-BI Dashboards/ · README.md · requirements.txt
```

> **Note:** `railway_operational_analysis.py` and `railway_config.py` are 2 modules **added** to your 6-module list — the operational pipeline (aging/dead-stock/valuation from `stock_summary`) needs a home that does not contaminate the strategic modules, and config centralises the locked thresholds. Flagged for your approval.

---

## 3. Dependency map

| Layer | Package | Status | Used by |
|---|---|---|---|
| Data load | `openpyxl` | present | strategic loader |
| Data load | stdlib `zipfile`/`xml` | present | operational loader (stock_summary has corrupt stylesheet) |
| Core | `numpy`, `pandas` | present | all |
| Stats | `scipy.stats` | present | z-values, safety stock |
| Secondary forecast | `statsmodels` (Holt) | present | `railway_forecasting` |
| Optimization | `pulp` | present | `railway_inventory_optimization` |
| **New dependencies** | — | **none** | — |

Prophet / SARIMAX / ARIMA / LightGBM / RandomForest / XGBoost: **excluded** (5 annual points).

---

## 4. Reused functions (lift as-is from notebooks)

| Function | From | Railway role |
|---|---|---|
| `croston_forecast` | nb04 | Secondary benchmark (pure numpy) |
| `sba_forecast` | nb04 | Secondary benchmark |
| `tsb_forecast` | nb04 | Secondary benchmark (zero-heavy items) |
| `calculate_intermittent_demand_metrics` | nb04 | Backtest scoring (MAE/RMSE/bias core) |
| PuLP problem-construction pattern in `solve_optimization_from_summary_df` | nb05 | Optimization skeleton |
| Safety-stock / ROP formula in `calculate_robust_unit_level_inventory_metrics` | nb05 | `SS=z·√(σ²·LT)`, `ROP=μ·LT+SS` |
| AnyLogistix table shapes (`generate_anylogistix_demand_table`, `format_inventory_policy_table`) | nb06 | Export structure |

## 5. Replaced functions (retail logic → railway logic)

| Replaced | From | Reason / railway replacement |
|---|---|---|
| `assign_forecast_model` | nb04 | Routes to Prophet/SARIMAX/ETS — forbidden. → backtest-error-minimising selector over {AAC, EAR, MA, CAGR, Croston, SBA, TSB, Holt}. |
| `prophet_forecast`, `sarimax_forecast`, `ets_forecast`, `combination_forecast` | nb04 | Dropped (series too short). |
| `LeadTimeCalculator` (class) | nb05 | Walmart location model → railway Tier-1/Tier-2 lead-time rule. |
| Retail stockout penalty in PuLP objective | nb05 | → Criticality-weighted stockout (S1=10, S2=5, S3=2, S4=1). |
| Geo/geocoding customer tables | nb06 | → 6 fixed SR divisions (MAS,TPJ,SA,MDU,PGT,TVC). |

## 6. Adapted functions (reuse skeleton, swap internals)

| Adapted | From | Change |
|---|---|---|
| `calculate_intermittent_demand_metrics` | nb04 | Add **MAPE**; keep MAE/Bias; used on 4→1 hold-out. |
| ADI / CV² classifier (inline in nb04) | nb04 | Extract to `railway_classification` → Smooth/Intermittent/Erratic/Lumpy (cutoffs ADI 1.32, CV² 0.49). |
| `calculate_robust_unit_level_inventory_metrics` | nb05 | σ from 5-pt annual series; `LT` from railway lead-time rule; service level by ABC. |
| `solve_optimization_from_summary_df` | nb05 | New objective = Holding + Ordering + criticality-weighted Stockout. |
| `create_sku_level_inventory_summary_safe` | nb05 | Drop Walmart-only columns (region/part_type). |
| AnyLogistix generators | nb06 | Divisions replace customers; demand from EAR Consumption sheet. |

## 7. New modules (purpose)

| Module | Pipeline | Responsibility |
|---|---|---|
| `railway_config.py` | shared | Locked thresholds: ABC lakh bands, criticality map, weights, lead-time bounds, coverage bands, sheet names. |
| `railway_data_preparation.py` | strategic | Load railways.xlsx, rebuild 2-row headers, normalise PL, join Safety/Vital + division sheets → `railway_demand_history.csv`. |
| `railway_classification.py` | strategic | ABC (AAC×Unit Cost), Criticality (S/V/N→S1/S2/S3), Demand class (ADI/CV²), Coverage KPI → `railway_sku_master.csv`. |
| `railway_forecasting.py` | strategic | Primary engine + secondary benchmarks + hold-out selection → `railway_forecast.csv`. |
| `railway_inventory_optimization.py` | strategic | Lead-time rule, safety stock, ROP, min/max, PuLP cost model → `railway_inventory_policy.csv`. |
| `railway_operational_analysis.py` | operational | stock_summary → aging, dead/slow stock, valuation tables. |
| `railway_powerbi_export.py` | shared | 5 page tables from BOTH pipelines (lineage-tagged). |
| `railway_anylogistix_export.py` | strategic | Locations/Products/Demand/Policy for 6 divisions. |

---

## 8. Output datasets (exact field order per spec)

**`railway_demand_history.csv`** — `PL_Code, Description, FY2020_21, FY2022_23, FY2023_24, FY2024_25, FY2025_26, AAC, EAR_Qty, Pending_Supply, Current_Stock, Unit_Cost`

**`railway_sku_master.csv`** — `PL_Code, Description, ABC_Class, Criticality, Safety_Flag, Current_Stock, Unit_Cost, Inventory_Value, AAC, EAR_Qty, Pending_Supply, Inventory_Coverage_Ratio, Demand_Class`

**`railway_forecast.csv`** — `PL_Code, Description, MA_Forecast, CAGR_Forecast, Croston_Forecast, SBA_Forecast, TSB_Forecast, Holt_Forecast, Selected_Model, Selected_Forecast, Forecast_2026_27`

**`railway_inventory_policy.csv`** — `PL_Code, Description, ABC_Class, Criticality, Current_Stock, Safety_Stock, ROP, Recommended_Min, Recommended_Max, Recommended_Reorder_Level, Inventory_Coverage_Ratio`

### Locked business rules
- **ABC:** `Annual_Issue_Value = AAC × Unit_Cost`; A >₹69L, B1 ₹35–69L, B2 ₹13–35L, C <₹13L. *(Preview: A=9, B1=4, B2=6, C=39.)*
- **Criticality:** S→S1, V→S2, N→S3, else→S4. **Safety_Flag** = Yes if flag ∈ {S,V}.
- **Demand class:** ADI/CV² → Smooth/Intermittent/Erratic/Lumpy. *(Preview: Smooth 30, Intermittent 7, Erratic 7, Dead/zero 14.)*
- **Lead time:** Tier 1 `EAR_Qty/Pending_Supply` bounded [1,12] when Pending>0; else Tier 2 by criticality (S1=6,S2=4,S3=3,S4=2). Store `Lead_Time_Months`, `Lead_Time_Source`.
- **Coverage:** `(Current_Stock + Pending_Supply)/EAR_Qty` → <0.5 Critical Shortage · 0.5–1 Understocked · 1–2 Healthy · 2–5 Overstocked · >5 Excess/Dead Capital.
- **Backtest:** train {2020-21,2022-23,2023-24,2024-25} → forecast 2025-26; score MAE/MAPE/Bias; lowest error → `Selected_Model`/`Selected_Forecast`.

---

## 9. Power BI tables (outputs/powerbi/)

| Page | File | Contents | Source pipeline |
|---|---|---|---|
| 1 Executive | `page1_executive.csv` | Total Inventory Value, Inventory Reduction Potential, Dead Stock, Slow Moving, Safety Items, Vital Items, Forecast Accuracy | Operational (value/dead/slow) + Strategic (safety/vital/accuracy) |
| 2 ABC | `page2_abc.csv` | A/B1/B2/C counts, Inventory Value, Annual Issue Value | Strategic |
| 3 Demand | `page3_demand.csv` | Forecast, AAC, EAR, Demand Classification | Strategic |
| 4 Criticality | `page4_criticality.csv` | S1–S4 counts/value, ABC×Criticality matrix | Strategic |
| 5 Optimization | `page5_optimization.csv` | Before/After Inventory Value, Safety Stock, ROP, Cost Savings | Strategic |

Each row carries a `source_workbook` lineage column (traceability mandate).

## 10. AnyLogistix tables (outputs/anylogistix/) — railways.xlsx only

| Table | File | Contents |
|---|---|---|
| Locations | `locations.csv` | 6 divisions MAS, TPJ, SA, MDU, PGT, TVC (+ stocking depots) |
| Products | `products.csv` | 59 SKUs with unit cost / class |
| Demand | `demand.csv` | Division-allocated AAC/forecast from `EAR Consumptions` |
| Inventory Policy | `inventory_policy.csv` | min/max/ROP/safety stock per SKU×division |

---

## 11. File-by-file implementation plan (incremental build order)

I will build and **show code before writing**, one module per step:

1. `railway_config.py` — constants only (no logic risk).
2. `railway_data_preparation.py` → verify `railway_demand_history.csv` (59 rows).
3. `railway_classification.py` → verify `railway_sku_master.csv` (ABC/Criticality/Demand/Coverage previews match).
4. `railway_forecasting.py` → verify `railway_forecast.csv` (backtest + selection).
5. `railway_inventory_optimization.py` → verify `railway_inventory_policy.csv` (lead-time/SS/ROP/PuLP).
6. `railway_operational_analysis.py` → verify aging/dead/slow/valuation tables.
7. `railway_powerbi_export.py` → verify 5 page CSVs.
8. `railway_anylogistix_export.py` → verify 4 division CSVs.
9. `notebooks/07_railway_inventory_analysis.ipynb` — orchestrate + narrate.
10. `README_RAILWAYS.md` — docs.

After each module: run it, show outputs, confirm Walmart untouched, then proceed.

---

## Open confirmations before Step 1
1. Approve adding **`railway_operational_analysis.py`** + **`railway_config.py`** (2 modules beyond the 6 listed) — needed for clean two-pipeline isolation.
2. Approve `railway/outputs/powerbi/` and `railway/outputs/anylogistix/` subfolders.
3. Confirm incremental build order above (config → strategic → operational → exports → notebook → docs).
