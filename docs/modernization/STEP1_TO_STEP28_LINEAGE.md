# STEP1 → STEP28 Lineage

Provenance of every railway module. **STEP1–19 are ACTIVE PRODUCTION RAILWAY CODE**
— some originated in the Walmart/M5 era but were adapted into the railway platform
and are *not* legacy. Only the Walmart **notebooks** and **M5 data** are historical.
Machine-readable: `repository_lineage.csv`, `active_dependency_map.csv`.

## ACTIVE_CORE_PLATFORM (STEP1–19) — 24 modules
Demand/forecast core: `railway_data_preparation`, `railway_classification`,
`railway_forecasting`, `railway_inventory_optimization`, `railway_inventory_rationalization`,
`railway_operational_analysis`.
Enterprise/governance: `railway_enterprise`, `railway_audit_trail`, `railway_lineage`,
`railway_domain_config`, `railway_business_unit_config`, `railway_business_unit_runner`,
`railway_context`, `railway_strategic_allocation` (STEP19).
Quality/validation: `railway_data_quality`, `schema_validation`,
`railway_dashboard_validation`, `railway_srrs_validation`, `railway_regression`.
Reporting/export: `railway_management_reports`, `railway_executive_summary`,
`railway_powerbi_export`, `railway_anylogistix_export`, `railway_explainability`.

**Multi-division note:** `business_unit_config`/`runner`/`context` already drive all
6 divisions (MAS/SA/TPJ/MDU/PGT/TVC) — proven in STEP18A (Configured→Live).

## ACTIVE_MAS_EXTENSION (STEP20–28) — 8 modules
| Module | Step | Produces |
|---|---|---|
| `railway_demand_reconstruction` | 21A | monthly_demand_history.csv |
| `railway_demand_classification` | 22 | demand_classification.csv |
| `railway_forecast_generation` | 23 | forecast_results.csv |
| `railway_lead_time_derivation` | 23.6B | lead_time_master.csv |
| `railway_pl_master` | 23.7 | enterprise_pl_master.csv |
| `railway_safety_stock` | 24 | safety_stock_results.csv |
| `railway_rop` | 25 | rop_results.csv |
| `railway_srrs_mas` | 26 | srss_results.csv |
*(Criticality discovery STEP23.8 + value signal STEP25.5 are embedded, not standalone modules.)*

## SHARED_INFRASTRUCTURE
`railway_config` — constants/paths/cutoffs, imported by 31 modules.

## LEGACY_HISTORICAL / DEAD (the only things safe to archive/remove)
| Asset | Class | Action |
|---|---|---|
| `notebooks/01–06*.ipynb` (Walmart M5) | legacy | archive (cite 04/05 as forecasting/optimizer provenance) |
| `notebooks/07_railway*.ipynb` | legacy | archive or convert to doc |
| M5 CSVs (`sales_train_*`, `sell_prices`, `calendar`, `sample_submission`, 430 MB) | dead | delete/archive — 0 railway imports |
| `sklearn`, `prophet`, `seaborn` | dead deps | remove from runtime requirements |
| 18 root `_step*`/`_*_audit` drivers | dormant | archive `scripts/legacy/` (keep provenance) |
| 88 root `.md` reports | docs | move to `docs/reports/` |

**Rule:** never archive a STEP1–28 `.py` module. Walmart origin ≠ legacy.
