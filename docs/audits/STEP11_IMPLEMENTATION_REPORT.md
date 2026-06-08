# Step 11 — Dashboard Data-Lineage Correction: Implementation Report

**Date:** 2026-06-07
**Scope:** Data-lineage / normalization-usage / value-aggregation correction only.
**Unchanged (as instructed):** analytical model, forecasting logic, operational-health logic,
budget-optimization logic, business rules. Confirmed by **zero regression drift** (ABC / criticality /
demand-class / confidence / inventory-status distributions identical to baseline).

---

## 1. Files modified

| File | Change |
|---|---|
| `railway/railway_inventory_optimization.py` | Extracted `priority_class_for_position()` (shared thresholds; original class behaviour identical). |
| `railway/railway_data_quality.py` | Computes `Normalized_Procurement_Priority_Class` from the normalized score (same Top-10/20/30/rest thresholds); appends it to `railway_inventory_policy.csv`. |
| `railway/railway_inventory_rationalization.py` | Strategic rows now use `Normalized_Inventory_Value`; added `Source_Universe` (Strategic/Operational). |
| `railway/railway_executive_summary.py` | Added `Strategic_Inventory_Value_Normalized` KPI. |
| `railway/railway_powerbi_export.py` | Rewired pages 0/1/3/5/7/9 to normalized columns; universe-split page0 & page9; recomputed page7 on normalized values; `Source_Universe` tags. |
| `railway/railway_anylogistix_export.py` | `service_risk` now uses `Normalized_Procurement_Priority_Score` + normalized-derived class (Fix B, repo-wide). |
| `railway/railway_dashboard_validation.py` | **New** — validations V1–V5 + report generation. |
| `railway/tests/test_powerbi_exports.py` | Updated for universe-split page0 and forbidden-column guard. |

## 2. Columns rewired (original → normalized)

| Page | Was | Now |
|---|---|---|
| page0 Executive | `Total_Inventory_Value` (original) | `Strategic Inventory Value (Normalized)` + `Operational Inventory Value` (split) |
| page1 Procurement | `Inventory_Investment_Required` | `Normalized_Investment_Required` |
| page1 Procurement | `Procurement_Priority_Score` | `Normalized_Procurement_Priority_Score` |
| page1 Procurement | `Procurement_Priority_Class` (orig-ranked) | recomputed from normalized score |
| page3 Criticality | `Inventory_Value` | `Normalized_Inventory_Value` |
| page5 Rationalization | `Inventory_Value` (mixed) | `Normalized_Inventory_Value` + `Source_Universe` |
| page7 Matrix | `Inventory_Value`, `Inventory_Investment_Required` | `Normalized_Inventory_Value`, `Normalized_Investment_Required` |
| page9 Actions | `Inventory_Value` (mixed total) | `Strategic_Inventory_Value` + `Operational_Inventory_Value` |
| anylogistix service_risk | `Procurement_Priority_Score` | `Normalized_Procurement_Priority_Score` |

## 3. Classifications recomputed

`Procurement_Priority_Class` re-derived from `Normalized_Procurement_Priority_Score` using the
**identical** positional thresholds (Immediate ≤10% / High ≤30% / Medium ≤60% / Low rest). The
original class is preserved in `railway_inventory_policy.csv`; the normalized class
(`Normalized_Procurement_Priority_Class`) is the one surfaced on page1 and in service_risk.

**Effect (V5 — Top-20 rank, before → after):**
| PL_Code | Description | Rank Before | Rank After | Δ |
|---|---|---:|---:|---:|
| 56119033 | Cable 19 C x 1.5 sq.mm | 1 | 14 | −13 |
| 56987122/56110029 | Cable 3 C x 10 sq.mm | 2 | 20 | −18 |

The two per-km cables that previously dominated procurement priority are correctly demoted; no other
item moved >10 positions.

## 4. Strategic vs operational separation (Fix C)

- **page0:** the single "Total Inventory Value" is **removed**; replaced by labelled
  **Strategic Inventory Value (Normalized) = ₹8.57 cr** and **Operational Inventory Value = ₹51.24 cr**,
  each tagged `Universe`.
- **page9:** the mixed-base total (₹1,171 M) is **removed**; value is now split into
  `Strategic_Inventory_Value` and `Operational_Inventory_Value` per action — never combined.
- **page5 / rationalization:** each row carries `Source_Universe`; strategic value is normalized,
  operational value is operational — sums are taken within a universe only.

## 5. Validation results (see STEP11_VALIDATION_REPORT.md)

| # | Validation | Result |
|---|---|---|
| V1 | Executive strategic value == Σ Normalized_Inventory_Value | ✅ ₹85,663,636 = ₹85,663,636 |
| V2 | Procurement page total == Σ Normalized_Investment_Required | ✅ ₹473,115,370 = ₹473,115,370 |
| V2b | Executive "Procurement Required" == page1 total | ✅ ₹473,115,370 = ₹473,115,370 |
| V3 | Criticality matrix == Σ Normalized_Inventory_Value | ✅ ₹85,663,636 = ₹85,663,636 |
| V4 | No original value/score columns on strategic pages | ✅ clean |
| V5 | Top-20 rank comparison generated | ✅ 2 items moved >10 (the cables) |

Plus: **54 pytest tests pass**, schema validation **PASS**, regression drift **none**.

## 6. Remaining risks

1. **Power BI rebind required** — page schemas changed (normalized column names, `Source_Universe`,
   page0 10 KPIs, page9 split). The .pbix must repoint fields. This is mandated by Validation 4, not optional.
2. **Operational values are not "normalized"** — they need no normalization (different item universe,
   no per-km cables), but the page5 column is named `Normalized_Inventory_Value` for schema uniformity;
   operational rows carry their raw (already-correct) value. `Source_Universe` disambiguates.
3. **Locked Safety_Stock dimensional convention** unchanged (out of Step-11 scope) — magnitudes remain
   conservative; treat as ranking, per the Step-9 controls.
4. **page8 non-monotonic Items_Funded** is unchanged (correct optimizer behaviour; a display caveat, not a lineage defect).

## 7. Before / After KPI comparison

| Metric | Before (original) | After (normalized) |
|---|---:|---:|
| Executive headline inventory value | ₹662 M ("Total", 87% artifact) | ₹85.7 M strategic + ₹512.4 M operational (split, labelled) |
| Procurement page Σ investment | ₹6,606 M | **₹473 M** |
| Page0 ↔ Page1 procurement consistency | 14× contradiction | **identical (₹473 M)** |
| Criticality matrix Σ value | ₹662 M | **₹85.7 M** |
| Management-actions value total | ₹1,171 M (mixed bases) | split: Procure ₹77 M strategic; Dispose ₹76 M operational |
| Top service-risk item | Cable 56119033 (₹5.26e10) | Lead-acid cells 50550081 (₹4.64e8) |

---

## Success criteria — status

- ✅ Executive page uses normalized strategic inventory values.
- ✅ Procurement page uses normalized investment requirements.
- ✅ Procurement classes recomputed from normalized scores.
- ✅ Criticality page uses normalized values.
- ✅ Rationalization page no longer mixes value bases (universe-tagged).
- ✅ Management Actions page no longer mixes value bases (strategic/operational split).
- ✅ Strategic and operational inventory clearly separated.
- ✅ All validation tests pass (V1–V5, 54 unit tests, schema, regression).
- ✅ No dashboard consumes original value columns when normalized equivalents exist.

**All success criteria met.**
