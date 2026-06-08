# DATA_SOURCE_AUDIT.md

**Type:** Read-only investigation. No code, no production files, no derivations.
**Date:** 2026-06-08 · **Scope:** MAS · Newly discovered sources in `raw_data/Railway_Operations/MAS/`.

---

## 1. Sources audited

| Source | Files | Rows | What it is |
|--------|------:|-----:|------------|
| `NS_DM_CONS_REPORT_08-06-2026*.xlsx` | 7 | 232 indents | **Indent → procurement-lifecycle register** (demand→tender→PO→delivery→receipt) |
| `SUMMARY OF STOCK HELD (as on 08-06-2026)_*.xlsx` | 1 | 1,260 | **Current-stock snapshot for depot 027534** |
| `stock_history.xlsx` | 1 | 907 | current-stock snapshot for depot **027029** (prior) |
| `outputs/MAS/history/*` | — | — | STEP21A–23.7 demand/forecast/LT/master artifacts |
| `enterprise_pl_master.csv` | 1 | 1,990 | STEP23.7 canonical PL union |
| `lead_time_master.csv` | 1 | 702 | STEP23.6B derived lead times |

## 2. NS_DM_CONS_REPORT — schema & nature

54 columns. Each row = one **indent line** tracked through the procurement lifecycle:
`S No · Indenting Consignee (Code 027534, SSE/SIG/SRM/PER) · Indent No · Indent Date · PL/Item Code · Item Details · Dmd Qty · Dmd Unit · Indent Value · Status · Purchase Section · Proposal No/Date · Tender No/Floating/Opening · LOA Supplier · PO No · PO Date · Item Qty · Item Rate · Item Value · Delivery Date · Qty Recd · Qty Recd Value · MA No/Date · UWID · Work Order No`.

| Attribute | Value |
|-----------|-------|
| Reporting period | indent dates **2023-02 → 2026-06** (report generated 08-06-2026) |
| Depot / consignee | **027534** — SSE/SIG/SRM/PER, SR (the *same depot* as the DMTR demand universe) |
| PL coverage | 181 distinct PLs across 232 indents |
| Quantity fields | `Dmd Qty` (indent), `Item Qty` (PO), `Qty Recd` |
| Value fields | `Indent Value`, `Item Rate`, `Item Value`, `Qty Recd Value` |
| **Represents** | **procurement DEMAND (indents) + full procurement lifecycle** — *not* consumption/issues, *not* AAC |

## 3. SUMMARY OF STOCK HELD — schema & nature

13 columns, identical layout to `stock_history.xlsx`:
`# · Consignee Depot · Ledger No · PL-Code/Type/Usage · Stock/Non-Stock Category · Brief Description · Last Receipt/Issue Dt · Stock · Unit · Threshold Limit · Average Rate · Value · Action`.

| Attribute | Value |
|-----------|-------|
| Depot code | **`SSE027534-S AND T-SR` — 100% depot 027534** |
| Consignee | SSE/SIG/SRM/PER (Perambur S&T) |
| PL count | 1,099 distinct (1,260 rows); **504 with stock > 0** |
| Stock quantity | 256,665 units |
| Stock value | **₹290,079,651** |
| Location | single consignee depot 027534 |
| **Represents** | **current-stock snapshot for depot 027534** (as on 08-06-2026) |

## 4. The two depots, side by side

| | Demand register (DMTR) | Old stock (`stock_history`) | **New stock (`SUMMARY`)** |
|---|---|---|---|
| Depot | **027534** | 027029 (PER) | **027534** |
| PLs | 1,083 | 907 | 1,099 |
| ∩ DMTR demand | — | 20 (1.8%) | **1,079 (99.6%)** |

**Headline:** the `SUMMARY OF STOCK HELD` is the stock ledger of the **same depot (027534)** that raised the demand transactions — the missing piece STEP 23.7 identified. `stock_history.xlsx` (027029) was a *different* depot, which is why it overlapped only 20 PLs.

## 5. Suitability summary

| Source | Best use | Not suitable for |
|--------|----------|------------------|
| NS_DM_CONS | **Lead-time validation** (Indent→PO→Delivery); procurement-demand insight | validating STEP21A *consumption* (different metric; 30-PL overlap) |
| SUMMARY OF STOCK HELD | **Resolving the STEP 23.7 current-stock blocker** (99.6% of demand universe) | criticality (not present) |

Detailed reconciliations: `CONSUMPTION_RECONCILIATION_REPORT.md`, `STOCK_RECONCILIATION_REPORT.md`. Readiness: `READINESS_REASSESSMENT_REPORT.md`.
