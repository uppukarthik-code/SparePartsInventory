# STOCK_RECONCILIATION_REPORT.md

**Type:** Read-only investigation. No derivations, no production files.
**Date:** 2026-06-08 · **Subject:** `SUMMARY OF STOCK HELD (as on 08-06-2026)` vs `stock_history.xlsx` and `enterprise_pl_master.csv`.

---

## 1. Identification

| Attribute | Value |
|-----------|-------|
| Depot code | **`SSE027534-S AND T-SR` — 100% of 1,260 rows → depot 027534** |
| Consignee | SSE/SIG/SRM/PER (Perambur S&T) |
| PL count | 1,099 distinct (504 with stock > 0) |
| Stock quantity | 256,665 units |
| Stock value | **₹290,079,651** |
| Snapshot date | 08-06-2026 |
| Schema | identical to `stock_history.xlsx` (PL-Code/Type/Usage, Stock, Unit, Avg Rate, Value, Last Receipt/Issue Dt) |

## 2. Which depot(s) does it contain?

| Option | Verdict |
|--------|---------|
| Depot 027029 | ❌ No (that is `stock_history.xlsx`) |
| **Depot 027534** | ✅ **Yes — 100%** |
| Both | ❌ No |
| Neither | ❌ No |

This is unambiguously the **depot-027534** stock ledger — the consignee that raised the DMTR demand transactions.

## 3. Comparison vs existing stock source

| | `stock_history.xlsx` | **`SUMMARY OF STOCK HELD`** |
|---|---|---|
| Depot | 027029 (PER) | **027534** |
| Distinct PLs | 907 | 1,099 |
| Total value | ₹512.4M | ₹290.1M |
| ∩ DMTR demand (1,083) | 20 (1.8%) | **1,079 (99.6%)** |
| ∩ each other | — | 20 (the two depots share only 20 PLs) |

The two snapshots are **different depots' ledgers** (only 20 common PLs), confirming the STEP 23.5/23.7 root cause: demand (027534) and the previously-loaded stock (027029) were different stores.

## 4. Overlap with the planning universes

| Universe | Size | ∩ SUMMARY (027534) |
|----------|-----:|-------------------:|
| **DMTR demand** | 1,083 | **1,079 (99.6%)** |
| Operational (027029) | 907 | 20 |
| Criticality | 59 | 32 |
| Lead-time-covered (702) | 702 | **698 (99.4%)** |
| Forecastable (961) | 961 | **961 (100%)** |

## 5. Does this resolve the STEP 23.7 current-stock blocker?

**YES — decisively.**

| | Before (STEP 23.7) | **After (SUMMARY 027534)** |
|---|---|---|
| DMTR demand PLs with current stock | **20 (1.8%)** | **1,079 (99.6%)** |
| Forecastable PLs with current stock | ~1.8% | **100% (961/961)** |
| Planning-complete (forecast + lead time + **stock**) | not possible | **626 PLs = 96.0% of forecast volume** |

The STEP 23.7 report stated the operational ROP/SRRS blocker was the absence of a depot-027534 current-stock snapshot. **That snapshot is exactly this file.** The enterprise PL master can now be joined to real current stock for essentially the entire demand universe.

## 6. Residual notes
- 4 DMTR demand PLs (0.4%) are not in SUMMARY — negligible.
- 504 of 1,099 PLs have non-zero stock; the rest are catalogued zero-stock items (normal for a stores ledger).
- Criticality is **not** in this file — it remains the one outstanding planning input (32/1,083).

## 7. Conclusion
`SUMMARY OF STOCK HELD` provides the **depot-027534 current stock** at **99.6% coverage of the demand universe**, resolving the STEP 23.7 current-stock blocker. Combined with forecasts (STEP 23) and lead times (STEP 23.6B), a **planning-complete set of 626 PLs covering 96% of forecast volume** now exists. The only remaining gap for full SRRS is **criticality**.
