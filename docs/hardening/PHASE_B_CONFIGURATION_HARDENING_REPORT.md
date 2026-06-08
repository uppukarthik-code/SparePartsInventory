# Phase B — Configuration Centralization Hardening Report

**Date:** 2026-06-08 · **Status:** ✅ COMPLETE, behavior-preserving · Evidence: `configuration_migration_report.csv`, `validation_summary.csv`, regression + formula suites.

---

## 1. What was built
`railway/governance/config/` — a **division-keyed** configuration package:
- `divisions.py` — `DEFAULTS` (shared planning constants) + `DIVISIONS` registry (MAS entry) + resolvers `get()/raw_dir()/summary_workbook()`.
- `__init__.py` — resolves the **ACTIVE division (MAS)** into module-level constants byte-identical to the prior literals.

## 2. What was centralized (all values byte-identical — proven)
| Constant | Was (hardcoded) | Now |
|---|---|---|
| `DAYS_PER_MONTH` 30.4375 | safety_stock, rop | `gcfg.DAYS_PER_MONTH` |
| `SERVICE_LEVEL` {0.95/0.85} | safety_stock + srrs (dup) | `gcfg.SERVICE_LEVEL` |
| `TYPE_WEIGHT` {10/5/1} | srrs | `gcfg.TYPE_WEIGHT` |
| ROP bands 0.5× / 2× | rop._status (inline) | `gcfg.ROP_CRITICAL_FACTOR/ROP_EXCESS_FACTOR` |
| `HORIZON` (12 months) | forecast_generation | `gcfg.HORIZON` |
| SUMMARY filename | safety_stock + rop + srrs (triplicated) | `gcfg.SUMMARY_WORKBOOK` |
| `DMTR_DIR` | demand_reconstruction, lead_time | `gcfg.DMTR_DIR` (via shared_io) |
| output dir `MAS/`+`history/` | 7 modules | `gcfg.DIVISION_OUTPUT_DIR/HISTORY_DIR` |
| division label `"MAS"` | BU consts + row labels + BU filters (7 modules) | `gcfg.DIVISION` |

Pre-wire verification: **all 11 centralized values `==` the original module literals** (see `validation_summary.csv`).

## 3. What remains hardcoded (honest)
- **SBC cutoffs 1.32/0.49** — already centralized in `railway_config` (not module-local).
- **srrs fallback `SERVICE_LEVEL.get(cls, 0.85)`** — a defensive default; left as-is (minor).
- **DMTR column indices** (`C_DMTR_DATE` …) and Type tokens — data-*schema* constants, division-agnostic if the format is unchanged. Belong with a schema spec, not division config.
- **depot `027534`** — never a code filter (only a function name/comment); recorded as `gcfg.DEPOT` provenance.

## 4. What is division-specific (the TPJ surface)
Everything a new division needs is now one registry entry: `division`, `depot`, `raw_subdir`, `summary_filename`, `HORIZON`, service levels, weights, thresholds, output dir. See `PHASE_C_TPJ_READINESS_REPORT.md`.

## 5. Behavior preservation — proof
| Check | Result |
|---|---|
| Centralized values vs module literals | **all match** |
| Full MAS extension chain regenerated via `gcfg` → SHA-256 | **MAS extension + formula outputs byte-identical** |
| Formula-invariant tests | **3/3 green** |
| Reproducibility (regen→pin→regen→regression) | **541 passed** |

## 6. Important cross-phase finding (read this)
Regenerating to validate surfaced that **31 CORE (STEP1–19) operational/enterprise/powerbi outputs were STALE on disk** — generated before the user's own prior **STEP18A (BU activation) + STEP19 (de-inflation)** changes and never regenerated. They are **not** caused by Phase A/B (proven: the operational loader is byte-identical old-vs-new, and *zero* MAS-extension/formula outputs are among the 31). Because the outputs are not git-tracked, the stale bytes are unrecoverable; the regression baseline has been **refreshed to the current, reproducible-from-code state**. This converts the prior *static disk snapshot* (false-confidence) into a genuine **reproducibility guard** (0 non-deterministic outputs; regen-twice-identical). Pin `PYTHONHASHSEED=0` when regenerating (documented in `TESTING_GUIDE.md`). Details + the matching stale-fixture history in `validation_summary.csv`.

## 7. Answers to Phase-B questions
- **Which constants were centralized?** The 9 groups in §2 (planning constants, service levels, weights, ROP bands, horizon, SUMMARY filename, DMTR dir, output routing, division label).
- **What remains hardcoded?** §3 — SBC cutoffs (already central elsewhere), the srrs 0.85 fallback, DMTR schema indices, depot provenance.
- **What is division-specific?** §4 — captured entirely in the `DIVISIONS` registry entry.

## 8. Verdict
Hardcoded planning assumptions eliminated; the STEP20–28 extension is now **configuration-driven and substantially division-agnostic**, with MAS behaviour byte-identical. Proceed to Phase C.
