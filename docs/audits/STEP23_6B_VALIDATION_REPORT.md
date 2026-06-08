# STEP 23.6B — Validation Report

**Date:** 2026-06-08 · **Subject:** Internal lead-time derivation + planning-universe reconciliation (MAS).
**Method:** Deterministic re-run + SHA-256 backward-compatibility guard.

---

## 1. Validation checklist

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Negative intervals = 0 | ✅ PASS | derivation rejects `delta<0`; 0 admitted; min Median_LT = 0.0 |
| 2 | Lead-time coverage % | ✅ PASS | 702/1,083 = **64.8%** PL; **96.0%** forecast-volume |
| 3 | Forecast-volume coverage % | ✅ PASS | 846,251 / 881,752 = 96.0% |
| 4 | Confidence distribution | ✅ PASS | High 20 · Medium 107 · Low 575 |
| 5 | Outlier analysis | ✅ PASS | global P5/P95 winsor: PO (33,668)d, Reqn (0,618)d; max Median_LT 668d (no multi-year outliers survive) |
| 6 | Universe reconciliation completeness | ✅ PASS | 1,990 union PLs classified; statuses sum to total; Fully_Reconciled=0 quantified |
| 7 | Backward compatibility | ✅ PASS | 508 existing files, **0 changed / 0 added** (excl. 2 new files) |
| 8 | Existing outputs unchanged | ✅ PASS | SHA-256 identical before/after; reproducible on re-run |

**All 8 checks PASS.**

## 2. No-synthesis assurance
Every lead time is the **median of real, chronologically-valid DMTR intervals** (Receipt date − PO/Reqn date). No industry average, no default, no estimate, no imputation. PLs without a dated procurement reference are **absent** from `lead_time_master.csv` (not filled). The `Lead_Time_Months` field of `planning_master_data_audit.csv` remains 0% populated (untouched).

## 3. Backward-compatibility (SHA-256)
```
Existing files fingerprinted (outputs/, excl. 2 new files) : 508
Changed : 0   Added : 0   UNCHANGED : True   Reproducible : True
```

## 4. Reliability detail
- PO→Receipt and Reqn→Receipt admitted **0 negative intervals**.
- Winsorization removed long-tail outliers (pre-winsor max ~2,000+ days → capped at 668/618).
- Confidence by source: PO_Date {High 11, Medium 75, Low 432}; Requisition_Date {High 9, Medium 32, Low 143}. 127 PLs at Medium/High (≥5 observations).

## 5. Universe reconciliation completeness
| Status | PLs | Coverage of 1,990 union |
|--------|----:|------------------------:|
| Demand_Only | 1,031 | 51.8% |
| Inventory_Only | 880 | 44.2% |
| Partial_Match | 67 | 3.4% |
| Criticality_Only | 12 | 0.6% |
| Fully_Reconciled | 0 | 0.0% |
Overlaps: DMTR∩Operational 20 · DMTR∩Criticality 32 · DMTR∩Strategic 27 · all-four 0.

## 6. Verdict
**STEP 23.6B validation PASSED (8/8).** Real internal lead times derived for 64.8% of PLs / 96% of forecast volume with zero negative intervals and full winsorization, plus a complete four-universe reconciliation — all additive, reproducible, and byte-for-byte backward compatible. Readiness re-scored in `STEP23_6B_READINESS_REPORT.md`.
