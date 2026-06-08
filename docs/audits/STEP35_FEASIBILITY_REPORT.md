# STEP35 Feasibility Report — Optimization Layer Audit

**Type:** Read-only audit. No code modified, no optimization modules created.
**Date:** 2026-06-09
**Scope reviewed:** `railway/` optimization & allocation modules, all PuLP usage, all optimization outputs (enterprise + 6 business units), all optimization dashboards, STEP1–20 optimization artifacts.
**Deliverables:** `optimization_capability_inventory.csv`, `optimization_gap_analysis.csv`, this report (all in `docs/audits/`).

---

## Verdict

> ## **B. PARTIALLY IMPLEMENTED**
>
> The **core** of the requested STEP35 capability — *budget-constrained procurement optimization with PL funding ranking and funding explainability* — is **already implemented and production-grade**. The gaps are at the **edges**: multi-period procurement *sequencing*, *cross-business-unit* capital allocation of a shared budget, and a *solved* (vs. reported) budget-scenario frontier.

This is not a "missing" feature to build from scratch — it is a **mature optimizer to extend**.

---

## ⚠️ Naming Collision (read first)

The repository **already uses the label "STEP35"** — but for an unrelated purpose. In `docs/release/remote_migration_plan.md` and the STEP33/STEP34 reports, **STEP35 = the git push / remote-migration step** (migrate `origin` to the PRIVATE `uppukarthik-code` repo, then push). There is **no optimization-flavored STEP35 spec anywhere in the repo** (searched all `*.md`, `*.py`, `*.ipynb`, `docs/{audits,reporting,modernization,release}`).

**Recommendation:** if this optimization initiative proceeds, give it a distinct name (e.g. `STEP35-OPT`) to avoid colliding with the documented release-push STEP35.

---

## Answers to the 9 Audit Questions

### 1. What optimization capabilities already exist?
- **Inventory policy optimization** — closed-form Safety Stock (`z·σ·√LT`), ROP, inventory gap, capital required (STEP5).
- **Budget-constrained procurement** — a real **PuLP binary knapsack** (CBC solver) selecting which PLs to fund under a hard budget (STEP13/15).
- **Two-stage Safety-Reserve allocation** — reserves a budget floor for S1/S2 "insurance" spares, then optimizes the remainder (STEP15).
- **PL funding ranking + classification** — SRRS ranking, priority classes, per-rupee efficiency, dominant-driver attribution (STEP13/15).
- **Funding explainability** — funded-vs-rejected with log-share decomposition of *why* (STEP15/17).
- **Multi-business-unit execution** — the full optimizer runs independently for each of 6 BUs (MAS/MDU/PGT/SA/TPJ/TVC).
- **Inventory rationalization** — rule-based retain/dispose/procure disposition (STEP16).
- **Strategic stock allocation across BUs** — deterministic depot→BU mapping (STEP18/19).

> **Only one module uses a solver:** `railway/railway_inventory_optimization.py` (PuLP + CBC). Everything else is closed-form, heuristic scoring, or deterministic rules.

### 2. What decision variables already exist?
Binary selection variables **`x_i ∈ {0,1}`**, one per procurement-required PL, in `_solve_knapsack` (`pulp.LpVariable(..., cat="Binary")`). In the two-stage reserve path the same variable type is solved twice (reserve stage, then remainder stage). **No continuous, integer-quantity, multi-period, or per-unit-budget-split variables exist.**

### 3. What objective functions already exist?
- **Primary (STEP13/15):** maximize `Σ Service_Risk_Reduction_Score · xᵢ`, where `SRRS = Criticality_Weight × Service_Factor × Positive_Gap` (cost-free objective; unit cost lives only in the constraint).
- **Legacy ranking score:** `Procurement_Priority_Score = Criticality_Weight × Gap × Unit_Cost` (used for sorting/Top-10, not the knapsack objective).

### 4. What constraints already exist?
- **Budget:** `Σ Investmentᵢ · xᵢ ≤ PROCUREMENT_BUDGET` (Rs 1 crore, from `railway_config`).
- **Affordability filter:** items costing more than the budget are dropped.
- **Safety-Reserve floor:** a configurable share of the budget is restricted to S1/S2 insurance spares before the open stage (a floor, not a cap).
- **Service-level / lead-time bounds** enter the *policy* layer (SL by ABC×Criticality, lead time capped 1–24 months) — not the LP.

### 5. Does the platform already solve budget-constrained procurement? **YES.**
`allocate_procurement_budget()` → `allocate_with_reserve()` → `_solve_knapsack()` solves a binary knapsack with CBC and writes `railway_procurement_plan.csv`. Validated by `railway_srrs_validation.py` (asserts `spent ≤ budget`).

### 6. Does the platform already generate optimal procurement sequences? **PARTIAL.**
It produces an **optimal procurement *portfolio*** (which items to fund now, ranked by SRRS) — but **not a time-phased *sequence***. Everything is a single-period snapshot; there is no multi-period schedule, phased budget release, or lead-time-aware PO timing.

### 7. Does the platform already rank PLs for funding? **YES — fully.**
`SRRS_Rank`, `Procurement_Priority_Class`, `Service_Risk_Priority_Class`, `SRRS_Per_Rupee`, and `Funding_Driver` columns; `executive_top10_procurement.csv`; and `railway_funding_explainability.csv` (funded vs. rejected with driver attribution). This requirement is mature.

### 8. Does the platform already support capital allocation decisions? **PARTIAL.**
Within a single budget/unit: **yes** (knapsack + two-stage reserve + budget-utilization reporting). **But** there is **no optimal division of one shared enterprise budget across the 6 BUs** — `enterprise_rollup()` only *concatenates* per-BU outputs, and each BU runs against its own independent Rs 1 crore. Budget *scenarios* are **reported** at a fixed level, not **solved** as an efficiency frontier.

### 9. What gaps remain relative to STEP35?
| Gap | Severity |
|---|---|
| Multi-period / time-phased procurement **sequencing** (a schedule, not a snapshot) | **High** |
| **Cross-BU** capital allocation of a *shared* enterprise budget (currently concatenation + per-unit fixed budgets) | **High** |
| Budget **frontier solved** through the optimizer (currently reported at discrete fixed levels) | Medium |
| Budget as a **runtime/scenario parameter** rather than a single config constant | Low |
| Strategic allocation is a deterministic **mapping**, not service-risk-optimized | Medium (if in scope) |

See `optimization_gap_analysis.csv` for full detail and recommendations.

---

## Optimization Outputs & Dashboards (evidence)

**Enterprise CSVs:** `railway_inventory_policy.csv`, `railway_procurement_plan.csv`, `railway_funding_explainability.csv`, `executive_budget_scenario.csv`, `executive_top10_procurement.csv`, `railway_abc_criticality_matrix.csv`, `railway_inventory_rationalization.csv`, `railway_rationalization_summary.csv`, `step11_top20_rank_comparison.csv`.
**Per business unit (×6):** each of MAS/MDU/PGT/SA/TPJ/TVC carries its own `procurement_plan`, `budget_scenario`, `funding_explainability`, and rationalization files → decentralized but **independent** allocation.
**Dashboards:** Power BI *Inventory Optimization Effectiveness* dashboard + pages `page1_procurement`, `page7_abc_criticality_matrix`, `page8_budget_scenarios`, `page9_management_actions`.
**Notebooks:** main notebook covers SRRS Prioritization → Capital Exposure (STEP25.5) → Procurement Portfolio (STEP27) → Business Case (STEP28).

---

## STEP1–20 Optimization Lineage (how the optimizer was built)

- **STEP5** — inventory policy: SS / ROP / gap / capital-required; first PuLP knapsack pattern.
- **STEP11** — demand classification (SBC / ADI–CV²) feeding forecaster selection; rank-comparison artifact.
- **STEP13** — rewired the knapsack objective from unit-cost-dominated to **SRRS** (service-risk reduction).
- **STEP14** — audit: confirmed the old objective was degenerate; established SHA-pinned golden regression suite.
- **STEP15** — **Safety Reserve** two-stage allocation + funding explainability columns (SRRS_Rank, per-rupee, driver).
- **STEP16** — inventory rationalization rule engine.
- **STEP17** — config hardening (centralized criticality weights, SL/lead-time bounds in `railway_config`).
- **STEP18/19** — multi-business-unit runner + deterministic strategic cross-BU allocation + enterprise rollup.

---

## Bottom Line

If STEP35 is defined as *"give the platform budget-constrained procurement optimization, rank PLs for funding, and explain capital allocation"* — **most of it already ships today** and is regression-pinned. The **net-new** work to make STEP35 a genuine advance is narrow and well-defined:

1. **Multi-period sequencing** (the biggest true gap — turns a portfolio into a schedule).
2. **Shared-budget cross-BU capital allocation** (replace concatenation + per-unit fixed budgets with one enterprise allocation).
3. **A solved budget frontier** (sweep the knapsack across budget levels for marginal-return curves).

Recommended classification for planning purposes: **B — Partially implemented (core complete; extend, don't rebuild).**
