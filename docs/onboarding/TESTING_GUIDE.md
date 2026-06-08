# Testing Guide

The test suite exists primarily to **prove behavior-preservation** during
modernization: the analytics are already audited; tests stop refactors from
silently changing outputs.

## Layout
```
railway/tests/
  regression/   golden_output_manifest.csv + test_golden_outputs.py   (536 outputs pinned)
  inventory/    test_formula_invariants.py                            (SS / ROP / SRRS math)
  (legacy unit tests for STEP1-17 modules)
```

## Run
```powershell
python -m pytest railway/tests/                     # everything (540+)
python -m pytest railway/tests/regression/ -q       # behavior guard only
python -m pytest railway/tests/inventory/ -v        # formula invariants
```

## The two guards you must keep green
### 1. Golden-file regression (`tests/regression/`)
Pins the SHA-256 of every produced output CSV. **A refactor is behavior-preserving
iff this stays green.** Workflow:
1. Make a behavior-preserving change.
2. Re-run the producing driver(s) so outputs regenerate.
3. `pytest railway/tests/regression/` → green = identical = safe.
4. Red = a hash diverged → **explain or revert** (the non-negotiable rule).

Re-baseline (delete the manifest and re-pin) **only** after an *approved, explained*
output change — never to force a failing refactor to pass.

### 2. Formula invariants (`tests/inventory/`)
Re-derives SS/ROP/SRRS from their input columns and asserts the pipeline matches the
documented formulas:
- `SS = z·σ·√(LT/30.4375)`
- `DDLT = Fcst·(LT/30.4375)/12`, `ROP = DDLT + SS`, `gap = ROP − stock`
- `Positive_Gap = max(0, ROP − stock)`, `SRRS ≥ 0`, rank-consistent, zero-gap→zero-SRRS

These use **relative tolerance** (`rtol 1e-2, atol 0.5`) because outputs are stored
rounded to 2 decimals and recomputed from already-rounded inputs — a real formula
error is off by orders of magnitude more than rounding.

## Coverage gaps to close next (`coverage_gap_analysis.csv`)
Currently 0% on: ingestion parsers, demand-reconstruction conservation/gap-fill, SBC
cutoffs, forecast method routing, lead-time winsor/median edges, criticality parsing.
Priorities and suites in `testing_implementation_plan.csv` (build ingestion + demand +
forecasting + lead-time unit tests next; regression + SS/ROP/SRRS already seeded).

## Reproducibility requirement (set the seed)
The golden baseline is **reproducible-from-code** (not just a disk snapshot): regenerate → re-pin → regenerate again → green. Two outputs depend on `set()` iteration order on tied sort keys (`pl_match_candidates.csv`; some tied report rows), so **regenerate and run the suite with `PYTHONHASHSEED=0`**:
```powershell
$env:PYTHONHASHSEED=0; python -m pytest railway/tests/
```
A tracked hardening follow-up is to add stable data tiebreakers so seed-pinning is unnecessary. Note: the baseline was refreshed once (2026-06-08) because 31 CORE STEP1–19 outputs were **stale on disk** (predated STEP18A/19, never regenerated); they are now reproducible. See `validation_summary.csv`.

## Rule for any code change
> If you touch a railway module, the regression suite **and** the formula invariants
> must be green before merge. If they can't be, the change is not behavior-preserving —
> stop and escalate.
