# STEP 19 — Validation Report

**Date:** 2026-06-08
**Subject:** Strategic Inventory Allocation Framework (zone-shared → BU-allocated)
**Method:** Read-only verification of `strategic_inventory_allocation.csv`, regenerated enterprise outputs, and SHA-256 byte-identity checks on protected layers.

---

## 1. Validation checklist — results

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Strategic stock conservation (Σ all-BU == original) | ✅ PASS | Σ allocated = **313,892.06** == Σ of 6 depot columns |
| 2 | No duplicated stock | ✅ PASS | One row per (PL, depot); each depot counted once |
| 3 | Each depot column allocated exactly once | ✅ PASS | 6 depots → 6 BUs, 1:1 (table §2) |
| 4 | MAS allocation uses PER only | ✅ PASS | `MAS → {GSD/PER}` |
| 5 | SA allocation uses ED only | ✅ PASS | `SA → {GSD/ED}` |
| 6 | MDU allocation uses MDU only | ✅ PASS | `MDU → {LSD/MDU}` |
| 7 | TVC allocation uses QLN only | ✅ PASS | `TVC → {DSD/QLN}` |
| 8 | PTJ allocation follows verified mapping | ✅ PASS | `PGT → {SSD/PTJ}`; TPJ → {GSD/GOC} |
| 9 | Enterprise totals preserved | ✅ PASS | Σ per-BU strategic = **₹85,663,635.52** = published zone |
| 10 | Operational outputs unchanged | ✅ PASS | 46 protected files/BU, **0 changed** (SHA-256) |
| 11 | SRRS formulas unchanged | ✅ PASS | module untouched; outputs byte-identical |
| 12 | Procurement formulas unchanged | ✅ PASS | `railway_procurement_plan.csv` identical across all 6 BUs, unchanged |
| 13 | Forecast formulas unchanged | ✅ PASS | `railway_forecast.csv` identical across all 6 BUs, unchanged |

**All 13 checks PASS.**

---

## 2. Depot-column allocation (each column → exactly one BU)

| Source_Depot_Column | Business_Unit | PLs allocated |
|---------------------|---------------|--------------:|
| GSD/PER | MAS | 41 |
| GSD/GOC | TPJ | 12 |
| DSD/QLN | TVC | 10 |
| LSD/MDU | MDU | 8 |
| GSD/ED | SA | 5 |
| SSD/PTJ | PGT | 2 |
| **Total** | 6 BUs | **78 rows** |

`depot→BU` and `BU→depot` are both strictly 1:1 (verified programmatically). No depot column is shared; no BU draws from two depots.

---

## 3. Stock conservation proof

```
Σ Strategic_Stock (allocation csv)        = 313,892.06 units
Σ of six depot columns (stock sheet)      = 313,892.06 units   ->  EXACT
Per-PL conservation (Σdepots == row TOTAL): 58 / 59 PLs exact
```

### 3.1 Documented exception (1 PL — source data error, not an allocation defect)
PL `50232356/ 50232319` ("Magneto telephone", composite code):

| Depot | PER | ED | MDU | QLN | GOC | PTJ | Σ depots | Workbook TOTAL |
|-------|----:|---:|----:|----:|----:|----:|---------:|---------------:|
| Stock | 241 | 85 | 148 | 173 | 161 | 0 | **808** | **114** |

Allocation uses the **depot columns** (the per-location source of truth, per approved decision): MAS 241, TVC 173, TPJ 161, MDU 148, SA 85. The workbook's `TOTAL` (114) is internally inconsistent — a source data-entry error, surfaced here rather than silently reconciled.

---

## 4. Enterprise totals preserved (de-inflation)

| | Σ strategic across 6 Live units | Inflation factor |
|---|-------------------------------:|-----------------:|
| **Before STEP 19** | ₹513,981,813.12 (= 6 × 85,663,635.52) | **6.000×** |
| **After STEP 19** | ₹85,663,635.52 | **1.000×** |

Per-BU split (sums exactly to the published zone total):

| BU | Strategic (de-inflated, ₹) |
|----|---------------------------:|
| MAS | 82,879,378.63 |
| TPJ | 986,649.15 |
| TVC | 857,752.29 |
| MDU | 793,711.41 |
| SA | 140,460.87 |
| PGT | 5,683.17 |
| **Σ Live** | **85,663,635.52** |

Enterprise `southern_railway_summary.csv` `Strategic_Inventory_Value` = **85,663,635.52** (was 6× inflated). The published page0 KPI value itself is **unchanged** — STEP 19 only splits it, it does not recompute it.

---

## 5. Backward compatibility (protected layers byte-identical)

| BU | Protected files (operational/forecast/SRRS/procurement/policy/exec) | Changed | Removed |
|----|---:|---:|---:|
| MAS | 46 | 0 | 0 |
| SA | 46 | 0 | 0 |
| TPJ | 46 | 0 | 0 |
| MDU | 46 | 0 | 0 |
| PGT | 46 | 0 | 0 |
| TVC | 46 | 0 | 0 |

Method: SHA-256 of every file under `outputs/<BU>/` except `enterprise/` and the new allocation csv, captured before/after STEP 19. **Zero changes.** STEP 19 never executed the operational, forecasting, optimization, SRRS or procurement modules.

- **Power BI pages still load:** the 10 `page*` + 5 `op_*` exports per BU are unchanged (part of the 46 protected files); enterprise-enriched copies regenerated with identical schema.
- **KPIs preserved:** published page0 KPIs unchanged; only enterprise strategic *attribution* changed.
- **Schemas preserved:** no column added/removed to any existing output; the allocation csv is a new file with its own documented schema.
- **Forecast / ROP / procurement / SRRS:** confirmed **identical across all six BUs** (zone-shared) and **identical before/after STEP 19** — proving the formulas were not touched.

---

## 6. Verdict

**STEP 19 validation PASSED (13/13).** Strategic inventory is now Business-Unit allocated with exact stock conservation; enterprise strategic aggregation no longer inflates (6×→1×); all protected analytics remain byte-for-byte identical. One source data-quality anomaly is documented (§3.1) for upstream correction.
