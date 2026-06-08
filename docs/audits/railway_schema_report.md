# Railway Stock Summary — Workbook Schema Report

**Source file:** `raw_data/railway_stock_summary.xlsx`
**Generated:** 2026-06-07 (Phase 1 — Discovery)
**Scope:** Read-only discovery. No data was modified.

---

## 1. Workbook overview

| Property | Value |
|---|---|
| Sheet names | `Sheet1` (single sheet) |
| Data rows | **907** (excluding header) |
| Populated columns | **14** (plus 1 empty leading padding column) |
| Engine note | The file's embedded stylesheet is malformed (`openpyxl` raises `Fill() takes no arguments`; `pandas.read_excel` fails the same way). All values were extracted by **direct OOXML/XML parsing** of `xl/worksheets/sheet1.xml`. The Phase-2 loader must use this raw-XML fallback, **not** `pd.read_excel`. |
| Shared strings | 0 — all text is stored as **inline strings** (`t="inlineStr"`). |

---

## 2. Sheet1 — column profile

Row count: **907** &nbsp;|&nbsp; Column count: **14 populated**

| Col | Header (verbatim) | Inferred type | Empty | Notes |
|----:|-------------------|---------------|------:|-------|
| 1 | `#` | Integer | 0 | Serial row number 1…907 |
| 2 | `Consignee Depot` | String | 0 | **Constant** — single value for all rows |
| 3 | `Ledger/Ledger Folio` | String (composite) | 0 | `ledger code/name / folio code/name` |
| 4 | `PL-Code/Type/Usage` | String (composite) | 0 | `PL-Code / Type / Usage` |
| 5 | `Stock or Non-Stock/Category` | String (composite) | 0 | `Stock\|Non-Stock / Category` |
| 6 | `Brief Description` | String | 0 | Item description |
| 7 | `Last Receipt/Issue Dt.` | String (composite) | 0 | `receiptDt / issueDt`, DD-MM-YYYY |
| 8 | `Stock` | Numeric | 0 | On-hand quantity |
| 9 | `Unit` | String | 0 | Unit of measure |
| 10 | `AAC` | String | 0 | Annual Avg Consumption — 906/907 are `--NA--` |
| 11 | `Threshold Limit` | Numeric | 0 | 906/907 are `0.000` |
| 12 | `Average Rate (Rs.)` | Numeric | 0 | Unit cost in ₹ |
| 13 | `Value (Rs.)` | Numeric | 0 | Inventory value (= Stock × Rate) in ₹ |
| 14 | `Action` | (blank) | 907 | 100% empty |

### Column value distributions

**`Consignee Depot` (col 2)** — 1 distinct value:
- `SSET/SRM/PER027029-S AND T-SR` × 907  *(Perambur S&T, Southern Railway)*

**`PL-Code/Type/Usage` (col 4)** — parsed into 3 parts on `/`:
- PL-Code lengths: 12-digit × 855, 8-digit × 52. **0 duplicate PL-Codes.**
- Type: `NA` (all rows)
- Usage: `Others` × 887, `T&P` × 17, `Consumable` × 3

**`Stock or Non-Stock/Category` (col 5)**:
- Left: `Non- Stock` × 855, `Stock` × 52
- Right (Category): `10-ORDINARY NEW STORES` × 907 (constant)

**`Stock` (col 8)** — numeric:
- Positive 500, **Zero 407**, Negative 0, Non-numeric 0

**`Unit` (col 9)**:
- `Nos.` 712, `MTR` 154, `Set` 12, `Pairs` 12, `Kgs.` 8, `THSND` 4, `HDS` 3, `LTR` 1, `Boxes` 1

**`AAC` (col 10)**:
- `--NA--` × 906, numeric × 1  ⚠ (effectively unusable)

**`Threshold Limit` (col 11)**:
- `0.000` × 906, `1.000` × 1  ⚠

**`Average Rate (Rs.)` (col 12)**:
- Positive 907, Zero 0, Negative 0, Non-numeric 0

**`Value (Rs.)` (col 13)**:
- Positive 500, Zero 407 (matches the 407 zero-stock rows), Negative 0
- Max single item: **₹52,823,383** ; Total: **₹512,406,406 (≈ ₹51.24 crore)**

**`Last Receipt/Issue Dt.` (col 7)** — parsed `receipt / issue`, format DD-MM-YYYY:
- Both blank 46, receipt-only 167, issue-only 61, both present 633
- Date span: **2022-03-01 → 2026-06-07**
- Year frequency (across both date fields): 2022:91, 2023:143, 2024:432, 2025:457, 2026:371

---

## 3. Sample records (first 3 data rows)

**Row 1**
- PL-Code/Type/Usage: `509041036045 / NA / Others`
- Description: `ADOPTER FC 0 DB (0 DB CONNECTOR)`
- Last Receipt/Issue: `/ 30-05-2022`  (receipt blank, issue 30-05-2022)
- Stock: `3.000` | Unit: `Nos.` | AAC: `--NA--` | Threshold: `0.000`
- Rate: `20.00` | Value: `60.00`

**Row 2**
- PL-Code/Type/Usage: `502200280020 / NA / Others`
- Description: `AUTO EXCHANGE INTERFACE EQUIPMENT`
- Last Receipt/Issue: `/`  (both blank)
- Stock: `6.000` | Unit: `Nos.` | Rate: `3093.00` | Value: `18558.00`

**Row 3**
- PL-Code/Type/Usage: `527900082614 / NA / Others`
- Description: `ALPHA Charger for MOTOROLA Walkie Talkie Set`
- Last Receipt/Issue: `/ 11-03-2023`
- Stock: `0.000` | Unit: `Nos.` | Rate: `1300.00` | Value: `0.00`

---

## 4. Likely columns for each required railway field

| Railway field | Identified source | Confidence |
|---|---|---|
| `PL_Code` | col 4, substring before first `/` | High |
| `Description` | col 6 `Brief Description` | High |
| `Current_Stock` | col 8 `Stock` | High |
| `Unit` | col 9 `Unit` | High |
| `Average_Rate` | col 12 `Average Rate (Rs.)` | High |
| `Inventory_Value` | col 13 `Value (Rs.)` | High |
| `Safety_Item` | **none present** | Must be derived |
| `Last_Receipt_Date` | col 7, left of `/` | High (sparse) |
| `Last_Issue_Date` | col 7, right of `/` | High (sparse) |

---

## 5. Detection summary

| Check | Result |
|---|---|
| Duplicate PL-Codes | **0** |
| Duplicate descriptions (across different PL-Codes) | 60 groups / 109 rows — legitimate, not true duplicates |
| Missing descriptions | 0 |
| Invalid stock quantities (negative/non-numeric) | 0 |
| Zero-stock rows | 407 |
| Invalid dates | 0 parse failures; 46 rows have no date at all |
| Negative / non-numeric rate or value | 0 |

---

## 6. Proposed field mapping table

| Railway Field | Source Column |
|---|---|
| PL_Code | `PL-Code/Type/Usage` (col 4) → token[0] |
| Description | `Brief Description` (col 6) |
| Current_Stock | `Stock` (col 8) |
| Unit | `Unit` (col 9) |
| Average_Rate | `Average Rate (Rs.)` (col 12) |
| Inventory_Value | `Value (Rs.)` (col 13) |
| Safety_Item | *(no source — derived from Criticality: S1/S2 ⇒ Yes)* |
| Last_Receipt_Date | `Last Receipt/Issue Dt.` (col 7) → token[0], DD-MM-YYYY |
| Last_Issue_Date | `Last Receipt/Issue Dt.` (col 7) → token[1], DD-MM-YYYY |

**Derived / supplementary fields**

| Field | Source |
|---|---|
| Depot | `Consignee Depot` (col 2) — constant `SSET/SRM/PER` |
| Division | Derived constant: `Southern Railway` |
| OEM | **Not present in source** — left as `NA` (not fabricated) |
| Asset_Type | Derived from `Description` keywords |
| Criticality | Derived from `Asset_Type` (+ Safety promotion) |
| ABC_Class | Derived from `Value (Rs.)` (indicative; see data-quality report) |
| Days_Since_Movement | `2026-06-07` − latest(receipt, issue) |
| Inventory_Aging_Class | Bucketed `Days_Since_Movement` |
