# Operations Guide

How to run the platform and regenerate outputs. Until an orchestrator exists
(`technical_debt_remediation.csv` TD06), runs are driven by module `run()` entry
points and the STEP driver scripts.

## Environment
```powershell
pip install -r requirements.txt
# runtime needs: pandas, numpy, scipy, openpyxl, statsmodels, pulp
# (sklearn/prophet/seaborn listed but UNUSED at runtime — see TD10)
```

## Core multi-division run (STEP1–19)
```powershell
python -m railway.railway_business_unit_runner
```
Produces per-division strategic/operational outputs under `railway/outputs/<DIVISION>/`.

## MAS planning extension (STEP20–28) — run order
The planning pipeline must run in dependency order (each stage consumes the prior):
```
demand reconstruction → classification → forecast generation
                     ↘ lead-time derivation
                       → safety stock → ROP → SRRS → reports
```
Invoke the corresponding module `run()` / STEP driver for each stage (drivers:
`_step21a_run.py` … `_step28_*.py`). Outputs land in
`railway/outputs/MAS/history/*.csv`.

## After any run — verify behavior
```powershell
python -m pytest railway/tests/regression/ -q   # 536 outputs must be byte-identical
python -m pytest railway/tests/inventory/  -q   # SS/ROP/SRRS invariants
```
Green = the run reproduced the validated baseline. Red on regression after an
*intended* data change is expected — re-pin only with sign-off (`TESTING_GUIDE.md`).

## Inputs expected (`raw_data/`)
- `DMTR_*.xlsx` (issue + procurement, depot 027534 for MAS)
- `SUMMARY OF STOCK HELD (... <date>).xlsx` (current stock + PL-Code/Type/Usage)
- per-division `stock_history.xlsx` (core strategic snapshot)

## Common operational notes
- **Windows console (cp1252):** avoid printing non-latin glyphs (∩/∪/←) — they raise
  `UnicodeEncodeError`. Use ASCII in logs.
- **`PL_Code "NA"` is a real item**, not missing — loaders use `keep_default_na=False`.
- **Stock is depot-snapshot only** (027534) — never substitute another depot.
- Re-runs are deterministic/byte-identical; safe to repeat.

## Health checks
- Funnel counts should follow the audited chain (e.g. MAS 1083→961→702→626→626→626).
- `python -m pytest railway/tests/` before any deploy.
