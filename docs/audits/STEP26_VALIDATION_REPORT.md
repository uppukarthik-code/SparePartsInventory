# STEP 26 — Validation Report

**Date:** 2026-06-08 · **Subject:** MAS Division SRRS prioritization engine.
**Method:** Deterministic re-run + SHA-256 backward-compatibility guard.

---

## 1. Validation checklist

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | SRRS mathematics unchanged | ✅ PASS | `SRRS = Criticality_Weight × Service_Factor × Positive_Gap`; `service_factor` imported from `railway_inventory_optimization` (verbatim) |
| 2 | No cost injected into SRRS | ✅ PASS | value kept in a separate column (`Reorder_Gap_Value_Rs`), never in SRRS |
| 3 | No negative SRRS | ✅ PASS | weight>0, SF>0, Positive_Gap≥0 → SRRS≥0 |
| 4 | No duplicate PLs | ✅ PASS | PL_Code unique (626) |
| 5 | SRRS_Rank / Value_Rank unique | ✅ PASS | both ranks unique |
| 6 | Positive_Gap = max(ROP−Stock,0) | ✅ PASS | sourced from STEP25 `rop_results.csv` |
| 7 | Existing outputs unchanged | ✅ PASS | 523 files, **0 changed** (SHA-256) |
| 8 | Reproducible | ✅ PASS | byte-identical on re-run |
| 9 | Traceable to source | ✅ PASS | gap from STEP25, weight from STEP23.8 Type, rate from SUMMARY (STEP25.5) |

**All checks PASS.**

## 2. Backward-compatibility (SHA-256)
```
Existing files fingerprinted (outputs/, excl. 2 new) : 523
Changed : 0   Added : 0   UNCHANGED : True   Reproducible : True
```

## 3. Formula-fidelity assurance
- The objective is the exact Step-15 calibrated SRRS; only the **criticality weight** is supplied via the binary/3-way Type signal (Safety=10/Vital=5/NA=1 = existing S1/S2/S4 values) because the source criticality is the STEP23.8 Type signal, not S1–S4 codes.
- `Service_Factor` values (2.0 / 1.0) are produced by the unmodified `opt.service_factor`.
- Demand-/Lead-Time-factors remain excluded from the objective (no reversion of the STEP14/15 calibration).

## 4. Independence of the value lens
SRRS and `Reorder_Gap_Value_Rs` are computed and ranked **separately** (`SRRS_Rank` ≠ `Value_Rank`); their Top-20 lists overlap on only 6 PLs — confirming service risk and capital exposure are distinct dimensions, as designed.

## 5. Disclosed caveat
`Positive_Gap` inherits the STEP 25 **issuing-depot context** (depot 027534 holds ~0 of fast-movers → inflated shortages). SRRS and gap-value therefore over-state absolute need; they remain valid for **relative prioritisation**, which is their purpose. No values were adjusted.

## 6. Verdict
**STEP 26 validation PASSED.** SRRS prioritization computed for 626 MAS PLs by reusing the exact existing objective (no cost injected), with an independent capital-exposure lens, reproducible and fully backward compatible.
