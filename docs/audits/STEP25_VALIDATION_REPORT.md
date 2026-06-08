# STEP 25 — Validation Report

**Date:** 2026-06-08 · **Subject:** MAS Division ROP + reorder-gap analysis.
**Method:** Deterministic re-run + SHA-256 backward-compatibility guard.

---

## 1. Validation checklist

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | No negative ROP | ✅ PASS | min ROP = 0.0 (DDLT ≥ 0, SS ≥ 0) |
| 2 | No duplicate PLs | ✅ PASS | PL_Code unique across 626 rows |
| 3 | Safety stock identical to STEP24 | ✅ PASS | every Safety_Stock matches `safety_stock_results.csv` (read verbatim) |
| 4 | Current stock sourced only from depot 027534 | ✅ PASS | SUMMARY OF STOCK HELD — `SSE027534` on 100% of rows; no 027029 |
| 5 | No synthetic stock introduced | ✅ PASS | stock = SUMMARY col8 only; PLs absent → `No_Stock_Data`, not fabricated |
| 6 | No synthetic lead times introduced | ✅ PASS | LT carried from `lead_time_master.csv` via STEP24 |
| 7 | Forecast outputs unchanged | ✅ PASS | within unchanged 518-file set |
| 8 | Safety-stock outputs unchanged | ✅ PASS | within unchanged set |
| 9 | Enterprise outputs unchanged | ✅ PASS | within unchanged set |
| 10 | Procurement outputs unchanged | ✅ PASS | within unchanged set |
| 11 | SRRS outputs unchanged | ✅ PASS | within unchanged set |

**All 11 checks PASS.**

## 2. Backward-compatibility (SHA-256)
```
Existing files fingerprinted (outputs/, excl. 2 new files) : 518
Changed : 0   Added : 0   UNCHANGED : True   Reproducible : True
```

## 3. Source-traceability assurance
- **ROP** = `Forecast_Annual × LT_months/12 + Safety_Stock` — repo formula reused verbatim.
- **Safety stock** identical to STEP 24 (assertion passed for all 626).
- **Current stock** exclusively from depot-027534 SUMMARY (No_Stock_Data flagged where absent — 0 such here).
- No synthetic demand / lead time / stock / criticality.

## 4. Coverage & status (honest)
| | Value |
|---|------:|
| PLs with ROP | 626 (= STEP24 SS set) |
| Forecast-volume coverage | 96.0% |
| Critical / Non-Critical | 360 / 266 |
| Critical Shortage | 465 |
| Shortage | 45 |
| Healthy | 43 |
| Excess | 60 |
| No_Demand | 13 |
| No_Stock_Data | 0 |

Total ROP 601,481 units; total positive reorder gap 502,668 units.

## 5. Disclosed caveat
The high Critical-Shortage count (465/626) reflects that depot **027534 is an issuing (high-throughput, low-holding) depot** — forecast-based ROP exceeds on-hand for fast-moving cables held near zero. The computation is correct; interpretation requires the depot-role context (documented in the impact analysis). No values were adjusted to mask this.

## 6. Verdict
**STEP 25 validation PASSED (11/11).** ROP and reorder gaps computed for 626 MAS PLs (96% of forecast volume) by reusing the existing ROP formula, with safety stock identical to STEP 24, current stock exclusively from depot 027534, zero synthetic inputs, and full byte-for-byte backward compatibility.
