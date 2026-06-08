# Railway Stock Summary — Data Quality Report

**Source file:** `raw_data/railway_stock_summary.xlsx` (Sheet1, 907 rows)
**Generated:** 2026-06-07 (Phase 1 — Discovery)
**Reference date for aging:** 2026-06-07

---

## 1. Missing values

| Column | Missing / placeholder | Impact |
|---|---|---|
| `Action` (col 14) | **907 / 907 empty** | Column carries no information — will be ignored. |
| `AAC` (col 10) | **906 / 907 = `--NA--`** | Annual Average Consumption is effectively absent. **Blocks true Annual-Issue-Value ABC.** |
| `Threshold Limit` (col 11) | **906 / 907 = 0.000** | No native reorder / safety-stock signal in the data. |
| `Last Receipt/Issue Dt.` (col 7) | 46 rows both dates blank; 167 receipt-only; 61 issue-only | Aging cannot be computed for the 46 fully-blank rows → bucket as `No Movement Date`. |
| All other columns | 0 missing | — |

No `Brief Description`, `Stock`, `Rate`, `Value`, `Unit`, or `PL-Code` values are missing.

---

## 2. Duplicate items

| Check | Result | Action |
|---|---|---|
| Duplicate **PL-Code** | **0** | PL-Code is a clean unique key → use as `SKU` base. |
| Duplicate **Description** (different PL-Codes) | 60 groups, 109 rows | **Legitimate** (same item, different folio/spec). Do **not** merge. |
| Fully identical rows | 0 | — |

---

## 3. Date quality

- **Format:** `DD-MM-YYYY`, stored as text inside the composite `Last Receipt/Issue Dt.` (`receipt / issue`).
- **Parse failures:** 0 (every non-blank token is a valid date).
- **Coverage:** both present 633 · receipt-only 167 · issue-only 61 · **both blank 46**.
- **Range:** 2022-03-01 → 2026-06-07. The maximum equals the report/extract date (2026-06-07), which recurs frequently — likely an extract artifact rather than true movement, **flagged but retained**.
- **Aging input:** `Days_Since_Movement = referenceDate − max(receiptDt, issueDt)`. The 46 blank-date rows get `Days_Since_Movement = NA` and aging class `No Movement Date`.

---

## 4. Inventory value quality

| Metric | Value |
|---|---|
| Total inventory value | **₹512,406,406 (≈ ₹51.24 crore)** |
| Items with Value > 0 | 500 |
| Items with Value = 0 (zero stock) | 407 |
| Negative / non-numeric values | 0 |
| Max single-item value | ₹52,823,383 |
| Internal consistency | `Value ≈ Stock × Average Rate` holds; Value = 0 exactly where Stock = 0 ✅ |

**ABC basis caveat.** The Southern Railway Stores ABC policy classifies on **Annual Issue Value** (A > ₹69 L, B1 35–69 L, B2 13–35 L, C < 13 L). Because `AAC` is `--NA--` for 906/907 rows, annual issue value **cannot be computed**. Per approval, ABC will be derived from **inventory `Value (Rs.)` as an indicative proxy** and labelled as such. Resulting distribution:

| ABC (value-based, indicative) | Items |
|---|---|
| A (> ₹69 L) | 12 |
| B1 (₹35–69 L) | 21 |
| B2 (₹13–35 L) | 53 |
| C (< ₹13 L) | 821 |

This is **not** a substitute for consumption-based ABC; supply `AAC`/issue history to upgrade it.

---

## 5. Other quality observations

- **Single depot:** all 907 rows are `SSET/SRM/PER027029-S AND T-SR` → `Depot` is constant; `Division` derived as `Southern Railway`.
- **No `Safety_Item` source column.** It will be **derived** (Criticality S1/S2 ⇒ `Safety_Item = Yes`) and clearly marked as derived, not measured.
- **No `OEM` data** → field emitted as `NA`, not fabricated.
- **Asset-type skew (telecom-heavy depot).** The spec keywords largely do not occur: `RELAY`=0, `POINT MACHINE`=0, `AXLE COUNTER`=0, `KAVACH`=0, `IPS`=0, `EI`=0. Actually present: `CABLE` 129, `OFC` 47, PHONE/TELEPHONE 43, `CARD` 43, `BATTERY` 35, `CONNECTOR` 32, `SIGNAL` 20, `MODULE` 17, CHARGER 9, POWER SUPPLY/SMPS ~12. The spec keyword list **alone** would leave ~840/907 items as `Other`; per approval the classifier adds data-driven categories with word-boundary matching (so `EI`/`IPS`/`OFC` do not false-match inside other words).

---

## 6. Suggested cleanup actions

1. **Loader:** parse via raw OOXML XML (file's stylesheet is corrupt for `openpyxl`/`pandas`).
2. **Split composites:** col 4 → `PL_Code` / Type / Usage; col 7 → receipt / issue; col 5 → stock-flag / category.
3. **Coerce numerics:** `Stock`, `Average_Rate`, `Value` to float (already clean).
4. **Dates:** parse DD-MM-YYYY; null the 46 blank rows; flag the recurring 2026-06-07 extract date.
5. **Drop dead columns:** ignore `Action` (100% empty) and `Category` / Type (constant).
6. **Treat `AAC` as missing** (`--NA--` → null); record that consumption-based ABC is unavailable.
7. **Derive** `Safety_Item`, `Division`, and emit `OEM = NA` (no source) — never fabricated.
8. **Do not de-duplicate** by description; PL-Code is the authoritative key.
9. **Label ABC** outputs as *indicative (value-based)* until issue/AAC data is supplied.
