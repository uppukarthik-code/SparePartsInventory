# Architecture Hardening Report

**Date:** 2026-06-08 · Evidence: `active_dependency_map.csv`, `architecture_migration_plan.csv`, `repository_lineage.csv`. Behavior-preserving; analytics untouched.
*(Supersedes the prior audit-only version: adds the empirical import graph, the STEP1–19=core reframe, and the now-built regression oracle.)*

---

## 1. Current architecture (as-is, empirically mapped)
```
railway/   (FLAT — 35 modules, no sub-packages)
  railway_config.py                 <- fan-in 31 (universal shared infra)
  railway_inventory_optimization.py <- fan-in 6 (shared SS/ROP/SRRS engine; reused by srrs_mas)
  railway_data_preparation.py       <- fan-in 6 (loaders + _xlsx_rows_via_xml reader)
  railway_demand_reconstruction.py  <- fan-in 4  *** its PRIVATE _sheet_rows is imported by
                                                     safety_stock / rop / srrs_mas / lead_time ***
  24 ACTIVE_CORE_PLATFORM (STEP1-19)  +  8 ACTIVE_MAS_EXTENSION (STEP20-28)  — intermixed
  tests/ (legacy unit tests)  +  tests/regression/ + tests/inventory/ (NEW, this phase)
root/  _step*_run.py x18 (manual orchestration)  +  *.md x88 (reports)
raw_data/  railway sources  +  430MB dead M5 data
(no pyproject; no orchestrator; no logging)
```

### Three structural problems (ranked)
1. **Leaky / inverted dependency (worst smell).** `safety_stock`, `rop`, `srrs_mas`, `lead_time_derivation` import `railway_demand_reconstruction` **solely for its private `_sheet_rows` XLSX reader** — a demand-layer private function is the de-facto shared I/O for the prioritization layer. Confirmed by import graph (fan-in 4, all for I/O).
2. **No layering.** 35 modules in one namespace; the 24 core (STEP1–19) and 8 MAS-extension (STEP20–28) are indistinguishable by location.
3. **God-module.** `railway_management_reports.py` = 1,548 LOC.

## 2. Target architecture (`architecture_migration_plan.csv`)
```
railway/
  ingestion/      xlsx_reader, dmtr_parser, pl_codes, summary_loader   (ALL shared I/O — single source)
  validation/     schema, backward_compat (the SHA-256 oracle lives here)
  demand/         reconstruction, classification
  forecasting/    generation            (reuses forecasting engine)
  inventory/      lead_time, safety_stock, rop, optimization (shared engine)
  prioritization/ srrs, value_exposure
  reporting/      (split from management_reports), powerbi, exports
  governance/     enterprise, pl_master, audit_trail, business_unit_config, context, strategic_allocation
  shared/         config
  legacy/         (only if a module is proven non-railway — currently NONE; STEP1-19 stay core)
tests/  unit + golden-file + e2e        scripts/ orchestrator + legacy/ drivers
docs/   the 8 platform docs + archived reports        pyproject.toml
archive/walmart/ (notebooks 01-06)   |   (M5 data removed)
```
**Dependency rule:** layers depend only downward (ingestion → demand → forecasting → inventory → prioritization → reporting); **no planning module imports a demand module for I/O.**

## 3. The hardening sequence (test-first — now executable)
The non-negotiable rule (no behavior change, SHA-256 before/after) was previously **unverifiable** — zero tests existed. This phase built the oracle:
- `tests/regression/` — **536 outputs pinned, 537 green**.
- `tests/inventory/` — SS/ROP/SRRS re-derived from inputs, **3 green**.

With the oracle green, the highest-leverage move is **extracting `ingestion/`** (kills the leaky dependency + 3 duplicate readers at once), then **layering**, then the **orchestrator**, then **god-module split** — each move re-runs the suite, which must stay byte-green. The map is in `architecture_migration_plan.csv`.

## 4. Verdict
Clean at the boundary that mattered for the prior audit (no Walmart contamination; correct formula reuse) but immature for maintenance: flat, leaky, god-moduled, manually orchestrated. **Architecture 45 → 75** is reachable via the `ingestion/`-first sequence — and is now *safe* to start because behavior-preservation is provable.
