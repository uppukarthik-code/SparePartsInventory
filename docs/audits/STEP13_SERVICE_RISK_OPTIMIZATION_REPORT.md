# STEP 13 — Service-Risk Optimization Review (Phase 3)

**Generated:** 2026-06-08
**Status:** 🔍 **REVIEW / PROPOSAL ONLY — NO CODE CHANGED.** Awaiting approval before implementation.
**Module under review:** `railway/railway_inventory_optimization.py`

---

## 1. Current Objective

`railway_inventory_optimization.py:149`:

```python
priority = crit_w * max(0.0, gap) * unit_cost      # Procurement_Priority_Score
```

i.e. **Procurement_Priority_Score = Criticality_Weight × Inventory_Gap⁺ × Unit_Cost**

with `Criticality_Weight = CRITICALITY_STOCKOUT_WEIGHT = {S1:10, S2:5, S3:2, S4:1}`.

The budget allocator (`allocate_procurement_budget`, line 225) solves a binary knapsack:

```
maximize   Σ_i  Procurement_Priority_Score_i · x_i
subject to Σ_i  Inventory_Investment_Required_i · x_i ≤ Budget       (Investment = Gap⁺ × Unit_Cost)
           x_i ∈ {0,1}
```

## 2. Alignment Assessment vs Railway Signalling Service-Risk Reduction

The stated mission (module docstring) is **service-risk reduction, not inventory reduction.**
The current objective is **mis-aligned** with that mission on five counts:

| # | Issue | Why it matters for signalling service risk |
|---|---|---|
| **A** | **`Unit_Cost` sits inside the objective.** | It rewards *expensive* items, not *service-critical* ones. A cheap S1 track-circuit relay that prevents a signalling failure scores below a costly S1 item with identical consequence. Service risk ≠ rupee value. |
| **B** | **Knapsack value-density degenerates.** Density = `Score/Investment = (C_w·G·UC)/(G·UC) = C_w`. | Cost and gap **cancel**. The optimizer effectively just buys items in `C_w` order until the budget runs out — `Forecast`, `Gap` magnitude and `Lead_Time` have **no effect** on selection. |
| **C** | **`Target_Service_Level` is unused in the objective.** | β (0.90–0.99) is computed and used only to size safety stock. How far an item sits **below its service target** never influences priority. |
| **D** | **`Forecast_2026_27` (demand throughput) is absent.** | A high-criticality, high-demand item (frequent stockout exposure) ranks identically to a low-demand one with the same `Gap×Cost`. Exposure frequency is ignored. |
| **E** | **`Lead_Time_Months` is absent from the objective.** | Lead time governs **how long a stockout persists** and the size of demand-during-lead-time at risk. Longer LT = longer service outage = higher risk — currently invisible to ranking. |

**Conclusion:** the present score is a *criticality-weighted capital-at-risk* metric. It answers
"where is weighted money tied up?" — **not** "which purchase most reduces signalling service
risk per rupee?"

## 3. Proposed `Service_Risk_Reduction_Score` (SRRS)

**Risk model.** Spare-part service risk ≈ *consequence* × *exposure* × *duration* × *intolerance*,
and procurement reduces it by closing the shortfall to ROP. Map each driver to an available field:

| Driver | Field | Symbol | Role |
|---|---|---|---|
| Consequence of stockout | `Criticality_Weight` | `C_w` ∈ {10,5,2,1} | severity multiplier (S1 → S4) |
| Service intolerance | `Target_Service_Level` | `β` | how unacceptable a stockout is |
| Units of risk procurement removes | `Inventory_Gap⁺` | `G⁺` = max(0,Gap) | shortfall to ROP being closed |
| Exposure / throughput | `Forecast_2026_27` | `D` | demand rate → stockout frequency |
| Outage duration / exposure window | `Lead_Time_Months` | `L` | how long a stockout lasts |

**Normalised, dimensionless factors** (keep terms on comparable scale, avoid one term dominating):

```
s_i = 1 / (1 − β_i)        # service-intolerance (newsvendor critical-ratio intuition):
                           #   β=0.90 → 10,  β=0.95 → 20,  β=0.99 → 100
ℓ_i = L_i / 12             # lead time in years (outage-duration / exposure window)
d_i = D_i / median(D)      # relative demand throughput (median-normalised, dimensionless)
```

**Proposed score:**

> **SRRS_i = C_w,i × s_i × G_i⁺ × ℓ_i × d_i**
>
> = `Criticality_Weight × [1/(1−Target_Service_Level)] × Inventory_Gap⁺ × (Lead_Time_Months/12) × (Forecast_2026_27 / median Forecast)`

**Revised ILP (existing PuLP framework preserved; cost demoted to constraint only):**

```
maximize   Σ_i  SRRS_i · x_i
subject to Σ_i  Inventory_Investment_Required_i · x_i ≤ Budget      (Unit_Cost ONLY here)
           x_i ∈ {0,1}
```

**Why this is correct economics.** The knapsack value-density becomes

```
SRRS_i / Investment_i  =  (C_w · s · G⁺ · ℓ · d) / (G⁺ · UnitCost)
                       =  C_w · s · ℓ · d / UnitCost          # service-risk reduction per rupee
```

— no longer a constant. The optimizer now prefers **cheap, high-consequence, high-exposure,
long-lead shortfalls**, i.e. it maximises **service-risk reduction per rupee** rather than
weighted spend. `Unit_Cost` correctly influences *affordability* (constraint) but no longer
*desirability* (objective).

**Properties / guardrails:**
- `Gap⁺ = 0` ⇒ `SRRS = 0` (sufficient items never selected) — same gate as today.
- SRRS is **normalization-invariant** to the unit-of-measure fix (it contains no unit cost), so a
  separate "Normalized_SRRS" is unnecessary — one column serves both raw and normalized layers.
- All inputs already exist in `railway_inventory_policy.csv` — **no new upstream data required.**

## 4. Current vs Proposed — Side by Side

| Aspect | Current `Procurement_Priority_Score` | Proposed `Service_Risk_Reduction_Score` |
|---|---|---|
| Formula | `C_w × G⁺ × UnitCost` | `C_w × 1/(1−β) × G⁺ × (L/12) × (D/median D)` |
| Unit_Cost | **inside objective** (rewards expensive) | **budget constraint only** |
| Target_Service_Level β | unused | core intolerance multiplier `1/(1−β)` |
| Forecast / demand D | unused | exposure factor `d` |
| Lead_Time L | unused | outage-duration factor `ℓ` |
| Knapsack density | `= C_w` (degenerate; cost & gap cancel) | `= C_w·s·ℓ·d / UnitCost` (true risk-per-rupee) |
| Optimises | weighted capital-at-risk | **signalling service-risk reduction** |
| Selection bias | expensive items first | high-consequence, high-exposure, long-lead shortfalls |
| New data needed | — | **none** (all fields already in policy CSV) |

## 5. Affected Modules (if approved)

| Module | Change |
|---|---|
| `railway_inventory_optimization.py` | Add `Service_Risk_Reduction_Score` column in `build_inventory_policy`; switch `allocate_procurement_budget` objective (line 225) to SRRS; add to `POLICY_FIELDS`. Keep budget constraint (line 227) unchanged. |
| `railway_data_quality.py` | `Normalized_Procurement_Priority_Score`/`_Class` (lines 100–110) — SRRS is cost-free so a normalized twin is redundant; decide whether page1/page8 rank on SRRS directly. |
| `railway_powerbi_export.py` | `_budget_scenarios` (line 57) and page1/page8 currently consume `Normalized_Procurement_Priority_Score` → repoint to SRRS; page8 "Criticality_Coverage_Pct" becomes "Service_Risk_Coverage_Pct". |
| `railway_dashboard_validation.py` | V2/V5 expectations reference the priority score/rank → update baselines. |
| `railway_executive_summary.py`, `railway_management_reports.py` | Any narrative citing "priority score" → align wording to service-risk. |

## 6. Open Calibration Questions (for approval discussion)

1. **Intolerance form:** `1/(1−β)` (steep, 10→100×) vs `β/(1−β)` (slightly gentler) vs capped — which risk appetite?
2. **Demand normalisation:** median-normalised `D/median(D)` vs raw `D` vs `log(1+D)` to damp high-volume outliers?
3. **Lead-time unit:** `L/12` (years) vs raw months — affects relative weighting vs the other factors.
4. **Double-count check:** `G⁺` already embeds demand-during-lead-time; confirm whether `d` and `ℓ` should both multiply, or whether `ℓ` alone (duration) is preferred to avoid emphasising LT twice.
5. Whether to **retain** `Procurement_Priority_Score` alongside SRRS for back-compatibility/audit.

---

## 7. Recommendation

✅ **Adopt `Service_Risk_Reduction_Score` as the budget-allocation objective**, keeping the
existing PuLP ILP and using `Inventory_Investment_Required` purely as the budget constraint. It
removes the cost-bias and density degeneracy, and activates the four currently-dormant
service-risk signals (β, D, L, plus consequence) — all from existing data.

🚫 **No code has been changed.** Implementation, baseline-rebaselining of V2/V5, and the
calibration choices in §6 are **pending your approval.**
