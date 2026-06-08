# STEP 20 — Recommended Implementation Roadmap

**Type:** Recommendation (read-only). No code/data/config changes.
**Date:** 2026-06-08
**Context:** Readiness ≈ 48% — infrastructure ready, **per-division demand foundation missing**. The roadmap sequences the work to lift the gating constraints in dependency order.

---

## Sequencing logic

Business-unit *planning* is blocked by one root cause: **no multi-year per-division demand history**, plus two governance gaps (PGT visibility, Perambur central-reserve). Therefore the data + governance foundation must come **before** any per-division forecasting/SS/ROP/SRRS. The three phases below are strictly dependency-ordered.

```
Phase 21 (data + governance foundation)  ──►  Phase 22 (forecast/SS/ROP)  ──►  Phase 23 (SRRS/procurement + benchmark hardening)
```

---

## Phase 21 — Per-Division Demand Foundation & Governance Reconciliation

| Field | Detail |
|-------|--------|
| **Objective** | Establish a trustworthy, multi-year, per-division demand & strategic-stock dataset — the single enabler for all downstream BU planning. |
| **Scope** | (1) Source and ingest **multi-year per-division consumption** (extend `EAR Consumptions` beyond 2020-21, or obtain divisional consumption returns FY20-21…FY25-26). (2) **Reconcile PGT** strategic holdings with the division stores dept (resolve the 12-unit gap; locate Palakkad's true vital-item stock). (3) Resolve **Perambur `GSD/PER` central-reserve vs Chennai-division** classification; add a "central reserve" flag to allocation if confirmed. (4) Fix the source workbook anomaly (PL `50232356/50232319`). (5) Stand up the **data-governance gate** (conservation + EAR/consumption reconciliation per snapshot). |
| **Benefits** | Unblocks every downstream capability; removes the PGT blind spot; makes the STEP19 allocation interpretation defensible; institutionalizes data quality. |
| **Risks** | External data dependency (divisional returns may not exist historically → may need proxy/estimation, which must be governed); reconciliation requires stores-dept engagement (organizational, not technical). |
| **Effort** | **Medium-High** (~3–5 person-weeks engineering + governance lead time for divisional data sourcing). Mostly ingestion + governance, low analytical-code risk. |

## Phase 22 — Division-Level Forecasting, Safety Stock & ROP

| Field | Detail |
|-------|--------|
| **Objective** | Run the existing (unchanged) forecasting + safety-stock + ROP engines **per division** on the Phase-21 demand history. |
| **Scope** | Produce per-division `railway_demand_history` (multi-year), feed the **existing** `railway_forecasting` and `railway_inventory_optimization` engines through the established per-BU context runner; compute per-division σ, lead time, SS, ROP. **No formula changes** — same engines, division-scoped inputs (mirrors the STEP18A/STEP19 additive pattern). |
| **Benefits** | True division-level forecasts, safety stock and reorder points; divisions stop inheriting the zone forecast; backtest becomes meaningful per division. |
| **Risks** | Short series (even 5 points) limit forecast confidence for intermittent/lumpy items — manage expectations, lean on Croston/SBA/TSB already in the engine; per-division lead-time/pending-supply data must exist (Phase-21 dependency). |
| **Effort** | **Medium** (~2–4 person-weeks). Reuses validated engines; effort is in scoping/orchestration + validation, not new analytics. |

## Phase 23 — Division-Level SRRS, Procurement Optimization & Benchmark Hardening

| Field | Detail |
|-------|--------|
| **Objective** | Deliver per-division service-risk (SRRS) ranking and budget-constrained procurement, and harden the enterprise benchmark. |
| **Scope** | Run the **existing** SRRS + knapsack procurement engines per division on Phase-22 ROP/gaps; allocate budget by division or zone-then-split; **fix the operational benchmark fan-out** (the STEP18A-noted issue where each BU's benchmark stamps that BU's KPIs on all Live rows) so operational measures aggregate like strategic does post-STEP19; finalize the STEP20 KPI scorecard. |
| **Benefits** | RAMS-aligned, division-specific procurement prioritization; a fully conserved enterprise benchmark (strategic *and* operational); board-ready scorecard. |
| **Risks** | Budget-allocation policy is a business decision (per-division vs central) requiring sponsor sign-off; benchmark refactor touches `railway_enterprise` — must preserve published KPI values (apply the STEP19 conservation discipline). |
| **Effort** | **Medium** (~3–4 person-weeks). |

---

## Roadmap summary

| Phase | Theme | Gating dependency | Effort | Unlocks |
|-------|-------|-------------------|--------|---------|
| **21** | Demand foundation + governance | source data + stores-dept reconciliation | M-H | everything downstream |
| **22** | Division forecast / SS / ROP | Phase 21 | M | per-division planning numbers |
| **23** | Division SRRS / procurement + benchmark | Phase 22 | M | division procurement + clean enterprise benchmark |

**Critical path:** Phase 21 is the bottleneck — without multi-year per-division demand, Phases 22–23 cannot produce trustworthy output. Recommend starting Phase 21's **governance reconciliation (PGT, Perambur) immediately** (organizational lead time) in parallel with scoping the demand-history ingestion.

*This roadmap recommends; it implements nothing. No code, data, configuration, KPI, forecasting, SRRS or procurement logic was changed.*
