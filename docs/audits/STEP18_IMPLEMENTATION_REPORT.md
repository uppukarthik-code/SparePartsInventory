# STEP 18 — Multi-Business-Unit Implementation Report

**Generated:** 2026-06-08
**Status:** ✅ **IMPLEMENTED & VALIDATED**
**Scope guard:** Implementation focused ONLY on (1) context-based path parameterization,
(2) Business-Unit input scoping, (3) BU output isolation, (4) enterprise aggregation.
**No analytical / KPI / SRRS / forecasting / procurement / reporting code was modified** — the
entire analytics layer runs unchanged; scoping and isolation are achieved from the orchestration
layer only.

---

## 1. What Was Built

| File | Role |
|---|---|
| **`railway/railway_context.py`** (NEW) | `use_context(BU)` context manager — redirects all I/O bindings to `outputs/<BU>/` and restores them on exit. Patches the 7 `cfg` path constants **and** the 20 module-level frozen `OUT`/`PBI`/`ENTERPRISE_DIR`/… captures. |
| **`railway/railway_business_unit_runner.py`** (NEW) | Discovers domains/BUs, loads workbooks once, scopes operational by depot→BU, runs the existing 12-module pipeline per BU into `outputs/<BU>/`, and builds the enterprise roll-up. |
| **`railway/tests/test_business_unit_runner.py`** (NEW) | 9 tests: context redirect/restore, depot routing, MAS reproduction (rows + KPIs), data-less skeleton, roll-up. |

**Analytical modules touched: 0.** The runner drives them via monkey-patched paths/loaders.

## 2. How "No Analytical Change" Was Achieved

The STEP18 assessment identified two blockers: (a) fixed global paths, several **frozen at import**
(`OUT = cfg.OUTPUT_DIR`), and (b) no input scoping. Both are solved from outside the analytics:

1. **Path context (`railway_context.use_context`)** — on entry, saves & overrides:
   - `cfg.OUTPUT_DIR/POWERBI_DIR/ANYLOGISTIX_DIR/DEMAND_HISTORY_CSV/SKU_MASTER_CSV/FORECAST_CSV/INVENTORY_POLICY_CSV`
   - the frozen captures in `powerbi_export, enterprise, anylogistix_export, management_reports, dashboard_validation, srrs_validation, audit_trail` (incl. `ENTERPRISE_DIR/ENTERPRISE_PBI/REPORTS_DIR/TRAIL_PATH`).
   - On exit every original binding is restored (even on exception).
2. **Data scope + load-once (runner)** — `railways.xlsx` + `stock_summary.xlsx` are parsed **once**;
   the raw loaders (`dp.load_strategic_stock/safety_vital/division_consumption/operational_stock`,
   `dq.load_units`) are monkey-patched to serve cached copies. In multi-BU mode the **operational**
   frame is filtered by `resolve_business_unit(Depot)`; the analytics receive scoped data unchanged.

## 3. Execution Semantics (honest to the data)

Per the STEP18 assessment, the **strategic** universe is zone-consolidated (59 items, shared) and the
**operational** universe is depot-granular (partitionable):

| Mode | Behaviour |
|---|---|
| **Single-BU (`run()` / `run(["MAS"])`)** | Consolidated: full dataset, **no scoping** → `outputs/MAS/` is **byte-for-byte identical** to the canonical tree. |
| **Multi-BU (`run(["MAS","TPJ"])`)** | Operational partitioned by depot→BU; strategic shared. BUs with data → full scoped pipeline; **data-less BUs → non-crashing skeleton** (`BU_STATUS.json`). Enterprise roll-up across processed BUs. |

**Data reality discovered:** all 907 operational rows carry a single depot (`…/PER…` → **MAS**), so the
operational universe is entirely MAS today; **TPJ** is `Status: Configured` with **no operational data
yet**. The runner therefore processes MAS fully and emits a TPJ skeleton — faithfully reflecting the
platform's onboarding model (MAS Live, TPJ Configured). Onboarding TPJ data later requires **zero code
change** (the depot→BU routing `GOC/PTJ → TPJ` is already configured and unit-tested).

## 4. Findings

| # | Finding | Resolution |
|---|---|---|
| F1 | Several modules **freeze** `OUT/PBI`/`ENTERPRISE_DIR` at import → patching `cfg` alone is insufficient. | Context patches both `cfg` and the 20 frozen module captures. |
| F2 | Hidden dependency: `enterprise.published_domain_kpis()` reads `anylogistix/digital_twin_readiness.csv` → anylogistix_export must precede enterprise. | Runner pipeline ordered `… powerbi_export → anylogistix_export → enterprise → explainability`. |
| F3 | One canonical file (`anylogistix/procurement_scenarios.csv`) was **stale** (pre-Step-15, never regenerated). | Refreshed the canonical tree with current code; runner reproduces the current-code output. |
| F4 | Operational source is **single-depot (all MAS)**; analytics crash on an empty universe. | Runner guards: data-less BU → skeleton (no crash), no analytical modification. |
| F5 | `reports/`, `data_lineage_report.csv`, `step11_*` are **stateful/append** logs (not byte-reproducible). | Excluded from the byte-identical scope and from the per-BU runner (separate entry points). |

## 5. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Loader monkey-patch could perturb bytes | — | Cached `.copy()` returns identical data; proven 64/64 byte-identical. |
| Context not restored on error | Low | `finally` restores all bindings; `test_context_restores_on_exception`. |
| Strategic shared (not divisible) across BUs | Inherent (data) | Documented in STEP18 assessment; operational is the partitionable universe. |
| Data-less BU skeleton may surprise users expecting full TPJ analytics | Low | `BU_STATUS.json` states reason; routing is ready for real TPJ data. |
| Auxiliary layers (anylogistix readiness MD, management reports) write to context-relative paths | Low | Non-CSV reports only; core CSV/KPI/Power BI outputs unaffected. |

## 6. Validation Results

| Check | Result |
|---|---|
| `outputs/MAS/` vs current-code canonical | ✅ **BYTE-IDENTICAL 64/64** (0 changed, 0 missing) |
| MAS KPIs == canonical KPIs (page0) | ✅ identical |
| MAS strategic rows / operational rows | ✅ 59 / 907 |
| MAS + TPJ split executes | ✅ MAS full, TPJ skeleton, no crash |
| Enterprise roll-up | ✅ `_enterprise_rollup/` (959 registry rows, BUs=[MAS]) |
| Context redirect + restore (incl. on exception) | ✅ |
| Existing pytest suite | ✅ 82 passed / 1 skipped (unchanged) |
| New runner tests | ✅ 9 passed → **91 passed / 1 skipped total** |
| schema / lineage V1–V6 / SRRS A–H on canonical | ✅ all pass |

## 7. Before/After Runtime

No analytical compute changed, so per-BU runtime ≈ the native pipeline (~4 s). The runner loads each
workbook once and reuses cached frames across BUs, so an N-BU run does **not** re-parse the workbooks N
times. Measured: single MAS run ≈ 4 s; MAS+TPJ ≈ 4 s (TPJ skeleton is near-instant).

## 8. Backward-Compatibility Verification

| Guarantee | Evidence |
|---|---|
| Existing analytics unchanged | 0 analytical files modified; 64/64 byte-identical outputs |
| KPI values unchanged | page0 KPIs identical (test + hash) |
| Power BI outputs unchanged | page0–9 + op_* + enterprise/powerbi byte-identical |
| Reports unchanged | enterprise reports reproduced; stateful logs out of scope |
| MAS baseline reproduced | byte-for-byte (64/64) |
| MAS + TPJ supported | runner accepts both; MAS full, TPJ skeleton; roll-up produced |
| Default behaviour preserved | importing the new modules has no effect until `use_context` is entered |

---

## 9. Conclusion

A context layer + BU runner deliver multi-Business-Unit execution with **per-BU output isolation**,
**load-once ingestion**, and **enterprise aggregation** — while the analytics, KPIs, SRRS, forecasting,
procurement logic, reporting and Power BI schemas remain **byte-for-byte unchanged** (`outputs/MAS/`
reproduces the canonical tree exactly). The platform is ready to onboard additional divisions (TPJ, SA,
…) by adding their depot data — no code change required. See `STEP18_VALIDATION_REPORT.md` for the
proof matrix.
