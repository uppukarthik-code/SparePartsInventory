# Southern Railway Spare-Parts Inventory Planning Platform

Division-level demand-forecasting and inventory-optimization platform for Southern
Railway spare parts (divisions **MAS, SA, TPJ, MDU, PGT, TVC**). Reconstructs
demand history from issue registers, classifies parts (Syntetos–Boylan), forecasts
intermittent demand, derives lead times from procurement records, and computes
safety stock, reorder points, and a service-risk reorder score (SRRS) to prioritize
replenishment.

> Platform entry-point doc. (The repo's top-level `README.md` is the analytics
> showcase.) New here? Read **`ARCHITECTURE.md` → `DATAFLOW.md` →
> `STEP1_TO_STEP28_LINEAGE.md`**. Add a division: `DIVISION_ONBOARDING_GUIDE.md`.
> Change code safely: `TESTING_GUIDE.md` + `MAINTENANCE_GUIDE.md`. Run it:
> `OPERATIONS_GUIDE.md`.

## What it does (pipeline)
```
DMTR issue registers ─► demand reconstruction ─► SBC classification ─► forecast generation
DMTR procurement     ─► lead-time derivation
SUMMARY OF STOCK     ─► current stock (depot snapshot)
        └──────────► safety stock ─► reorder point + gap ─► SRRS prioritization ─► reports
```

## Two layers (read before changing anything)
| Layer | Modules | Status |
|---|---|---|
| **Core platform (STEP1–19)** | data prep, classification, forecasting, optimization, enterprise, BU config/runner/context, strategic allocation, reporting/exports | **Active production, multi-division ready** (6 divisions ran in STEP18A). **Not legacy.** |
| **MAS planning extension (STEP20–28)** | `railway_demand_reconstruction`, `_demand_classification`, `_forecast_generation`, `_lead_time_derivation`, `_pl_master`, `_safety_stock`, `_rop`, `_srrs_mas` | **Active; currently hardcoded to MAS** |
| Shared infra | `railway_config` (fan-in 31) | central constants/paths |
| Legacy/dead | Walmart notebooks 01–06, 430 MB M5 data, unused deps | archive/remove |

## Quick start
```powershell
pip install -r requirements.txt
python -m railway.railway_business_unit_runner   # core multi-division run
python -m pytest railway/tests/                  # 540+ tests; behavior guard
```

## Key formulas (do not change without sign-off — `TESTING_GUIDE.md`)
- **SS** `= z · σ_monthly · √(LeadTimeDays / 30.4375)`, `z = norm.ppf(SL)`
- **ROP** `= DDLT + SS`, `DDLT = ForecastAnnual · (LT/30.4375) / 12`
- **SRRS** `= Criticality_Weight × Service_Factor × Positive_Gap`
- **SBC** ADI 1.32 / CV² 0.49 → SES·Holt / Croston / SBA / TSB

## Outputs
`railway/outputs/<DIVISION>/history/*.csv` — 536 CSVs SHA-256-pinned by the regression suite.

## Docs & reports
Docs: `ARCHITECTURE.md` · `DATAFLOW.md` · `STEP1_TO_STEP28_LINEAGE.md` · `DIVISION_ONBOARDING_GUIDE.md` · `TESTING_GUIDE.md` · `OPERATIONS_GUIDE.md` · `MAINTENANCE_GUIDE.md`.
Modernization: `PLATFORM_MODERNIZATION_REPORT.md`, `ARCHITECTURE_HARDENING_REPORT.md`, `MULTI_DIVISION_READINESS_REPORT.md`, `TECHNICAL_DEBT_REMEDIATION_REPORT.md`.
