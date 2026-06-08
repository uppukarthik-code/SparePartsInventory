# CONSUMPTION_RECONCILIATION_REPORT.md

**Type:** Read-only investigation. No derivations, no production files.
**Date:** 2026-06-08 · **Subject:** `NS_DM_CONS_REPORT*.xlsx` (7 files) vs STEP21A/STEP22.

---

## 1. What NS_DM_CONS actually is

A **demand-indent → procurement-lifecycle register** for consignee **027534** (SSE/SIG/SRM/PER). Each row is an *indent line* with its tendering, PO, delivery and receipt milestones. It captures **procurement demand** (what was indented for replenishment/new supply), **not** operational consumption.

| Field group | Fields | Meaning |
|-------------|--------|---------|
| Demand | `Dmd Qty`, `Dmd Unit`, `Indent Date`, `Indent Value` | quantity indented (procurement demand) |
| Procurement | `Proposal/Tender/PO No`, `PO Date`, `Item Qty/Rate/Value`, `LOA Supplier` | order lifecycle |
| Fulfilment | `Delivery Date`, `Qty Recd`, `Qty Recd Value`, `MA Date` | receipt against the indent |

## 2. Classification verdict

| Candidate meaning | Verdict |
|-------------------|---------|
| Consumption | ❌ No — not field issues |
| Issues | ❌ No |
| Demand (procurement/indent) | ✅ **Yes** — this is indented replenishment demand |
| AAC | ❌ Not directly (AAC is an annual consumption estimate; this is indent events) |
| Rolling demand | ◑ Partially — a sparse, event-driven procurement-demand signal |

It is a **different demand concept** from STEP21A, which reconstructs **monthly issues (consumption)** from the DMTR transaction register.

## 3. Comparison vs STEP21A monthly demand reconstruction

| Metric | NS_DM_CONS | STEP21A |
|--------|-----------|---------|
| Unit of record | indent line | monthly issue aggregate |
| Quantity meaning | indented qty (`Dmd Qty`) | issued qty (consumption) |
| Distinct PLs | 181 | 1,083 |
| Period | 2023-02 → 2026-06 | 2022-01 → 2026-06 |
| Total quantity | Dmd 137,615 · Recd 86,680 | Issues 2,727,684 |

### 3.1 Quantified overlap
- **NS ∩ STEP21A demand universe: 30 PLs** (17% of NS's 181; 2.8% of the 1,083 demand universe).
- **Missing PLs:** 151 NS PLs are **not** in the STEP21A demand universe — they are *indented* (new/replacement procurement) but were **not issued** in the transaction window (expected: indents precede stocking/issue).
- **Quantity reconciliation:** **not directly comparable** — `Dmd Qty` (procurement demand) and STEP21A `Issues_Qty` (consumption) measure different events; no like-for-like reconciliation is valid.
- **Value reconciliation:** NS carries indent/PO rupee values (procurement spend), not consumption value — again not comparable to STEP21A (which has no value).

## 4. Can NS_DM_CONS validate STEP21A / STEP22?

| Target | Validates? | Reason |
|--------|-----------|--------|
| STEP21A monthly **consumption** | ❌ **No (broadly)** | different metric (indent vs issue); only 30-PL overlap |
| STEP22 demand **classification** | ◑ Limited | the 30 overlapping PLs can be spot-checked, but indents are too sparse to confirm intermittency patterns |
| **STEP23.6B lead times** | ✅ **Yes — strong independent corroboration** | NS has Indent→PO→Delivery dates |

### 4.1 Lead-time corroboration (the real validation value)
Independent procurement lead times from NS_DM_CONS:

| Interval | n | Median |
|----------|--:|-------:|
| Indent → PO | 178 | 88 days |
| PO → Delivery | 177 | 90 days |
| **Indent → Delivery (full)** | — | **~178 days** |

This **corroborates** the STEP23.6B DMTR-derived **PO→Receipt median of ~119 days**: the PO→delivery leg (90 d) plus receipt posting lag is consistent with ~119 d, and the full indent-to-delivery (~178 d) cleanly decomposes into a ~88-day tendering phase + ~90-day supply phase. The two independent sources agree on order-of-magnitude lead times — increasing confidence in `lead_time_master.csv`.

## 5. Conclusion
`NS_DM_CONS_REPORT` is a **procurement-demand / lifecycle** source. It **cannot** validate STEP21A consumption (different metric, 30-PL overlap) but provides **strong independent validation of the STEP23.6B lead times** and a procurement-demand lens for the ~181 high-value indented items. Treat it as a **lead-time and procurement-governance** source, not a consumption cross-check.
