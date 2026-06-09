# TPJ READINESS REPORT

**Date:** 2026-06-09
**Status:** **LIVE — TPJ executes end-to-end on its native data.**

---

## 1. Verdict

TPJ (Tiruchirappalli Division, S&T) is now a **first-class division**. It runs the
full pipeline from its **native inputs** with no schema mapping or transformation
layer — confirmed by automated tests and an end-to-end validation run.

| Capability | Source | Result |
|---|---|---|
| Operational inventory | `raw_data/Railway_Operations/TPJ/SUMMARY OF STOCK HELD*.xlsx` | 1,355 rows, **Rs 20.90 Cr** stock value, 787 zero-stock items |
| Demand history (STEP21A) | `raw_data/Railway_Operations/TPJ/DMTR_*.xlsx` (×54) | 16,390 transactions → 841 PLs → 31,289 monthly rows |
| Inventory policy | strategic (railways.xlsx) + TPJ operational | `railway_inventory_policy.csv`: 59 rows, 50 procurement-required |

---

## 2. What STEP37 Enabled for TPJ

1. **Registered** in the planning config (`divisions.DIVISIONS`) alongside the other 5 live divisions, with glob-based SUMMARY resolution (no date-stamped filename to maintain).
2. **Operational source of truth** = TPJ's own `SUMMARY OF STOCK HELD` snapshot (read at native columns), feeding aging / dead-stock / slow-moving / valuation analytics with **real TPJ stock** (1,355 depot rows) instead of a stale clone.
3. **Native demand history** reconstructed from TPJ's 54 DMTR registers via the runtime division switch `gcfg.use_division("TPJ")` — the STEP20-28 planning modules required **no code change** (they were already parameterized through `gcfg`).
4. **End-to-end run** produces TPJ's own output set (`outputs/TPJ/…`) including its `railway_inventory_policy.csv` and a TPJ-specific operational view.

---

## 3. Honest Scope Boundary

- TPJ's `railway_inventory_policy.csv` is **strategic-driven** (the 59-item zone universe from `railways.xlsx`, shared across divisions). It is **not yet differentiated** by TPJ's deep-planning signals (division-specific SRRS / safety-stock / ROP feeding the enterprise allocation). That connection is **STEP38 (enterprise differentiation)** — **out of scope** here and intentionally not implemented.
- What is genuinely TPJ-specific today: the **operational universe** (1,355 real rows, Rs 20.90 Cr) and the **reconstructed demand history** (from native DMTR). The deep STEP24-26 chain is runnable for TPJ on demand via `use_division("TPJ")` (TPJ and MAS are the only divisions with DMTR data).

---

## 4. Division Data Availability (for future onboarding)

| Division | DMTR (demand) | SUMMARY (operational) | Deep planning runnable? |
|---|---|---|---|
| MAS | 54 | ✅ | Yes |
| **TPJ** | **54** | **✅** | **Yes** |
| SA | 0 | ✅ | Operational only (no DMTR) |
| MDU | 0 | ✅ | Operational only |
| PGT | 0 | ✅ | Operational only |
| TVC | 0 | ✅ | Operational only |

SA/MDU/PGT/TVC are operationally onboarded (SUMMARY present) but need **DMTR registers** before their STEP21A-26 deep planning can run.

---

## 5. Guarantees Preserved

- **661 pass / 0 fail / 1 skip** (647 originals green + 14 new STEP37 tests).
- **STEP36 golden baseline**: 537 pinned outputs byte-unchanged; `manifest integrity OK`.
- **STEP35 enterprise allocation**: tests green; no behavioural change.
- Legacy `railway_stock_summary.xlsx` and `stock_history.xlsx` fully retired.

---

## 6. Recommended Next Step

**STEP38 — Enterprise differentiation:** wire each division's deep-planning outputs
(STEP24-26 SRRS / safety-stock / ROP) into the policy that STEP35 consumes, so the
enterprise capital allocation stops pooling identical strategic clones and reflects
each division's true risk profile. Begin with TPJ (the only non-MAS division with
full DMTR depth).
