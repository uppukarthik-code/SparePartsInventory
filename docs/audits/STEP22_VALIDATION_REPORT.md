# STEP 22 — Validation Report

**Date:** 2026-06-08
**Subject:** MAS demand classification + forecast-method assignment.
**Method:** Independent re-computation, reproducibility re-run, and SHA-256 backward-compatibility guard.

---

## 1. Validation checklist

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Every PL classified | ✅ PASS | 1,083 / 1,083 PLs in `demand_classification.csv`, every row has a `Demand_Class` |
| 2 | Every PL assigned exactly one method | ✅ PASS | 1,083 unique PLs, all `Forecast_Method` non-null; class→method mapping 100% consistent |
| 3 | Classification reproducible | ✅ PASS | second run produced byte-identical CSVs (SHA-256 match) |
| 4 | Existing forecasting code unchanged | ✅ PASS | `railway_forecasting.py` / `railway_classification.py` not modified; outputs in unchanged set |
| 5 | Existing SRRS unchanged | ✅ PASS | SRRS/policy outputs within the unchanged 498 files |
| 6 | Existing procurement logic unchanged | ✅ PASS | procurement outputs within the unchanged 498 files |
| 7 | Backward compatibility maintained | ✅ PASS | 498 existing files, **0 changed / 0 removed / 0 added** (SHA-256, excl. 3 new files) |

**All 7 checks PASS.**

## 2. Coverage & integrity

```
PLs classified (demand_classification)      : 1083  (unique 1083)
Every PL has a Demand_Class                  : True
Every PL exactly one Forecast_Method         : True
All Demand_Class values in valid set         : True   {Smooth,Erratic,Intermittent,Lumpy,Dead}
All Forecast_Method values in valid set      : True   {SES/Holt,Croston,SBA,TSB,No Forecast}
Class -> Method mapping consistent (all PLs)  : True
```

Mapping audit (per spec): Smooth→SES/Holt, Erratic→Croston, Intermittent→SBA, Lumpy→TSB, Dead→No Forecast — **0 violations** across 1,083 PLs.

## 3. Reproducibility
The module is deterministic (pure functions of the input series; no randomness, no time dependence). Re-running `build()` produced identical `demand_classification.csv`, `xyz_classification.csv`, `forecast_method_assignment.csv` (verified by SHA-256). Cutoffs are read-only constants in `railway_config`.

## 4. Backward-compatibility proof
```
Existing files fingerprinted (outputs/, excl. 3 new CSVs) : 498
Changed : 0     Removed : 0     Added : 0     UNCHANGED : True
```
SHA-256 of the whole outputs tree captured before/after execution. The module writes only the three new files; all forecasting, SRRS, procurement, optimization, enterprise, Power BI and KPI outputs are byte-for-byte identical. **No forecasting model was executed.**

## 5. Data-quality exception (disclosed)
PL_Code `NA` (literal) — uncoded DMTR transactions, 47 months, 0 issues → classified **Dead / No Forecast**. Preserved for completeness; flagged for exclusion from planning. No duplicates, no null/blank classes, no PL left unclassified.

## 6. Verdict
**STEP 22 validation PASSED (7/7).** All 1,083 MAS PLs are classified by the Syntetos–Boylan matrix and assigned exactly one forecasting method, reproducibly and additively, with every existing output unchanged.
