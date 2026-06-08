# STEP 23.7 — Enterprise PL Master Reconciliation: Implementation Report

**Type:** Data reconciliation / master-data foundation. **No forecasting, safety-stock, ROP, SRRS, procurement or optimization logic modified. No PL code silently changed. All existing outputs byte-identical.**
**Date:** 2026-06-08 · **Scope:** MAS.

---

## 1. Objective
Build a canonical enterprise PL entity linking Demand, Inventory, Strategic, Criticality, Forecasting and Lead-Time — and quantify the STEP 23.5 universe mismatch.

## 2. Architecture diagram
```
 Universe A  DMTR demand        (demand_classification.csv, 1083 PLs)
 Universe B  Operational stock  (railway_operational_inventory.csv, 907 PLs)
 Universe C  Strategic          (strategic_inventory_allocation.csv, MAS 41)
 Universe D  Criticality        (railway_sku_master.csv, 59)
 Derived     Forecast (961) · Lead Time (lead_time_master.csv, 702)
        │
        ▼  railway_pl_master.py  (exact PL key = canonical; normalized key documented)
        │     Phase 1 exact match → Phase 2 normalized match → Phase 3 candidates (flagged, not merged)
        ▼
 enterprise_pl_master.csv   (1990 PLs = A∪B∪C∪D, 21 cols, Master_Status)
 pl_code_normalization_report.csv   (every rule documented; 12 codes changed)
 pl_match_candidates.csv    (144 review candidates — NEVER auto-merged)
```

## 3. Reconciliation flow & canonical design
- **Canonical key:** the exact `PL_Code` (codes never overwritten). `PL_Code_Normalized` = digits-only, leading zeros stripped — *documented*, used only for analysis, never as the merge key.
- **Matching:** Phase 1 exact → Phase 2 normalized → Phase 3 description-exact + 8↔12-digit prefix **candidates flagged for human review** (no auto-merge, per spec).
- **Master_Status rules:** Fully_Reconciled (D&I&C) → Planning_Ready (D&LT&C) → Forecast_Ready (D&LT) → Inventory_Only → Demand_Only → Criticality_Only → Partial.

## 4. Module added (additive)
`railway/railway_pl_master.py` — reads existing CSVs, writes 3 new files to `outputs/MAS/history/`. No existing module modified.

## 5. Results

### enterprise_pl_master.csv (1,990 PLs)
| Master_Status | PLs |
|---------------|----:|
| Inventory_Only | 880 |
| Forecast_Ready | 675 |
| Demand_Only | 376 |
| Planning_Ready | 27 |
| Partial | 20 |
| Criticality_Only | 12 |
| **Fully_Reconciled** | **0** |

- **Planning_Ready (27)** + **Forecast_Ready (675)** = 702 = the lead-time-covered demand PLs (96% of forecast volume). 27 of them also carry criticality (full SS inputs available).
- **Fully_Reconciled = 0** — no PL has demand AND inventory AND criticality together.

### pl_code_normalization_report.csv
12 / 1,990 codes changed (LeadingZero 2, Composite 9 `a/b`, NonNumeric 1 = literal "NA"). Length profile: Len12 1,842 · Len8 135 · Composite 9 · Len20 1. **Normalization recovered 0 new exact matches** → the mismatch is not a formatting problem.

### pl_match_candidates.csv (144 review candidates — not merged)
Prefix8-OP 133 · Description-OP 10 · Description-SK 1. Across **69 distinct DMTR PLs**; only **15 high-score (≥0.6)**. At most **~68 DMTR PLs** could gain an inventory link after manual review (mostly low-confidence category-prefix collisions).

## 6. Root-cause analysis (quantitative)
| Match method | DMTR∩Operational |
|--------------|-----------------:|
| Exact | 20 |
| Normalized | 20 (+0) |
| 8↔12 prefix (candidates) | up to 62 (review) |
| Description-exact | +10 (generic items: WiFi router, office table, …) |

**The mismatch is a COMBINATION, dominated by depot/ledger separation:** the demand register (issuing depot **027534**) and the stock snapshot (consignee depot **027029**) hold/transact largely different material sets. PL-coding inconsistency (8-vs-12-digit; ad-hoc general-item codes) is a **secondary, minor** factor (~68 candidate PLs, ~15 reliable). It is **not** a normalization/leading-zero issue (12/1990 codes touched, 0 matches recovered).

## 7. Files
| Path | Action |
|------|--------|
| `railway/railway_pl_master.py` | new module |
| `railway/outputs/MAS/history/{enterprise_pl_master,pl_code_normalization_report,pl_match_candidates}.csv` | new |
| `_step23_7_run.py` | one-off validation driver, retained |
| all existing outputs (510 files) | **untouched (SHA-256 verified)** |

See `STEP23_7_VALIDATION_REPORT.md` and `STEP23_7_IMPACT_ANALYSIS.md`.
