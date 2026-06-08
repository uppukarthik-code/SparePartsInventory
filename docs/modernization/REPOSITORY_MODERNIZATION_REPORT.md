# Repository Modernization Report

**Type:** Technical-debt / modernization audit (NOT inventory-theory). **Read-only — no code/outputs modified.**
**Date:** 2026-06-08 · **Lens:** a railway engineer must maintain this for 5 years. Adversarial; debt assumed until disproven.

---

## 1. Executive modernization verdict
The repository is **functionally correct and reproducible** (the analytics work, outputs are deterministic and backward-compatible) but **structurally immature**: a flat 35-module package with no layering, a leaky I/O dependency, a 1,548-LOC god-module, **zero tests on the entire STEP18A–28 pipeline**, 17 one-off driver scripts and 84 reports cluttering the repo root, 430 MB of dead Walmart/M5 data, hardcoded constants bypassing the config, and unpinned dependencies. **It is maintainable by its author, but NOT by a new engineer without modernization.** Overall scorecard **45.5/100**.

## 2. Repository inventory (Part A — `repository_modernization_inventory.csv`)
35 railway modules (26 legacy STEP1–17 + 9 new STEP18A–28) · 10 test files (legacy only) · 17 root drivers · 7 notebooks (6 Walmart + 1 railway) · 84 root `.md` · 56 history CSVs · `requirements.txt` (unpinned) · 430 MB unused M5 CSVs · **no `pyproject.toml`/`setup.py`**.

## 3. Top-20 technical-debt findings
1. **0 / 9 STEP18A–28 modules tested** (safety_stock, rop, srrs, lead_time, demand_reconstruction…).
2. **Leaky dependency:** planning modules import `railway_demand_reconstruction._sheet_rows` (private I/O) — cross-layer coupling.
3. **God-module** `railway_management_reports.py` = 1,548 LOC.
4. **Flat package** — 35 modules, no sub-packages / layering.
5. **17 one-off drivers**, no orchestrator; manual run order.
6. **84 `.md` reports at repo root** — clutter.
7. **430 MB dead M5 data** in `raw_data/`.
8. **6 obsolete Walmart notebooks** (01–06).
9. **Duplicated logic** — 3 XLSX readers, 2 PL-normalizers, repeated `rd()`/regex/SHA-tree.
10. **Hardcoded constants** (DAYS_PER_MONTH, service levels, 0.5/2.0 thresholds, weights, depot `027534`, dated filename) bypass config.
11. **Dead/divergent config** — `cfg.SERVICE_LEVEL_TABLE`/`CRITICALITY_STOCKOUT_WEIGHT` unused by STEP24–26.
12. **Unpinned deps** + 3 unused runtime libs (sklearn, prophet, seaborn) + notebook libs mixed in.
13. **No packaging** (`pyproject`/`setup`) → not installable / CI-ready.
14. Bare `except → 0.0` **silent failures** (qty/value/date parse).
15. **Fragile regex** parsing of DMTR (breaks on format change).
16. **Latent crash** — `np.median([])` if winsor clips all intervals.
17. **Silent depot drop** — non-027534 rows ignored without warning.
18. **No logging** framework (print-only).
19. **Single division hardcoded** — no parametrization for rollout.
20. **Repeated file re-reads** (SUMMARY, 54 DMTRs) across modules.

## 4. Top modernization opportunities (Part L — ranked)
**Quick wins (<1 day):** archive M5 data; move 84 reports → `docs/`; archive 17 drivers → `scripts/legacy/`; pin & split `requirements`.
**Short (<1 wk):** centralize XLSX-reader + PL-normalize + CSV-loader + all constants; add `pyproject.toml`.
**Medium (<1 mo):** **unit + golden-file tests** (SS/ROP/SRRS/lead-time/demand) — top priority; **layered package refactor**; pipeline orchestrator; split god-module.
**Major (>1 mo):** CI + logging + schema validation; multi-division parametrization.

## 5. Modernization roadmap (Part N — `modernization_roadmap.csv`)
P1 Immediate cleanup (<1wk) → P2 Architecture cleanup (2–4wk) → P3 Testing framework (2–4wk) → P4 Production hardening (3–6wk) → P5 Enterprise-scale readiness (6–12wk).

## 6. Go / No-Go (long-term maintainability)
**NO-GO as-is** for hands-off 5-year maintenance. **GO after Phases 1–3** (cleanup + layering + tests) — the analytics are sound; the debt is structural and addressable without touching formulas. Details in `TECHNICAL_DEBT_REPORT.md`, `ARCHITECTURE_HARDENING_REPORT.md`, `FIVE_YEAR_MAINTAINABILITY_REPORT.md`.
