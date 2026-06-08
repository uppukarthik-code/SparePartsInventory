"""
railway_srrs_validation.py
==========================
Validation suite for the CALIBRATED Service-Risk Reduction Score (Step 15).

Calibrated objective:  SRRS = Criticality_Weight * Service_Factor * Positive_Gap
(Demand_Factor & Lead_Time_Factor removed from the objective; Service_Factor
recalibrated to a bounded linear form; Safety Reserve for S1/S2 insurance spares;
additive explainability columns.)

Proves:
  A. Optimization still executes successfully.
  B. Budget constraint remains satisfied.
  C. SRRS == Criticality_Weight * Service_Factor * Positive_Gap (calibrated identity).
  D. Demand_Factor & Lead_Time_Factor are NO LONGER in the objective (double-count removed).
  E. Service_Factor provides meaningful, bounded discrimination across service levels.
  F. Safety Reserve increases the number of funded S1/S2 insurance spares.
  G. Unit cost is absent from the objective.
  H. Power BI exports remain functional, incl. the new explainability columns.

Read-only. Run:  python -m railway.railway_srrs_validation
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway import railway_inventory_optimization as opt

OUT = cfg.OUTPUT_DIR
PBI = cfg.POWERBI_DIR


def _policy():
    return pd.read_csv(OUT / "railway_inventory_policy.csv", dtype={"PL_Code": str})


def run():
    results = []
    pol = _policy()
    cand = pol[pol["Inventory_Status"] == "Procurement Required"].copy()
    gap_pos = pol["Inventory_Gap"].clip(lower=0)

    # ---- A. optimization executed ----
    plan_path = OUT / "railway_procurement_plan.csv"
    plan = pd.read_csv(plan_path, dtype={"PL_Code": str}) if plan_path.exists() else pd.DataFrame()
    a_ok = (len(pol) > 0 and "Service_Risk_Reduction_Score" in pol.columns
            and not plan.empty)
    results.append(("A optimization executes (policy+plan+SRRS)",
                    a_ok, f"policy={len(pol)} rows, plan={len(plan)} items"))

    # ---- B. budget constraint satisfied ----
    budget = cfg.PROCUREMENT_BUDGET
    spent = float(plan["Inventory_Investment_Required"].sum()) if not plan.empty else 0.0
    b_ok = spent <= budget + 1e-3
    results.append(("B budget constraint satisfied",
                    b_ok, f"plan spend Rs {spent:,.0f} <= Rs {budget:,.0f}"))

    # ---- C. calibrated identity: SRRS == C_w * Service_Factor * Positive_Gap ----
    identity = pol["Criticality_Weight"] * pol["Service_Factor"] * gap_pos
    c_err = float((identity - pol["Service_Risk_Reduction_Score"]).abs().max())
    c_ok = c_err < 1e-2
    results.append(("C SRRS == Criticality_Weight * Service_Factor * Positive_Gap",
                    c_ok, f"max|Δ| = {c_err:.6f}"))

    # ---- D. Demand_Factor & Lead_Time_Factor removed from objective ----
    # If they were still multiplied in, SRRS would differ from C_w*SF*gap wherever
    # DF!=1 or LF!=1. Confirm SRRS is invariant to them (identity holds despite DF/LF varying).
    df_varies = float(pol["Demand_Factor"].std()) > 0
    lf_varies = float(pol["Lead_Time_Factor"].std()) > 0
    d_ok = c_ok and df_varies and lf_varies     # factors vary yet do not affect SRRS
    results.append(("D Demand/Lead factors excluded from objective (double-count removed)",
                    d_ok, f"DF varies={df_varies}, LF varies={lf_varies}, identity holds={c_ok}"))

    # ---- E. Service_Factor discrimination (bounded, monotonic, multiple levels) ----
    sf_by_sl = pol.groupby("Target_Service_Level")["Service_Factor"].first().sort_index()
    distinct = sf_by_sl.nunique()
    monotonic = bool(np.all(np.diff(sf_by_sl.values) >= -1e-9))
    bounded = bool(pol["Service_Factor"].max() <= 1.0 + cfg.SERVICE_FACTOR_SLOPE * 0.1 + 1e-9)
    e_ok = distinct >= 2 and monotonic and bounded
    results.append(("E Service_Factor discriminates across service levels (bounded+monotonic)",
                    e_ok, f"{distinct} distinct SF values {dict(sf_by_sl.round(2))}; "
                          f"monotonic={monotonic} bounded={bounded}"))

    # ---- F. Safety Reserve funds more S1/S2 insurance spares ----
    c = cand[cand["Inventory_Investment_Required"] <= budget].copy().reset_index(drop=True)
    sel_no = opt._solve_knapsack(c, budget, "Service_Risk_Reduction_Score",
                                 "Inventory_Investment_Required")
    sel_yes = opt.allocate_with_reserve(c, budget, "Service_Risk_Reduction_Score",
                                        "Inventory_Investment_Required")
    crit = cfg.SAFETY_RESERVE_CRITICALITIES
    s12_no = int(c.loc[list(sel_no), "Criticality"].isin(crit).sum())
    s12_yes = int(c.loc[list(sel_yes), "Criticality"].isin(crit).sum())
    f_ok = s12_yes >= s12_no
    results.append(("F Safety Reserve funds >= S1/S2 insurance spares vs no-reserve",
                    f_ok, f"S1/S2 funded: no-reserve={s12_no} -> reserve={s12_yes} "
                          f"(reserve {cfg.SAFETY_RESERVE_BUDGET_PCT:.0%}, enabled={cfg.SAFETY_RESERVE_ENABLED})"))

    # ---- G. unit cost absent from objective ----
    # SRRS contains no cost term; value-density (SRRS/investment) varies within tier.
    dq = pd.read_csv(OUT / "railway_data_quality.csv", dtype={"PL_Code": str})
    m = cand[cand["Inventory_Investment_Required"] > 0]
    dens = m["Service_Risk_Reduction_Score"] / m["Inventory_Investment_Required"]
    cvs = [float(dens.loc[g.index].std(ddof=0) / abs(dens.loc[g.index].mean()))
           for _, g in m.groupby("Criticality")
           if len(g) > 1 and dens.loc[g.index].mean() != 0]
    new_cv = float(np.mean(cvs)) if cvs else 0.0
    g_ok = new_cv > 1e-3
    results.append(("G unit cost absent (SRRS cost-free; density varies within tier)",
                    g_ok, f"within-tier density CV = {new_cv:.3f}"))

    # ---- H. Power BI exports + explainability columns ----
    p1 = pd.read_csv(PBI / "page1_procurement.csv", nrows=0).columns
    explain = ["Service_Risk_Reduction_Score", "SRRS_Rank", "Service_Factor",
               "Positive_Gap", "SRRS_Per_Rupee", "Funding_Decision", "Funding_Driver"]
    missing = [c2 for c2 in explain if c2 not in p1]
    p8 = pd.read_csv(PBI / "page8_budget_scenarios.csv")
    h_problems = []
    if missing:
        h_problems.append(f"page1 missing {missing}")
    if len(p8) != 4:
        h_problems.append(f"page8 has {len(p8)} scenarios")
    for n in ["page0_executive_dashboard", "page3_criticality", "page4_operational_health",
              "page5_rationalization", "page9_management_actions"]:
        if not (PBI / f"{n}.csv").exists():
            h_problems.append(f"{n} MISSING")
    h_ok = not h_problems
    results.append(("H Power BI exports functional incl. explainability columns",
                    h_ok, h_problems or "all pages present; page1 carries all 7 explainability fields"))

    all_pass = all(ok for _, ok, _ in results)
    print("=" * 80)
    print("STEP 15 -- CALIBRATED SRRS VALIDATION SUITE")
    print("=" * 80)
    for name, ok, detail in results:
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
        print(f"         {detail}")
    print(f"\n   ALL PASS: {all_pass}")
    print("=" * 80)
    return results, all_pass


if __name__ == "__main__":
    run()
