# `railways.xlsx` — Discovery Report & Migration Plan

**Generated:** 2026-06-07 (Phase 1 — Discovery, re-run on new workbook)
**Scope:** Read-only discovery. No code generated, no data modified.
**Supersedes (for forecasting/optimization):** `railway_stock_summary.xlsx`

---

## 1. Workbook overview

`raw_data/railways.xlsx` — opens cleanly in `openpyxl`/`pandas` (unlike the older file). **9 sheets:**

| # | Sheet | Data rows | Role |
|---|-------|----------:|------|
| 1 | `Form Responses 1` | 0 | Google-Form artifact — **ignore** |
| 2 | `Stock as on 03.04.2023` | 57 | Older stock + consumption 2019-20 → 2023-24 |
| 3 | **`  Stock as on 31.03.2026`** | **59** | ⭐ **PRIMARY** — consumption 2020-21…2025-26, AAC, EAR, pending, stock, rate |
| 4 | `  Stock as on 15.05.2026` | 40 | Latest snapshot, fewer years (2024-25…2026-27); 2026-27 blank |
| 5 | `% EARAAC as on 03.04.2023` | ~57 | EAR/AAC% + **Safety/Vital flag** (2023-24) |
| 6 | **`  % EARAAC as on 31.03.2026`** | **57** | ⭐ **Safety/Vital flag** + EAR/AAC/consumed/stock (2025-26) |
| 7 | `  % EARAAC as on 15.05.2026` | 57 | Duplicate of sheet 6 (same values) |
| 8 | `EAR Consumptions` | 52 | ⭐ **Division-level** consumption (MAS,TPJ,SA,MDU,PGT,TVC) + EAR 2020-21 |
| 9 | `Sheet20` | 0 | Empty |

> **Header layout:** the Stock and EARAAC sheets use a **2-row banner header** (title in R1, column names spanning R2–R3 with merged cells). The loader must reconstruct headers from R2+R3 and start data at R4 (Stock) / R3 (EARAAC).

---

## 2. PRIMARY sheet — `  Stock as on 31.03.2026` (59 items, 21 columns)

| Col | Reconstructed header | Type | Non-null | Maps to requirement |
|----:|----------------------|------|---------:|---------------------|
| 0 | SL. No. | float | 59 | — |
| 1 | **P.L.No.** | float/str | 59 | **PL Code** |
| 2 | **Description** | str | 60 | **Description** |
| 3 | Total consumption 2020-21 | float | 59 | **Consumption 2020-21** |
| 4 | Total consumption 2022-23 | float | 59 | **Consumption 2022-23** |
| 5 | Total consumption 2023-24 | float | 59 | **Consumption 2023-24** |
| 6 | Total consumption 2024-25 | float | 59 | **Consumption 2024-25** |
| 7 | Total consumption 2025-26 | float | 59 | **Consumption 2025-26** |
| 8 | **AAC** | float | 58 | **AAC** |
| 9–14 | Stock at GSD/PER, GSD/ED, LSD/MDU, DSD/QLN, GSD/GOC, SSD/PTJ | float | 59 | Depot-wise stock |
| 15 | **TOTAL** | int/float | 59 | **Current Stock** |
| 16 | **EAR QTY. 2025-26** | float | 59 | **EAR Qty** |
| 17 | **P.O. qty pending supply** | float/str | 59 | **Pending Supply** |
| 18 | **Rate in Rs.** | float | 59 | **Unit Cost** |
| 19 | DD | float/str | 58 | (demand during lead time?) — ambiguous, hold |
| 20 | UDM STOCK | mixed | 60 | Free-text (e.g. `'50423 Nos '`) — **unreliable**, ignore |

**Sample (row 1):** PL `56509376`, `A.R.A Terminal Block 25mm PBT small`, consumption [11270, 9000, 8400, 12000, 10675], AAC 13500, stock TOTAL 10200, EAR 21500, pending 6000, rate ₹52.42.

> **Note on consumption years:** the requested set (2020-21, 2022-23, 2023-24, 2024-25, 2025-26) is **non-contiguous — 2021-22 is absent** in the source. This is a true gap, not a load error; the demand series has a hole between 2020-21 and 2022-23.

---

## 3. Supporting sheets

**`  % EARAAC as on 31.03.2026`** (57 rows) — join key `P.L.No.`:
- `Safety / Vital` flag distribution: **V (Vital) 15 · S (Safety) 13 · N (Normal) 18 · blank 11**.
  → This is the **real `Safety_Item` source** (the old workbook had none). Proposed rule: `Safety_Item = Yes` when flag ∈ {S, V}.
- Also carries EAR Qty 2025-26, AAC, Consumed 2025-26, Stock, Supplied-% vs EAR, Supplied-% vs AAC.

**`EAR Consumptions`** (52 rows) — **division-level** consumption for 2020-21 across **6 divisions: MAS, TPJ, SA, MDU, PGT, TVC**, plus total and EAR.
- → This is the **real `Division` source** (old workbook was single-depot). Enables division-level demand allocation for AnyLogistix.

**Join consistency** (key = `P.L.No.`):
- `Stock31` 59 items · ∩ `EARAAC31` = **53** · ∩ `EAR Consumptions` = **41**.
- 6 PL codes in Stock31 are missing from EARAAC; some are **composite/dirty** (e.g. `47200054/ 47200250`, `50360693/ 50370110` — two codes in one cell) — needs split/normalise.
- No exact duplicate PL within Stock31.
- PL format: **8-digit** (50) + composite 18-char (9). Differs from the old workbook's 12-digit codes.

---

## 4. New calculations enabled (replacing inventory-value ABC)

**Annual Issue Value = AAC × Unit Cost** — computable for **58/59 items** (was impossible before):
- Total ₹16.14 crore; max single item ₹2.10 crore.

**ABC (Southern Railway policy, on Annual Issue Value, lakh thresholds):**

| Class | Rule | Items |
|---|---|---:|
| A | > ₹69 L | **9** |
| B1 | ₹35–69 L | **4** |
| B2 | ₹13–35 L | **6** |
| C | < ₹13 L | **39** |

> This **replaces** the earlier indicative inventory-value ABC from `railway_stock_summary.xlsx`. It is now policy-correct (consumption-based).

**Demand metrics** (from the 5 annual consumption points per SKU):
- **Consumption trend:** slope / CAGR across 2020-21 → 2025-26.
- **Consumption variability:** CV (σ/μ) of the annual series.
- **Demand intermittency:** ADI (avg demand interval) + CV² → Syntetos-Boylan class.

**Syntetos-Boylan demand-pattern preview (5 annual points):**

| Pattern | Items |
|---|---:|
| Smooth | 30 |
| Intermittent | 7 |
| Erratic | 7 |
| Lumpy | 0 |
| Zero / Dead (no consumption any year) | 14 |

---

## 5. Forecasting-model applicability ⚠

The existing SparePartsInventory / M5-Walmart forecasting architecture (notebook 04) is built for **daily series with ~1,900 observations** and sub-annual seasonality. `railways.xlsx` provides **5 annual points per SKU (with a 2021-22 gap)**. This is a fundamentally different regime — most heavy models **do not transfer**.

| Model | Applicable to railways.xlsx? | Reason |
|---|---|---|
| **AAC / EAR anchor (naive)** | ✅ Primary | Railway already supplies an annual forecast (AAC = Anticipated Annual Consumption; EAR = Estimated Annual Requirement). Use as baseline. |
| **Moving average / CAGR trend** | ✅ Yes | Works on 5 annual points; good for *Smooth* items (30). |
| **Holt (linear trend)** | 🟡 Limited | Usable for trending smooth items, but 5 points is below comfort; treat as secondary. |
| **Croston / SBA / TSB** | 🟡 Classify, don't forecast | Designed for intermittent demand, but need a longer regular-interval series. With 5 annual buckets use them to *characterise* the 14 intermittent/erratic items, not to produce reliable point forecasts. |
| **Prophet / ARIMA / SARIMA** | ❌ No | Require long series + seasonality; 5 annual points → unidentifiable. |
| **LightGBM / ML (M5 style)** | ❌ No | No daily features, no calendar/price panel, far too few rows. |

**Recommended railway forecasting approach:** a lightweight **annual** engine — AAC/EAR baseline, reconciled with CAGR/MA trend, gated by Syntetos-Boylan demand class — **not** the M5 daily ML pipeline. The forecasting *architecture/interfaces* (per-SKU model selection, demand classification, output schema) can be reused; the *models* mostly cannot.

---

## 6. Workbook comparison

| Dimension | `railway_stock_summary.xlsx` | `railways.xlsx` |
|---|---|---|
| Items | 907 (broad depot inventory) | 59 vital S&T items (curated) |
| File health | Corrupt stylesheet (XML-parse only) | Clean (openpyxl OK) |
| Consumption history | ❌ none (AAC 906/907 `--NA--`) | ✅ 5 annual years + division split |
| AAC usable | ❌ no | ✅ 58/59 |
| EAR / Pending supply | ❌ no | ✅ yes |
| Safety flag | ❌ derived only | ✅ real (S/V/N) |
| Division data | ❌ single depot | ✅ 6 divisions |
| ABC basis | Inventory value (indicative) | **Annual Issue Value (policy-correct)** |
| Stock granularity | 1 depot total | 6 depots (PER/ED/MDU/QLN/GOC/PTJ) |
| PL overlap between the two | — | only **7** PL codes in common (largely disjoint scopes) |
| Best for | Broad stock/dead-stock & Power BI breadth | **Forecasting & optimization** |

---

## 7. Recommended data source per consumer

| Consumer | Recommended source | Rationale |
|---|---|---|
| **Forecasting** | ✅ **`railways.xlsx`** (`Stock 31.03.2026` + `EARAAC` + `EAR Consumptions`) | Only workbook with consumption history, AAC, EAR. |
| **Inventory Optimization** | ✅ **`railways.xlsx`** | Needs demand, lead-time proxy (pending supply), unit cost, safety flag, division split. |
| **Power BI** | 🔀 **Both** | `railways.xlsx` for forecast/ABC/criticality KPIs (59 vital items, deep); `railway_stock_summary.xlsx` for breadth (907-item dead-stock/value coverage). Keep both feeds, clearly labelled. |
| **AnyLogistix** | ✅ **`railways.xlsx`** | Division-level demand (6 divisions) + depot-wise stock (6 depots) → real network nodes & flows; the old single-depot file cannot supply this. |

---

## 8. Data-quality flags for `railways.xlsx`

1. **2021-22 consumption missing** → demand series has a structural gap; interpolate or treat as a 5-point irregular series (do **not** assume zero).
2. **Composite PL codes** (`a/ b`) in ~9 rows → split and normalise; decide whether they're one logical item or two.
3. **53/59** items have a Safety/Vital flag; 6 unmatched → default those to `N`/derive, flagged.
4. **`UDM STOCK` (col 20)** is free-text/mixed → ignore for numerics.
5. **`DD` (col 19)** meaning ambiguous → hold pending confirmation (possible "demand during lead time").
6. **14 zero/dead items** (no consumption any year) → exclude from trend models; route to dead-stock reporting.
7. **`Current Stock`**: use `TOTAL` (col 15); cross-check = sum of 6 depot columns.
8. Multiple snapshot sheets → standardise on `31.03.2026` as the modelling baseline; `15.05.2026` only as a freshness overlay (it drops to 3 consumption years).
