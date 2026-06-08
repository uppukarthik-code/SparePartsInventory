# STEP 25.5 — Validation Report

**Date:** 2026-06-08 · **Subject:** Inventory value signal discovery (depot-027534 SUMMARY OF STOCK HELD).
**Method:** Deterministic re-scan + SHA-256 backward-compatibility guard. Evidence only.

---

## 1. Constraint compliance

| Constraint | Status | Evidence |
|------------|--------|----------|
| No synthetic costs | ✅ | only observed `Average Rate` / `Value` cells reported |
| No estimation of missing values | ✅ | zero-stock items left at observed (₹0 stock value), not imputed |
| No inference of inventory value | ✅ | unit rate read directly; consistency verified, not assumed |
| No modification of forecasting / LT / SS / ROP / SRRS / enterprise | ✅ | no such module/output touched |
| Backward compatibility | ✅ | 518 existing files, **0 changed** (SHA-256) |
| Traceable to source | ✅ | every figure from SUMMARY cells + STEP25 rop_results |

## 2. Validation checks

| # | Check | Result |
|---|-------|--------|
| 1 | All SUMMARY columns inventoried | ✅ 13 columns |
| 2 | Monetary fields identified | ✅ Average Rate (Rs.), Value (Rs.) |
| 3 | Coverage computed | ✅ unit rate 100%, stock value 45.9% |
| 4 | Internal consistency checked | ✅ Value == Stock×Rate on 99.3% (1,251/1,260) |
| 5 | PL-linkage classified | ✅ Average Rate Directly Usable; Value Partially Usable |
| 6 | ROP/gap linkability validated | ✅ 626/626 ROP PLs have a unit rate |
| 7 | No production ranking emitted | ✅ value-weighting shown as preview only, no output ranking written |
| 8 | Reproducible | ✅ deterministic re-run |
| 9 | Backward compatibility | ✅ 0 changed |

## 3. Outputs (new catalogue CSVs only)
`inventory_value_field_inventory.csv`, `inventory_value_candidates.csv`, `inventory_value_linkage.csv` — all additive; no production planning output created or modified.

## 4. Disclosed caveats
- The ₹3.37B value-weighted gap is **inflated by the issuing-depot context** (027534 holds ~0 of fast-movers — STEP 25 caveat carries forward) and by a few **extreme unit-cost outliers** (e.g. ₹6.83M/unit). Both are flagged in the discovery report; value-ranking must be used alongside service-risk, not alone.
- `Value (Rs.)` is a *current-holding* valuation (45.9%), unsuitable for prioritizing zero-stock shortages — correctly classified Partially Usable.

## 5. Verdict
**STEP 25.5 validation PASSED.** A genuine, internally-sourced inventory-value signal exists — **`Average Rate (Rs.)`, 100% coverage, internally consistent, Directly Usable** and linkable to ROP/reorder gaps. STEP 26 can become **value-aware** via a complementary `Reorder_Gap_Value (₹)` lens **without modifying the cost-free SRRS objective**. Fully read-only, evidence-based, backward compatible.
