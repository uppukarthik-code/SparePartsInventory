# STEP 23.6A — Validation Report

**Date:** 2026-06-08 · **Subject:** Lead-time discovery & procurement signal mining (feasibility, read-only).
**Method:** Deterministic re-scan of all DMTR files + SHA-256 backward-compatibility guard.

---

## 1. Validation checklist

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | All DMTR files scanned | ✅ PASS | 54 / 54 files, 3,670 receipt transactions parsed |
| 2 | Procurement signals catalogued | ✅ PASS | 10 signals in `procurement_signal_inventory.csv` (vendor, PO no/date, Reqn no/date, DBR no/date, Challan, receipt date/qty) |
| 3 | Candidate lead-time fields identified | ✅ PASS | PO Date & Reqn Date confirmed as order-side dates preceding receipt |
| 4 | Coverage calculated | ✅ PASS | PL-level + receipt-level coverage in both CSVs |
| 5 | No synthetic values created | ✅ PASS | only observed dates measured; **no lead time derived or written** to any output |
| 6 | No forecasting outputs changed | ✅ PASS | within unchanged 506-file set |
| 7 | No planning outputs changed | ✅ PASS | `planning_master_data_audit.csv` etc. within unchanged set |
| 8 | No inventory outputs changed | ✅ PASS | within unchanged set |
| 9 | Backward compatibility maintained | ✅ PASS | SHA-256: 506 existing files, **0 changed / 0 added** (excl. 2 new catalogue CSVs) |

**All 9 checks PASS.**

## 2. Backward-compatibility (SHA-256)
```
Existing files fingerprinted (outputs/, excl. 2 new catalogue CSVs) : 506
Changed : 0     Added : 0     UNCHANGED : True
```
The step is purely investigative: it reads DMTR + existing outputs and writes only `procurement_signal_inventory.csv` and `lead_time_feasibility.csv`. No forecasting, planning, inventory, SRRS, procurement, Power BI or KPI artifact was modified.

## 3. No-synthesis assurance
- Lead-time **intervals were measured** (Receipt date − order date) **solely to assess feasibility** — coverage, reliability, distribution.
- **No per-PL lead time was assigned, estimated, or written into any planning master or production output.** The `Lead_Time_Months` field in `planning_master_data_audit.csv` remains untouched (0% populated).
- Where an order date was absent, the observation was excluded (not imputed).

## 4. Reliability evidence
- PO→Receipt: 1,545 paired observations, **0 negative intervals** (100% chronological validity).
- Reqn→Receipt: 1,276 paired observations, **0 negative intervals**.
- Combined PL coverage 702 / 1,083 = **64.8%**.

## 5. Verdict
**STEP 23.6A validation PASSED (9/9).** Procurement signals catalogued, two feasible internal lead-time derivation paths confirmed with 100% chronological reliability and 64.8% PL coverage, all with zero synthetic values and full byte-for-byte backward compatibility.
