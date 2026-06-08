# STEP 23.5 — Planning Master Data Foundation: Discovery Report

**Type:** Read-only data audit. **No synthetic values, no estimated lead times/criticality/pending-supply. No analytical logic modified.**
**Date:** 2026-06-08 · **Scope:** MAS · **Planning universe:** the 1,083 DMTR demand PLs (the items STEP24/25/26 would plan).
**Deliverable companion:** `outputs/MAS/history/planning_master_data_audit.csv` (one row per PL, value populated only where a real source exists; blank = missing).

---

## 1. Field-by-field availability (over 1,083 planning PLs)

| Field | Source file(s) | Populated | Missing | Coverage | Suitability for planning |
|-------|----------------|----------:|--------:|---------:|--------------------------|
| Description | demand_classification / DMTR | 1,083 | 0 | 100% | ✅ ready |
| Business_Unit | STEP21A (MAS) | 1,083 | 0 | 100% | ✅ ready |
| Forecast_Method | forecast_method_assignment | 1,083 | 0 | 100% | ✅ ready |
| Forecastability_Class | forecast_accuracy | 961 | 122 | 88.7% | ✅ (122 Dead n/a) |
| Forecast_2026_27 | forecast_results | 961 | 122 | 88.7% | ✅ (Dead → no forecast) |
| Supplier_Info | DMTR receipts (vendor "From …") | 852 | 231 | 78.7% | ✅ strong |
| Procurement_History | DMTR receipts (any) | 861 | 222 | 79.5% | ✅ strong |
| Unit_Cost | operational_inventory / sku_master | 52 | 1,031 | 4.8% | ❌ sparse |
| Current_Stock | operational_inventory / sku_master | 52 | 1,031 | 4.8% | ❌ sparse |
| ABC_Class | railway_sku_master (strategic 59) | 32 | 1,051 | 3.0% | ❌ sparse |
| Criticality | railway_sku_master | 32 | 1,051 | 3.0% | ❌ sparse |
| Criticality_Name | code→label map (S1–S4) | 32 | 1,051 | 3.0% | ❌ sparse |
| Pending_Supply | railway_sku_master / railways.xlsx | 31 | 1,052 | 2.9% | ❌ sparse |
| Strategic_Stock | strategic_inventory_allocation | 27 | 1,056 | 2.5% | ❌ sparse |
| Operational_Stock | operational_inventory | 20 | 1,063 | 1.8% | ❌ sparse |
| Inventory_Value | operational_inventory | 20 | 1,063 | 1.8% | ❌ sparse |
| **Lead_Time_Months** | **none (no stored field anywhere)** | **0** | **1,083** | **0%** | ❌ **absent** |

> `Criticality_Name` uses a fixed S1→Safety / S2→Vital / S3→Essential / S4→Desirable label map applied **only where Criticality already exists** — no criticality was estimated.

## 2. Required coverage headlines

| Coverage | Value | Note |
|----------|------:|------|
| Criticality | **3.0%** | only 32/1,083 in the strategic vital-items master |
| Lead-time (native) | **0.0%** | no stored lead-time field in any source |
| Pending-supply | **2.9%** | only strategic 59-item universe |
| Supplier | **78.7%** | DMTR receipt "From <vendor>" |
| Procurement-history | **79.5%** | DMTR receipt transactions (incl. DBR refs) |

## 3. Root cause — the demand and inventory universes are different stores ledgers

The low coverage is **not** a key-format problem (digit-normalization does not change the overlap). It is a genuine **universe/depot mismatch**:

| Universe | Key / depot | Items | Overlap with DMTR (1,083) |
|----------|-------------|------:|--------------------------:|
| **DMTR demand register** (forecast source) | office/depot **`027534`** | 1,083 | — |
| Operational stock snapshot (`stock_history`) | consignee depot **`PER027029`** | 907 | **20** |
| Strategic vital-items master (criticality/ABC/pending) | zone-level | 59 | **32** |
| Strategic allocation (strategic stock) | zone-level | — | **27** |

The forecast is built from depot **027534**'s transactions, while current stock sits in depot **027029** and criticality is zone-level. **They share almost no items**, so the forecast cannot today be joined to stock, criticality, lead time or pending supply for the same PL. This is the single structural blocker behind every sparse field above.

## 4. Readiness assessment (STEP24/25/26)

Each capability's formula inputs and their real availability:

### STEP 24 — Safety Stock (`SS = z·σ·√LT`)
| Input | Available? |
|-------|-----------|
| Demand σ (monthly) | ✅ 100% (STEP21A/22) |
| Service-level z ← Criticality | ❌ 3% |
| Lead time (LT) | ❌ 0% |
**Verdict: 🔴 Not Ready.** Demand variability is in place; the two remaining multiplicative inputs (lead time, criticality-driven service level) are essentially absent for the forecast universe.

### STEP 25 — Division ROP (`ROP = demand·LT + SS`)
| Input | Available? |
|-------|-----------|
| Forecast demand | ✅ 88.7% |
| Lead time | ❌ 0% |
| Safety stock (STEP24) | ⛔ depends on 24 |
| Current stock (for gap) | ❌ 4.8% |
**Verdict: 🔴 Not Ready.** Blocked by lead time (0%) and current stock (4.8%) for the forecast items.

### STEP 26 — Division SRRS (`Crit_Wt · Service · Positive_Gap · LT_Factor · Demand_Factor`)
| Input | Available? |
|-------|-----------|
| Criticality weight | ❌ 3% |
| Positive gap (ROP − stock) | ⛔ depends on 25 (stock 4.8%) |
| Lead-time factor | ❌ 0% |
| Pending supply | ❌ 2.9% |
**Verdict: 🔴 Not Ready.** Every non-demand input is missing for the forecast universe.

## 5. Blockers ranked by impact

| # | Blocker | Coverage | Impact |
|---|---------|---------:|--------|
| 1 | **Demand↔inventory universe reconciliation** (DMTR 027534 ↔ stock 027029 ↔ zone criticality) | 1.8–3% | **Critical** — gates joining forecasts to stock/criticality/pending; blocks 24, 25, 26 |
| 2 | **Lead-time data** (no stored field) | 0% | **Critical** — appears in every SS/ROP/SRRS formula |
| 3 | **Criticality linkage** for DMTR items | 3% | High — service-level differentiation (24) + SRRS weight (26) |
| 4 | **Current stock** for forecast items | 4.8% | High — ROP gap (25) + SRRS gap (26) |
| 5 | **Pending supply** for forecast items | 2.9% | Medium — Tier-1 lead-time derivation + SRRS |

## 6. Strengths (foundation already strong)
- **Forecasting layer complete:** method (100%), forecast (88.7%), demand variability/σ (100%).
- **Procurement/supplier signal rich:** ~79% of forecast items have receipt transactions with named vendors and DBR references — a viable basis to **derive** lead times from order→receipt intervals (a data path, not an estimate to fabricate here).

## 7. Readiness scores

| Step | Score / 100 | Rationale |
|------|------------:|-----------|
| **STEP 24 Safety Stock** | **28** | σ ready (strong); lead time 0% + criticality 3% absent |
| **STEP 25 Division ROP** | **18** | forecast ready; lead time 0% + current stock 4.8% absent |
| **STEP 26 Division SRRS** | **12** | all of criticality/gap/lead-time/pending absent for forecast universe |

## 8. Recommended data-acquisition actions (no synthesis)
1. **Obtain the current stock + ledger for DMTR depot 027534** (or a unified PL master linking 027534 ↔ 027029) so forecast items gain current stock, unit cost and a consistent key. *(Unblocks #1, #4.)*
2. **Source lead times** — preferred: extract order-to-receipt intervals from DMTR procurement events (DBR/receipt dates) where ~79% coverage exists; alternative: a PO/procurement master. *(Unblocks #2.)*
3. **Extend criticality (S1–S4 / vital-items) to the DMTR PL universe** — link the safety/vital classification beyond the 59 zone items. *(Unblocks #3.)*
4. **Obtain open-PO / pending-supply data** for depot 027534. *(Unblocks #5.)*
5. **Build a unified cross-depot PL master** as the canonical join key for all planning. *(Foundation for #1.)*

## 9. Recommended implementation sequence
```
STEP 23.6  Universe & PL-master reconciliation  (depot 027534 stock + key map)   [Critical, prerequisite]
   └─ STEP 23.7  Lead-time derivation (DMTR order→receipt) + criticality extension
        └─ STEP 24  Safety Stock      (σ ready + LT + service level)
             └─ STEP 25  Division ROP (forecast + LT + SS + current stock)
                  └─ STEP 26  Division SRRS (criticality + gap + LT + pending)
```
Until reconciliation (23.6) and lead-time/criticality (23.7) are delivered, STEP24–26 can only run on the **~20–32 reconciled pilot PLs** or remain zone-level. **Do not proceed to STEP24 on the full universe** until lead-time and criticality coverage materially improve.

---

### Closeout
1. **STEP24 readiness:** 28/100 (σ ready; lead time + criticality absent).
2. **STEP25 readiness:** 18/100 (forecast ready; lead time + current stock absent).
3. **STEP26 readiness:** 12/100 (all non-demand inputs absent).
4. **Data-acquisition actions:** §8 — depot-027534 stock/key master, lead-time derivation from DMTR procurement events, criticality extension, open-PO data, unified PL master.
5. **Implementation sequence:** §9 — reconcile universe (23.6) → lead-time + criticality (23.7) → STEP24 → 25 → 26.

*No existing file was modified. Two new artifacts written: `planning_master_data_audit.csv`, `STEP23_5_DISCOVERY_REPORT.md`. No values were synthesized; missing data is left blank.*
