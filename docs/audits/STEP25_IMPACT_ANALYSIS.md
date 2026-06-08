# STEP 25 — Impact Analysis

**Date:** 2026-06-08 · **Scope:** MAS · ROP & reorder-gap impact.

---

## 1. Reorder-gap & stock-status distribution

| Stock_Status | PLs | % of 626 |
|--------------|----:|---------:|
| Critical Shortage (Current < 0.5×ROP) | 465 | 74.3% |
| Shortage (0.5×ROP ≤ Current < ROP) | 45 | 7.2% |
| Healthy (ROP ≤ Current ≤ 2×ROP) | 43 | 6.9% |
| Excess (Current > 2×ROP) | 60 | 9.6% |
| No_Demand (ROP = 0) | 13 | 2.1% |

- **Total ROP:** 601,481 units · **Total positive reorder gap:** **502,668 units**.
- **Shortage items (510)** carry **722,783 units of annual forecast = 85.4%** of covered forecast volume → the replenishment signal is concentrated on the high-throughput catalogue.

## 2. Top shortages (by reorder gap — all Critical)

| PL_Code | Reorder Gap | ROP | Current Stock | Forecast (annual) | Description |
|---------|------------:|----:|--------------:|------------------:|-------------|
| 56501006 | 86,474 | 86,474 | 0 | 139,193 | PVC insulated armoured cable |
| 56509959 | 47,378 | 47,378 | 0 | 58,378 | PVC insulating cable |
| 56501018 | 41,291 | 41,527 | 236 | 62,168 | PVC insulated cable |
| 561196180021 | 41,205 | 47,178 | 5,973 | 90,614 | Cable jelly-filled underground |
| 509000396559 | 39,065 | 42,178 | 3,113 | 60,027 | 48-fibre OFC (armoured) |
| 539804752183 | 34,065 | 34,065 | 0 | 18,644 | OFC 24-fibre armoured |
| 56119033 | 22,042 | 22,042 | 0 | 20,018 | PVC armoured cable |

## 3. Top excesses (by reorder gap)

| PL_Code | Reorder Gap | ROP | Current Stock | Description |
|---------|------------:|----:|--------------:|-------------|
| 539802804167 | −70,266 | 8,534 | 78,800 | HDPE pipe |
| 56507641 | −35,664 | 20,746 | 56,410 | Channel bond pin |
| 539851110029 | −5,399 | 847 | 6,246 | Fuse block |
| 56509376 | −5,183 | 12,540 | 17,723 | ARA terminal block |
| 56110029 | −3,915 | 908 | 4,823 | PVC armoured cable |

Excess items are capital tied up against low forecast demand — candidates for redistribution/rationalization (existing operational rationalization layer, unchanged).

## 4. Coverage of shortages vs total forecast volume
- Shortage (Critical + Shortage) PLs = 510 → **85.4% of covered forecast volume** is in a shortage position at depot 027534.
- *(Inventory-value of gaps not computed here — unit cost for the 027534 universe is a separate data layer; flagged for procurement step. Reorder gap is reported in units, traceable.)*

## 5. Interpretation caveat
Depot **027534 is an issuing depot** (high flow, low holding). The 74% Critical-Shortage rate is therefore partly **structural** (issuing depots don't buffer fast-movers) and partly **real** (genuine under-stock vs forecast). The ROP/gap is a correct replenishment *signal*; the downstream procurement decision should weigh the depot operating model and open POs (NS_DM_CONS shows active procurement against several of these PLs).

## 6. STEP 26 SRRS readiness

| | Before STEP 25 | **After STEP 25** |
|---|---:|---:|
| STEP 26 SRRS | 80 | **90** |

SRRS = `Criticality_Weight × Service_Factor × Positive_Gap × …`. The **Positive_Gap** term is now computed for 626 PLs (96% volume), and binary criticality covers 99.6%. With ROP and the reorder gap in hand, SRRS is directly computable by reusing the existing SRRS objective. Remaining headroom to 100: precise S1–S4 criticality weights (binary only today) and the 4%-volume lead-time tail.

## 7. Can STEP 26 proceed?
✅ **Yes.** All SRRS inputs now exist: Positive_Gap (STEP 25), binary Criticality_Weight (STEP 23.8), service factor / lead-time factor / demand factor (derivable from existing data). SRRS can run at binary-criticality granularity for the 626-PL / 96%-volume set.

## 8. Recommended next phase
**STEP 26 — Division SRRS (MAS):** compute the Service-Risk-Reduction Score using the existing SRRS objective on the STEP 25 reorder gaps + binary criticality, to **prioritize the 510 shortage items** for action. In parallel (optional): obtain unit cost for the 027534 universe to express reorder gaps in ₹, and pursue an extended S1–S4 criticality master for finer SRRS weighting.

*Additive computation only. No forecasting, safety-stock, procurement, SRRS, or enterprise output was modified.*
