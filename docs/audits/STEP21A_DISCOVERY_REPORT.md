# STEP 21A — DMTR Discovery Report

**Type:** Read-only schema discovery (pre-implementation gate).
**Date:** 2026-06-08
**Source:** `raw_data/Railway_Operations/MAS/` — 54 DMTR (Material Transaction Register) workbooks + `stock_history.xlsx`.

---

## 1. Decision: DMTR files DO contain transaction-level demand → implementation proceeds

The files are line-level material transaction registers (issues, receipts, opening stock). This is exactly the evidence required to reconstruct monthly demand. **No fabrication is necessary.**

## 2. Verified workbook structure (no assumptions)

- **One sheet per file:** `Sheet1`. **Header in row 1**, data from row 2. 12 columns, bilingual (Hindi/English) headers.
- **54 files = 54 distinct calendar months, Jan 2022 → Jun 2026, continuous, exactly one file per month** (verified: zero months covered by >1 file).

| Col (0-based) | Header (English part) | Field role | Example |
|---|---|---|---|
| 1 | `#` | serial | `1` |
| 2 | DMTR No. & date | **Date** (and DMTR id) | `027534-21-01561 dt. 03-01-2022 11:52:37by VENKATESH L` |
| 3 | Transaction type | **Issue/Receipt classification** | `Issue-To User Depot (Consignee)` |
| 4 | Ledger details | ledger | `001-ELECTRICAL I` |
| 5 | Folio details | folio | `0081-110V DC MOTOR…` |
| 6 | `PL No. / Code` | **PL_Code** | `539829580021` |
| 7 | Item description | Description | `110v DC motor with Gear` |
| 8 | Transaction detail | counterparty | `To SSE/Sig/BBQ Southern` |
| 9 | `Quantity` (+UOM) | **Quantity** | `10.000Number` |
| 10 | Value (₹) | value | `295000.00` |
| 11 | Remarks | — | `Issued through…` |
| 12 | Action | — | (blank) |

### 2.1 Field-by-field discovery answers
1. **Workbook structure:** single-sheet, flat transaction table. 2. **Sheet names:** `Sheet1` (all 54). 3. **Column names:** as table above. 4. **Transaction fields:** type (col 3), detail (col 8), value (col 10). 5. **PL code field:** col 6 (`PL No./Code`), **0 nulls**. 6. **Quantity field:** col 9 (`NN.NNN<UOM>`), **0 parse failures**. 7. **Receipt fields:** identified via transaction type `Receipt-*`. 8. **Issue fields:** transaction type `Issue-*`. 9. **Closing-stock field:** **NONE** — no running-balance column exists (see §4). 10. **Date field:** embedded in col 2 (`dt. DD-MM-YYYY HH:MM:SS`), **0 unparseable**.

## 3. Transaction-type vocabulary (17 types, full census of 19,618 transactions)

| Class | Types (count) |
|-------|---------------|
| **Issues — true consumption (demand)** | Issue-To User Depot (14,705) · Issue-For End Use (82) · Issue-To Contractor (35) |
| **Issues — non-demand** | Issue-Book Transfer (33, internal) · Write-Back Issue (78, reversal) |
| **Receipts (inflow)** | From Vendor (1,558) · Shop Mfrd./Old Demand (1,162) · Stores Depot S1313 (557) · User Depot (307) · Return by Contractor (34) · Book Transfer (33) · From Field (11) · Unconnected (7) · Vendor Warranty (1) |
| **Opening / adjustments** | Initial Stock (990) · Stock-Verification no-discrepancy (20) · Return of Rejected Material to Vendor (5) |

## 4. Critical finding — Closing_Stock is not a source field

The DMTR schema carries **no running balance / closing-stock column**. The required `Closing_Stock` output is therefore **reconstructed** (per agreed decision): opening from `Initial Stock` + cumulative (inflows − outflows). `stock_history.xlsx` (the current end-snapshot) is available as a reconciliation anchor, but its PL-key universe overlaps the DMTR universe in only ~20 codes, so Closing_Stock is treated as a **derived running balance**, not a verified absolute.

## 5. Data-quality census (source)

| Metric | Value |
|--------|------:|
| DMTR files | 54 |
| Transactions | 19,618 |
| Distinct PL codes | 1,083 |
| Null PL codes | 0 |
| Unparseable dates | 0 |
| Quantity parse failures | 0 |
| PLs with mixed UOM | 6 (0.55%) |
| Months covered by >1 file | 0 |
| Month span | 2022-01 → 2026-06 (54, continuous) |

## 6. Agreed reconstruction rules (carried into implementation)
1. **Issues_Qty (demand)** = Issue-To User Depot + Issue-For End Use + Issue-To Contractor (book-transfer & write-back excluded from demand, retained in balance + QA).
2. **Receipts_Qty** = all `Receipt-*`.
3. **Closing_Stock** = reconstructed running balance (Initial Stock + Σinflows − Σoutflows), reconciled vs stock_history in validation.
4. **Gap-fill** = per PL, first-observed month → 2026-06, missing months zero-filled.

**Verdict:** source is sufficient, clean, and continuous. Proceed to additive implementation.
