# STEP 23.6B — Readiness Report

**Date:** 2026-06-08 · **Scope:** MAS · Evidence-based, post lead-time derivation.

---

## 1. Lead-time distribution analysis

| Statistic (days) | Value |
|------------------|------:|
| n (PLs) | 702 |
| min / p25 / median / p75 / p90 / max | 0 / 66 / **128** / 249 / 437 / 668 |
| mean | 184 |

- **PO_Date (vendor procurement):** 518 PLs, median **131 d** (~4.3 months) — dominant, reflects external replenishment.
- **Requisition_Date (internal fulfilment):** 184 PLs, median **81 d** (~2.7 months).
- Distribution is operationally credible for signalling spares; winsorized to (33–668 d PO; 0–618 d Reqn). Most PLs are **Low confidence** (575, <5 receipts) — usable but with wider uncertainty; 127 PLs are Medium/High.

## 2. Long-lead, high-volume items (top forecast volume with LT ≥ 180 d)

| PL_Code | Median LT | Forecast vol | Conf | Description |
|---------|----------:|-------------:|------|-------------|
| 539804752183 | 333 d | 18,644 | Medium | OFC cable 24-fibre armoured |
| 569003030023 | 367 d | 12,876 | Low | Fire-alarm fire-survival cable |
| 569003030035 | 365 d | 9,870 | Low | Fire-alarm fire-survival cable |
| 569034910069 | 209 d | 9,713 | Low | Cable protection tube |
| 569060390045 | 248 d | 5,700 | Low | Weatherproof rain protection |
| 910100820060 | 474 d | 5,700 | Low | Aluminium sheet |
| 539880410093 | 206 d | 3,992 | Medium | Modular terminal block 2.5 |

These long-lead high-volume items drive the largest safety-stock requirements (SS ∝ √LT) and are the priority focus for STEP 24 — flagged that several are Low confidence (few receipts), warranting conservative buffering.

## 3. Universe reconciliation findings
- Four planning universes are **near-disjoint**: **Fully_Reconciled = 0** of 1,990 union PLs.
- Demand register (depot 027534) ∩ Operational stock (depot 027029) = **20 PLs**; ∩ Criticality = 32; ∩ Strategic = 27.
- 1,031 PLs are Demand_Only (forecastable but no stock/criticality); 880 are Inventory_Only.
- **Implication:** demand/forecast and inventory/criticality live in separate stores ledgers — the binding constraint for ROP/SRRS (which need current stock + criticality for the *same* PL).

## 4. Recalculated readiness

| Step | 23.5 | 23.6A | **23.6B** | Rationale |
|------|----:|----:|----:|-----------|
| **STEP 24 Safety Stock** | 28 | 55 | **72** | σ (100%) + **derived LT (96% of volume)** in hand; can run on 702 PLs with default/tiered service level. Gap: criticality-tiered service (3%) + 4%-volume tail |
| **STEP 25 Division ROP** | 18 | 35 | **45** | ROP *level* derivable (forecast + LT + SS); **gap-vs-stock blocked** — DMTR∩Operational only 20 PLs (1.8%) |
| **STEP 26 Division SRRS** | 12 | 22 | **30** | LT in hand; still blocked by criticality (3%) + current-stock gap |

## 5. Remaining blockers (ranked)

| # | Blocker | Coverage | Impact |
|---|---------|---------:|--------|
| 1 | **Current-stock reconciliation** (demand depot 027534 ↔ stock depot 027029) | 1.8% (20 PLs) | **Critical** — gates ROP gap (25) + SRRS gap (26); now the #1 blocker (lead time resolved) |
| 2 | **Criticality linkage** to DMTR PLs | 3% | High — service-level tiering (24) + SRRS weight (26) |
| 3 | LT confidence for low-observation PLs | 575 Low | Medium — usable, wider uncertainty; buffer conservatively |
| 4 | LT tail (PLs without dated procurement refs) | 35% PL / **4% volume** | Low — immaterial by volume |

## 6. Expected-outcome answer
**Yes — STEP 24 Safety Stock can be executed for a meaningful subset without external systems.** The 702 lead-time-covered PLs represent **96% of MAS forecast volume**; with demand σ already derived, safety stock is computable now (uniform or criticality-tiered service level). Lead time is **no longer the blocker**.

## 7. Recommended next phase
**STEP 24 — Safety Stock (pilot on the 702-PL / 96%-volume subset)** using `lead_time_master.csv` + demand σ + a default service level (criticality-tiered where the 32 overlapping PLs allow), reusing the existing `SS = z·σ·√LT` logic unchanged. **In parallel: current-stock reconciliation** (obtain depot-027534 stock or a unified cross-depot PL master) to unblock STEP 25 ROP-gap and STEP 26 SRRS. Do **not** gate STEP 24 on the stock reconciliation — it can proceed independently and immediately.
