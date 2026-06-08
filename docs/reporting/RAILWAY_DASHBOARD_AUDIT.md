# Railway Spare-Parts Analytics — Dashboard Audit (Critical Review)

**Auditor roles:** railway inventory domain · supply-chain analytics · Power BI architect · data-quality auditor
**Date:** 2026-06-07 · **Stakes:** real inventory decisions over crores of value.
**Verdict up front:** ⛔ **NOT READY for crore-level decisions as-is.** Three of eight dashboards
carry **mathematically wrong headline figures** caused by one root defect (below). The
operational and forecast pages are sound; the executive, procurement, criticality, rationalization
and management-action pages are not safe to present until fixed.

---

## ROOT DEFECT (drives most findings)

**The Data-Quality normalization layer was built but NOT propagated to the dashboards.**
`railway_data_quality.csv` produced `Normalized_*` values precisely to remove the per-km cable
inflation, but pages 0, 1, 7 and 9 still consume the **original** inflated columns.

Evidence (from the actual CSVs):
- **page0 "Total Inventory Value" = ₹662,075,255 is 87.1% a data artifact.** Normalized value =
  ₹85,663,636. A **single** cable SKU (3C×10) is **75% of the headline**.
- **page1 procurement `SUM(Inventory_Investment_Required)` = ₹6,606,343,723**, of which the
  **top item alone is 79.6%**. Any bar/total on this page is dominated by 2 data-error rows.
- **Internal contradiction:** page0 "Procurement Required Value" = **₹47.3 cr (normalized)** while
  its own drill-down page1 sums to **₹660.6 cr (original)** — a **14× mismatch for the same metric.**

Until normalized columns feed these pages, **every rupee figure shown to DRM/PCSTE is wrong.**

---

## A. Data Model Issues

| Issue | Status | Evidence / Impact |
|---|---|---|
| **Double counting across value bases** | 🔴 Critical | page5/page9 `SUM(Inventory_Value)` = **₹1,171 M** = strategic-master value (59 items, basis A) **+** operational value (907 items, basis B) summed together. That total is **neither portfolio** and is meaningless. |
| **Cross-domain denominator mixing** | 🔴 Critical | page0 places strategic "Total Inventory Value" (₹662 M, 59 items) beside operational "Dead Stock Value" (₹76 M, 907 items). A viewer computing dead% = 76/662 = 11.5% is **wrong**; true operational dead% = 14.89% of ₹512 M. No universe label on any card. |
| **Incorrect SUM vs COUNT / inflated SUM** | 🔴 Critical | page1/page7 SUM use original investment → 1000× inflation from 2 SKUs. |
| **Inconsistent normalization** | 🔴 Critical | page0 Procurement Required = normalized; page1 = original. Same concept, different basis, same report. |
| **Missing relationships** | 🟠 High | No shared `dim_sku`; `Description` denormalized across 5+ tables; Power BI slicers cannot cross-filter pages on one PL_Code key. |
| **Null handling** | 🟡 Medium | `Forecast_to_Stock_Ratio = inf` for zero-stock items (in forecast.csv) is not numeric-safe for BI; 46 "Unknown" aging handled correctly (good). |
| **KPI definition errors** | 🟠 High | "Total Inventory Value" is undefined as to *which* universe (strategic 59? operational 907? both?). Currently the inflated strategic 59. "Procurement Required Value" basis differs from its drill-down. |
| **Data lineage** | 🟡 Medium | page0 silently blends 3 sources (strategic+operational+forecast) with no `Source_Pipeline` shown; lineage exists in `data_lineage_report.csv` but isn't surfaced on the canvas. |

---

## B & E. Dashboard-by-Dashboard Review (with management lens)

### 1. Executive Dashboard (page0) — **most dangerous page**
- **Meaningful?** KPIs are relevant *concepts*; values are wrong/mixed.
- **Misleading/incorrect?** Yes — Total Inventory Value 87% artifact; cross-domain cards invite false ratios; Procurement Required contradicts page1.
- **Answers:** "How big is the portfolio / how much risk / how much to buy" — **but with wrong numbers.**
- **Unanswered:** which universe each KPI belongs to; how much of the headline is the 2 cable errors.
- **Strengths:** right *set* of executive concepts; concentration & turn-risk are good ideas.
- **Weaknesses:** inflated, inconsistent, cross-domain, two non-actionable cards (Data Quality Impact ₹613 cr; Annual Issue Value ₹161 cr).
- **Missing:** normalized headline; strategic-vs-operational split; "stock-out imminent" count.
- **Fix:** use normalized values; split into a Strategic band and an Operational band; drop/relabel meta-cards.

### 2. Procurement Dashboard (page1)
- **Misleading/incorrect?** Yes — `Inventory_Investment_Required` and `Procurement_Priority_Score` are original (inflated). A bar of investment is 79.6% one SKU.
- **Answers:** "what to buy first" — the *priority ranking order* is largely correct, but the **magnitudes are wrong.**
- **Missing:** days-of-cover / stockout date; expected PO arrival (Pending_Supply exists, unused as ETA).
- **Strengths:** ROP/gap/priority structure is exactly right for procurement.
- **Weaknesses:** non-normalized values; no lead-time-to-stockout.
- **Fix:** swap to `Normalized_Investment_Required` / `Normalized_Procurement_Priority_Score`.

### 3. Forecast Dashboard (page2) — **trustworthy**
- Clean (no inflated fields). Answers demand-class, confidence, model recommendation, forecast vs AAC/EAR.
- **Weakness:** MAPE is unreliable on single-point annual backtest (document on canvas); "High confidence 37%" needs context.
- **Missing:** consumption trend per SKU; forecast-vs-actual track record.

### 4. Criticality Dashboard (page3)
- `Inventory_Value` is strategic original → S1/C cells inflated by cables.
- **Answers:** S1–S4 exposure; ABC×criticality. **Weakness:** inflated value; **Missing:** service-level achieved vs target by criticality.

### 5. Operational Health Dashboard (page4 / op_*) — **best page**
- Operational values are **clean** (different item set, no per-km cables). Aging bug fixed (Unknown=46 surfaced).
- **Answers:** dead/slow/active, aging, value bands, Pareto-ABC — all correct.
- **Missing:** disposal value-recovery estimate; turn-rate trend over time.

### 6. Rationalization Dashboard (page5)
- **Incorrect?** `SUM(Inventory_Value)` mixes strategic+operational bases (₹1,171 M is not a real total).
- **Answers:** procure/retain/monitor/rationalize/dispose split — the **counts are valid**, the **summed value is not.**
- **Fix:** never total value across the mixed register; show counts, and value **within** each source separately.

### 7. Budget Scenario Dashboard (page8)
- **Uses normalized values — correct basis (good).** But `Items_Funded` = 6, 6, 8, 6 → **non-monotonic**: ₹50 L and ₹1 cr fund the *same 6* (identical bars), and ₹5 cr funds *fewer* than ₹2 cr (6 < 8). To an executive this reads as broken even though coverage rises (1.31→13.96%).
- **Answers:** "what does ₹X buy" by criticality coverage. **Weakness:** item-count is the wrong primary visual; **Missing:** which high-value items are *unfundable* at each budget.
- **Fix:** lead with criticality-coverage %; annotate why count is non-monotonic; add unfunded-high-value callout.

### 8. Management Actions Dashboard (page9)
- **Incorrect?** `Inventory_Value` per action mixes bases (Procure = strategic incl inflated cables; Dispose/Rationalize = operational). Summing/pie-ing across actions is invalid.
- **Answers:** action counts + priority — counts valid. **Weakness:** value column not comparable across rows; **Missing:** ₹ value freed by disposal vs ₹ capital needed for procurement on the same comparable basis.

---

## C. Railway Inventory Domain — Decision Coverage

| Decision question | Covered? | Caveat |
|---|---|---|
| What should be procured? | ✅ page1 | values inflated (ranking ok) |
| What should be disposed? | ✅ page5 / op_dead_stock | clean (operational) |
| What should be rationalized? | ✅ page5 | counts clean; value mixed |
| What is dead stock? | ✅ operational | clean |
| What is slow-moving? | ✅ operational | clean |
| Max-risk inventory? | 🟡 page1 priority | inflated magnitudes |
| Max-capital inventory? | 🔴 page0 concentration / top-value | dominated by 2 data-error cables |
| Budget required? | 🟡 page8 | correct basis but confusing count |
| Management actions? | ✅ page9 | value column not comparable |

**Missing operational decision support (material):**
1. **"Stock-out imminent" alert** = items where `Current_Stock + Pending_Supply < Forecast × Lead_Time/12` → *when* will we run dry. This is the single most valuable missing view for an S&T depot.
2. **Service level achieved vs target** (back-calculated).
3. **Expected PO arrival** from Pending_Supply (it's loaded but never surfaced as ETA).
4. **Division-level view** (currently Equal_Split — no real division insight).
5. **Strategic-item aging** (only operational items are aged today).

---

## D. Specific Validation-Rule Flags

| Rule | Flagged where |
|---|---|
| **Every bar identical** | page8 — ₹50 L and ₹1 cr both fund **6** items (identical bars). |
| **Counts non-monotonic / look wrong** | page8 — Items_Funded 6,6,8,6 (5 cr < 2 cr). |
| **Inventory value duplicated across categories** | page5 & page9 — value summed across **mixed strategic+operational bases** (₹1,171 M phantom total). |
| **Inappropriate pie** | Any value pie on page5/page9 (mixed bases) or page7 (inflated) is invalid; ABC/criticality **count** pies are tolerable but bars are better. |
| **Coverage / ratio mislabel** | `Inventory_Coverage_Ratio` is **months-of-cover (can exceed 1.0 / "100%")**, not a share — if any visual labels it "%" it is wrong (Overstocked/Excess bands legitimately exceed 100%). |
| **Counts shown as %** | risk on ABC/criticality cards — ensure count vs % is explicit. |
| **KPI cards not actionable** | page0 — "Data Quality Impact ₹613 cr" and "Annual Issue Value ₹161 cr" are meta/context, not decisions. |
| **Coverage > 100%** | page8 coverage values are all < 100% (OK); but the coverage-ratio metric elsewhere can exceed it — guard the label. |

---

## F. Scores (be critical — 0–10)

| Dashboard | Business | Data-Quality Conf. | Executive | Technical Correctness |
|---|---:|---:|---:|---:|
| 1 Executive | 4 | **2** | 3 | **2** |
| 2 Procurement | 6 | 3 | 5 | 3 |
| 3 Forecast | 7 | 7 | 6 | 8 |
| 4 Criticality | 6 | 4 | 6 | 5 |
| 5 Operational Health | 8 | 8 | 7 | 8 |
| 6 Rationalization | 6 | 3 | 6 | 3 |
| 7 Budget Scenario | 6 | 6 | 5 | 5 |
| 8 Management Actions | 5 | 3 | 5 | 3 |
| **Average** | **6.0** | **4.5** | **5.4** | **4.6** |

Data-quality confidence (4.5) and technical correctness (4.6) are the failing dimensions — both
trace to the un-propagated normalization and cross-domain mixing.

---

### Top 10 Fixes BEFORE deployment (correctness, ranked by decision impact)
1. **Propagate `Normalized_*` to page0/1/7/9.** Replace original investment/value/priority with normalized. (Removes 87% headline inflation.)
2. **Make page0 "Total Inventory Value" normalized AND split** into a labelled *Strategic* (₹8.6 cr) and *Operational* (₹51.2 cr) band — never one ambiguous number.
3. **Reconcile page0 ↔ page1** to one normalized procurement basis (kills the 14× contradiction).
4. **Never sum `Inventory_Value` across the mixed rationalization register** (page5/page9). Report counts across, value *within* each source.
5. **Tag every KPI with its universe / `Source_Pipeline`** and disable any visual that ratios across strategic and operational denominators.
6. **page8:** lead with criticality-coverage %, annotate non-monotonic item count, add an "unfundable high-value" list.
7. **Cap/flag `inf`** in `Forecast_to_Stock_Ratio`; relabel `Inventory_Coverage_Ratio` as *months-of-cover*, not %.
8. **Add a shared `dim_sku`** (PL_Code key) so pages cross-filter; drop redundant `Description` copies.
9. **Replace mixed-base value pies with bars**; remove value pies on page5/9/7.
10. **Add a data-quality banner** ("2 SKUs unit-normalized; ₹576 M of per-km inflation excluded from all values").

### Top 10 Future Enhancements (decision value)
1. **Stock-out-imminent alert** (stock + pending vs forecast×LT) — days-to-dry per SKU.
2. **Service-level achieved vs target** by ABC/criticality.
3. **Pending-supply → expected-arrival ETA** timeline.
4. **Division-level demand** (replace Equal_Split with real consumption %).
5. **Consumption trend sparkline** per SKU (5-year).
6. **Strategic-item aging** parallel to operational.
7. **Live what-if budget slider** (re-solve knapsack on the fly).
8. **Drill-through Division → Depot → SKU.**
9. **Disposal value-recovery estimate** (scrap/resale) for the 190 dead items.
10. **Reliability/shelf-life attributes** for batteries, relays, point machines.

---

## Overall Readiness Assessment

**NOT READY** for crore-level decisions in current form — driven by one fixable root defect
(normalization not propagated) plus cross-domain value mixing. This is **not** a modeling failure:
the corrected values already exist in `railway_data_quality.csv`; the dashboards simply point at the
wrong columns.

- **After Fixes 1–5** (≈ column swaps + universe labels, low effort, high impact) the executive,
  procurement, criticality and action pages become **conditionally deployable** under the Step-9
  human-review controls.
- **Most trustworthy today:** Operational Health (8/8/7/8) and Forecast (7/7/6/8) — safe to show now.
- **Do not show today:** Executive (page0) and Procurement value figures — they will mislead DRM/PCSTE
  by a factor of 10–100× and contradict each other.

**Bottom line:** the analytical *design* is sound and domain-appropriate; the *wiring* leaks a known
data error into the headlines. Fix the five correctness items, label the two universes, and this
becomes a defensible decision-support tool for a Southern Railway S&T depot.
