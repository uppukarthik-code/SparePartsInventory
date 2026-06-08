# Technical-Debt Remediation Report

**Date:** 2026-06-08 · Evidence: `technical_debt_remediation.csv` (25 items), `coverage_gap_analysis.csv`, `configuration_hardening_plan.csv`. Behavior-preserving; analytics untouched.

---

## 1. Posture
The debt is **structural/hygiene, not correctness** — none of it changes the audited formulas or outputs. It concentrates in four clusters: **(a) testing, (b) leaky/duplicated I/O, (c) hardcoded config/division, (d) repo clutter.** This phase already retired the single highest-impact item.

## 2. Top items and status (`technical_debt_remediation.csv`)
| ID | Finding | Impact | Status / Remediation |
|---|---|---|---|
| TD01 | 0 tests on STEP20–28 (9 modules) | **CRITICAL** | ✅ **seeded** — golden-file (536 pinned) + SS/ROP/SRRS invariants (3) green; extend per `testing_implementation_plan.csv` |
| TD02 | Leaky dep: planning imports `demand_reconstruction._sheet_rows` (private I/O) | High | extract `ingestion/xlsx_reader.py` — **highest-leverage refactor** |
| TD03 | God-module `management_reports.py` (1548 LOC) | High | split into `reporting/` |
| TD04 | Flat 35-module package | High | layered package (`architecture_migration_plan.csv`) |
| TD05 | MAS extension hardcoded → blocks TPJ | High | config-driven division registry |
| TD06 | 17+ one-off drivers, no orchestrator | High | CLI/DAG over `run()` fns |
| TD07 | 88 root `.md` + 430 MB M5 clutter | Med | `docs/` + delete M5 |
| TD08 | 3 dup XLSX readers + 2 PL-normalizers | Med | centralize in `ingestion/` |
| TD09 | Constants bypass config | Med | centralize (`configuration_hardening_plan.csv`) |
| TD10 | Unpinned deps + 3 unused (sklearn/prophet/seaborn) | Med | pin/split/remove |
| TD11 | No `pyproject`/`setup` (not installable/CI) | Med | add `pyproject.toml` |
| TD12–25 | silent-failure `except→0.0`, fragile DMTR regex, `np.median([])` guard, silent depot drop, no logging, no boundary schema-validation, embedded criticality, repeated re-reads, per-driver SHA tree, mixed output namespace, no lock file | Low–Med | see CSV — all behavior-preserving |

## 3. The decisive move
**Extract `ingestion/` shared-I/O first.** It resolves TD02 (leak) **and** TD08 (3 duplicate readers + 2 PL-normalizers) in one refactor, and gives every layer a single, testable I/O surface. Do it behind the green suite: the 536 pinned outputs prove the extracted reader produces byte-identical results.

## 4. Sequence (each step gated by the green suite)
1. ✅ Tests (TD01) — done.
2. Cleanup TD07/TD10 (archive M5/reports/drivers, pin deps) — no logic change.
3. `ingestion/` extraction TD02/TD08 — re-run producers, suite must stay green.
4. Layering TD03/TD04 + god-module split — move-and-verify.
5. Config/division TD05/TD09 — parametrize, MAS outputs unchanged.
6. Packaging/CI TD11 + hardening TD12–25.

**Coverage gaps to close next** (`coverage_gap_analysis.csv`): ingestion parsers, demand reconstruction conservation, SBC cutoffs, forecast routing, lead-time winsor/median edges — all currently 0%.
