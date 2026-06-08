# STEP35-OPT — Enterprise Budget Optimization & Capital Allocation — Report

**Date:** 2026-06-09
**Branch:** `step35-opt-enterprise-budget-optimization` (9 commits; not merged/pushed)
**Mandate:** Extend the existing optimizer from divisional procurement to enterprise capital allocation. Do NOT build a new optimizer; reuse `railway_inventory_optimization.py`. Additive only; existing outputs unchanged.

> **Scale note:** ₹1 Crore (Cr) = ₹1,00,00,000 = 10⁷. All "Cr" figures below are derived from raw-rupee CSV values ÷10⁷.

---

## 1. What was built (all additive; reuses the existing PuLP knapsack)

Three SOLVER PRIMITIVES were appended to the single source of truth `railway/railway_inventory_optimization.py` — each *reuses* the existing `allocate_with_reserve`/`_solve_knapsack` (same binary `x_i`, same SRRS objective, same budget constraint, same Safety-Reserve):
- `solve_budget_frontier()` — solves the knapsack across 9 budget levels.
- `enterprise_capital_allocation()` — one pooled knapsack across all divisions' candidates at an enterprise budget.
- `procurement_roadmap()` — year-by-year knapsack, unfunded items carried forward.

A new ORCHESTRATION/IO module `railway/governance/enterprise_allocation.py` reads existing per-division `railway_inventory_policy.csv` outputs and writes the new CSVs. Board KPIs + the decision dashboard extend `railway/governance/division_summary.py`. Notebook **Section 17** (6 figures, live data) was added to `notebook_railway.ipynb` and (3 figures) `notebook_railway_executive.ipynb`.

**Deliverables produced (`railway/outputs/`):** `optimization_baseline_validation.csv`, `risk_reduction_frontier.csv`, `budget_efficiency_analysis.csv`, `enterprise_budget_allocation.csv`, `enterprise_budget_allocation_readiness.csv`, `procurement_roadmap.csv`, `executive_budget_scenarios.csv`, `enterprise_decision_dashboard.csv`.

---

## 2. The risk-reduction frontier (enterprise, 50 procurement-required PLs)

| Budget | PLs funded | Critical (S1/S2) | Capital used | Risk reduction | Marginal SRRS/₹ |
|---|---|---|---|---|---|
| ₹1 Cr | 27 | 6 | ₹0.98 Cr | **20.69%** | 0.2198 |
| ₹5 Cr | 28 | 8 | ₹4.99 Cr | **56.24%** | 0.0926 |
| ₹10 Cr | 30 | 10 | ₹9.99 Cr | **72.69%** | 0.0343 |
| ₹25 Cr | 33 | 14 | ₹25.00 Cr | **93.44%** | 0.0144 |
| ₹50 Cr | 48 | 21 | ₹46.70 Cr | **97.85%** ⟵ knee | 0.0021 |
| ₹100 Cr | 48 | 21 | ₹46.70 Cr | 97.85% | 0.0000 |
| ₹200 Cr | 49 | 22 | ₹134.71 Cr | 98.52% | 0.00008 |
| ₹500 Cr | 49 | 22 | ₹134.71 Cr | 98.52% | 0.0000 |
| Unlimited | 50 | 23 | ₹660.63 Cr | **100.00%** | — |

**Headline insight — a single ₹525.9 Cr mega-item dominates the tail.** 98.52% of enterprise service-risk is removed for **₹134.7 Cr** (49 of 50 PLs). The final 1.48% (to 100%) requires one PL costing **₹525.9 Cr** — it is unaffordable below the "Unlimited" level. The board's value lies almost entirely in the **₹25–50 Cr region**.

---

## 3. Answers to the 10 expected questions

1. **Budget for 50% risk reduction:** ≈ **₹4.30 Cr** (interpolated, between ₹1 Cr and ₹5 Cr).
2. **Budget for 75% risk reduction:** ≈ **₹11.67 Cr** (between ₹10 Cr and ₹25 Cr).
3. **Budget for 90% risk reduction:** ≈ **₹22.51 Cr** (between ₹10 Cr and ₹25 Cr).
4. **Budget knee-point:** **₹50 Cr** (97.85% risk reduction; `Is_Knee_Point` in `budget_efficiency_analysis.csv`). Practical diminishing returns begin at **₹10 Cr** (`Is_Diminishing_Returns`).
5. **Optimal investment level:** the **₹25–50 Cr** band — ₹25 Cr already buys 93.4% and ₹50 Cr buys 97.85%; everything above is steep diminishing returns.
6. **How to allocate ₹100 Cr across divisions** (`enterprise_budget_allocation.csv`, ₹100 Cr rows): ~₹16.5 Cr per division (MAS 165.5M, MDU 165.4M, PGT 169.9M, SA 165.4M, TPJ 168.4M, TVC 165.4M), each reaching ~90.68% of its own risk. **Caveat — see §5: the six divisions currently hold identical data, so this split reflects identical inputs, not true divisional differences.**
7. **Highest SRRS reduction per ₹ (division):** all six are within 0.3% of each other (PGT marginally highest at ₹100 Cr, capital efficiency ≈ 0.0573) — again because inputs are identical today.
8. **3-year procurement roadmap** (`procurement_roadmap.csv`, equal-thirds default ≈ ₹220 Cr/yr): FY2026-27 funds **49 PLs for ₹134.7 Cr → 98.52% cumulative**; FY2027-28 and FY2028-29 fund 0 additional (the only remaining item is the ₹525.9 Cr mega-item, which exceeds a one-year third). **Remaining exposure ₹525.9 Cr.** A realistic multi-year phasing should set `cfg.ANNUAL_PROCUREMENT_BUDGET` to ~₹25–50 Cr/yr (see §5).
9. **What the Railway Board should fund first:** the **S1/S2 (safety/operational-critical) high-SRRS-per-rupee PLs** — at ₹25 Cr, 14 of 33 funded items are S1/S2 and 93.4% of risk is removed. Tier-1 (S1/S2) total funding requirement = **₹657.82 Cr** (but the bulk of *risk* is cheap to retire).
10. **Maximum achievable enterprise risk reduction:** **100%** — but only at full funding of ₹660.63 Cr; 98.52% is reached at ₹134.7 Cr.

---

## 4. Executive scenarios (`executive_budget_scenarios.csv`)

| Scenario | PLs | S1 | S2 | S3 | S4 | Capital used | Risk reduction | Efficiency (SRRS/₹) |
|---|---|---|---|---|---|---|---|---|
| ₹25 Cr | 33 | 8 | 6 | 7 | 12 | ₹25.0 Cr | 93.44% | 0.0390 |
| ₹50 Cr | 48 | 11 | 10 | 13 | 14 | ₹46.7 Cr | 97.85% | 0.0219 |
| ₹100 Cr | 48 | 11 | 10 | 13 | 14 | ₹46.7 Cr | 97.85% | 0.0219 |
| ₹200 Cr | 49 | 12 | 10 | 13 | 14 | ₹134.7 Cr | 98.52% | 0.0076 |
| Unlimited | 50 | 13 | 10 | 13 | 14 | ₹660.6 Cr | 100.00% | 0.0016 |

Capital efficiency falls ~25× from the ₹25 Cr scenario to full funding — the quantitative case for capping investment near the knee.

---

## 5. Honest limitations (must read)

1. **Cross-division allocation is structurally correct but currently non-differentiated.** Every `railway/outputs/<DIV>/railway_inventory_policy.csv` holds the **same 50-row consolidated dataset** (a STEP29-30 artifact — divisions were not partitioned at the policy level). `enterprise_budget_allocation_readiness.csv` flags all six as `REPORTABLE` with identical totals (SRRS 10,443,980; investment ₹660.63 Cr). The pooled-knapsack machinery is real and optimal; it will produce a *meaningful* divisional split the moment divisions carry distinct policies. **Until then, treat §3 Q6/Q7 as mechanism demonstrations, not investment advice.**
2. **The roadmap is degenerate under the equal-thirds default** because one year's third (₹220 Cr) exceeds the entire affordable portfolio (₹134.7 Cr). The model is correct; the *default* annual cap is too large. Set `cfg.ANNUAL_PROCUREMENT_BUDGET = 25_00_00_000` (₹25 Cr) for a realistic 3-year phasing.
3. **The knee at ₹50 Cr is sensitive to the wide budget axis** (levels up to ₹500 Cr stretch the normalization). The decision-relevant takeaway is robust regardless: 93% at ₹25 Cr, ~98% at ₹50 Cr, then a cliff.

---

## 6. Success-criteria verdicts

1. **Optimization-extension verdict:** ✅ **Achieved.** Three primitives added to the single source of truth, reusing the existing knapsack; zero duplicate solver (`procurement_optimizer.py` absent; no `LpProblem`/`LpVariable` executable code outside `railway_inventory_optimization.py`).
2. **Budget-frontier verdict:** ✅ **Achieved.** 9-level frontier with all required metrics; monotonic; budget constraint holds at every level (0 violations).
3. **Enterprise-allocation verdict:** ⚠️ **Mechanism achieved; data-blocked for real divisional insight.** Pooled-knapsack allocation works and respects budget; divisional differentiation awaits true per-division policies (§5.1).
4. **Multi-year-roadmap verdict:** ⚠️ **Achieved, default needs tuning.** 3-year sequencing works; set a realistic annual cap for non-degenerate phasing (§5.2).
5. **Executive-decision-support verdict:** ✅ **Achieved.** Five board scenarios + decision dashboard answer all 10 questions with live numbers.
6. **Railway Board usefulness:** ✅ **High for the enterprise frontier / scenarios / dashboard** (the "how much to invest and what it buys" question is fully answered); **conditional for divisional allocation** until divisions carry distinct data.
7. **Recommendation for Railway Platform v1.1:** **Ship the frontier, efficiency, scenarios, roadmap (with a ₹25 Cr/yr annual cap), and decision dashboard as v1.1 enterprise decision-support.** Before promoting the *cross-division* allocation to a board tool, (a) partition per-division policies so divisions are genuinely distinct, and (b) fix the pre-existing baseline (line-ending golden-manifest defect + stale fixtures) documented in `STEP35_OPT_VALIDATION_REPORT.md` so the regression gate is trustworthy again.

---

*Optimization formulas (SRRS, ROP, safety stock, criticality, lead time, procurement tiers) were not modified. The existing `railway_inventory_optimization.py` remains the single source of truth. See `optimization_baseline_validation.csv` (all aspects UNCHANGED).*
