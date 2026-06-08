# STEP 23.7 — Enterprise Impact Analysis

**Date:** 2026-06-08 · **Scope:** MAS · Before vs After reconciliation.

---

## 1. Universe sizes (unchanged — reconciliation preserves, never mutates)

| Universe | Source | PLs |
|----------|--------|----:|
| A — DMTR demand | demand_classification.csv | 1,083 |
| B — Operational stock | railway_operational_inventory.csv | 907 |
| C — Strategic | strategic_inventory_allocation.csv (MAS) | 41 |
| D — Criticality | railway_sku_master.csv | 59 |
| **Union (enterprise master)** | enterprise_pl_master.csv | **1,990** |

## 2. Before vs After reconciliation

| Metric | Before | After (exact master) | After (incl. review candidates) |
|--------|-------:|---------------------:|--------------------------------:|
| DMTR ∩ Inventory | 20 | 20 | up to ~88 (20 + ≤68 candidate, review-only) |
| DMTR ∩ Criticality | 32 | 32 | 33 |
| Fully_Reconciled (D&I&C) | 0 | **0** | ~0 (candidates add inventory, not criticality) |
| Planning_Ready (D&LT&C) | n/a | **27** | 27 |
| Forecast_Ready (D&LT) | n/a | **675** | 675 |
| Forecast-volume covered (Planning+Forecast Ready) | n/a | **96%** | 96% |

**Reconciliation recovers essentially zero *confirmed* additional overlaps.** Normalization changed 12 codes and recovered **0** new exact matches; candidate matching offers ≤68 *review* leads (only 15 high-confidence). The structural gap is unchanged.

## 3. Expected-outcome answers (quantitative)

1. **Why only 20 PLs overlap:** the demand register (issuing depot **027534**) and the operational stock snapshot (consignee depot **027029**) are **different stores ledgers holding/transacting largely different material sets** — only 20 materials are common.
2. **Mismatch type — COMBINATION, in order of magnitude:**
   - **Different depots/ledgers (dominant):** 027534 vs 027029 — explains ~95% of the gap.
   - **Different PL coding (secondary, minor):** 8-vs-12-digit eras + ad-hoc general-item codes — ~68 candidate PLs (~15 reliable).
   - **Different material classes (embedded in the above):** the two depots stock different signalling-material subsets.
   - **NOT normalization:** leading-zero/whitespace fixes recovered 0 matches.
3. **Additional PLs reconciled after normalization:** exact = **+0** (stays 20); after *manual review* of candidates, up to **+68** DMTR PLs could link to inventory (realistically ~15 high-confidence). No automatic gain.
4. **Can STEP 25 / STEP 26 proceed after reconciliation?** **No — not operationally.** Even at the optimistic ~88 DMTR∩Inventory (≤8% of demand universe), ROP-gap (25) and SRRS-gap (26) need *current stock* for the demand items — which lives at depot **027534**, absent from all current sources. Reconciliation **quantifies** the blocker; it cannot **supply the missing stock data**.
5. **Remaining blockers, ranked by business impact:**
   | # | Blocker | Impact |
   |---|---------|--------|
   | 1 | **Acquire depot-027534 current-stock snapshot** (the demand depot's own inventory) | **Critical** — sole path to operational ROP/SRRS for the demand universe |
   | 2 | **Extend criticality (S1–S4)** to the DMTR PL universe | High — service-level tiering (24) + SRRS weight (26); only 32/1,083 today |
   | 3 | Manual review of 144 PL match candidates | Low — recovers ~15–68 PLs; marginal |
   | 4 | LT confidence for low-observation PLs | Low — usable, wider uncertainty |

## 4. Readiness scores

| Step | 23.6B | **23.7** | Note |
|------|------:|---------:|------|
| **STEP 24 Safety Stock** | 72 | **74** | master confirms routing; 27 PLs now have criticality-tiered service, 702 default-service ready; **can proceed now** |
| **STEP 25 Division ROP** | 45 | **45** | unchanged — reconciliation quantified but did not fix the current-stock gap |
| **STEP 26 Division SRRS** | 30 | **30** | unchanged — criticality + stock gaps persist |

## 5. Recommended next step
**Proceed to STEP 24 Safety Stock** on the **702-PL / 96%-volume** subset (`lead_time_master.csv` + demand σ + default/criticality-tiered service), reusing the existing `SS = z·σ·√LT` logic unchanged. **In parallel, the single highest-value data action is acquiring the depot-027534 current-stock snapshot** (or a unified cross-depot stock ledger) — this, not further normalization, is what makes STEP 25/26 operational. The enterprise PL master is now the canonical join surface ready to absorb that stock feed when it arrives.
