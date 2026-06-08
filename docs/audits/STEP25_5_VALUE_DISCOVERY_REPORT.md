# STEP 25.5 — Inventory Value Signal Discovery Report

**Type:** Discovery only. **No synthetic costs, no estimation, no inference, no production/logic changes.**
**Date:** 2026-06-08 · **Source:** `SUMMARY OF STOCK HELD (as on 08-06-2026)` (depot 027534). All findings traceable to source cells.

---

## 1. Inventory-value architecture
```
SUMMARY OF STOCK HELD (depot 027534, 1,260 rows / 1,099 PLs)
 ├─ col11  Average Rate (Rs.)  [UNIT COST]    100% coverage  (₹0.95 – ₹6.83M, median ₹13,457)
 ├─ col12  Value (Rs.)         [STOCK VALUE]  45.9% (in-stock only)  = Stock × Rate
 └─ col8   Stock                              (consistency: Value == Stock×Rate on 99.3% of rows)
                                   │
   STEP25 Reorder_Gap × Average Rate  =  Reorder_Gap_Value (₹)  → complementary STEP26 lens
```

## PART A — Field inventory (13 columns)
All 100% populated except `Action` (empty). Two monetary fields: **`Average Rate (Rs.)`** (numeric, 100%) and **`Value (Rs.)`** (numeric, 100% populated; 45.9% > 0). Full table: `inventory_value_field_inventory.csv`.

## PART B — Value-signal candidates

| Candidate | Coverage | Distinct | Range (₹) | Median (₹) | PL coverage |
|-----------|---------:|---------:|-----------|-----------:|------------:|
| **Average Rate (Rs.)** — unit cost | **100%** | 820 | 0.95 – 6,826,248 | 13,457 | **100%** |
| Value (Rs.) — stock value | 45.9% | 479 | 71 – 26,666,508 | 140,000 | 45.9% |

**Internal consistency:** `Value == Stock × Average Rate` on **99.3%** of rows (1,251/1,260) — confirms `Average Rate` is a genuine per-unit cost and `Value` is its derived stock valuation. Full detail: `inventory_value_candidates.csv`.

## PART C — PL-linkage feasibility

| Field | PL_Code | Current_Stock | ROP | Reorder_Gap | Classification |
|-------|---------|---------------|-----|-------------|----------------|
| **Average Rate (Rs.)** | ✅ 100% | ✅ | ✅ (100% of 626 ROP PLs) | ✅ `Gap × Rate` = ₹ exposure | **Directly Usable** |
| Value (Rs.) stock value | ✅ | ✅ (=Stock×Rate) | Partial | ❌ (0 for zero-stock shortage items) | **Partially Usable** |

`inventory_value_linkage.csv`. The unit rate links cleanly to every ROP PL and, crucially, **works for zero-stock shortage items** (the very items STEP 25 flags) — the stock-value field does not (₹0 when stock = 0).

## PART D — STEP 26 scenarios

| Scenario | Coverage (of 626) | Additional insight | Operational benefit | Risk of misuse |
|----------|------------------:|--------------------|---------------------|----------------|
| 1 — Units only | 100% | service-risk by quantity | current STEP25/26 baseline | none new |
| 2 — Units + value (Rate×Gap) | **100%** | ₹ exposure of the gap | targets capital-at-risk, not just quantity | outlier unit-costs can dominate (e.g. ₹6.83M item) |
| 3 — Units + value + criticality | **100%** | service-risk × ₹ × criticality | full 3-axis prioritization | over-weighting if axes combined naively |

### Value-weighting preview (NOT a production ranking)
Total positive **Reorder_Gap_Value = ₹3,367,367,459**. Top by ₹ exposure:

| PL_Code | Gap-Value (₹) | Gap (units) | Unit Rate (₹) | Description |
|---------|--------------:|------------:|--------------:|-------------|
| 567912550075 | 1,226,505,206 | 8,480 | 144,642 | Fire alarm resettable type |
| 569003030023 | 794,750,402 | 12,010 | 66,174 | Fire alarm fire-survival |
| 567919640033 | 132,497,474 | 19 | 6,826,248 | Alteration in existing EI |
| 560403020365 | 88,135,167 | 824 | 107,016 | Front panel VUR-P |

**Key insight:** value-weighting *materially reorders* priorities. Unit-based ranking favored high-volume cheap **PVC cables**; value-based ranking surfaces expensive low-volume **fire-alarm / electronic-interlocking systems**. The two views answer different questions (quantity-of-service-risk vs capital-at-risk).

## Expected-question answers
1. **Inventory value present?** ✅ Yes — `Average Rate (Rs.)` (unit cost) and `Value (Rs.)` (stock value).
2. **Which fields?** col11 Average Rate; col12 Value.
3. **% PLs covered?** Unit rate **100%**; stock value 45.9%.
4. **Linkable to ROP / reorder gaps?** ✅ Yes — `Reorder_Gap × Average Rate` (Directly Usable, 100%); stock Value only Partially Usable.
5. **Can STEP 26 become value-aware?** ✅ Yes, via the unit-rate-weighted gap.
6. **Is value-based prioritization justified?** ✅ Yes — it reveals ₹3.37B exposure concentrated in a few high-cost systems and reorders priorities meaningfully; **use as complementary, not replacement**.
7. **Highest-confidence value signal?** **`Average Rate (Rs.)`** — 100% coverage, internally consistent (`Value=Stock×Rate`, 99.3%), Directly Usable.
8. **Unit-based or value-aware?** **Both — keep the cost-free SRRS service-risk score unchanged AND add a complementary ₹-exposure lens (`Reorder_Gap_Value`).** A two-axis (service-risk × ₹-at-risk) prioritization, respecting the repo's documented separation of service-risk from procurement cost.

## Recommendation for STEP 26
Run SRRS at binary criticality (as planned) **without modifying the cost-free SRRS objective**, and add an **independent value lens** `Reorder_Gap_Value (₹) = Reorder_Gap × Average Rate` for a two-dimensional priority view. **Caveats to carry:** (a) the issuing-depot context (027534 holds ~0 of fast-movers → inflated shortage/₹), and (b) extreme unit-cost outliers can dominate a pure ₹-ranking — present ₹-exposure alongside, not instead of, service-risk.
