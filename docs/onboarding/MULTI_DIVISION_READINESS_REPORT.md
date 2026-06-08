# Multi-Division Readiness Report

**Date:** 2026-06-08 · Evidence: `multi_division_readiness.csv`, `active_dependency_map.csv`. Read-only assessment; no behavior changed.

---

## 1. The two-speed picture
The platform is **two layers moving at different readiness**:

| Layer | Multi-division status | Evidence |
|---|---|---|
| **CORE (STEP1–19)** | ✅ **Config-ready for 6 divisions** | `railway_business_unit_config` defines MAS/SA/TPJ/MDU/PGT/TVC (`DEPOT_TOKEN_TO_BUSINESS_UNIT`, `BUSINESS_UNITS`); `railway_context` resolves per-BU output paths; **all 6 ran in STEP18A** (Configured→Live) |
| **MAS EXTENSION (STEP20–28)** | ⛔ **Hardcoded to MAS** | depot `'027534'`, dated SUMMARY filename, `"MAS"` literals, `raw_data/Railway_Operations/MAS` DMTR path, fixed Jul-2026…Jun-2027 horizon |

**Bottom line:** onboarding a new division to *operational/strategic analytics* is a **config + data** task; onboarding it to the *new planning pipeline* (SS/ROP/SRRS) additionally needs **code parametrization** of the 8 extension modules.

## 2. TPJ onboarding readiness (worked example)
| Requirement | State | Action |
|---|---|---|
| BU recognized by core | ✅ ready | none — TPJ already in `BUSINESS_UNITS` |
| Per-BU output paths | ✅ ready | none — `railway_context` |
| TPJ demand data (DMTR) | ⛔ missing | acquire TPJ DMTR register |
| TPJ stock snapshot (SUMMARY, depot) | ⛔ missing | acquire TPJ SUMMARY OF STOCK HELD |
| Extension division-parametrization | ⛔ code change | route depot/filename/path/horizon through config |
| Behavior-preservation for MAS | ✅ guarded | golden-file suite proves MAS outputs unchanged after parametrization |

**Verdict:** TPJ is **not** a config-only flip for the planning pipeline. It needs (a) data acquisition and (b) the extension-parametrization in `configuration_hardening_plan.csv`. The core layer for TPJ is ready today.

## 3. What to parametrize (extension → division-config)
Per `multi_division_readiness.csv` + `configuration_hardening_plan.csv`:
- `depot '027534'`, SUMMARY glob, `DMTR_DIR` → a **division registry** keyed by BU.
- Service levels (0.95/0.85), status bands (0.5×/2×), criticality weights (10/5/1), SBC cutoffs (1.32/0.49), `DAYS_PER_MONTH` → shared defaults, division-overridable.
- Horizon → derived from a `SNAPSHOT_DATE` per division, not literals.

Each change is behavior-preserving for MAS **by construction**: MAS values must equal the current config; the golden-file suite enforces it.

## 4. Scaling order
1. Parametrize extension behind the green suite (MAS outputs unchanged).
2. Onboard the next **data-complete** division (whichever has DMTR + SUMMARY) as the first non-MAS planning run.
3. Generalize the orchestrator to fan out per division.

**Multi-Division Readiness score:** 50 → 80 target (`platform_scorecard.csv`) — core already high, extension is the gap.
