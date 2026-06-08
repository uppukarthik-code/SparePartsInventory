# Division Onboarding Guide

How to bring a new division (e.g. **TPJ**) onto the platform. See
`MULTI_DIVISION_READINESS_REPORT.md` for the readiness assessment behind this.

## The platform is two-speed
- **Core analytics (STEP1–19):** already 6-division ready. Onboarding = **data + config**.
- **Planning pipeline (STEP20–28, SS/ROP/SRRS):** currently **hardcoded to MAS**.
  Onboarding = **data + a one-time code parametrization** (then config per division).

## Step A — confirm the division is registered (core)
The 6 divisions already exist in `railway_business_unit_config`
(`DEPOT_TOKEN_TO_BUSINESS_UNIT`, `BUSINESS_UNITS`). A new BU beyond the 6 is added here.
`railway_context` will create `railway/outputs/<DIVISION>/...` automatically.

## Step B — acquire the division's data (the real blocker)
| Data | Why | Status for TPJ |
|---|---|---|
| DMTR issue + procurement registers | demand history + lead times | **missing** — acquire |
| SUMMARY OF STOCK HELD (with depot, PL-Code/Type/Usage) | current stock + criticality | **missing** — acquire |
| (optional) `stock_history.xlsx` | strategic snapshot (core only) | present for some divisions |

Without DMTR + SUMMARY, the planning pipeline cannot run for that division. No
synthetic demand, lead times, stock, or criticality may be substituted.

## Step C — parametrize the MAS extension (one-time code change)
Per `configuration_hardening_plan.csv`, route these out of the 8 extension modules
into a **division registry** in `railway_config`:
- depot id (`027534`), SUMMARY filename glob, DMTR directory, forecast horizon
- service levels (0.95/0.85), status bands (0.5×/2×), criticality weights (10/5/1),
  SBC cutoffs (1.32/0.49), `DAYS_PER_MONTH` → shared defaults, division-overridable

**Behavior-preservation requirement:** after parametrization, MAS must reproduce its
current outputs **byte-for-byte**. Verify with:
```powershell
python -m pytest railway/tests/regression/   # 536 MAS outputs must stay green
```

## Step D — run and validate the new division
1. Run the producing drivers for `<DIVISION>` (see `OPERATIONS_GUIDE.md`).
2. Sanity-check funnel counts and formula invariants (`tests/inventory/`, re-pointed at the division).
3. Pin the new division's outputs into its own golden manifest.

## Onboarding checklist
- [ ] BU in `railway_business_unit_config`
- [ ] DMTR + SUMMARY acquired (real data)
- [ ] extension parametrized; **MAS regression suite still green**
- [ ] division run produced outputs; funnel + invariants checked
- [ ] new-division outputs pinned
