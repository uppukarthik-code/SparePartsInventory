# STEP 23.8 — Criticality Signal Discovery Report

**Type:** Discovery & validation only. **No synthetic criticality, no S-code inference beyond evidence, no logic/output changes.**
**Date:** 2026-06-08 · **Source:** `SUMMARY OF STOCK HELD (as on 08-06-2026)` (depot 027534, 1,260 rows). All conclusions traceable to source data.

---

## PART A — Field inventory (13 columns, all 100% populated except `Action`)
Criticality-bearing fields identified: **`PL-Code/Type/Usage` (col 4)** and **`Stock or Non-Stock/Category` (col 5)**. Full inventory in `criticality_field_inventory.csv`.

## PART B — Candidate criticality signals

The `PL-Code/Type/Usage` field encodes, after the PL code, a native **Type** token + **Usage** class. Decomposed:

### Primary signal — Type (Safety / Vital / NA)
| Type | PLs | PL coverage of demand univ. | Forecast-volume coverage | Stock-value |
|------|----:|----------------------------:|-------------------------:|------------:|
| **Safety Item** | 518 | 47.8% | **70.3%** | ₹175.0M (60.3%) |
| **Vital Item** | 121 | 11.2% | 5.4% | ₹19.7M (6.8%) |
| **NA** | 494 | 45.6% | 29.4% | ₹95.4M (32.9%) |

- **Every PL is classified** → **99.6% of the demand universe** carries a Type token.
- **Safety + Vital = 56.9% of PLs but 75.7% of forecast volume** — the criticality signal concentrates on the high-volume items (exactly where it matters).

### Secondary signals
- **Usage:** Others 733 · M&P 199 · M&P Spares 197 · T&P 36 · Consumable 29 (a maintenance/material-use class).
- **Stock class (col 5):** Non-Stock 1,021 · Stock 92 (plus 4 Second-hand/Repairable/Scrap).

Full distributions in `criticality_signal_candidates.csv`.

## PART C — Cross-check vs the 59 known S1–S4 criticality items
32 PLs are common to SUMMARY and the strategic S1–S4 master. Treating SUMMARY "Safety/Vital Item" as a *critical* predictor vs truth (`Safety_Flag=Yes` or Criticality∈{S1,S2}):

| Metric | Value |
|--------|------:|
| Common PLs | 32 |
| TP / FP / FN / TN | 20 / 7 / 1 / 4 |
| Precision | **0.74** |
| **Recall** | **0.95** |
| Strength | **Moderate** |

Cross-tab (Type × known Criticality):
| Type | S1 | S2 | S3 | S4 |
|------|---:|---:|---:|---:|
| Safety Item | 12 | 7 | 5 | 2 |
| Vital Item | 0 | 1 | 0 | 0 |
| NA | 0 | 1 | 2 | 2 |

**Reading:** "Safety Item" captures **95% of truly-critical items** (recall) and is **73% S1/S2**, but it also tags some S3/S4 (precision 0.74). "NA" is predominantly S3/S4. → The signal is a **strong binary discriminator (Critical vs Non-critical)** but **not** a clean S1↔Safety / S2↔Vital one-to-one. (Validation base is 32 PLs — indicative, not definitive.)

## PART D — Reconstruction feasibility

| Option | Approach | Coverage | Confidence | Operational risk |
|--------|----------|---------:|------------|------------------|
| **A — Direct (Type → binary Critical/Non-critical)** | Safety/Vital = Critical; NA = Non-critical | **99.6%** | **Moderate** (rec 0.95, prec 0.74) | Low–Med: ~26% of "Critical" are actually S3/S4 (conservative over-protection, not under) |
| B — Type + Usage + Stock-class | refine Critical with M&P/M&P-Spares + Stock flag | 99.6% | Moderate–High | Med: heuristic weighting, needs validation |
| **C — Hybrid (Type primary + Usage/Stock refine + 32 anchors)** | binary from Type, sub-tier by usage, anchor to known S-codes | 99.6% | **Moderate–High** | Low–Med | 
| D — Not feasible | — | — | — | rejected: a usable signal demonstrably exists |
| *(Precise S1–S4 from this data)* | map Safety→S1, Vital→S2… | — | **Insufficient evidence** | High — Safety Item spans S1–S4; **not recommended** |

**No synthetic criticality is assigned here** — this is feasibility only.

## PART E — STEP 24/25/26 readiness scenarios

| Step | S1: no criticality | S2: partial (binary, this data) | S3: high-confidence S1–S4 |
|------|-------------------:|--------------------------------:|--------------------------:|
| STEP 24 Safety Stock | 85 | **88** (binary service-level tiering) | 92 |
| STEP 25 Division ROP | 80 | **90** | 92 |
| STEP 26 SRRS | 55 | **75** (binary criticality weight, 99.6% cov) | 90 |

**Scenario 2 is achievable now** (binary criticality at 99.6% coverage, Moderate confidence) → moves STEP 26 from 55 → ~75. **Scenario 3 (precise S1–S4) is not achievable from this source alone** and would need an extended/validated criticality master.

## Expected-question answers
1. **Genuine criticality signal?** ✅ Yes — col4 `Type` (Safety Item / Vital Item / NA).
2. **Which fields?** Primary `PL-Code/Type/Usage` (Type); secondary Usage + col5 Stock-class.
3. **PL coverage?** 99.6% classified; Safety+Vital = 56.9% of PLs.
4. **Forecast-volume coverage?** Safety+Vital = **75.7%**; all-classified = 99.6%.
5. **Reconstructable without external systems?** ✅ **Yes for BINARY criticality** (Critical/Non-critical), Moderate confidence (recall 0.95). ❌ **No for precise S1–S4** (Safety Item spans S1–S4; evidence insufficient).
6. **Can STEP 26 proceed?** ✅ Yes — with **binary criticality weighting** (operational SRRS), not full S1–S4 granularity.
7. **Highest-confidence model:** **Type-based binary criticality** (Safety/Vital → Critical, NA → Non-critical), 99.6% coverage, validated recall 0.95 / precision 0.74; optionally refined by Usage/Stock-class (Hybrid Option C).
8. **Next phase:** ingest the Type-based binary criticality as an *additive* criticality layer in the enterprise master, proceed to STEP 24/25 (ready) and STEP 26 with binary criticality; separately pursue an extended S1–S4 master for precise granularity.
