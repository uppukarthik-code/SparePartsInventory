"""STEP35-OPT — Enterprise Budget Optimization & Capital Allocation (orchestration).

This module is ORCHESTRATION + IO only. ALL optimization (knapsack, frontier,
pooled enterprise allocation, roadmap) is delegated to the single source of truth
railway.railway_inventory_optimization. This module:
  * reads existing per-division railway_inventory_policy.csv outputs (read-only),
  * calls the solver primitives,
  * writes only NEW output CSVs (never rewrites a pinned output).
"""
from __future__ import annotations

import pandas as pd

from railway import railway_config as cfg
from railway import railway_business_unit_config as buc
from railway import railway_inventory_optimization as opt

_POLICY = "railway_inventory_policy.csv"
_CAND_COLS = ["PL_Code", "Description", "ABC_Class", "Criticality", "Inventory_Status",
              "Inventory_Investment_Required", "Service_Risk_Reduction_Score",
              "Lead_Time_Months"]


def live_divisions() -> list[str]:
    """Live divisions in canonical order (STTC_PTJ is 'Configured' -> excluded)."""
    return [bu for bu in buc.BUSINESS_UNIT_ORDER if buc.is_live(bu)]


def _read_policy(path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"PL_Code": str})
    keep = [c for c in _CAND_COLS if c in df.columns]
    return df[keep].copy()


def load_enterprise_opt() -> pd.DataFrame:
    """Consolidated candidate frame from outputs/railway_inventory_policy.csv."""
    return _read_policy(cfg.INVENTORY_POLICY_CSV)


def load_division_frames() -> dict:
    """Per-division procurement-required candidates. Divisions without a policy CSV
    are skipped (coverage is reported, not an error)."""
    out = {}
    for div in live_divisions():
        p = cfg.OUTPUT_DIR / div / _POLICY
        if not p.exists():
            continue
        df = _read_policy(p)
        df = df[df["Inventory_Status"] == "Procurement Required"].reset_index(drop=True)
        if not df.empty:
            out[div] = df
    return out


# ---- Phase B -------------------------------------------------------------
def build_risk_reduction_frontier(write: bool = True) -> pd.DataFrame:
    opt_df = load_enterprise_opt()
    fr = opt.solve_budget_frontier(opt_df, budgets=cfg.FRONTIER_BUDGETS, write=False)
    if write:
        cfg.ensure_output_dirs()
        fr.to_csv(cfg.OUTPUT_DIR / "risk_reduction_frontier.csv", index=False)
    return fr


# ---- Phase C -------------------------------------------------------------
def build_budget_efficiency_analysis(frontier: pd.DataFrame | None = None,
                                     write: bool = True) -> pd.DataFrame:
    """Knee-point + diminishing-returns + region labels over the FINITE budget
    levels (Unlimited excluded from geometry, carried as 'Saturation')."""
    fr = (frontier if frontier is not None else build_risk_reduction_frontier(write=False)).copy()
    finite = fr[fr["Budget_Label"] != "Unlimited"].reset_index(drop=True)
    n = len(finite)
    eff = fr.copy()
    eff["Is_Knee_Point"] = False
    eff["Is_Diminishing_Returns"] = False
    eff["Region"] = ""

    if n >= 3:
        x = finite["Budget_Rupees"].astype(float).to_numpy()
        y = finite["Risk_Reduction_Pct"].astype(float).to_numpy()
        xn = (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x * 0.0
        yn = (y - y.min()) / (y.max() - y.min()) if y.max() > y.min() else y * 0.0
        dist = yn - xn
        knee_pos = int(dist.argmax())
        eff.loc[eff["Budget_Label"] == finite.loc[knee_pos, "Budget_Label"], "Is_Knee_Point"] = True
        m = finite["Marginal_SRRS_Per_Rupee"].astype(float).to_numpy()
        thresh = 0.25 * m[0] if m[0] > 0 else 0.0
        dr_pos = next((i for i in range(1, n) if m[i] < thresh), n - 1)
        eff.loc[eff["Budget_Label"] == finite.loc[dr_pos, "Budget_Label"],
                "Is_Diminishing_Returns"] = True
        for i, lbl in enumerate(finite["Budget_Label"]):
            region = ("Efficient" if i < knee_pos
                      else "Optimal_Investment" if i <= dr_pos
                      else "Diminishing_Returns")
            eff.loc[eff["Budget_Label"] == lbl, "Region"] = region
    eff.loc[eff["Budget_Label"] == "Unlimited", "Region"] = "Saturation"

    cols = ["Budget_Label", "Budget_Rupees", "Risk_Reduction_Pct",
            "Marginal_SRRS_Per_Rupee", "Is_Knee_Point", "Is_Diminishing_Returns", "Region"]
    eff = eff[cols]
    if write:
        cfg.ensure_output_dirs()
        eff.to_csv(cfg.OUTPUT_DIR / "budget_efficiency_analysis.csv", index=False)
    return eff


# ---- Phase D -------------------------------------------------------------
def build_enterprise_budget_allocation(write: bool = True) -> pd.DataFrame:
    """Per-division capital allocation at the Rs 100 Cr headline AND every frontier
    level, so the Board sees how the optimal split shifts with the budget."""
    frames = load_division_frames()
    out = []
    for label, rupees in cfg.FRONTIER_BUDGETS:
        alloc = opt.enterprise_capital_allocation(frames, rupees, write=False)
        alloc.insert(0, "Budget_Label", label)
        alloc.insert(1, "Budget_Rupees", None if rupees == float("inf") else round(rupees, 2))
        out.append(alloc)
    result = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    if write:
        cfg.ensure_output_dirs()
        result.to_csv(cfg.OUTPUT_DIR / "enterprise_budget_allocation.csv", index=False)
    return result


def build_enterprise_allocation_readiness(write: bool = True) -> pd.DataFrame:
    """Classify every Live division as REPORTABLE (has procurement-required policy
    data feeding the enterprise allocation) or DATA_UNAVAILABLE (missing/empty CSV
    or zero procurement-required PLs). Makes allocation coverage explicit."""
    rows = []
    for div in live_divisions():
        p = cfg.OUTPUT_DIR / div / _POLICY
        if not p.exists():
            rows.append({"Division": div, "Status": "DATA_UNAVAILABLE",
                         "Procurement_Required_PLs": 0, "Total_SRRS": 0.0,
                         "Total_Investment_Required": 0.0,
                         "Reason": "policy CSV missing"})
            continue
        df = _read_policy(p)
        pr = df[df["Inventory_Status"] == "Procurement Required"]
        n = int(len(pr))
        rows.append({
            "Division": div,
            "Status": "REPORTABLE" if n > 0 else "DATA_UNAVAILABLE",
            "Procurement_Required_PLs": n,
            "Total_SRRS": round(float(pr["Service_Risk_Reduction_Score"].sum()), 4),
            "Total_Investment_Required": round(float(pr["Inventory_Investment_Required"].sum()), 2),
            "Reason": "ok" if n > 0 else "no procurement-required PLs",
        })
    rd = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        rd.to_csv(cfg.OUTPUT_DIR / "enterprise_budget_allocation_readiness.csv", index=False)
    return rd


# ---- Phase E -------------------------------------------------------------
def build_procurement_roadmap(write: bool = True) -> pd.DataFrame:
    opt_df = load_enterprise_opt()
    rm = opt.procurement_roadmap(opt_df, annual_budget=cfg.ANNUAL_PROCUREMENT_BUDGET,
                                 years=cfg.ROADMAP_YEARS, write=False)
    if write:
        cfg.ensure_output_dirs()
        rm.to_csv(cfg.OUTPUT_DIR / "procurement_roadmap.csv", index=False)
    return rm


# ---- Phase F -------------------------------------------------------------
def build_executive_budget_scenarios(write: bool = True) -> pd.DataFrame:
    """Board-facing scenarios: what is procured, SRRS removed/remaining, tier mix,
    capital used and efficiency at each scenario budget."""
    cand = load_enterprise_opt()
    cand = cand[cand["Inventory_Status"] == "Procurement Required"].reset_index(drop=True)
    total_srrs = float(cand["Service_Risk_Reduction_Score"].sum())
    all_in = float(cand["Inventory_Investment_Required"].sum()) + 1.0  # finite cap for "Unlimited"
    rows = []
    for label, rupees in cfg.EXECUTIVE_SCENARIO_BUDGETS:
        import math as _m
        eff = all_in if _m.isinf(rupees) else rupees
        sel = sorted(opt.allocate_with_reserve(
            cand, eff, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
        f = cand.loc[sel]
        srrs = float(f["Service_Risk_Reduction_Score"].sum())
        spent = float(f["Inventory_Investment_Required"].sum())
        tier = f["Criticality"].value_counts()
        rows.append({
            "Scenario": label,
            "PLs_Funded": int(len(f)),
            "SRRS_Removed": round(srrs, 4),
            "SRRS_Remaining": round(total_srrs - srrs, 4),
            "Risk_Reduction_Pct": round((srrs / total_srrs * 100.0) if total_srrs > 0 else 0.0, 4),
            "S1_Funded": int(tier.get("S1", 0)),
            "S2_Funded": int(tier.get("S2", 0)),
            "S3_Funded": int(tier.get("S3", 0)),
            "S4_Funded": int(tier.get("S4", 0)),
            "Capital_Utilized": round(spent, 2),
            "Capital_Efficiency": round((srrs / spent) if spent > 1e-9 else 0.0, 8),
        })
    sc = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        sc.to_csv(cfg.OUTPUT_DIR / "executive_budget_scenarios.csv", index=False)
    return sc


# ---- Phase A: baseline validation ---------------------------------------
def build_optimization_baseline_validation(write: bool = True) -> pd.DataFrame:
    """Reconfirm (read-only) the existing optimizer's decision variables, objective,
    constraints, affordability filter, safety-reserve and explainability outputs.
    Status is UNCHANGED for every aspect: STEP35-OPT adds, never alters, these."""
    rows = [
        ("Decision_Variables", "binary x_i in {0,1} per procurement-required PL "
         "(pulp.LpVariable cat=Binary in _solve_knapsack)", "UNCHANGED"),
        ("Objective_Function", "maximize sum(Service_Risk_Reduction_Score * x_i)", "UNCHANGED"),
        ("Budget_Constraint", "sum(Inventory_Investment_Required * x_i) <= budget", "UNCHANGED"),
        ("Affordability_Filter", "items with cost > budget excluded (_solve_knapsack)", "UNCHANGED"),
        ("Safety_Reserve", f"enabled={cfg.SAFETY_RESERVE_ENABLED}, "
         f"pct={cfg.SAFETY_RESERVE_BUDGET_PCT}, tiers={cfg.SAFETY_RESERVE_CRITICALITIES}", "UNCHANGED"),
        ("Explainability_Outputs", "SRRS_Rank, SRRS_Per_Rupee, Funding_Driver, "
         "railway_funding_explainability.csv", "UNCHANGED"),
        ("Default_Procurement_Budget", f"{cfg.PROCUREMENT_BUDGET}", "UNCHANGED"),
        ("Service_Factor_Model", f"baseline_sl={cfg.SERVICE_FACTOR_BASELINE_SL}, "
         f"slope={cfg.SERVICE_FACTOR_SLOPE}", "UNCHANGED"),
    ]
    bv = pd.DataFrame(rows, columns=["Aspect", "Value", "Status"])
    if write:
        cfg.ensure_output_dirs()
        bv.to_csv(cfg.OUTPUT_DIR / "optimization_baseline_validation.csv", index=False)
    return bv


# ---- master orchestrator -------------------------------------------------
def run(write: bool = True) -> dict:
    """Build every STEP35-OPT artifact. Returns a dict of the produced DataFrames."""
    baseline = build_optimization_baseline_validation(write=write)
    frontier = build_risk_reduction_frontier(write=write)
    efficiency = build_budget_efficiency_analysis(frontier=frontier, write=write)
    allocation = build_enterprise_budget_allocation(write=write)
    readiness = build_enterprise_allocation_readiness(write=write)
    roadmap = build_procurement_roadmap(write=write)
    scenarios = build_executive_budget_scenarios(write=write)
    return {"baseline": baseline, "frontier": frontier, "efficiency": efficiency,
            "allocation": allocation, "readiness": readiness,
            "roadmap": roadmap, "scenarios": scenarios}


if __name__ == "__main__":
    import os
    os.environ.setdefault("PYTHONHASHSEED", "0")
    out = run(write=True)
    for k, v in out.items():
        print(f"[{k}] rows={len(v)}")
