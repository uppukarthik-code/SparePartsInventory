# STEP35-OPT — Validation Report

**Date:** 2026-06-09
**Branch:** `step35-opt-enterprise-budget-optimization`
**Runs:** `PYTHONHASHSEED=0`, pandas 3.0.3 / numpy 2.4.6 / scipy 1.17.1 / pulp 3.3.2 (all match `requirements.txt`).

---

## 1. Test floor — NO NEW FAILURES (corrected baseline)

The baseline was **pre-existing RED** before any STEP35-OPT work (root-caused below). The agreed floor is *no-new-failures*: the pre-existing failing set must be unchanged, all new tests pass, zero regressions.

| Metric | Baseline (commit `2bf6e82`) | Final (this branch) | Δ |
|---|---|---|---|
| Passed | 88 | **103** | **+15** (all new STEP35-OPT tests) |
| Failed | 544 | **544** | **0** (identical set) |
| Skipped | 1 | 1 | 0 |

- **New failures introduced:** **0** (`comm -13 baseline final` → empty).
- **Previously-passing tests flipped:** **0** (`comm -23 baseline final` → empty).
- The 544 failing tests are **byte-for-byte the same set** before and after. ✅ Floor satisfied.

### Why the baseline is red (pre-existing, NOT caused by STEP35-OPT)
1. **~537 golden-output failures = line-ending defect.** Committed output CSVs are **LF** (e.g., `MAS/railway_procurement_plan.csv` = 1993 bytes, sha `b91d…`); `golden_output_manifest.csv` pinned the **CRLF** rendering (2021 bytes, sha `27de…`). `LF→CRLF` of the current file reproduces the manifest hash exactly — **content is identical; only EOL differs.** `.gitattributes` `* -text` + committed-as-LF blobs is the inconsistency. This predates this work.
2. **~7 stale-fixture failures.** `test_mas_operational_rows` expects 907, gets 15913; `page5_rationalization` expects 959, gets 5351; one schema-validation failure. The fixtures encode row counts from an older/smaller dataset (matches the project memory note "stale fixtures … not regressions").

Per user decision, the baseline was **left untouched** (no manifest re-pin, no fixture edits). Remediation is recommended for v1.1 (see report §6.7).

---

## 2. Existing optimization outputs unchanged (golden set)

`python -m pytest railway/tests/regression/test_golden_outputs.py -q` → the SAME ~537 pre-existing line-ending failures, **no more, no fewer**. STEP35-OPT:
- Never rewrote an existing output (no pinned-hash flips).
- Added only NEW CSVs (not in the manifest) → `test_no_unexpected_new_outputs` lists them as info, never fails.

`optimization_baseline_validation.csv` records all optimizer aspects (decision variables, objective, budget constraint, affordability filter, safety reserve, explainability, default budget, service-factor model) as **UNCHANGED**.

---

## 3. No duplicate optimizer

- `railway/procurement_optimizer.py` — **absent** ✅
- Executable `LpProblem`/`LpVariable`/`PULP_CBC_CMD` outside the single source of truth `railway_inventory_optimization.py`: **none.** The only match (`enterprise_allocation.py:212`) is a **string-literal documentation row**, not code.
- All three new primitives delegate to the existing `allocate_with_reserve`/`_solve_knapsack`.

---

## 4. Reproducibility

Each builder was run twice (`PYTHONHASHSEED=0`); all 8 new CSVs are **byte-identical across runs** (SHA-256 confirmed per cluster). PuLP CBC is deterministic; sorts are stable.

---

## 5. Notebook execution

`jupyter nbconvert --to notebook --execute --inplace` on both notebooks (kernel CWD = `notebooks/`):
- `notebook_railway.ipynb` — executed end-to-end, **no errors** (34 → 36 cells; Section 17 + 6 figures).
- `notebook_railway_executive.ipynb` — executed end-to-end, **no errors** (18 → 20 cells; Section 17 + 3 figures).
- Figures are generated from live `railway/outputs/*.csv`; no hardcoded values.

---

## 6. Per-phase results

| Phase | Deliverable | Status |
|---|---|---|
| A — baseline validation | `optimization_baseline_validation.csv` | ✅ PASS (all aspects UNCHANGED) |
| B — budget frontier | `risk_reduction_frontier.csv` (9 levels, 7 metrics) | ✅ PASS (monotonic; 0 budget violations) |
| C — efficiency / knee | `budget_efficiency_analysis.csv` (knee ₹50 Cr) | ✅ PASS |
| D — enterprise allocation | `enterprise_budget_allocation.csv` + `enterprise_budget_allocation_readiness.csv` | ⚠️ PASS (mechanism); divisions non-differentiated in current data |
| E — multi-year roadmap | `procurement_roadmap.csv` (3 years) | ⚠️ PASS; equal-thirds default degenerate (tune `ANNUAL_PROCUREMENT_BUDGET`) |
| F — executive scenarios | `executive_budget_scenarios.csv` (5 scenarios) | ✅ PASS |
| G — notebook Section 17 | both notebooks | ✅ PASS (execute clean) |
| H — board dashboard | `enterprise_decision_dashboard.csv` (7 KPIs) | ✅ PASS |
| I — validation | this report + `STEP35_OPT_REPORT.md` | ✅ PASS |

---

## 7. New output files

| File | Rows (data) |
|---|---|
| optimization_baseline_validation.csv | 8 |
| risk_reduction_frontier.csv | 9 |
| budget_efficiency_analysis.csv | 9 |
| enterprise_budget_allocation.csv | 54 (9 budgets × 6 divisions) |
| enterprise_budget_allocation_readiness.csv | 6 |
| procurement_roadmap.csv | 3 |
| executive_budget_scenarios.csv | 5 |
| enterprise_decision_dashboard.csv | 7 |

---

## 8. Commits (9, branch only — not merged/pushed)

```
c40d9a6 feat(step35-opt): notebook Section 17 — enterprise capital allocation visuals
42264b5 feat(step35-opt): enterprise decision dashboard KPIs in division_summary
4f7d2f2 feat(step35-opt): generate enterprise optimization deliverable CSVs
3ff43d6 feat(step35-opt): enterprise_allocation orchestration module
c10b935 refactor(step35-opt): module-level math import + empty-input/budget-bound tests
7da8d43 feat(step35-opt): add procurement_roadmap multi-year sequencing
45a5659 feat(step35-opt): add enterprise_capital_allocation pooled knapsack
9f4ef46 feat(step35-opt): add solve_budget_frontier reusing existing knapsack
cc5d188 feat(step35-opt): add enterprise budget optimization config constants
```

**Modified existing files (all append-only, 0 deletions of pre-existing lines):** `railway/railway_config.py`, `railway/railway_inventory_optimization.py`, `railway/governance/division_summary.py`, `notebooks/notebook_railway.ipynb`, `notebooks/notebook_railway_executive.ipynb`.
**New files:** `railway/governance/enterprise_allocation.py`, `railway/tests/test_enterprise_allocation.py`, 8 output CSVs, 2 reports.

---

## Verdict

**STEP35-OPT is implemented, additive, reproducible, and introduces zero test regressions** (15 new passing tests; pre-existing 544-failure baseline unchanged). The enterprise frontier, efficiency, scenarios, and decision dashboard are board-ready. Cross-division allocation and the multi-year roadmap are mechanically correct but require (a) genuinely partitioned per-division data and (b) a realistic annual budget cap to yield actionable divisional/temporal advice. The pre-existing baseline defects (line-ending manifest + stale fixtures) are documented and recommended for a separate v1.1 fix.
