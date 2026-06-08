# STEP 23.6A — Lead-Time Discovery & Procurement Signal Mining

**Type:** Investigative / feasibility. **No synthetic lead times. No lead times derived into production. No analytical logic modified.**
**Date:** 2026-06-08 · **Scope:** MAS DMTR (54 files, 3,670 receipt transactions, 1,083 demand PLs).
**Question answered:** *Can lead times be reconstructed from internal DMTR data with enough coverage/reliability to support Safety Stock, ROP and SRRS?* → **Yes, for ~65% of the demand universe.**

---

## 1. Procurement signal architecture

```
DMTR receipt transaction
 ├─ col2  Receipt Date          (anchor, 100%)            ◄── interval end
 ├─ col3  Transaction type      (Vendor / Stores-Depot / User-Depot / Shop-Mfrd)
 ├─ col8  Transaction detail
 │     ├─ "From M/s <VENDOR>"                  42.5%  (177 distinct vendors)
 │     ├─ "PO / Contract No. <id> dt. <DATE>"  42.4%  ─┐ order date
 │     ├─ "Reqn No. <id> dt. <DATE>"           34.8%  ─┤ precedes receipt  ◄── interval start
 │     └─ "vide Challan No. <id> dt. <date>"   42.9%  (dispatch → transit only)
 └─ col11 Remarks "DBR No. <id> ... dt. <date>" 95.9%/72.1%  (≈ receipt posting date)
                                   │
                                   ▼
   Lead time = Receipt Date − {PO date  |  Reqn date}
                                   ▼
   PO→Receipt (vendor)  ∪  Reqn→Receipt (internal)  =  702 PLs (64.8%)
```

## 2. Procurement signal inventory (of 3,670 receipt transactions)

| Signal | Source field | Coverage | Distinct | Suitable for LT |
|--------|--------------|---------:|---------:|-----------------|
| Receipt Date | col2 `dt.` | 100% | — | No (anchor) |
| Receipt Quantity | col9 | 100% | — | No |
| Vendor Receipt | col3 type | 42.5% | 177 vendors | Indirect |
| **PO / Contract Date** | col8 `PO … dt.` | **42.4%** | — | **YES** |
| PO / Contract Number | col8 | 42.8% | 293 | Indirect |
| **Requisition (Demand/Indent) Date** | col8 `Reqn … dt.` | **34.8%** | — | **YES** |
| Requisition Number | col8 | 55.0% | 778 | Indirect |
| Challan Number | col8 `vide Challan` | 42.9% | 612 | Indirect (transit) |
| DBR Number | col11 | 95.9% | 1,456 | No |
| DBR Date | col11 | 72.1% | — | No (≈ receipt date) |

*(Full machine-readable catalogue: `procurement_signal_inventory.csv`.)*

## 3. Candidate lead-time derivation paths

| Method | Required fields | PL coverage | Reliability (non-neg) | Feasible | Note |
|--------|-----------------|------------:|----------------------:|----------|------|
| **PO→Receipt** | PO date + Receipt date | **47.8%** | **100%** | ✅ Yes | vendor procurement LT; 1,545 obs / 516 PLs; median **119 d**, p90 480 d |
| **Reqn→Receipt** | Reqn date + Receipt date | **22.5%** | **100%** | ✅ Yes | internal fulfilment LT; 1,276 obs / 244 PLs; median **49 d** |
| **Combined (PO∪Reqn)** | either order date + receipt | **64.8%** | 100% | ✅ Yes | **702 PLs** of 1,083 |
| Challan→Receipt | Challan date + Receipt | 47.8% | — | ❌ No | transit time only, not full LT |
| DBR→Receipt | DBR date + Receipt | ~72% | — | ❌ No | DBR ≈ receipt posting date → ~0 interval |
| Demand(Issue)→Receipt | Issue + next receipt | — | — | ❌ No | replenishment interval, not a procurement LT |

*(Machine-readable: `lead_time_feasibility.csv`. Feasible rule: PL coverage ≥20% AND reliability ≥95% AND plausible distribution.)*

## 4. Coverage analysis
- **64.8% of the 1,083 demand PLs** have ≥1 derivable lead-time observation (PO or Reqn → Receipt).
- Two complementary semantics: **vendor** procurement LT (PO, 516 PLs, ~4-month median) and **internal** stores-fulfilment LT (Reqn, 244 PLs, ~7-week median).
- Uncovered ~35% (381 PLs): Dead items (122, no receipts), items only *issued* in-window, and receipts lacking a dated order reference (e.g. some Shop-Mfrd, book transfers, returns).

## 5. Reliability analysis
- **Zero negative intervals** on both PO→Receipt (1,545) and Reqn→Receipt (1,276) — order dates always precede receipt dates (clean chronology, high integrity).
- Distributions are operationally plausible (vendor median 119 d; 84% within a year). Long-tail outliers exist (max ~5 yr) — to be **winsorized/aggregated** in the derivation phase (not here).
- Risk: PO/Reqn dates are *document* dates (order placement / indent raising), so the derived LT is **order-to-receipt** — the correct replenishment lead time for SS/ROP, but it bundles internal approval + vendor lead + transit (acceptable, and what inventory theory wants).

## 6. Readiness scores (evidence-based)

| Dimension | Before 23.6A | After 23.6A | Basis |
|-----------|-------------:|------------:|-------|
| **Lead-Time Derivation Readiness** | 0 | **70** | 64.8% PL coverage, 100% reliability, 2 clean paths; −30 for the 35% uncovered + outlier handling pending |
| **STEP 24 (Safety Stock)** | 28 | **55** | σ ready + LT now derivable (65%); still limited by criticality/service-level (3%) |
| **STEP 25 (Division ROP)** | 18 | **35** | LT improves; still blocked by current-stock coverage (4.8%) for the gap |
| **STEP 26 (Division SRRS)** | 12 | **22** | LT improves; criticality (3%) + stock still block |

## 7. Verdicts

- **Can STEP 24 proceed on internal data only?** **Yes — for the ~702 covered PLs.** Lead time is derivable internally; with demand σ already in place, Safety Stock can be computed for that subset (using default/criticality-tiered service levels until criticality is linked).
- **Are external procurement systems still required?** **Not for lead time** (internally derivable for 65%). They (or other internal data) remain needed to (a) reach the last ~35% of items, (b) link **criticality**, and (c) supply **current stock** for the DMTR depot — the STEP 23.5 universe-reconciliation gaps, which still gate STEP 25/26.
- **Recommended next phase:** **STEP 23.6B — Internal Lead-Time Derivation** (per-PL LT from PO + Reqn paths, outlier winsorizing, per-PL median + variability), feeding STEP 24 on the covered subset; run criticality + current-stock reconciliation in parallel for STEP 25/26.
