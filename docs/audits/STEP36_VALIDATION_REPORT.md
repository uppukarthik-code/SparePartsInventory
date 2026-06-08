# STEP36 — Validation Report

**Date:** 2026-06-09
**Branch:** `step36-regression-baseline-repair`
**Runs:** `PYTHONHASHSEED=0`; pandas 3.0.3 / numpy 2.4.6 / scipy 1.17.1 / pulp 3.3.2.

---

## Final result

```
647 passed, 1 skipped, 0 failed   (648 collected)
```
- The 1 skip is `test_golden_manifest_if_present` (optional STEP17 baseline absent — intended).
- `manifest_tools.check()` → `manifest integrity OK`.

---

## Per-phase results

| Phase | Deliverable | Status |
|---|---|---|
| A — manifest forensics | `manifest_forensics.csv` + `manifest_tools.py` | ✅ 537/537 `IDENTICAL_EOL_ONLY`, 0 `CONTENT_DIFFERENCE`, 61 `EXTRA_FILE` |
| B — line-ending repair | `golden_output_manifest.csv` re-pinned + `manifest_repair_report.csv` | ✅ 537 re-pinned to LF; golden suite 538 passed; no output modified |
| C — stale fixture forensics | `stale_fixture_inventory.csv` | ✅ 7 fixtures classified (all STALE, 0 regressions) |
| D — fixture repair | `fixture_repair_report.csv` + edits | ✅ 7/7 repaired; all escalation gates cleared with evidence |
| E — governance hardening | `.gitattributes` + `test_governance_review.csv` | ✅ outputs+manifest LF-normalized (EOL-only); golden still green |
| F — regression governance | `REGRESSION_GOVERNANCE.md` | ✅ ownership / re-baselining / approval / change-control documented |
| G — full validation | `baseline_validation_report.csv` | ✅ 647 pass / 0 fail / 1 skip |
| H — CI hardening | `ci.yml` + `ci_hardening_report.csv` | ✅ manifest-integrity gate + full-suite run added; YAML valid |

---

## Safety proofs

- **No real regression:** forensics found 0 `CONTENT_DIFFERENCE` across 537 pinned files; `rebuild()` would have aborted otherwise.
- **No analytics/formula change:** no change to forecasting / demand / lead-time / criticality / safety-stock / ROP / SRRS / optimization / reporting modules. The only non-test source edit is `schema_validation.py` — removal of one mis-applied operational uniqueness check (a validation-rule scope fix, not a computation).
- **No output content change:** golden suite (538) green ⇒ the 537 pinned outputs are byte-consistent with the manifest. The only `railway/outputs` diffs are EOL-only (CRLF→LF, balanced ins/del) on 8 STEP35-OPT CSVs (not part of the pinned baseline).
- **Escalation gates cleared with evidence:** enterprise registry populated (4022 rows, PL_Code present); STTC_PTJ data-less (`operational_rows=0`, `processed=False`); operational duplicates explained by depot-level grain (rows=5335, uniq PL=4006, uniq(PL,Depot)=4590).
- **Reproducible & self-healing:** `.gitattributes` forces LF on output CSVs + manifest; CI is Linux/LF; git normalizes any regenerated CRLF to LF on add.

---

## Files touched (with rationale)

| File | Change | Rationale |
|---|---|---|
| `railway/tests/regression/manifest_tools.py` | NEW | governed forensics/rebuild/check tooling |
| `railway/tests/regression/golden_output_manifest.csv` | re-pinned to LF | EOL-only; pinned content unchanged |
| `railway/tests/test_business_unit_runner.py` | 4 fixtures repaired | routing STEP19, data-volume invariants, data-less BU |
| `railway/tests/test_production_hardening.py` | 2 counts updated | operational volume grew (committed-authoritative) |
| `railway/schema_validation.py` | 1 rule removed | operational is depot/line-level; PL_Code not its key |
| `.gitattributes` | +2 eol=lf rules | reproducible LF manifest across OS |
| `.github/workflows/ci.yml` | +2 steps | manifest-integrity gate + full-suite run |
| `docs/REGRESSION_GOVERNANCE.md` | NEW | governance doc |
| `docs/audits/*.csv` (8) + 2 reports | NEW | deliverables |
| `railway/outputs/*.csv` (8 STEP35-OPT) | EOL-normalized | content identical (CRLF→LF) |

**Commits (STEP36):** `2d03799`, `0f22aed`, `a963372`, `7410028`, `f54bc4f`, `011fdf2`, `882e9c5`, `16c7158` (+ this report commit).
