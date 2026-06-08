# STEP 19 — Enterprise Impact Analysis

**Date:** 2026-06-08
**Comparison:** Before STEP 19 (zone-shared strategic) vs After STEP 19 (BU-allocated strategic)

---

## 1. Strategic Inventory Value — by Business Unit

| BU | Before (zone-shared, ₹) | After (allocated, ₹) | Δ |
|----|------------------------:|---------------------:|---|
| MAS | 85,663,635.52 | 82,879,378.63 | −2,784,256.89 |
| SA  | 85,663,635.52 | 140,460.87 | −85,523,174.65 |
| TPJ | 85,663,635.52 | 986,649.15 | −84,676,986.37 |
| MDU | 85,663,635.52 | 793,711.41 | −84,869,924.11 |
| PGT | 85,663,635.52 | 5,683.17 | −85,657,952.35 |
| TVC | 85,663,635.52 | 857,752.29 | −84,805,883.23 |
| **Σ (enterprise)** | **513,981,813.12** | **85,663,635.52** | **−428,318,177.60** |

Before, every unit carried the **full** zone value; after, each carries only its **allocated** share. The enterprise sum collapses from 6× to 1× the true zone value — the headline correction.

Underlying raw allocation (stock × unit cost), for reference:

| BU | Strategic Stock (units) | Strategic Value raw (₹) | Share |
|----|------------------------:|------------------------:|------:|
| MAS | 220,422 | 644,079,280 | 96.75% |
| TPJ | 38,284 | 7,667,532 | 1.15% |
| TVC | 30,744 | 6,665,838 | 1.00% |
| MDU | 15,446 | 6,168,158 | 0.93% |
| SA  | 8,984 | 1,091,561 | 0.16% |
| PGT | 12 | 44,166 | 0.01% |
| **Zone** | **313,892** | **665,716,535** | **100%** |

---

## 2. Forecast / ROP / Procurement / SRRS — by Business Unit

These layers are **out of STEP 19 scope** (design principle: no change). They remain **zone-level shared** and **byte-identical before/after**:

| Measure (per BU) | Before | After | Differentiated by division? |
|------------------|--------|-------|-----------------------------|
| Forecast (`railway_forecast.csv`, 59 items) | zone-shared, identical across MAS/SA/TPJ/MDU/PGT/TVC | **unchanged** | No (by design) |
| ROP / Inventory policy (`railway_inventory_policy.csv`) | zone-shared, identical | **unchanged** | No (by design) |
| Procurement (`railway_procurement_plan.csv`) | zone-shared, identical | **unchanged** | No (by design) |
| SRRS (service-risk / reserve) | zone-shared, identical | **unchanged** | No (by design) |

Verification: the forecast, policy and procurement CSVs hash **identically across all six BUs** and are **unchanged** by STEP 19 — confirming the formulas were not altered. STEP 19 differentiates the **stock/value** dimension only.

---

## 3. Enterprise strategic inflation — quantified

| Metric | Value |
|--------|------:|
| Current (pre-STEP19) enterprise strategic inflation factor | **6.000×** |
| Post-allocation inflation factor | **1.000×** |
| Phantom strategic value removed | **₹428,318,177.60** |
| Net improvement | **inflation eliminated** (enterprise strategic total now equals the true zone value, conserved exactly) |

**Inflation factor** = (Σ strategic across the 6 Live units reported by enterprise aggregation) ÷ (true zone strategic value). Six Live units each carrying the full zone value produced 6×; allocation by verified depot share reduces this to 1× while preserving the zone total to the rupee.

---

## 4. Per-division strategic standing revealed (previously invisible)

Allocation surfaces division-level strategic posture that the shared model masked:

| BU | Strategic stock | Read |
|----|----------------:|------|
| MAS | 220,422 | holds ~70% of zone strategic units, ~97% of value — the strategic hub |
| TPJ | 38,284 | second-largest strategic holding |
| TVC | 30,744 | substantial |
| MDU | 15,446 | moderate |
| SA  | 8,984 | low |
| **PGT** | **12** | **strategically under-stocked** (vs 42,027 annual consumption in `EAR Consumptions`) — a genuine risk signal, previously hidden by zone-sharing |

PGT's near-empty strategic position is the most actionable insight: it was completely invisible while strategic stock defaulted to MAS.

---

## 5. Backward-compatibility impact

| Area | Impact |
|------|--------|
| Operational outputs | none (byte-identical, 46 files/BU) |
| Power BI page schemas | none (unchanged; enterprise-enriched copies regenerated, same schema) |
| Published KPIs | none (page0 values unchanged; only enterprise strategic attribution split) |
| Enterprise aggregation | **improved** — strategic totals no longer inflate (6×→1×) |

---

## 6. Recommended next step

STEP 19 allocated the **stock** dimension. The natural follow-on — **per-division strategic forecasting / ROP / SRRS** computed on each BU's allocated strategic stock — would make the *planning* layer division-specific too (today it remains zone-shared by design). This is a larger change that touches the forecasting/optimization/SRRS modules and should be gated and scoped separately, with the same backward-compatibility discipline applied here.

**Priority signal for that work:** PGT (12 strategic units vs 42,027 consumption) indicates an immediate strategic stock-out exposure worth validating with the division before the next procurement cycle.
