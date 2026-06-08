# STEP 15 — SRRS Calibration Implementation Report

**Generated:** 2026-06-08
**Status:** ✅ **IMPLEMENTED & VALIDATED**
**Scope guard:** Architecture unchanged. PuLP framework, constraints, budget handling, page
pipeline, CSV schemas and KPIs preserved. Every change is additive or confined to the SRRS
objective. The four STEP14 calibration actions were each verified against report evidence before
implementation (table below).

---

## 0. Evidence Check — every action is STEP14-supported

| # | Action | STEP14 evidence | Accepted? |
|---|---|---|---|
| 1 | Remove `Demand_Factor` | §4.2 elasticity 1.73; §3 Model B funds identical set | ✅ |
| 2 | Remove `Lead_Time_Factor` | §4.2 elasticity 3.16 (worst); re-encodes criticality; §3 Model C identical | ✅ |
| 3 | Retain `C_w × Service_Factor × Positive_Gap` | §4.3 recommended formulation | ✅ |
| 4 | Recalibrate `Service_Factor` | §2.4 saturated (median=min, SL=0.90→SF=10); §4.3 re-scale | ✅ |
| 5 | Safety Reserve for S1/S2 | §5 only 2/6 funded; "consequence-based provisioning floor" | ✅ |
| 6 | Explainability columns | §6 recommended column set | ✅ |

No action was unsupported; none rejected.

---

## 1. Code Changes

### `railway/railway_config.py` (new knobs, all configurable)
```python
SERVICE_FACTOR_BASELINE_SL   = 0.90        # SL mapped to Service_Factor = 1.0
SERVICE_FACTOR_SLOPE         = 20.0        # 1 + slope*(SL-baseline)
SAFETY_RESERVE_ENABLED       = True
SAFETY_RESERVE_BUDGET_PCT    = 0.20        # 20% of each budget reserved for insurance spares first
SAFETY_RESERVE_CRITICALITIES = ("S1","S2")
```

### `railway/railway_inventory_optimization.py`
- **`service_factor()`** recalibrated: `1 + SLOPE·max(0, SL−baseline)` (was steep `1/(1−SL)`).
- **SRRS objective** reduced to `Criticality_Weight × Service_Factor × Positive_Gap`.
  `Demand_Factor` and `Lead_Time_Factor` are still computed but **diagnostic only** (kept as
  columns for backward compatibility — not in the objective).
- **Explainability columns** added to `POLICY_FIELDS` (additive): `Positive_Gap`, `SRRS_Rank`,
  `SRRS_Per_Rupee`, `Funding_Driver`.
- **`_solve_knapsack()` + `allocate_with_reserve()`** helpers added; `allocate_procurement_budget`
  now calls the two-stage reserve. Reserve is a **floor not a cap** (S1/S2 can also win stage-2
  funding); disabling the config reduces it to the legacy single knapsack.

```python
SRRS = (Criticality_Weight * Service_Factor * Positive_Gap)        # calibrated objective
# Safety Reserve (two-stage):
reserve = SAFETY_RESERVE_BUDGET_PCT * budget
sel1 = knapsack(insurance_spares(S1/S2),  reserve)                 # stage 1
sel2 = knapsack(all_remaining,  budget - spent(sel1))             # stage 2
plan = sel1 ∪ sel2
```

### `railway/railway_powerbi_export.py`
- **page8** budget knapsack now calls the shared `allocate_with_reserve` (same SRRS objective +
  reserve); output schema unchanged.
- **page1** gains additive explainability columns: `Service_Factor`, `Positive_Gap`, `SRRS_Rank`,
  `SRRS_Per_Rupee`, `Funding_Driver`, `Funding_Decision` (Funded/Not Funded vs the Rs 1 Cr plan).

### `railway/railway_srrs_validation.py`
- Rewritten to validate the **calibrated** model (A–H, below).

---

## 2. Before vs After

| Item | Before (Step 13) | After (Step 15) |
|---|---|---|
| Objective | `C_w × SF × Gap⁺ × Lead_Time_Factor × Demand_Factor` | `C_w × Service_Factor × Gap⁺` |
| `Service_Factor` @ SL 0.90/0.95/0.97/0.98/0.99 | 10 / 20 / 33.3 / 50 / 100 (steep, saturated) | **1.0 / 2.0 / 2.4 / 2.6 / 2.8** (bounded, discriminating) |
| Demand elasticity `d ln SRRS / d ln Forecast` | **1.73** | **1.12** (→ single count via gap) |
| Lead-time elasticity `d ln SRRS / d ln LeadTime` | **3.16** | **1.93** (explicit double-count removed) |
| Procurement plan (Rs 1 Cr) | 26 items, **5** S1/S2 | 27 items, **6** S1/S2 |
| `Inventory_Gap`, `Investment`, page0 KPIs | — | **byte-identical (unchanged)** |
| Explainability columns on page1 | 0 | **6 added** |

The residual lead-time elasticity (1.93 > 1) is the **legitimate single count**: lead time genuinely
lives inside `Inventory_Gap` (via `EDLT = F·L/12` and `safety = z·σ·√L`) and is partly correlated
with criticality (the fallback lead time is S-tier-derived). The *explicit* multiplicative
double-count is eliminated; the remaining content is the upstream gap model (out of calibration scope).

## 3. Sensitivity Analysis (Rs 1 Crore, original-cost basis, n=35 candidates)

| Model | Reserve | Funded | S1/S2 funded | Budget Util % |
|---|---|---:|---:|---:|
| **A — SRRS = C_w·SF·Gap** | off | 24 | 5 | 99.7 |
| **A — SRRS = C_w·SF·Gap** | **on** | **27** | **6** | 98.3 |
| no Service_Factor (`C_w·Gap`) | on | 27 | 6 | 98.3 |
| Criticality only (`C_w`) | on | 29 | 6 | 86.2 |
| Gap only | on | 27 | 5→6 | 98.3 |

**Driver structure (Spearman vs SRRS):** Gap **0.961** (dominant), Service_Factor **0.423**,
Criticality **0.405** (meaningful secondary tilts). **Funding_Driver** distribution across items:
Gap 20 / Criticality 18 / Service_Level 12 — a balanced objective, no single factor dominating.

Interpretation: the calibrated objective is **exposure-led** (Gap = single-counted demand×lead-time
+ safety), weighted by consequence (criticality) and intolerance (service level), with the **Safety
Reserve guaranteeing the +1 insurance spare** that the pure economic knapsack omits. Criticality-only
funds more items but at much lower capital utilisation (86%), confirming gap-based differentiation
remains valuable.

## 4. Impact on Funded S1/S2 Insurance Spares

- **Plan S1/S2 funded: 5 → 6** (Safety Reserve effect; reserve = 20% × budget funds insurance spares first).
- **Low-demand S1/S2 (forecast ≤ median, n=7): mean SRRS rank 33.1 → 31.0**; of the deep-insurance
  items (gap ≤ 21 units), **3 of 4 are now Funded**, including one that flipped **no → FUNDED** purely
  via the reserve:

```
PL_Code        Crit  rank(old->new)  funding(old->new)   forecast  gap
50901126       S2    33 -> 33        FUNDED -> FUNDED        114    38
56160100       S2    41 -> 36        no     -> FUNDED          8    21   <-- rescued by reserve
52156618/56509 S2    43 -> 40        FUNDED -> FUNDED          8     8
56511516       S2    42 -> 41        FUNDED -> FUNDED         88     7
```

The Safety Reserve directly addresses STEP14 §5 (RAMS objection): consequence-driven insurance
spares are now provisioned ahead of the discretionary economic optimisation.

## 5. Validation Evidence — `railway_srrs_validation.py` → **ALL PASS**

| Req | Check | Result |
|---|---|---|
| A | Optimization executes (policy 59, plan 27 items, SRRS present) | ✅ PASS |
| B | Budget satisfied — plan spend Rs 9,834,650 ≤ Rs 10,000,000 | ✅ PASS |
| C | `SRRS == Criticality_Weight × Service_Factor × Positive_Gap` (max\|Δ\|=0.000000) | ✅ PASS |
| D | Demand/Lead factors excluded from objective (vary but do not affect SRRS) | ✅ PASS |
| E | Service_Factor bounded+monotonic, 5 distinct values {1.0,2.0,2.4,2.6,2.8} | ✅ PASS |
| F | Safety Reserve: S1/S2 funded **5 → 6** vs no-reserve | ✅ PASS |
| G | Unit cost absent (within-tier density CV = 1.816) | ✅ PASS |
| H | Power BI functional; page1 carries all 7 explainability fields | ✅ PASS |

**Regression gates (regenerated pipeline):**
- optimizer / data-quality / rationalization / executive-summary — ALL PASS
- powerbi export executive test + gate — ALL PASS
- dashboard lineage **V1–V6 — ALL PASS** (page1 grew to 21 cols; no forbidden raw column → V4 clean)
- enterprise backward-compat hash — **0 existing files changed**; 15 pages re-enriched
- **page0 executive KPIs byte-identical**; `Inventory_Gap` and `Investment` byte-identical

## 6. Power BI Compatibility Verification

| Check | Result |
|---|---|
| Page names unchanged (page0–page9) | ✅ |
| Existing columns preserved on every page (only appends) | ✅ |
| page0 KPIs byte-identical | ✅ |
| page8 schema intact (6 base + `Service_Risk_Coverage_Pct`); 4 scenarios | ✅ |
| page1 row count 59 unchanged; +6 additive explainability columns (21 total) | ✅ |
| V4 "no raw value/score on strategic pages" still clean | ✅ |
| Enterprise-enriched copies inherit new columns automatically | ✅ |
| Phase-1 compatibility columns (Description, Criticality_Name, aliases) intact | ✅ (V6 PASS) |

New page1 explainability columns for Power BI users: `Service_Factor`, `Positive_Gap`, `SRRS_Rank`,
`SRRS_Per_Rupee`, `Funding_Driver`, `Funding_Decision` — letting a user reconstruct the score
(`C_w × Service_Factor × Positive_Gap`), see its rank and per-rupee economics, the dominant driver,
and whether it was funded.

## 7. Risks & Assumptions

| Risk / Assumption | Note |
|---|---|
| Residual lead-time elasticity 1.93 | Gap legitimately contains lead time; the fallback-LT↔criticality coupling is an upstream model choice, not re-introducible here. Out of calibration scope. |
| `Service_Factor` is decision-light at Rs 1 Cr (noSF funds same set) | It still discriminates in **ranking** and explainability and matters at other budgets; slope is configurable if stronger tilt is wanted. |
| Reserve % (20%) and qualifying tiers (S1/S2) are assumptions | Fully configurable; F-test confirms +1 S1/S2 at 20%. Tune per RAMS policy. |
| `Demand_Factor`/`Lead_Time_Factor` columns retained but unused in objective | Kept for backward compatibility / diagnostics; clearly documented as non-objective. |
| `SRRS_Per_Rupee` uses procurement-basis investment (same basis as the funding knapsack) | Consistent with `Funding_Decision`. |

---

## 8. Conclusion

All six calibration actions implemented, each backed by STEP14 evidence; the double-counting is
removed (elasticities 1.73→1.12 and 3.16→1.93), `Service_Factor` now discriminates across service
levels, the Safety Reserve rescues low-demand S1/S2 insurance spares (5→6 funded), and six additive
explainability columns expose the funding rationale — all with **page-level KPIs, gaps, investments
and schemas unchanged** and **every validation gate green**.

This resolves the STEP14 "APPROVED WITH CALIBRATION REQUIRED" conditions. Recommend re-running the
STEP14 audit to confirm the production-readiness upgrade to **APPROVED FOR PRODUCTION**.
