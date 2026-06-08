# STEP 23.8 — Criticality Signal Discovery: Implementation Report

**Type:** Discovery & validation only. **No forecasting / safety-stock / ROP / SRRS / enterprise-output changes. No synthetic criticality. No S-code inference beyond validated evidence.**
**Date:** 2026-06-08 · **Scope:** MAS.

---

## 1. Objective
Determine empirically whether internal criticality can be reconstructed from `SUMMARY OF STOCK HELD` without external systems — the sole remaining planning blocker after STEP 23.7.

## 2. Method (read-only audit)
`_step23_8_audit.py` re-reads `SUMMARY OF STOCK HELD` via the raw-XML reader and:
1. inventories all 13 columns (datatype, uniques, nulls, coverage);
2. decomposes `PL-Code/Type/Usage` into **Type** (Safety/Vital/NA) + **Usage**, and `Stock or Non-Stock/Category` into **Stock-class** — measuring PL / forecast-volume / stock-value coverage;
3. validates the Type signal against the 59 known S1–S4 strategic items (precision/recall/FP/FN).
Writes 3 catalogue CSVs; modifies nothing existing (SHA-256 verified, 0 changed).

## 3. Key result
The `Type` token is a **genuine native railway criticality signal** (Safety Item / Vital Item / NA), present on **99.6% of the demand universe**, concentrated on high-volume items (Safety+Vital = 75.7% of forecast volume). Validation vs known criticality: **recall 0.95, precision 0.74 (Moderate)** — a strong **binary** Critical/Non-critical discriminator; a precise S1–S4 mapping is **not** supported (Safety Item spans S1–S4).

## 4. Outputs (new, `outputs/MAS/history/`)
| File | Rows | Purpose |
|------|-----:|---------|
| `criticality_field_inventory.csv` | 13 | per-column datatype/uniques/nulls/coverage |
| `criticality_signal_candidates.csv` | per Type/Usage/Stock-class value | distribution + PL / forecast-vol / stock-value coverage |
| `criticality_signal_validation.csv` | 1 | Type-signal precision/recall/strength vs 59 known items |

## 5. Decisions applied (agreed)
- **Signal scope:** Type (primary) + Usage + Stock-class (secondary).
- **S-code crosswalk:** evidence-gated — binary Critical/Non-critical is supported; precise S1–S4 is **not** asserted (insufficient evidence).

## 6. Outcome
Criticality is reconstructable internally as a **binary Critical/Non-critical** signal at 99.6% coverage (Moderate confidence). This unblocks an **operational** (not yet S1–S4-granular) STEP 26 SRRS and refines STEP 24/25 service levels. Full evidence in `STEP23_8_CRITICALITY_DISCOVERY_REPORT.md`.

## 7. Files
| Path | Action |
|------|--------|
| `railway/outputs/MAS/history/criticality_{field_inventory,signal_candidates,signal_validation}.csv` | new |
| `_step23_8_audit.py` | one-off discovery driver, retained |
| all existing outputs (513 files) | **untouched (SHA-256 verified)** |
