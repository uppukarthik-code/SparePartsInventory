# Railway Platform Modernization Report

**Program:** FULL RAILWAY PLATFORM MODERNIZATION · **Date:** 2026-06-08
**Constraint honored:** no analytical / forecasting / inventory / lead-time / safety-stock / ROP / SRRS behavior changed. All work this phase is **additive** and behavior-preserving; a SHA-256 golden-file guard now proves it.
**Scope correction applied:** STEP1–19 are treated as **ACTIVE PRODUCTION RAILWAY CODE**, not legacy — *no* STEP1–19 component is classified legacy merely for Walmart-era origin.

---

## 1. What this phase delivered (additive, zero behavior change)
| Deliverable | Status |
|---|---|
| Phase-0 lineage + dependency graphs | `repository_lineage.csv`, `active_dependency_map.csv` |
| Cleanup / archive plan | `cleanup_manifest.csv` |
| Layered-architecture migration plan | `architecture_migration_plan.csv` |
| Multi-division readiness | `multi_division_readiness.csv` |
| Testing plan + coverage gaps | `testing_implementation_plan.csv`, `coverage_gap_analysis.csv` |
| Config hardening plan | `configuration_hardening_plan.csv` |
| Tech-debt remediation (25) | `technical_debt_remediation.csv` |
| 5-yr maintainability | `five_year_maintainability_assessment.csv` |
| Scorecard (9 dims) | `platform_scorecard.csv` |
| **Golden-file regression harness** | `railway/tests/regression/` — **536 outputs pinned, 537 tests green** |
| **P0 formula-invariant tests (SS/ROP/SRRS)** | `railway/tests/inventory/` — **3 green** |
| 8 platform docs | `README.md`, `ARCHITECTURE.md`, `DATAFLOW.md`, `STEP1_TO_STEP28_LINEAGE.md`, `DIVISION_ONBOARDING_GUIDE.md`, `TESTING_GUIDE.md`, `OPERATIONS_GUIDE.md`, `MAINTENANCE_GUIDE.md` |

## 2. Lineage reframe (the headline finding)
Empirical import-graph classification of 35 modules:
- **ACTIVE_CORE_PLATFORM (24)** — STEP1–19 railway analytics + the multi-division scaffolding (`business_unit_config`/`runner`/`context`, proven across 6 divisions in STEP18A). **Not legacy.**
- **ACTIVE_MAS_EXTENSION (8)** — STEP20–28 MAS planning (`demand_reconstruction`, `demand_classification`, `forecast_generation`, `lead_time_derivation`, `pl_master`, `safety_stock`, `rop`, `srrs_mas`). Active, but **hardcoded to MAS**.
- **SHARED_INFRASTRUCTURE** — `railway_config` (fan-in 31).
- **LEGACY_HISTORICAL / DEAD** — only the 6 Walmart notebooks + 430 MB M5 data + 3 unused deps (sklearn/prophet/seaborn = 0 imports).

## 3. Why the refactor is now *safe to start* (it wasn't before)
A behavior-preserving refactor is impossible to verify without a regression oracle. There were **zero tests on the STEP20–28 pipeline**. This phase built that oracle first:
- **536 output CSVs pinned by SHA-256** → any byte change after a refactor fails the suite and must be explained or reverted.
- **SS/ROP/SRRS re-derived from inputs** → the *math* is pinned independent of code structure, so modules can move without silent drift.

This is the gating prerequisite the non-negotiable rule requires. **The actual layered refactor (moving modules, rewriting imports) is staged and ready, but remains behind explicit approval** — see `architecture_migration_plan.csv` and §5.

## 4. Scorecard (current → target)
Mean **43.9 → 76.7** across 9 dimensions (`platform_scorecard.csv`). Largest gaps: Testing 25→75 (harness now seeded), Architecture 45→75, Production-Readiness 40→75. Documentation 50→80 is largely closed *this phase* by the 8 docs.

## 5. Recommended execution order (test-first, behavior-preserving)
1. **[DONE] Build regression + formula oracle** — green.
2. Quick wins (no code-logic change): archive M5 (430 MB) + 88 reports → `docs/`, archive 18 drivers, pin/split deps. *Run suite after.*
3. Extract `ingestion/` shared-I/O (kills the leaky `_sheet_rows` dependency + 3 duplicate readers) — **highest-leverage**. *Run suite.*
4. Layer the package per `architecture_migration_plan.csv`; split the 1548-LOC god-module. *Run suite after every move.*
5. Centralize config; parametrize the MAS extension for multi-division. *Run suite.*
6. Add `pyproject.toml` + CI that runs the suite on every push.

**No formula or output may change in steps 2–6; the green suite is the proof.** Companion reports: `ARCHITECTURE_HARDENING_REPORT.md`, `MULTI_DIVISION_READINESS_REPORT.md`, `TECHNICAL_DEBT_REMEDIATION_REPORT.md`.
