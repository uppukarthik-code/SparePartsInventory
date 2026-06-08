"""
railway_inventory_optimization.py
=================================
Railway Signalling Spare Parts -- SERVICE-RISK inventory optimization.

This is NOT an inventory-reduction exercise. Current state = 40 procurement-risk
/ 33 critical-shortage / 0 excess items, so the optimizer's job is to answer:

  1. Which signalling spares need immediate procurement?
  2. How much capital is required?
  3. Which S1/S2 items are most exposed?
  4. What service level is targeted/achievable?
  5. Given a Rs 1 crore budget next month, what should be bought first?

Inputs (validated Step 2-4 artifacts):
  railway_demand_history.csv, railway_sku_master.csv, railway_forecast.csv

Reuse (Notebook 05): PuLP LpProblem pattern; SS = z*sigma*sqrt(LT), ROP formula;
z = norm.ppf(service_level).
Adapted: service level on ABC x Criticality; railway Tier1/Tier2 lead time;
criticality-weighted penalty; LP repurposed to a budget-constrained knapsack.
New: gap / status / investment / priority score+class / matrix / concentration.

Output: railway/outputs/railway_inventory_policy.csv (+ matrix + procurement plan)
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

from railway import railway_config as cfg

PROCUREMENT_BUDGET = cfg.PROCUREMENT_BUDGET      # Rs 1 crore (centralized in config)

POLICY_FIELDS = [
    "PL_Code", "Description",
    "ABC_Class", "Criticality", "Criticality_Weight",
    "Forecast_2026_27",
    "Target_Service_Level", "Z_Value",
    "Lead_Time_Months", "Lead_Time_Source",
    "Demand_Sigma",
    "Safety_Stock",
    "Expected_Demand_During_LT",
    "ROP",
    "Current_Stock",
    "Inventory_Gap", "Inventory_Status",
    "Inventory_Investment_Required",
    "Procurement_Priority_Score", "Procurement_Priority_Class",
    "Recommended_Min", "Recommended_Max", "Recommended_Reorder_Level",
    # ---- Step 13/15: Service-Risk Reduction objective (additive; cost-free) ----
    "Service_Factor", "Lead_Time_Factor", "Demand_Factor",
    "Positive_Gap",
    "Service_Risk_Reduction_Score", "Service_Risk_Priority_Class",
    # ---- Step 15: explainability (additive) ----
    "SRRS_Rank", "SRRS_Per_Rupee", "Funding_Driver",
]

# Target service level by (ABC, Criticality) -- centralized in railway_config
# (Step 17 hardening). Kept as module aliases for backward-compatible references.
SERVICE_LEVEL_TABLE = cfg.SERVICE_LEVEL_TABLE
DEFAULT_TARGET_SL = cfg.DEFAULT_TARGET_SL


def _safe(x):
    return 0.0 if (x is None or pd.isna(x)) else float(x)


def priority_class_for_position(i, n):
    """Positional procurement-priority class (Top 10% / 20% / 30% / rest).

    Shared by the original (Procurement_Priority_Score) ranking here and by the
    normalized ranking in railway_data_quality, so both use identical thresholds.
    """
    pct = (i / n) if n else 1.0
    if pct < 0.10:
        return "Immediate"
    if pct < 0.30:
        return "High"
    if pct < 0.60:
        return "Medium"
    return "Low"


# ----------------------------------------------------------------------
# component models
# ----------------------------------------------------------------------
def target_service_level(abc, crit):
    return SERVICE_LEVEL_TABLE.get((abc, crit), DEFAULT_TARGET_SL)


def lead_time_months(pending_supply, ear_qty, criticality):
    """Locked two-tier lead-time rule. Returns (months, source)."""
    ps = _safe(pending_supply)
    if ps > 0:
        lt = _safe(ear_qty) / ps
        lt = min(max(lt, cfg.LEAD_TIME_MIN_MONTHS), cfg.LEAD_TIME_MAX_MONTHS)
        return lt, "Tier1_PendingSupply"
    lt = cfg.LEAD_TIME_FALLBACK_MONTHS.get(criticality, cfg.LEAD_TIME_DEFAULT_FALLBACK)
    return float(lt), "Tier2_Criticality"


def demand_sigma(series):
    """Sample standard deviation of the annual consumption series."""
    vals = np.array([_safe(v) for v in series], dtype=float)
    return float(np.std(vals, ddof=1)) if vals.size > 1 else 0.0


# ----------------------------------------------------------------------
# Step 13 -- Service Risk Reduction Score (SRRS) factor models
# ----------------------------------------------------------------------
# SRRS = Criticality_Weight * Service_Factor * Positive_Gap
#        * Lead_Time_Factor * Demand_Factor
# A cost-free objective: maximises service-risk reduction, NOT inventory value.
# Unit_Cost is deliberately excluded here (it belongs only in the budget
# constraint / procurement-cost calculations).
def service_factor(target_sl) -> float:
    """Service-level intolerance multiplier (Step 15 recalibration).

    Bounded linear form  1 + SLOPE * max(0, SL - baseline)  (0.90->1.0, 0.95->2.0,
    0.97->2.4, 0.98->2.6, 0.99->2.8). Replaces the steep 1/(1-SL), which saturated at
    the 0.90 floor (median == min) and double-counted the z(SL) already carried in the
    safety-stock term of Inventory_Gap. Slope/baseline are configurable."""
    sl = _safe(target_sl)
    return 1.0 + cfg.SERVICE_FACTOR_SLOPE * max(0.0, sl - cfg.SERVICE_FACTOR_BASELINE_SL)


def lead_time_factor(lead_time_mo) -> float:
    """Outage-duration / exposure-window multiplier = min(LT_months/12, 2.0).
    Lead time in years, capped at 2.0 (24 months) so a single long-lead item
    cannot dominate the objective."""
    return min(_safe(lead_time_mo) / 12.0, 2.0)


def demand_factor(forecast, median_forecast) -> float:
    """Throughput / exposure multiplier = ln(1 + Forecast / Median_Forecast).
    Natural log damps high-volume outliers. Documented fallbacks:
      * Forecast missing or <= 0        -> 1.0
      * Median_Forecast missing or <= 0 -> 1.0
    """
    f = _safe(forecast)
    if f <= 0:
        return 1.0
    mf = _safe(median_forecast)
    if mf <= 0:
        return 1.0
    return float(np.log1p(f / mf))


# ----------------------------------------------------------------------
# load validated artifacts (no merge of the two business domains)
# ----------------------------------------------------------------------
def _load_inputs() -> pd.DataFrame:
    hist = pd.read_csv(cfg.DEMAND_HISTORY_CSV, dtype={"PL_Code": str})
    master = pd.read_csv(cfg.SKU_MASTER_CSV, dtype={"PL_Code": str})
    fc = pd.read_csv(cfg.FORECAST_CSV, dtype={"PL_Code": str})

    df = hist.merge(
        master[["PL_Code", "ABC_Class", "Criticality", "Criticality_Weight", "Inventory_Value"]],
        on="PL_Code", how="left")
    df = df.merge(fc[["PL_Code", "Forecast_2026_27"]], on="PL_Code", how="left")
    return df


# ----------------------------------------------------------------------
# main build
# ----------------------------------------------------------------------
def build_inventory_policy(write: bool = True) -> pd.DataFrame:
    df = _load_inputs()
    rows = []
    for _, r in df.iterrows():
        abc = r["ABC_Class"]
        crit = r["Criticality"]
        crit_w = cfg.CRITICALITY_STOCKOUT_WEIGHT.get(crit, 1)
        unit_cost = _safe(r["Unit_Cost"])
        cur_stock = _safe(r["Current_Stock"])
        forecast = _safe(r["Forecast_2026_27"])

        sl = target_service_level(abc, crit)
        z = float(stats.norm.ppf(sl))

        lt, lt_src = lead_time_months(r["Pending_Supply"], r["EAR_Qty"], crit)
        sigma = demand_sigma([r[y] for y in cfg.CONSUMPTION_YEARS])

        safety_stock = z * sigma * np.sqrt(lt)
        edlt = forecast * lt / 12.0
        rop = edlt + safety_stock
        gap = rop - cur_stock
        status = "Procurement Required" if gap > 0 else "Sufficient"
        investment = max(0.0, gap) * unit_cost
        priority = crit_w * max(0.0, gap) * unit_cost

        rows.append({
            "PL_Code": r["PL_Code"], "Description": r["Description"],
            "ABC_Class": abc, "Criticality": crit, "Criticality_Weight": crit_w,
            "Forecast_2026_27": round(forecast, 2),
            "Target_Service_Level": sl, "Z_Value": round(z, 4),
            "Lead_Time_Months": round(lt, 3), "Lead_Time_Source": lt_src,
            "Demand_Sigma": round(sigma, 3),
            "Safety_Stock": round(safety_stock, 2),
            "Expected_Demand_During_LT": round(edlt, 2),
            "ROP": round(rop, 2),
            "Current_Stock": round(cur_stock, 2),
            "Inventory_Gap": round(gap, 2), "Inventory_Status": status,
            "Inventory_Investment_Required": round(investment, 2),
            "Procurement_Priority_Score": round(priority, 2),
            "Recommended_Min": round(rop),
            "Recommended_Max": round(rop + forecast),
            "Recommended_Reorder_Level": round(rop),
            "_Inventory_Value": round(_safe(r["Inventory_Value"]), 2),
        })

    out = pd.DataFrame(rows).sort_values(
        "Procurement_Priority_Score", ascending=False).reset_index(drop=True)

    # --- Procurement_Priority_Class: positional Top10/20/30/rest ---
    n = len(out)
    out["Procurement_Priority_Class"] = [priority_class_for_position(i, n) for i in range(n)]

    # --- Step 15: CALIBRATED Service Risk Reduction Score (SRRS) ---
    # SRRS = Criticality_Weight * Service_Factor * Positive_Gap
    # Demand_Factor and Lead_Time_Factor were removed from the objective (STEP14 audit:
    # they re-multiplied demand x lead time already embedded in Inventory_Gap). They are
    # still computed as DIAGNOSTIC columns (retained for backward compatibility / explain).
    mf = out["Forecast_2026_27"].median()
    median_forecast = 0.0 if pd.isna(mf) else float(mf)
    pos_gap = out["Inventory_Gap"].clip(lower=0)
    out["Service_Factor"] = out["Target_Service_Level"].map(service_factor).round(4)
    out["Lead_Time_Factor"] = out["Lead_Time_Months"].map(lead_time_factor).round(4)      # diagnostic only
    out["Demand_Factor"] = out["Forecast_2026_27"].map(
        lambda f: demand_factor(f, median_forecast)).round(4)                              # diagnostic only
    out["Positive_Gap"] = pos_gap.round(2)
    out["Service_Risk_Reduction_Score"] = (
        out["Criticality_Weight"] * out["Service_Factor"] * pos_gap).round(4)
    # positional SRRS priority class (same Top10/20/30/rest thresholds)
    srrs_ranked = out.sort_values(
        "Service_Risk_Reduction_Score", ascending=False).reset_index(drop=True)
    srrs_ranked["Service_Risk_Priority_Class"] = [
        priority_class_for_position(i, n) for i in range(n)]
    out = out.merge(srrs_ranked[["PL_Code", "Service_Risk_Priority_Class"]],
                    on="PL_Code", how="left")

    # ---- explainability columns (Step 15; additive) ----
    out["SRRS_Rank"] = out["Service_Risk_Reduction_Score"].rank(
        ascending=False, method="first").astype(int)
    inv = out["Inventory_Investment_Required"].replace(0, np.nan)
    out["SRRS_Per_Rupee"] = (out["Service_Risk_Reduction_Score"] / inv).round(6).fillna(0.0)
    # Funding_Driver: which of Criticality / Service_Level / Gap deviates most (log) above
    # its median among procurement-required items -- the dominant reason for the score.
    pr = pos_gap > 0
    med_cw = float(out.loc[pr, "Criticality_Weight"].median() or 1.0)
    med_sf = float(out.loc[pr, "Service_Factor"].median() or 1.0)
    med_gap = float(pos_gap[pr].median() or 1.0)

    def _driver(cw, sf, g):
        if g <= 0:
            return "None"
        cand_d = {
            "Criticality": np.log(cw / med_cw) if med_cw > 0 else 0.0,
            "Service_Level": np.log(sf / med_sf) if med_sf > 0 else 0.0,
            "Gap": np.log(g / med_gap) if med_gap > 0 else 0.0,
        }
        return max(cand_d, key=cand_d.get)

    out["Funding_Driver"] = [
        _driver(cw, sf, g) for cw, sf, g in
        zip(out["Criticality_Weight"], out["Service_Factor"], pos_gap)]

    policy = out[POLICY_FIELDS].copy()
    if write:
        cfg.ensure_output_dirs()
        policy.to_csv(cfg.INVENTORY_POLICY_CSV, index=False)
    # keep inventory value alongside for matrix/concentration (not in policy CSV)
    out._inv_value_attached = True
    return out


# ----------------------------------------------------------------------
# ABC x Criticality matrix
# ----------------------------------------------------------------------
def build_abc_criticality_matrix(opt: pd.DataFrame, write: bool = True) -> pd.DataFrame:
    recs = []
    for abc in cfg.ABC_ORDER:
        for crit in cfg.CRITICALITY_ORDER:
            cell = opt[(opt["ABC_Class"] == abc) & (opt["Criticality"] == crit)]
            recs.append({
                "ABC_Class": abc, "Criticality": crit,
                "Count": int(len(cell)),
                "Inventory_Value": round(float(cell["_Inventory_Value"].sum()), 2),
                "Inventory_Gap": round(float(cell["Inventory_Gap"].clip(lower=0).sum()), 2),
                "Inventory_Investment_Required": round(float(cell["Inventory_Investment_Required"].sum()), 2),
            })
    matrix = pd.DataFrame(recs)
    if write:
        cfg.ensure_output_dirs()
        matrix.to_csv(cfg.OUTPUT_DIR / "railway_abc_criticality_matrix.csv", index=False)
    return matrix


# ----------------------------------------------------------------------
# Knapsack helpers (PuLP) + Safety Reserve  (Step 15)
# ----------------------------------------------------------------------
def _solve_knapsack(frame: pd.DataFrame, budget: float,
                    score_col: str, cost_col: str) -> set:
    """Binary knapsack: maximise Σ score s.t. Σ cost <= budget. Returns selected
    frame-index labels. Items costing more than the budget are skipped."""
    import pulp
    aff = [i for i in frame.index if float(frame.loc[i, cost_col]) <= budget]
    if not aff or budget <= 0:
        return set()
    prob = pulp.LpProblem("alloc", pulp.LpMaximize)
    x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in aff}
    prob += pulp.lpSum(float(frame.loc[i, score_col]) * x[i] for i in aff)
    prob += pulp.lpSum(float(frame.loc[i, cost_col]) * x[i] for i in aff) <= budget
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return set(i for i in aff if x[i].value() == 1)


def allocate_with_reserve(frame: pd.DataFrame, budget: float,
                          score_col: str, cost_col: str,
                          crit_col: str = "Criticality", return_stages: bool = False):
    """Two-stage allocation (Step 15 Safety Reserve).

    Stage 1 funds high-consequence INSURANCE spares (criticality in
    cfg.SAFETY_RESERVE_CRITICALITIES) from a reserved share
    (cfg.SAFETY_RESERVE_BUDGET_PCT) of the budget. Stage 2 optimises the remaining
    budget across every still-unfunded item. The reserve is a FLOOR, not a cap:
    insurance spares can also win stage-2 funding. When the reserve is disabled this
    reduces to a single knapsack identical to the legacy behaviour.

    Returns the selected index set. The selection is UNCHANGED by `return_stages`;
    when it is True the function additionally returns the stage-1 (reserve-funded)
    subset for read-only explainability -- it never alters the allocation."""
    if not cfg.SAFETY_RESERVE_ENABLED or cfg.SAFETY_RESERVE_BUDGET_PCT <= 0:
        sel = _solve_knapsack(frame, budget, score_col, cost_col)
        return (sel, set()) if return_stages else sel
    reserve = cfg.SAFETY_RESERVE_BUDGET_PCT * budget
    insurance = frame[frame[crit_col].isin(cfg.SAFETY_RESERVE_CRITICALITIES)]
    sel1 = _solve_knapsack(insurance, reserve, score_col, cost_col)
    spent1 = float(frame.loc[list(sel1), cost_col].sum()) if sel1 else 0.0
    rest = frame.drop(index=list(sel1))
    sel2 = _solve_knapsack(rest, budget - spent1, score_col, cost_col)
    sel = sel1 | sel2
    return (sel, sel1) if return_stages else sel


# ----------------------------------------------------------------------
# Rs 1 crore procurement allocation  (PuLP knapsack -- reuses nb05 pattern)
# ----------------------------------------------------------------------
def allocate_procurement_budget(opt: pd.DataFrame, budget: float = PROCUREMENT_BUDGET,
                                write: bool = True):
    """Select procurement-required items to maximise total SERVICE-RISK REDUCTION
    (Service_Risk_Reduction_Score) funded, subject to total investment <= budget.

    Step 13: objective is SRRS (cost-free); Unit_Cost only in the budget constraint.
    Step 15: a configurable Safety Reserve funds S1/S2 insurance spares first."""
    cand = opt[opt["Inventory_Status"] == "Procurement Required"].copy()
    cand = cand[cand["Inventory_Investment_Required"] <= budget]   # singly-affordable
    cand = cand.reset_index(drop=True)

    sel = sorted(allocate_with_reserve(
        cand, budget, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
    plan = cand.loc[sel, ["PL_Code", "Description", "ABC_Class", "Criticality",
                          "Inventory_Gap", "Inventory_Investment_Required",
                          "Service_Risk_Reduction_Score", "Procurement_Priority_Score"]] \
        .sort_values("Service_Risk_Reduction_Score", ascending=False).reset_index(drop=True)
    if write and not plan.empty:
        cfg.ensure_output_dirs()
        plan.to_csv(cfg.OUTPUT_DIR / "railway_procurement_plan.csv", index=False)
    return plan, float(plan["Inventory_Investment_Required"].sum()) if not plan.empty else 0.0


# ----------------------------------------------------------------------
# STEP35-OPT (Phase B): budget frontier -- solve the EXISTING knapsack
# repeatedly across budget levels. Reuses allocate_with_reserve; no new
# optimization logic, no change to objective/constraints/reserve.
# ----------------------------------------------------------------------
def solve_budget_frontier(opt: pd.DataFrame, budgets=None, write: bool = True):
    """For each budget level solve the existing Safety-Reserve knapsack and report
    funded PLs, SRRS mitigated/remaining, risk-reduction %, capital used and the
    marginal SRRS per rupee vs the previous level. Returns a DataFrame."""
    if budgets is None:
        budgets = cfg.FRONTIER_BUDGETS
    cand = opt[opt["Inventory_Status"] == "Procurement Required"].copy().reset_index(drop=True)
    total_srrs = float(cand["Service_Risk_Reduction_Score"].sum())
    all_in = float(cand["Inventory_Investment_Required"].sum()) + 1.0  # finite cap for "Unlimited"
    rows = []
    prev_srrs = 0.0
    prev_spent = 0.0
    for label, rupees in budgets:
        eff = all_in if math.isinf(rupees) else rupees   # never feed inf to PuLP
        sel = sorted(allocate_with_reserve(
            cand, eff, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
        funded = cand.loc[sel]
        srrs = float(funded["Service_Risk_Reduction_Score"].sum())
        spent = float(funded["Inventory_Investment_Required"].sum())
        crit_funded = int(funded["Criticality"].isin(cfg.SAFETY_RESERVE_CRITICALITIES).sum())
        d_srrs = srrs - prev_srrs
        d_spent = spent - prev_spent
        marginal = (d_srrs / d_spent) if d_spent > 1e-9 else 0.0
        rows.append({
            "Budget_Label": label,
            "Budget_Rupees": (None if math.isinf(rupees) else round(rupees, 2)),
            "PLs_Funded": int(len(funded)),
            "Critical_PLs_Funded": crit_funded,
            "SRRS_Mitigated": round(srrs, 4),
            "SRRS_Remaining": round(total_srrs - srrs, 4),
            "Risk_Reduction_Pct": round((srrs / total_srrs * 100.0) if total_srrs > 0 else 0.0, 4),
            "Budget_Utilized": round(spent, 2),
            "Marginal_SRRS_Per_Rupee": round(marginal, 8),
        })
        prev_srrs, prev_spent = srrs, spent
    frame = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        frame.to_csv(cfg.OUTPUT_DIR / "risk_reduction_frontier.csv", index=False)
    return frame


# ----------------------------------------------------------------------
# STEP35-OPT (Phase D): enterprise capital allocation -- pool every
# division's procurement-required candidates into ONE frame and solve the
# EXISTING Safety-Reserve knapsack once at the enterprise budget.
# ----------------------------------------------------------------------
def enterprise_capital_allocation(division_frames: dict, budget: float,
                                  write: bool = True):
    """division_frames: {division: DataFrame of procurement-required candidates}.
    Returns a per-division allocation DataFrame for the given enterprise budget."""
    pooled = []
    for div, df in division_frames.items():
        d = df[df["Inventory_Status"] == "Procurement Required"].copy()
        d["Division"] = div
        pooled.append(d)
    if not pooled:
        return pd.DataFrame(columns=["Division", "Allocated_Budget", "PLs_Funded",
                                     "SRRS_Mitigated", "Risk_Reduction_Pct", "Capital_Efficiency"])
    pool = pd.concat(pooled, ignore_index=True)
    total_by_div = pool.groupby("Division")["Service_Risk_Reduction_Score"].sum()

    eff = budget
    if math.isinf(budget):                       # never feed inf to PuLP
        eff = float(pool["Inventory_Investment_Required"].sum()) + 1.0
    sel = sorted(allocate_with_reserve(
        pool, eff, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
    funded = pool.loc[sel]

    rows = []
    for div in sorted(division_frames):
        f = funded[funded["Division"] == div]
        spent = float(f["Inventory_Investment_Required"].sum())
        srrs = float(f["Service_Risk_Reduction_Score"].sum())
        tot = float(total_by_div.get(div, 0.0))
        rows.append({
            "Division": div,
            "Allocated_Budget": round(spent, 2),
            "PLs_Funded": int(len(f)),
            "SRRS_Mitigated": round(srrs, 4),
            "Risk_Reduction_Pct": round((srrs / tot * 100.0) if tot > 0 else 0.0, 4),
            "Capital_Efficiency": round((srrs / spent) if spent > 1e-9 else 0.0, 8),
        })
    alloc = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        alloc.to_csv(cfg.OUTPUT_DIR / "enterprise_budget_allocation.csv", index=False)
    return alloc


# ----------------------------------------------------------------------
# STEP35-OPT (Phase E): multi-year procurement roadmap. Each year runs the
# EXISTING Safety-Reserve knapsack on the still-unfunded procurement-required
# items under that year's budget; unfunded items carry to the next year.
# ----------------------------------------------------------------------
def procurement_roadmap(opt: pd.DataFrame, annual_budget=None, years=None,
                        write: bool = True):
    """annual_budget None => total procurement requirement / len(years) (equal thirds)."""
    if years is None:
        years = cfg.ROADMAP_YEARS
    cand = opt[opt["Inventory_Status"] == "Procurement Required"].copy().reset_index(drop=True)
    total_srrs = float(cand["Service_Risk_Reduction_Score"].sum())
    total_req = float(cand["Inventory_Investment_Required"].sum())
    if annual_budget is None:
        annual_budget = total_req / len(years) if years else 0.0

    remaining = cand.copy()
    cum_srrs = 0.0
    cum_cap = 0.0
    rows = []
    for yr in years:
        rem = remaining.reset_index(drop=True)
        sel = sorted(allocate_with_reserve(
            rem, annual_budget, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
        funded = rem.loc[sel]
        cap = float(funded["Inventory_Investment_Required"].sum())
        cum_cap += cap
        cum_srrs += float(funded["Service_Risk_Reduction_Score"].sum())
        rows.append({
            "Year": yr,
            "Annual_Budget": round(annual_budget, 2),
            "Items_Funded": int(len(funded)),
            "Capital_Required": round(cap, 2),
            "Cumulative_Risk_Reduction_Pct": round((cum_srrs / total_srrs * 100.0) if total_srrs > 0 else 0.0, 4),
            "Remaining_Exposure": round(total_req - cum_cap, 2),
        })
        remaining = remaining[~remaining["PL_Code"].isin(set(funded["PL_Code"]))]
    rm = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        rm.to_csv(cfg.OUTPUT_DIR / "procurement_roadmap.csv", index=False)
    return rm


# ----------------------------------------------------------------------
# Validation / reporting
# ----------------------------------------------------------------------
def run():
    opt = build_inventory_policy(write=True)
    matrix = build_abc_criticality_matrix(opt, write=True)
    policy = opt[POLICY_FIELDS]

    # validation gate
    gate = {
        "no_negative_safety_stock": bool((policy["Safety_Stock"] >= 0).all()),
        "no_negative_rop": bool((policy["ROP"] >= 0).all()),
        "no_duplicate_pl": bool(policy["PL_Code"].is_unique),
        "no_nan_investment": bool(policy["Inventory_Investment_Required"].notna().all()),
        "no_negative_priority": bool((policy["Procurement_Priority_Score"] >= 0).all()),
    }

    print("=" * 78)
    print("STEP 5 VALIDATION REPORT  -- railway_inventory_policy.csv")
    print("=" * 78)
    # 1. Inventory status
    print("\n1. Inventory Status Distribution:", policy["Inventory_Status"].value_counts().to_dict())
    # 2. Criticality of procurement-required
    pr = policy[policy["Inventory_Status"] == "Procurement Required"]
    print("2. Criticality of Procurement-Required:",
          pr["Criticality"].value_counts().reindex(cfg.CRITICALITY_ORDER, fill_value=0).to_dict())

    # 3. Top 20 procurement-required by priority
    print("\n3. Top 20 Procurement-Required (by Procurement_Priority_Score):")
    c = ["PL_Code", "Description", "ABC_Class", "Criticality", "Current_Stock",
         "ROP", "Inventory_Gap", "Inventory_Investment_Required", "Procurement_Priority_Score"]
    with pd.option_context("display.width", 240, "display.max_columns", 30):
        print(pr.sort_values("Procurement_Priority_Score", ascending=False).head(20)[c].to_string(index=False))

    # 4. Top 10 inventory value
    print("\n4. Top 10 Inventory Value Items:")
    inv = opt[["PL_Code", "Description", "_Inventory_Value"]].rename(columns={"_Inventory_Value": "Inventory_Value"})
    print(inv.sort_values("Inventory_Value", ascending=False).head(10).to_string(index=False))

    # 5. Top 10 investment required
    print("\n5. Top 10 Inventory Investment Required Items:")
    print(policy.sort_values("Inventory_Investment_Required", ascending=False)
          .head(10)[["PL_Code", "Description", "Inventory_Investment_Required"]].to_string(index=False))

    # 6. Capital requirement summary
    total_inv = float(policy["Inventory_Investment_Required"].sum())
    by_crit = policy.groupby("Criticality")["Inventory_Investment_Required"].sum() \
        .reindex(cfg.CRITICALITY_ORDER, fill_value=0)
    print("\n6. Capital Requirement Summary:")
    print(f"   Total Inventory Investment Required: Rs {total_inv:,.0f}")
    for cr in cfg.CRITICALITY_ORDER:
        print(f"      {cr}: Rs {by_crit[cr]:,.0f}")

    # 7. ABC x Criticality matrix
    print("\n7. ABC x Criticality Matrix (Count | Investment Rs):")
    piv_n = matrix.pivot(index="ABC_Class", columns="Criticality", values="Count").reindex(cfg.ABC_ORDER)[cfg.CRITICALITY_ORDER]
    piv_i = matrix.pivot(index="ABC_Class", columns="Criticality", values="Inventory_Investment_Required").reindex(cfg.ABC_ORDER)[cfg.CRITICALITY_ORDER]
    print("   Counts:\n", piv_n.fillna(0).astype(int).to_string())
    print("   Investment (Rs):\n", piv_i.fillna(0).round(0).astype('int64').to_string())

    # 8. Concentration index
    inv_sorted = inv.sort_values("Inventory_Value", ascending=False)
    total_value = float(inv_sorted["Inventory_Value"].sum())
    top10_value = float(inv_sorted.head(10)["Inventory_Value"].sum())
    conc = (top10_value / total_value * 100.0) if total_value > 0 else 0.0
    level = "Low" if conc < 40 else ("Medium" if conc < 70 else "High")
    print(f"\n8. Inventory Concentration Index (Top 10 SKUs / Total): {conc:.1f}%  -> {level} concentration")

    # Q5: Rs 1 crore budget allocation
    plan, spent = allocate_procurement_budget(opt, write=True)
    print(f"\nQ5. Rs 1 crore procurement plan: {len(plan)} items, Rs {spent:,.0f} allocated "
          f"({spent/PROCUREMENT_BUDGET*100:.1f}% of budget). Top 8:")
    if not plan.empty:
        print(plan.head(8).to_string(index=False))

    print("\n" + "-" * 78)
    print("VALIDATION GATE:")
    for k, v in gate.items():
        print(f"   {k:28s}: {v}")
    gate["csv_written"] = cfg.INVENTORY_POLICY_CSV.exists()
    all_pass = all(gate.values())
    print(f"   {'csv_written':28s}: {gate['csv_written']}")
    print(f"   ALL PASS: {all_pass}")
    print("=" * 78)
    print(f"Wrote: {cfg.INVENTORY_POLICY_CSV}")
    return policy, gate


if __name__ == "__main__":
    run()
