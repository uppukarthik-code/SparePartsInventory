# Technical-Debt Report

**Date:** 2026-06-08 · Read-only. Evidence-backed; adversarial. CSVs: dead_code, duplicate_logic, configuration, error_handling, dependency, performance.

---

## 1. Dead code (Part B — `dead_code_audit.csv`)
| Item | Class | Action |
|------|-------|--------|
| M5 raw CSVs (430 MB) | **Dead** | delete / archive out of repo |
| Notebooks 01–06 (Walmart) | Dormant/Obsolete | archive `archive/walmart/` |
| Notebook 07 (railway) | Dormant | archive or convert to doc |
| 17 root `_step*`/`_*_audit` drivers | Dormant | archive `scripts/legacy/` (keep for provenance) |
| `cfg.SERVICE_LEVEL_TABLE`, `CRITICALITY_STOCKOUT_WEIGHT` | Dormant/divergent | consolidate or mark legacy |
| `prophet`, `scikit-learn`, `seaborn` (runtime deps) | **Dead** (0 imports in railway/*.py, verified) | remove from runtime requirements |
| `railway_performance_test.py`, `railway_regression.py` | Dormant | keep, archived |

**Safe to remove now:** 430 MB M5 data + 3 unused runtime deps. **Archive:** Walmart notebooks + one-off drivers.

## 2. Duplicate logic (Part C — `duplicate_logic_audit.csv`)
- **Raw-XLSX reader × 3** (`_xlsx_rows_via_xml`, `_sheet_rows`, `read_rows`) → one `ingestion/xlsx_reader.py`.
- **PL normalization × 2** (`_norm_pl`, `normalize_pl`) → `ingestion/pl_codes.py`.
- **CSV loader `rd()`/`_read`** repeated 8+ places → `io.read_pl_csv()`.
- **DMTR date/qty regex** duplicated → `ingestion/dmtr_parser.py`.
- **SHA-256 `tree()`** reimplemented in **every** driver → `testing/backward_compat.py`.
- *(service_factor/SS/ROP are correctly reused, not duplicated.)*

## 3. Configuration debt (Part F — `configuration_audit.csv`)
Magic constants live in modules, not config: `DAYS_PER_MONTH=30.4375`, service levels `{0.95/0.85}`, status thresholds `0.5×/2.0× ROP`, weights `{10/5/1}`, depot `'027534'`, the dated SUMMARY filename, the 12-month HORIZON labels. `cfg.SERVICE_LEVEL_TABLE`/`CRITICALITY_STOCKOUT_WEIGHT` exist but are bypassed. → **single source of truth in `railway_config`**; parametrize per division.

## 4. Error-handling debt (Part G — `error_handling_audit.csv`)
Bare `except → 0.0/None` (silent parse failures); `np.median([])` latent crash; silent non-027534 depot drop; fragile DMTR regex; print-only (no logging); no CSV schema validation at module boundaries. → explicit validation + logging + guards + quarantine of bad rows.

## 5. Dependency debt (Part J — `dependency_audit.csv`)
`requirements.txt` **unpinned**, no lock file, mixes runtime + notebook + dev libs. **Unused runtime:** sklearn, prophet, seaborn (0 imports). → pin all; split `requirements.txt` (runtime) / `requirements-notebooks.txt` / dev extras; add lock.

## 6. Performance debt (Part I — `performance_audit.csv`)
Mostly **Low** impact (small data, batch): SUMMARY re-read by 3 modules + audits (Medium); 54 DMTRs re-parsed by demand + lead-time (Medium); per-driver full-tree SHA-256 (Low-Med); `iterrows` builders (Low). → read-once/cache shared parses; scope hashing. Not urgent at current scale; matters at enterprise rollout.

## 7. Net debt posture
The debt is **structural and hygiene-level, not correctness-level** — none of it changes the (already-audited) formulas or outputs. It is concentrated in: **(a) no tests on the new pipeline, (b) duplicated/leaky I/O, (c) hardcoded config, (d) repo clutter (drivers/reports/M5).** All are addressable in Phases 1–3 without touching analytics.
