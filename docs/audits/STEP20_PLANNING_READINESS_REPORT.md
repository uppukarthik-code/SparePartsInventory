# STEP 20 — Strategic Planning Readiness Report

**Type:** Read-only governance & readiness assessment. **No code, data, configuration, KPI, forecasting, SRRS or procurement changes.**
**Date:** 2026-06-08
**Question:** Is the platform ready to move from **zone-level** to **business-unit** strategic planning (Forecasting · Safety Stock · ROP · Procurement Prioritization · SRRS)?

---

## 0. How the planning engines consume data (basis for this assessment)

| Engine | Required inputs (from code review) | Current grain |
|--------|------------------------------------|---------------|
| Forecasting (`railway_forecasting.py`) | 5-year consumption series `CONSUMPTION_YEARS` (FY20-21…FY25-26), `AAC`, `EAR_Qty`, `Current_Stock` | **Zone** (59 items, shared) |
| Safety Stock (`railway_inventory_optimization.py`) | `Demand_Sigma` = std of the 5-year series; `Z` from service table; lead time | **Zone** |
| ROP | `Expected_Demand_During_LT` + `Safety_Stock`; lead time = `EAR_Qty / Pending_Supply` (Tier-1) or criticality fallback | **Zone** |
| Procurement (knapsack) | `Inventory_Gap` (ROP − stock), `Unit_Cost`, budget | **Zone** demand, **per-BU** stock now exists |
| SRRS | `Criticality_Weight × Service_Factor × Positive_Gap × Lead_Time_Factor × Demand_Factor` | **Zone** |

**Critical structural fact:** every strategic planning engine is driven by the **zone** demand series. The only per-division strategic signals that exist are: **(a) allocated stock** (STEP 19) and **(b) a single year (2020-21) of per-division consumption + EAR** (`EAR Consumptions` sheet). **Multi-year per-division consumption does not exist.**

---

## PART 1 — Data Sufficiency Assessment

### 1.1 Per-division data inventory

| Data element | MAS | SA | TPJ | MDU | PGT | TVC | Grain available |
|--------------|----|----|-----|-----|-----|-----|-----------------|
| Operational current stock | ✅ 907 | ✅ 542 | ✅ 1355 | ✅ 769 | ✅ 920 | ✅ 842 | per-division (STEP18A) |
| Strategic stock (allocated) | ✅ 220,422 | ✅ 8,984 | ✅ 38,284 | ✅ 15,446 | ⚠ 12 | ✅ 30,744 | per-division (STEP19) |
| Multi-year demand series (5 yr) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **zone only** |
| Single-year consumption (2020-21) | ✅ 77,323 | ✅ 64,775 | ✅ 27,034 | ✅ 28,538 | ✅ 42,027 | ✅ 32,119 | per-division (1 point) |
| EAR requirement (2020-21) | ✅ 217,200 | ✅ 96,125 | ✅ 79,290 | ✅ 79,761 | ✅ 114,742 | ✅ 83,395 | per-division (1 point) |
| Demand variability σ (per division) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | not derivable (1 point) |
| Lead time / Pending supply (per division) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **zone only** |
| Criticality / ABC (item level) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | item-level (scope-neutral) |

### 1.2 Capability sufficiency (structural — gaps are common across all six BUs)

| Capability | Available | Missing | Current assumption | Risk |
|------------|-----------|---------|--------------------|------|
| **Division forecasting** | Single-year (2020-21) per-division consumption + zone 5-yr series | ≥3-5 yr **per-division** consumption series | Every division inherits the **zone** forecast (identical) | 🔴 High |
| **Division safety stock** | Item criticality/ABC, service table | Per-division demand **σ**; per-division lead time | σ computed on **zone** series; SS identical across divisions | 🔴 High |
| **Division ROP** | Per-division stock (STEP19) | Per-division SS + lead time + pending supply | ROP = zone value applied to all divisions | 🔴 High |
| **Division procurement** | Per-division stock; budget; unit cost | Per-division gap (needs per-division ROP) | Gap computed vs **zone** ROP | 🟠 Medium |
| **Division SRRS** | Criticality weights, service factors | Per-division Positive_Gap, lead-time & demand factors | SRRS identical across divisions (zone) | 🔴 High |

**Conclusion (Part 1):** the **stock** dimension is division-ready; the **demand / variability / lead-time** dimensions are not. Four of five strategic capabilities lack the per-division *demand history* they require.

---

## PART 4 — Divisional Planning Readiness

Verdicts use the standard scale with justification. Because the missing inputs are *structural* (a single shared zone demand series), the verdicts are uniform across divisions, with PGT flagged separately for a data-integrity reason (see Governance report).

| Capability | Verdict | Justification |
|------------|---------|---------------|
| **Business-Unit Forecasting** | 🔴 **Not Ready** | Forecast engine needs a 5-year series per series-key. Only **zone** 5-year data exists; per-division history is a **single** year (2020-21). Cannot fit MA/CAGR/Croston/SBA/TSB/Holt per division, nor backtest (4→1 hold-out impossible with 1 point). |
| **Business-Unit ROP** | 🔴 **Not Ready** | ROP = expected demand over lead time + safety stock. Lead time derives from `EAR_Qty/Pending_Supply` — both **zone**. Safety stock needs per-division σ (unavailable). |
| **Business-Unit SRRS** | 🔴 **Not Ready** | SRRS Positive_Gap = ROP − stock. Per-division stock exists, but per-division ROP does not (above). The other factors (service/lead-time/demand) are zone. |
| **Business-Unit Procurement Optimization** | 🟠 **Partially Ready** | The budget-constrained knapsack can run per division on **per-division stock** (STEP19) + **per-division operational valuation** (STEP18A). It would, however, rank gaps against a **zone** ROP/target until per-division demand exists — usable for *operational* rationalization now, approximate for *strategic* procurement. |
| *(reference)* Division operational analytics (dead stock, aging, valuation, rationalization) | 🟢 **Ready** | Delivered in STEP18A; genuinely per-division. |
| *(reference)* Division strategic **stock visibility** | 🟢 **Ready** | Delivered in STEP19; allocated & conserved. |

---

## Readiness scoring (0–100%)

Weighted rubric (infrastructure enablers 40% · planning-data gate 60%):

| Dimension | Weight | Score | Notes |
|-----------|-------:|------:|-------|
| Multi-BU execution infrastructure | 12% | 95% | Proven (STEP18A) |
| Strategic stock allocation per BU | 12% | 88% | Done (STEP19); governance caveats (PGT, PER central-store) |
| Operational analytics per BU | 8% | 95% | Done (STEP18A) |
| Enterprise aggregation integrity | 8% | 85% | Strategic de-inflated (STEP19); operational benchmark fan-out still open |
| **Per-division multi-year demand history** | 25% | 15% | Only 1 year (2020-21) per division |
| **Per-division σ / lead time / pending supply** | 20% | 10% | Zone-only |
| Data governance & quality | 15% | 35% | PGT reconciliation, PER central-store ambiguity, 1 source anomaly |

**Overall Strategic-Planning Readiness: ≈ 48% — "Partially Ready: infrastructure ready, division demand data not."**

- Platform / orchestration / allocation / enterprise layers: **ready (~90%)**.
- Division-level *demand* foundation required by forecasting/SS/ROP/SRRS: **not ready (~12%)**.

---

## Headline

The platform **can mechanically run** per-division pipelines (proven), and the **stock** side is division-aware. It is **not ready** for business-unit strategic *planning* because the planning engines are demand-driven and **no multi-year per-division demand history exists**. The single decisive enabler is constructing per-division demand history; everything else is in place or low-effort. See `STEP20_RECOMMENDED_ROADMAP.md`.
