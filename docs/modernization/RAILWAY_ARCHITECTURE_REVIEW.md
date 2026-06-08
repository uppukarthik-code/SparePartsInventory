# Railway Inventory Analytics Platform — Architecture Review & Technical Debt Assessment

**Type:** Read-only review (Step 5B). No code changed, no modules added.
**Date:** 2026-06-07
**Reviewers (roles):** Sr. Railway Asset-Management Architect · Sr. Data Architect · Sr. Supply-Chain Analytics Architect
**Scope reviewed:** `railway/` package (8 modules, ~1,908 LOC) + 13 generated CSVs + 1 JSON.
**Scaling lens:** 59 strategic items → 907 depot items → full SR S&T → multi-zonal Indian Railways.

> Current build state (factual): Steps 2–5A delivered. **Not yet built:** operational pipeline (Step 6), Power BI pages 1–5 (Step 7), AnyLogistix exports (Step 8). `railway/tests/` and `railway/examples/sample_outputs/` exist but are **empty**. This review judges what exists and what the architecture implies for what's next.

---

## Section 1 — Code Quality Review

| Dimension | Score /10 | Justification (specific) |
|---|---:|---|
| **Maintainability** | 8 | Clear module-per-responsibility split (`data_preparation`→`classification`→`forecasting`→`optimization`→`data_quality`→`executive_summary`). Each module ~200–334 LOC, single-purpose. Deduction: business constants correctly centralised in `railway_config`, but a few literals leaked (e.g. `UNIT_COST_THRESHOLD=100_000` and `METRE_TOKENS` in `railway_data_quality`, `BLEND_WEIGHTS` in `railway_forecasting`, `PROCUREMENT_BUDGET` in optimizer) — should migrate to config. |
| **Readability** | 9 | Descriptive names, docstrings on every module/function, explicit field-order lists (`DEMAND_HISTORY_FIELDS`, `POLICY_FIELDS`). Reuse provenance is commented (`# Reused VERBATIM from notebooks/04`). |
| **Modularity** | 8 | Strict pipeline DAG; strategic and operational domains kept separate by design. Deduction: `railway_data_quality.build_quality_layer` both rebuilds Step-5 policy *and* mutates its CSV (append) — a cross-module write coupling. |
| **Reusability** | 7 | `croston/sba/tsb` lifted cleanly; config helpers (`classify_abc`, `map_criticality`, `classify_coverage`) are pure and reusable. Deduction: loaders are bound to one workbook layout (positional columns), so reuse across new schemas needs config edits, not just calls. |
| **Configurability** | 7 | Thresholds, weights, service levels, lead-time tiers, sheet names, and column coordinates all in config. Deduction: no external config file (YAML/ENV) — config is Python, so non-engineers can't tune it; no per-zone config overlay yet. |
| **Testability** | 4 | Functions are pure enough to test (deterministic, dataframe in/out), and each module has a `run()` with an internal validation gate. **But `railway/tests/` is empty** — zero automated unit tests despite the directory being provisioned. Validation is print-based, not assertion-based-in-CI. |

**Average: 7.2 / 10** — strong structure and readability; the gap is automated testing and a small amount of config leakage.

---

## Section 2 — Scalability Review

Current core operates on **59 rows**; all transforms are O(n) per-SKU Python loops (`iterrows`) plus a PuLP solve.

| Scale | Verdict | Notes |
|---|---|---|
| **59 items** | ✅ Instant | Sub-second end to end. |
| **907 items** (operational) | ✅ Fine | `iterrows` over 907 rows is trivial; XML loader already reads 907 rows in Step 2. |
| **10,000 items** | 🟡 Watch | `df.iterrows()` in `classification`, `forecasting`, `optimization` becomes the hotspot (~3× row-wise passes). PuLP binary knapsack with 10k vars/1 constraint still solvable but slower. |
| **100,000 items** | 🔴 Redesign hotspots | Row-wise `iterrows` + per-row Python math will dominate; PuLP knapsack at 100k binaries is heavy; full-frame CSV rewrites become I/O-bound. |

**Bottlenecks (concrete):**
- **Performance:** `iterrows()` loops in `railway_classification.build_sku_master`, `railway_forecasting.build_forecast`, `railway_inventory_optimization.build_inventory_policy`. → vectorise with numpy/pandas; the demand-metric and blend math is fully vectorisable.
- **Memory:** acceptable to ~100k (narrow tables). The strategic loader uses `openpyxl read_only` (streaming) — good; the operational loader builds a full Python list of row dicts via XML — at 1M cells this materialises everything in memory.
- **File I/O:** every module rewrites whole CSVs; `data_quality` re-reads then rewrites the policy CSV. At scale → switch to Parquet + incremental/partitioned writes.
- **Power BI:** flat single-file CSV imports per page is fine to ~1M rows; beyond that needs a star schema / incremental refresh.
- **Optimization:** PuLP CBC is fine for thousands; for 100k+ items the budget knapsack should move to a greedy density-ranking (priority/₹) with provable bound, or a specialised MIP.
- **Forecasting:** statsmodels Holt per-SKU in a loop is the slowest model; everything else is closed-form. Holt should be batched/short-circuited for `Dead`/zero series (already partially guarded).

---

## Section 3 — Data Model Review

| File | Rows×Cols | Assessment |
|---|---|---|
| `railway_sku_master.csv` | 59×19 | Solid hub table. **Missing:** `Unit`, `Depot`, `Division`, `Asset_Type` (depot/division exist in source but aren't surfaced here). **Redundant:** `Inventory_Value` is derivable (`Current_Stock×Unit_Cost`) — acceptable as a materialised KPI. |
| `railway_forecast.csv` | 59×20 | Rich. `Forecast_to_Stock_Ratio` stores `inf` for zero-stock items — **not Power-BI-numeric-safe**; needs a sentinel/cap or a companion boolean. `Demand_Class` duplicated from master (acceptable denormalisation for BI). |
| `railway_inventory_policy.csv` | 59×27 | Good audit design (original + normalized side-by-side). `Description` repeated across all tables (denormalised); fine for BI, redundant for a warehouse. |
| `railway_data_quality.csv` | 59×13 | Clean audit trail. Only **one** anomaly rule encoded (per-km cable); schema can hold more rule types but `Potential_Unit_Mismatch` is a single boolean, not a rule-id. |
| `executive_kpi_summary.csv` | 41×3 | Tidy Section\|KPI\|Value long form — ideal for BI. No issues. |

**Normalization opportunities:** `PL_Code → Description/Unit/Depot/Division/Asset_Type` is a clean dimension; the 5 transactional tables all carry `Description` redundantly. A future star schema = 1 `dim_sku` + fact tables keyed by `PL_Code`.
**Future-proofing:** add `Source_Workbook`, `Snapshot_Date`, `Schema_Version` columns to every output for lineage when multiple snapshots/zones coexist (the workbook already has 3 snapshot sheets).

---

## Section 4 — Technical Debt Register

| ID | Issue | Severity | Impact | Recommended Fix |
|---|---|---|---|---|
| TD-001 | Hard-coded positional workbook coordinates (`STRATEGIC_COLS`, `UDM_COL=20`) | Medium | Breaks if SR re-orders/renames columns; blocks reuse on other zones' workbooks | Header-name-based resolver with positional fallback; per-zone schema map in config |
| TD-002 | Data-quality framework has a single rule (per-km cable) | Medium | Other UoM errors (per-100m, per-coil, per-set) and price outliers go undetected | Generalise to a rule registry (`rule_id`, predicate, action); add statistical outlier detection on `Unit_Cost` |
| TD-003 | 5-point annual forecasting (2021-22 missing) | High (domain) | Limits forecast confidence; no seasonality/trend power; blocks ML models | Ingest monthly issue transactions when available; until then keep blend + document confidence (already done) |
| TD-004 | No automated schema validation on inputs/outputs | High | A changed workbook silently produces wrong KPIs | Add `pandera`/explicit schema contracts per CSV; fail-fast on column/type drift |
| TD-005 | `railway/tests/` empty — no automated unit tests | High | Regressions undetectable; refactors risky at scale | Add pytest for config helpers, ABC/criticality/coverage edges, lead-time tiers, blend math, normalization |
| TD-006 | `Forecast_to_Stock_Ratio = inf` persisted to CSV | Low | Power BI mis-types the column | Cap to sentinel (e.g. 999) + keep a `Zero_Stock_Flag`, or emit null |
| TD-007 | Safety_Stock mixes annual σ with √months (dimensional) | Medium | Overstates safety stock ~√12×; inflates ROP/investment | Period-consistent σ (monthly) OR document as deliberate conservatism (currently locked + documented) |
| TD-008 | `iterrows()` per-SKU loops in 3 core modules | Medium | O(n) Python overhead at 10k–100k | Vectorise (numpy); reserve loops for PuLP only |
| TD-009 | Budget knapsack silently drops items whose single investment > budget | Low | "Unfundable" exposures invisible in the plan | Emit an explicit `Unfundable_HighValue` list alongside the plan |
| TD-010 | Config is Python-only; no external/zonal config | Medium | Non-engineers can't tune; no multi-zone overlay | Externalise thresholds to YAML with a loader; per-zone overrides |
| TD-011 | Whole-CSV rewrites + cross-module CSV mutation (`data_quality` appends to policy) | Low | I/O churn; ordering coupling | Parquet + a single assembly step; treat policy CSV as immutable, write a separate enriched file |
| TD-012 | No `Snapshot_Date`/`Source_Workbook`/`Schema_Version` lineage columns | Medium | Can't distinguish snapshots/zones when combined | Stamp every output |

---

## Section 5 — Railway Domain Review (store-type suitability)

The strategic dataset is **telecom/power-heavy vital S&T stock** (cables, LED aspects, lead-acid cells, chargers, magneto telephone). Suitability of the *current model* per store type:

| Store type | Suitability | Gap |
|---|---|---|
| **Signal Stores** (LED aspects, relays, signal cables) | ✅ Good | Well represented (LED Red/Yellow/Green, signal cables, AC shunt LED). Criticality from Safety/Vital works. |
| **Telecom Stores** (cables, OFC, telephone, modems) | ✅ Good | Cables/magneto telephone present; UoM normalization now handles per-km cable. |
| **OFC Stores** | 🟡 Partial | Items exist in the 907-depot file (operational) but the strategic 59 carry few OFC SKUs; `Asset_Type` classifier not yet wired into the strategic master. |
| **Relay Stores** | 🟡 Partial | Relays present (QBCA1/QSPA1) but no relay-specific shelf-life/test-cycle attributes. |
| **Track Circuit Stores** | 🟡 Partial | Rail-joint insulation present; no track-circuit-specific tuning/calibration fields. |
| **Point Machine Stores** | 🟡 Partial | "Ground connection for IRS Point Machine" present; no point-machine reliability/overhaul cycle modelling. |
| **Kavach Stores** | 🔴 Gap | No Kavach SKUs in the strategic set; `Asset_Type` keyword exists in config but unused here. |
| **IPS Stores** | 🔴 Gap | No IPS SKUs surfaced; battery/charger proxies only. |

**Key domain gap:** `Asset_Type` classification (relay/point-machine/axle-counter/EI/IPS/Kavach/OFC) is defined conceptually but **not computed in the strategic master**. Wiring it in is the single biggest domain-coverage lift.

---

## Section 6 — Power BI Review

**Built:** `page0_executive_dashboard.csv` (41 KPIs) and `page6_data_quality.csv` (5 KPIs).
**Not yet built (Step 7):** pages 1–5 (ABC, Demand, Criticality, Aging, Asset-Type / Optimization) referenced in the plan.

| Aspect | Finding |
|---|---|
| **Missing dashboards** | ABC, Criticality (incl. ABC×Criticality matrix — data already in `railway_abc_criticality_matrix.csv`), Demand/Forecast, Aging (needs Step 6 operational data), Optimization before/after. |
| **Missing KPIs** | Forecast Accuracy (MAE/MAPE roll-up exists per-SKU but not aggregated to a page), Service-level achieved vs target, Coverage-band rollup. |
| **Recommended visuals** | ABC×Criticality heat-matrix (4×4), procurement priority Pareto (priority vs cumulative %), coverage-band stacked bar, forecast-vs-AAC-vs-EAR clustered column, concentration donut (Top-10 vs rest). |
| **Recommended drill-downs** | Division → Depot → SKU; ABC → Criticality → SKU; Demand_Class → Confidence → SKU. |
| **Recommended executive views** | Single KPI banner from `page0`; "Where to focus" = Top-10 procurement (already exported); "Capital ask" = ₹1 cr scenario card. |

Strength: outputs are pre-aggregated (BI only visualises). Gap: a shared `dim_sku` would enable cross-page slicers.

---

## Section 7 — AnyLogistix Review

**Status: not yet generated** (Step 8). `railway/outputs/anylogistix/` is empty. Config defines the 6 divisions (MAS,TPJ,SA,MDU,PGT,TVC) and depot-stock columns (PER/ED/MDU/QLN/GOC/PTJ), and `load_division_consumption()` already reads division demand.

| AnyLogistix need | Readiness | Note |
|---|---|---|
| **Locations** | 🟡 Data ready | 6 divisions + 6 depots derivable; **no geo-coordinates** in source — needs a division/depot lat-long lookup. |
| **Products** | ✅ Ready | 59 SKUs with unit cost / ABC / criticality. |
| **Demand** | ✅ Ready | Division-wise consumption present (`EAR Consumptions`); allocate forecast by division share. |
| **Inventory Policy** | ✅ Ready | Safety stock / ROP / min-max per SKU already computed in Step 5. |
| Network optimization | 🟡 | Possible once locations have coordinates + lane/lead-time matrix. |
| Multi-echelon | 🟡 | Depot stock split exists; needs echelon hierarchy (division↔depot) modelled. |
| Depot optimization | 🟡 | Depot-wise stock columns available; demand is division-level — needs depot-level demand mapping. |
| Safety-stock placement | ✅ | Per-SKU SS ready to push to nodes. |

---

## Section 8 — Indian Railways Deployment Readiness

| Level | Score | Rationale |
|---|---|---|
| **Depot level** | **Partially Ready** | Strategic pipeline fully functional for one depot's vital list; operational pipeline (aging/dead stock for the 907-item depot file) is designed but **not yet built**. |
| **Division level** | **Partially Ready** | Division demand is ingested; division dimension not yet propagated into master/policy outputs; no per-division KPI rollups. |
| **Zonal level** | **Not Ready** | Single-zone (Southern) hard-coded; no multi-snapshot/zone lineage columns; config is single-zone. |
| **Indian Railways level** | **Not Ready** | Requires schema-driven ingestion, external config, automated validation, star-schema warehouse, and scale work (TD-001/004/008/010/012). |

---

## Section 9 — Top 20 Improvements (ranked by ROI)

| Rank | Improvement | Effort | Impact | Priority |
|---:|---|---|---|---|
| 1 | Add pytest suite (config helpers, lead-time tiers, blend, normalization) — fills empty `tests/` | Low | High | P0 |
| 2 | Schema validation contracts on every input/output (TD-004) | Low | High | P0 |
| 3 | Wire `Asset_Type` classifier into strategic master (domain coverage) | Low | High | P0 |
| 4 | Build operational pipeline (Step 6: aging/dead/slow/valuation) | Med | High | P0 |
| 5 | Build Power BI pages 1–5 (Step 7) from existing aggregates | Med | High | P0 |
| 6 | Vectorise `iterrows` loops in 3 core modules (TD-008) | Med | High | P1 |
| 7 | Generalise data-quality to a rule registry (TD-002) | Med | High | P1 |
| 8 | Add lineage columns `Snapshot_Date/Source_Workbook/Schema_Version` (TD-012) | Low | Med | P1 |
| 9 | AnyLogistix export + division/depot geo lookup (Step 8) | Med | High | P1 |
| 10 | Externalise config to YAML with per-zone overlays (TD-010) | Med | Med | P1 |
| 11 | Cap/flag `inf` Forecast_to_Stock_Ratio (TD-006) | Low | Med | P1 |
| 12 | Emit `Unfundable_HighValue` list from budget knapsack (TD-009) | Low | Med | P2 |
| 13 | Header-name workbook resolver with positional fallback (TD-001) | Med | Med | P2 |
| 14 | Period-consistent safety-stock option (TD-007) | Low | Med | P2 |
| 15 | Switch outputs to Parquet + single assembly step (TD-011) | Med | Med | P2 |
| 16 | Star-schema `dim_sku` + fact tables for BI/warehouse | Med | Med | P2 |
| 17 | Division-level KPI rollups for division deployment | Med | Med | P2 |
| 18 | Service-level-achieved vs target back-calculation | Med | Med | P2 |
| 19 | Shelf-life / overhaul-cycle attributes for relays, batteries, point machines | High | Med | P3 |
| 20 | Multi-zone ingestion + zonal config registry | High | High | P3 |

---

## Section 10 — Recommended Next Phase Roadmap

Toward a **Railway Enterprise Asset & Spare-Parts Optimization Platform**:

- **Phase 6 — Complete the single-depot platform (productionise).**
  Build the operational pipeline (aging/dead/slow/valuation), Power BI pages 1–5, and AnyLogistix exports. Add the pytest suite + schema contracts. Wire `Asset_Type`. *Exit: one depot fully analysed, dashboards live, tests green.*

- **Phase 7 — Multi-depot / division scale + engineering hardening.**
  Vectorise hotspots, externalise config to YAML with per-division overlays, add lineage columns, Parquet outputs, header-based schema resolver, data-quality rule registry. Roll up KPIs to division. *Exit: N depots in one division, repeatable ingestion, division dashboards.*

- **Phase 8 — Zonal → Indian Railways enterprise.**
  Star-schema warehouse, automated multi-snapshot/zone ingestion, multi-echelon AnyLogistix network with geo + lead-time matrices, service-level optimization at network scale, reliability/overhaul-cycle attributes per asset class. *Exit: zonal deployment, multi-zone roadmap proven.*

---

### Bottom line
The platform is **well-structured and readable (7.2/10)** with a clean domain-separated pipeline and honest, auditable data-quality handling. The principal debts are **absent automated tests, no schema validation, an unwired `Asset_Type`, and the not-yet-built operational/Power-BI/AnyLogistix layers** — all already on the Step 6–8 path. Architecturally it is **depot-ready, division-partial, zonal-not-yet** — and the scaling gaps are known, localised, and fixable without redesign.
