# STEP 31 — Reporting Cut-Over Report

**Date:** 2026-06-08 · Reporting architecture only; additive + backward-compatible. Strategy: **strangler-fig** (approved Fork A). Evidence: `reporting_inventory.csv`, `reporting_cutover_design.csv`, `reporting_validation.csv`, `reporting_backward_compatibility.csv`, regression + formula suites.

---

## 1. The constraint that shaped the design
The two legacy reporting modules are invoked by the `business_unit_runner` orchestrator and own **60 pinned reporting outputs** (executive_kpi_summary, page0_executive_dashboard, executive_top10_*, page8/9, management_action_plan — across all 6 divisions). A literal "replace the computation" would change all 60 → break the non-negotiable "regression must remain green / no output changes." Resolved with a **strangler cut-over**: a single modern engine becomes the source of truth while the legacy outputs stay byte-identical behind a deprecation boundary.

## 2. What changed (all additive)
| Module | Change | Pinned outputs |
|---|---|---|
| `railway/governance/division_summary.py` | **enhanced** — `--division` CLI, `build_all_divisions()` roll-up, `has_data()` guard | n/a (new) |
| `railway_executive_summary.py` | **+** delegating `kpis()`/`summary()` → division_summary, deprecation boundary | **unchanged (byte-identical)** |
| `railway_management_reports.py` | **+** delegating `modern_kpis()`/`modern_summary()`, deprecation boundary | **unchanged** |

`build_kpis()` / `collect_kpis()` / `run()` were **not modified** — proven byte-identical (`executive_kpi_summary.csv` re-run hash matched).

## 3. Single source of truth — proven
`es.kpis() == mr.modern_kpis() == division_summary.compute_kpis()` → **True** (object equality). Every modern consumer — the 3 rebuilt notebooks, executive reporting, management reporting, the division summary — now derives from **one** L1/L2/L3 engine. No modern KPI is computed twice (`reporting_validation.csv`).

## 4. Backward compatibility — proven
- Forecasting / demand / lead-time / criticality / SS / ROP / SRRS outputs: **unchanged**.
- 60 pinned reporting outputs: **unchanged**.
- **Regression 537/537 + formula 3/3 = 541 green** (PYTHONHASHSEED=0).
- All edits additive (imports + new functions + deprecation comments).

## 5. Verdicts
- **Legacy reporting fully retired?** *Functionally* yes — no modern consumer depends on it; the legacy compute is **frozen behind a deprecation boundary** for output compatibility. *Physical* removal (and the consequent re-pin of the 60 outputs) is deliberately deferred to the repository-purification phase.
- **division_summary the source of truth?** **Yes.**
- **Analytics changed?** **No.** **Regression green?** **Yes.**

## 6. Verdict
**Reporting cut-over complete (strangler).** One engine, one KPI source of truth, division-aware, zero analytics change, zero output change, regression green.
