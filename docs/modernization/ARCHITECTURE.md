# Architecture

Current (as-is) and target (to-be) structure of the railway platform. For the
*rationale* and migration sequence see `ARCHITECTURE_HARDENING_REPORT.md`.

## Module map (empirical, from import graph)
| Module | Layer | Fan-in | Role |
|---|---|---:|---|
| `railway_config` | shared infra | 31 | constants, paths, cutoffs (single config source) |
| `railway_inventory_optimization` | core engine | 6 | `service_factor`, SS/ROP/SRRS primitives — **reused** by `srrs_mas` |
| `railway_data_preparation` | core ingestion | 6 | strategic/operational loaders; `_xlsx_rows_via_xml` reader |
| `railway_demand_reconstruction` | MAS demand | 4 | DMTR reader; **its private `_sheet_rows` is imported by 4 planning modules (known leak)** |
| `railway_business_unit_config` | core governance | 4 | 6-division BU resolver (multi-division ready) |
| `railway_forecasting` | core | 2 | Croston/SBA/TSB/Holt engine — reused by `forecast_generation` |
| 24 core (STEP1–19) + 8 MAS-extension (STEP20–28) | — | — | see `STEP1_TO_STEP28_LINEAGE.md` |

External libs actually used: pandas (30), numpy (18), scipy (2), openpyxl (2),
statsmodels (1), pulp (1). **sklearn / prophet / seaborn = 0 imports (dead).**

## Layering rule (target)
```
ingestion → demand → forecasting → inventory → prioritization → reporting
                         (validation + governance + shared cross-cut)
```
Dependencies point **only downward**. No planning/prioritization module may import
a demand module for I/O — shared I/O belongs in `ingestion/`.

## As-is vs target
| Aspect | As-is | Target |
|---|---|---|
| Package shape | flat 35 modules | 8 layered sub-packages |
| Shared I/O | private `_sheet_rows` reused cross-layer | `ingestion/xlsx_reader.py` |
| Reporting | `management_reports.py` 1548 LOC | split `reporting/` |
| Orchestration | 18 root drivers | CLI/DAG over `run()` fns |
| Config | constants in modules | centralized in `railway_config` |
| Packaging | none | `pyproject.toml` + CI |

Target tree and the per-module destination are in `architecture_migration_plan.csv`.

## Invariants that must survive any refactor
1. Every output CSV byte-identical (guarded by `tests/regression/`).
2. SS/ROP/SRRS formulas unchanged (guarded by `tests/inventory/`).
3. Core platform stays multi-division; MAS extension parametrization must keep MAS values identical.
