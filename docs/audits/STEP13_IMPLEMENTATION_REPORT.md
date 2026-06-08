# STEP 13 — Service-Risk Reduction Score (SRRS) Implementation Report

**Generated:** 2026-06-08
**Author roles:** Principal Engineer · OR Reviewer · Railway Inventory Optimization Expert
**Status:** ✅ **IMPLEMENTED & VALIDATED** (independent review verdict: **APPROVE**)
**Scope guard:** Only the optimization **objective** and its supporting calculations changed.
Existing PuLP framework, constraints, budget handling, page pipeline, CSV schemas, KPIs and
ranking columns are preserved; every new field is **additive**.

---

## 1. Independent Review — Defect Confirmed

**Old objective** (`railway_inventory_optimization.py:149`): `priority = Criticality_Weight × Gap⁺ × Unit_Cost`
**Budget weight** (`:148`): `investment = Gap⁺ × Unit_Cost`

For every knapsack candidate (`Inventory_Status == "Procurement Required"` ⇒ `Gap⁺ > 0`, `Unit_Cost > 0`):

$$\text{density}_i=\frac{C_w\cdot G^+\cdot UC}{G^+\cdot UC}=C_w$$

**`Gap⁺` and `Unit_Cost` cancel exactly.** The allocator degenerates to "buy the highest-criticality
affordable items," blind to **forecast demand, gap magnitude, lead time, service level, and
cost-effectiveness.** Empirically confirmed: within-criticality-tier density coefficient of
variation = **6.0×10⁻⁸ ≈ 0** under the old objective (see §6-G). Defect is **real and exact.**

## 2. Technical Rationale

Spare-part **service risk** ≈ *consequence × intolerance × shortfall × outage-duration × exposure*.
Procurement reduces it by closing the gap to ROP. Each driver maps to an existing policy field, so
**no new data** is required. `Unit_Cost` is removed from the objective and retained **only** in the
budget constraint, converting the knapsack from "maximize weighted value" to **"maximize
service-risk reduction per rupee."**

## 3. Equations (as implemented)

```
SRRS = Criticality_Weight × Service_Factor × Positive_Gap × Lead_Time_Factor × Demand_Factor

Service_Factor   = 1 / (1 − Target_Service_Level)          # 0.90→10, 0.95→20, 0.99→100  (SL capped 0.9999)
Positive_Gap     = max(Inventory_Gap, 0)
Lead_Time_Factor = min(Lead_Time_Months / 12, 2.0)         # outage-duration, capped at 24 months
Demand_Factor    = ln(1 + Forecast_2026_27 / Median_Forecast)   # natural log; exposure/throughput
                   = 1.0   if Forecast missing or ≤ 0
                   = 1.0   if Median_Forecast ≤ 0
```

**Criticality weights** (`cfg.CRITICALITY_STOCKOUT_WEIGHT`, applied consistently in
`build_inventory_policy`): **S1=10, S2=5, S3=2, S4=1** — verified (validation §6-C).

**Revised ILP** (PuLP framework unchanged):
```
maximize   Σ_i  SRRS_i · x_i
subject to Σ_i  Inventory_Investment_Required_i · x_i ≤ Budget       # Unit_Cost lives ONLY here
           x_i ∈ {0,1}
```
Value-density is now `SRRS_i / Investment_i = C_w·s·ℓ·d / UnitCost` — a genuine
service-risk-reduction-per-rupee, no longer constant.

## 4. Code Changes

### 4.1 `railway/railway_inventory_optimization.py`
- **POLICY_FIELDS (`:53–54`)** — appended 5 additive columns: `Service_Factor`, `Lead_Time_Factor`,
  `Demand_Factor`, `Service_Risk_Reduction_Score`, `Service_Risk_Priority_Class`.
- **Factor models (`:119–151`)** — added `service_factor()`, `lead_time_factor()`, `demand_factor()`.
- **`build_inventory_policy` (`:222–238`)** — compute `Median_Forecast`, the three factors, SRRS, and
  a positional `Service_Risk_Priority_Class`.
- **`allocate_procurement_budget` (`:291`, `:300–301`)** — objective switched to SRRS; plan now carries
  `Service_Risk_Reduction_Score` and is sorted by it. **Budget constraint unchanged** (`:293`).

```diff
- prob += pulp.lpSum(cand.loc[i, "Procurement_Priority_Score"] * x[i] for i in cand.index)
+ prob += pulp.lpSum(cand.loc[i, "Service_Risk_Reduction_Score"] * x[i] for i in cand.index)
  prob += pulp.lpSum(cand.loc[i, "Inventory_Investment_Required"] * x[i] for i in cand.index) <= budget
```

```python
# build_inventory_policy — SRRS block
mf = out["Forecast_2026_27"].median(); median_forecast = 0.0 if pd.isna(mf) else float(mf)
pos_gap = out["Inventory_Gap"].clip(lower=0)
out["Service_Factor"]   = out["Target_Service_Level"].map(service_factor).round(4)
out["Lead_Time_Factor"] = out["Lead_Time_Months"].map(lead_time_factor).round(4)
out["Demand_Factor"]    = out["Forecast_2026_27"].map(lambda f: demand_factor(f, median_forecast)).round(4)
out["Service_Risk_Reduction_Score"] = (out["Criticality_Weight"] * out["Service_Factor"] * pos_gap
                                       * out["Lead_Time_Factor"] * out["Demand_Factor"]).round(4)
```

### 4.2 `railway/railway_powerbi_export.py`
- **`_budget_scenarios` / page8 (`:51`, `:59`, `:66`, `:75`)** — knapsack objective switched to SRRS;
  budget constraint (normalized investment) unchanged; **additive** `Service_Risk_Coverage_Pct` column
  added; all six original page8 columns retained.
- **page1 (`:122`)** — added additive `Service_Risk_Reduction_Score`, `Service_Risk_Priority_Class`.

### 4.3 `railway/railway_srrs_validation.py` — **NEW** (196 lines)
Read-only validation suite proving requirements A–H.

### Files modified / added
| File | Change | Lines |
|---|---|---|
| `railway_inventory_optimization.py` | objective + factors + SRRS columns | ~70 added/modified |
| `railway_powerbi_export.py` | page8 SRRS knapsack + page1 columns | ~10 added/modified |
| `railway_srrs_validation.py` | new validation suite | 196 new |

**Untouched:** `railway_config.py` weights, `railway_data_quality.py`, `railway_inventory_rationalization.py`,
all KPI/page0 logic, every existing CSV schema (columns only appended).

## 5. Before vs After

### 5.1 Budget allocation (`page8_budget_scenarios`, normalized investment)
| Scenario | Items_Funded OLD→NEW | Criticality_Cov% OLD→NEW | **Service_Risk_Cov% (new)** |
|---|---|---|---|
| Rs 50 Lakh | 6 → 13 | 1.31 → 0.41 | 0.42 |
| Rs 1 Crore | 6 → 9 | 2.77 → 2.19 | 6.98 |
| Rs 2 Crore | 8 → 12 | 5.52 → 4.50 | 7.46 |
| Rs 5 Crore | 6 → 14 | 13.96 → 13.63 | **57.66** |

The SRRS objective funds **more items per rupee** and, at Rs 5 Crore, covers **57.7 % of total
service-risk** vs only 13.6 % criticality-value coverage — the budget now buys risk reduction, not value.
`railway_procurement_plan.csv` (original-cost basis, Rs 1 Crore): **6 → 26 items funded** (21 added, 1 removed).

### 5.2 Re-ranking driven by the previously-dormant signals (`Procurement Required` set)
| Direction | PL_Code | Crit | OLD#→SRRS# | Forecast | Lead_Time | Service_Lvl | Why |
|---|---|---|---|---:|---:|---:|---|
| ⬆ promoted | 41095066 | S4 | 48 → 11 (**+37**) | 261,761 | 2.0 | 0.90 | huge demand exposure now counts |
| ⬆ promoted | 40981381 | S3 | 39 → 18 (**+21**) | 25,899 | 3.0 | 0.90 | high demand + longer lead time |
| ⬇ demoted | 56987122 | S1 | 2 → 15 (**−13**) | 2,278 | 12.0 | 0.90 | was inflated by Unit_Cost (now removed) |
| ⬇ demoted | 56160100 | S2 | 21 → 41 (**−20**) | 8 | 5.0 | 0.90 | very low demand → low service exposure |

### 5.3 Signal correlation (Spearman, candidate set)
`SRRS↔Forecast = 0.908`, `SRRS↔Lead_Time = 0.629`, `SRRS↔Service_Level = 0.653` — all three now drive
prioritization, where the old score embedded none of them in its formula.

## 6. Validation Evidence (`python -m railway.railway_srrs_validation` → ALL PASS)

| Req | Check | Result |
|---|---|---|
| **A** | Optimization executes (policy 59 rows, plan 26 items, SRRS column present) | ✅ PASS |
| **B** | Budget constraint satisfied — plan spend Rs 9,886,743 ≤ Rs 10,000,000 | ✅ PASS |
| **C** | SRRS correct — product identity max\|Δ\|=5.0e-5; factor formulas SF/LF/DF max\|Δ\|≤5.0e-5 | ✅ PASS |
| **D** | Forecast influences — 50/50 positive-forecast items ↑ SRRS when forecast doubled | ✅ PASS |
| **E** | Lead time influences — 50/50 sub-cap items ↑ SRRS at +1 month | ✅ PASS |
| **F** | Service level influences — 50/50 items ↑ SRRS at higher SL | ✅ PASS |
| **G** | Unit cost no longer dominates — within-tier density CV OLD=6.0e-8 (collapsed) → NEW=1.836 | ✅ PASS |
| **H** | Power BI exports functional — all pages present, required schemas intact, page8 = 4 scenarios | ✅ PASS |

**Regression gates also green after regeneration:**
- `railway_inventory_optimization` validation gate — ALL PASS
- `railway_data_quality` / `railway_inventory_rationalization` / `railway_executive_summary` — ALL PASS
- `railway_powerbi_export` executive test + gate — ALL PASS
- `railway_dashboard_validation` lineage **V1–V6 — ALL PASS** (V4 clean: SRRS not a forbidden raw column)
- `railway_enterprise` backward-compat hash — **0 existing files changed**, 15 pages re-enriched
- **page0 executive KPIs byte-identical** before vs after (Capital Rs 473,115,370; Concentration 82.42 %)

## 7. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `Service_Factor = 1/(1−SL)` is steep (0.99→100×); a future SL=1.0 would explode | Low | SL capped at 0.9999 in `service_factor()`; current SL table max = 0.99 |
| `Median_Forecast` shifts as the SKU set scales (59→907), moving Demand_Factor baseline | Low–Med | Documented; median is robust to outliers; recomputed each run |
| Page8 `Items_Funded` / coverage values changed (expected) — downstream Power BI bookmarks referencing old numbers | Low | Schema preserved; only optimization-output values changed (permitted) |
| `procurement_plan` grew 6→26 rows; any visual hard-coded to 6 rows | Low | Schema additive; row count is optimization output, not a fixed contract |
| Potential double-weighting of demand (Gap⁺ already embeds demand-during-lead-time; `Demand_Factor` re-introduces demand) | Med | Intentional: `Gap⁺` = one-off shortfall, `Demand_Factor` = ongoing exposure; `ln()` damps it. Flagged for calibration review. |

## 8. Assumptions

1. **`Median_Forecast`** = median of `Forecast_2026_27` across the **full strategic policy set** (all 59
   items, non-null), used as the demand-normalization reference.
2. **Lead-time cap** of 2.0 (24 months) is the intended saturation point for outage duration.
3. **`Procurement_Priority_Score` retained** alongside SRRS (not removed) for audit/back-compatibility.
4. SRRS is **cost-free**, hence **normalization-invariant** — no separate `Normalized_SRRS` is needed; one
   column serves both the raw and unit-normalized layers.
5. Operational universe is out of scope (no demand/forecast signal — see `SOURCE_UNIVERSE_AUDIT_REPORT.md`).

---

## 9. Final Summary

1. **Files modified:** `railway_inventory_optimization.py`, `railway_powerbi_export.py`; **added:** `railway_srrs_validation.py`.
2. **Lines changed:** ~80 modified/added across the two modules + 196 new validation lines.
3. **Validation results:** SRRS suite **A–H ALL PASS**; all existing regression/lineage gates **PASS**; KPIs byte-identical.
4. **Remaining risks:** demand double-weighting (calibration), Median_Forecast drift at scale — both low/medium, documented.
5. **Final recommendation:** ✅ **Adopt SRRS as the procurement objective.** The cost-bias and density
   collapse are eliminated; forecast, lead time, and service level now measurably drive prioritization, with
   all backward-compatibility guarantees intact. Optional next step: calibrate the demand/lead-time
   double-count (§6 of the Phase-3 review) if domain experts prefer a single exposure term.
