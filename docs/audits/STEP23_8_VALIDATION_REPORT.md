# STEP 23.8 — Validation Report

**Date:** 2026-06-08 · **Subject:** Criticality signal discovery (depot-027534 SUMMARY OF STOCK HELD).
**Method:** Deterministic re-run + SHA-256 backward-compatibility guard. Evidence over assumptions.

---

## 1. Constraint compliance

| Constraint | Status | Evidence |
|------------|--------|----------|
| DO NOT invent criticality | ✅ | only observed col4/col5 values catalogued |
| DO NOT infer S1–S4 without evidence | ✅ | S1–S4 mapping explicitly **rejected** (Safety Item spans S1–S4); only binary Critical/Non-critical asserted, validated |
| No forecasting / lead-time / SS / SRRS / enterprise changes | ✅ | no such module or output touched |
| Backward compatibility | ✅ | 513 existing files, **0 changed** (SHA-256) |
| Conclusions traceable to source | ✅ | every figure derives from SUMMARY OF STOCK HELD cells + the 59-item master |

## 2. Validation checks

| # | Check | Result |
|---|-------|--------|
| 1 | All SUMMARY rows scanned | ✅ 1,260 rows |
| 2 | Field inventory complete | ✅ 13 columns catalogued |
| 3 | Candidate signals identified | ✅ Type, Usage, Stock-class |
| 4 | Coverage computed (PL / forecast-vol / stock-value) | ✅ |
| 5 | Cross-checked vs known criticality | ✅ 32 common PLs; prec 0.74 / rec 0.95 |
| 6 | No synthetic criticality created | ✅ feasibility only |
| 7 | Reproducible | ✅ deterministic re-run identical |
| 8 | Backward compatibility | ✅ SHA-256, 0 changed |

## 3. Signal-strength verdict (evidence-based)

| Signal | Coverage | Validation | Verdict |
|--------|---------:|-----------|---------|
| col4 **Type** → binary Critical/Non-critical | 99.6% | recall 0.95, precision 0.74 (n=32) | **Moderate — usable** |
| col4 Type → precise S1–S4 | 99.6% | Safety Item spans S1(12)/S2(7)/S3(5)/S4(2) | **Not usable** (no clean mapping) |
| col4 Usage (M&P/T&P/Consumable) | 99.6% | not independently validated | candidate refinement only |
| col5 Stock/Non-Stock | 100% | inventory-policy signal, not criticality | not a criticality signal |

## 4. Caveats (disclosed)
- Validation base is **32 common PLs** (the known-criticality universe is only 59 strategic items, 32 in SUMMARY) — results are **indicative, not definitive**; a larger validated sample would firm up precision.
- Precision 0.74 means the binary signal **over-includes** (~26% of "Critical" are actually S3/S4) — operationally **conservative** (over-protect), not under-protective.
- "NA" = "not a Safety/Vital item", a legitimate lower-criticality bucket — not missing data.

## 5. Verdict
**STEP 23.8 validation PASSED.** A genuine, internally-sourced criticality signal exists (col4 Type) covering 99.6% of the demand universe, validated as a **Moderate-strength binary** Critical/Non-critical discriminator (recall 0.95). Precise S1–S4 reconstruction is **not** evidence-supported and was correctly **not** asserted. Fully read-only and backward compatible. Readiness movement and recommendation in `STEP23_8_CRITICALITY_DISCOVERY_REPORT.md` Part E.
