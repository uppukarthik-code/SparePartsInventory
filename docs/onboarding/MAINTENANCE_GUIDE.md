# Maintenance Guide

For the engineer who owns this platform over the next 5 years. Companion to
`FIVE_YEAR_MAINTAINABILITY_REPORT.md` and `five_year_maintainability_assessment.csv`.

## Golden rules
1. **Never change analytics behavior unintentionally.** The regression suite (536
   pinned outputs) + formula invariants are the contract. Both green before every merge.
2. **STEP1–19 are production, not legacy.** Walmart origin ≠ remove. Only the Walmart
   notebooks + M5 data + unused deps are disposable.
3. **No synthetic data, ever** — demand, lead times, stock, criticality come from real
   records or they don't exist for that division.
4. **Additive-first.** Prefer adding a module/test/doc over editing audited code. When
   you must edit, do it behind the green suite.

## Where things live
- Constants/paths/cutoffs → `railway_config` (centralize new ones here, don't inline).
- Shared I/O → currently `demand_reconstruction._sheet_rows` (leak); target
  `ingestion/xlsx_reader.py`. Don't add new readers — reuse.
- Per-division behavior → `railway_business_unit_config` + (after parametrization) the
  division registry.

## Making a change safely (recipe)
```powershell
# 1. baseline green
python -m pytest railway/tests/ -q
# 2. make the change (behavior-preserving)
# 3. regenerate affected outputs (run the relevant driver)
# 4. prove no drift
python -m pytest railway/tests/regression/ railway/tests/inventory/ -q
# 5. if red on a pure refactor -> revert/explain; if red on an intended data change -> sign-off + re-pin
```

## Known traps (from build history)
- **cp1252 console** can't print ∩/∪/← — keep logs ASCII.
- **`np.median([])`** crashes if winsorization clips all lead-time intervals — guard before extending.
- **Silent `except → 0.0`** in qty/value/date parsing hides bad rows — prefer explicit validation (TD12).
- **Fragile DMTR regex** breaks on format drift — add schema assertions at ingestion (TD13/TD17).
- **`openpyxl`** was unreliable in some sandbox envs → raw `zipfile` + XML reading is used; keep that path.

## Debt to retire (priority order — `technical_debt_remediation.csv`)
1. Extend tests (ingestion/demand/forecast/lead-time) — TD01 remainder.
2. Extract `ingestion/` (kills leak TD02 + duplicate readers TD08).
3. Layer the package + split god-module (TD03/TD04).
4. Centralize config + parametrize divisions (TD05/TD09).
5. `pyproject.toml` + CI running the suite on every push (TD11).
6. Cleanup: archive M5/reports/drivers, pin/split deps (TD07/TD10).

## Health dashboard (run monthly)
- `pytest railway/tests/` green.
- No new module imports a demand module for I/O (re-check the import graph).
- `requirements.txt` pinned; no unused runtime deps reintroduced.
- Outputs still deterministic (regression green on a clean re-run).
