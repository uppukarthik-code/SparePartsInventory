"""STEP35-OPT: enterprise budget optimization & capital allocation tests."""
import math
import numpy as np
import pandas as pd
import pytest

from railway import railway_config as cfg


def test_step35opt_config_constants_exist():
    labels = [lbl for lbl, _ in cfg.FRONTIER_BUDGETS]
    assert labels == ["Rs 1 Cr", "Rs 5 Cr", "Rs 10 Cr", "Rs 25 Cr",
                      "Rs 50 Cr", "Rs 100 Cr", "Rs 200 Cr", "Rs 500 Cr", "Unlimited"]
    assert cfg.FRONTIER_BUDGETS[0][1] == 1_00_00_000.0
    assert cfg.FRONTIER_BUDGETS[5][1] == 1_00_00_00_000.0
    assert math.isinf(cfg.FRONTIER_BUDGETS[-1][1])
    assert cfg.ENTERPRISE_BUDGET == 1_00_00_00_000.0
    assert cfg.ANNUAL_PROCUREMENT_BUDGET is None
    assert cfg.ROADMAP_YEARS == ["FY2026-27", "FY2027-28", "FY2028-29"]
    assert cfg.RISK_REDUCTION_TARGETS == [0.50, 0.75, 0.90]
    exec_labels = [lbl for lbl, _ in cfg.EXECUTIVE_SCENARIO_BUDGETS]
    assert exec_labels == ["Rs 25 Cr", "Rs 50 Cr", "Rs 100 Cr", "Rs 200 Cr", "Unlimited"]


from railway import railway_inventory_optimization as opt


def _toy_opt():
    return pd.DataFrame({
        "PL_Code": ["P1", "P2", "P3", "P4"],
        "Description": ["a", "b", "c", "d"],
        "ABC_Class": ["A", "A", "B1", "C"],
        "Criticality": ["S1", "S2", "S3", "S4"],
        "Inventory_Status": ["Procurement Required"] * 4,
        "Service_Risk_Reduction_Score": [100.0, 40.0, 30.0, 10.0],
        "Inventory_Investment_Required": [1_00_00_000.0, 50_00_000.0, 30_00_000.0, 10_00_000.0],
    })


def test_frontier_monotonic_and_unlimited_funds_all():
    fr = opt.solve_budget_frontier(_toy_opt(), budgets=cfg.FRONTIER_BUDGETS, write=False)
    rr = fr["Risk_Reduction_Pct"].tolist()
    assert all(b >= a - 1e-9 for a, b in zip(rr, rr[1:]))
    last = fr.iloc[-1]
    assert last["Budget_Label"] == "Unlimited"
    assert last["PLs_Funded"] == 4
    assert abs(last["Risk_Reduction_Pct"] - 100.0) < 1e-6
    for col in ["Budget_Label", "Budget_Rupees", "PLs_Funded", "Critical_PLs_Funded",
                "SRRS_Mitigated", "SRRS_Remaining", "Risk_Reduction_Pct",
                "Budget_Utilized", "Marginal_SRRS_Per_Rupee"]:
        assert col in fr.columns


def test_enterprise_pooled_allocation_respects_budget_and_aggregates():
    frames = {
        "MAS": pd.DataFrame({
            "PL_Code": ["M1", "M2"], "Description": ["m1", "m2"],
            "ABC_Class": ["A", "B1"], "Criticality": ["S1", "S3"],
            "Inventory_Status": ["Procurement Required"] * 2,
            "Service_Risk_Reduction_Score": [90.0, 20.0],
            "Inventory_Investment_Required": [60_00_000.0, 30_00_000.0]}),
        "SA": pd.DataFrame({
            "PL_Code": ["S1x"], "Description": ["s1"],
            "ABC_Class": ["A"], "Criticality": ["S2"],
            "Inventory_Status": ["Procurement Required"],
            "Service_Risk_Reduction_Score": [70.0],
            "Inventory_Investment_Required": [50_00_000.0]}),
    }
    alloc = opt.enterprise_capital_allocation(frames, budget=1_00_00_000.0, write=False)
    assert set(alloc["Division"]) <= {"MAS", "SA"}
    assert alloc["Allocated_Budget"].sum() <= 1_00_00_000.0 + 1e-6
    for col in ["Division", "Allocated_Budget", "PLs_Funded", "SRRS_Mitigated",
                "Risk_Reduction_Pct", "Capital_Efficiency"]:
        assert col in alloc.columns


def test_roadmap_three_years_cumulative_nondecreasing():
    rm = opt.procurement_roadmap(_toy_opt(), annual_budget=60_00_000.0,
                                 years=["FY2026-27", "FY2027-28", "FY2028-29"], write=False)
    assert list(rm["Year"]) == ["FY2026-27", "FY2027-28", "FY2028-29"]
    cum = rm["Cumulative_Risk_Reduction_Pct"].tolist()
    assert all(b >= a - 1e-9 for a, b in zip(cum, cum[1:]))
    assert rm["Items_Funded"].sum() <= 4
    for col in ["Year", "Items_Funded", "Capital_Required",
                "Cumulative_Risk_Reduction_Pct", "Remaining_Exposure"]:
        assert col in rm.columns


def test_enterprise_allocation_empty_input_returns_schema():
    alloc = opt.enterprise_capital_allocation({}, budget=1_00_00_000.0, write=False)
    assert alloc.empty
    assert list(alloc.columns) == ["Division", "Allocated_Budget", "PLs_Funded",
                                   "SRRS_Mitigated", "Risk_Reduction_Pct", "Capital_Efficiency"]


def test_frontier_budget_utilized_within_declared_budget():
    fr = opt.solve_budget_frontier(_toy_opt(), budgets=cfg.FRONTIER_BUDGETS, write=False)
    for _, r in fr.iterrows():
        if r["Budget_Label"] != "Unlimited":
            assert r["Budget_Utilized"] <= float(r["Budget_Rupees"]) + 1e-6


# ---------------------------------------------------------------------------
# STEP35-OPT Cluster 2: enterprise_allocation orchestration module
# ---------------------------------------------------------------------------
from railway.governance import enterprise_allocation as ea
from railway.governance import division_summary as ds  # (used in a later cluster; import-safe)


def test_build_risk_reduction_frontier_from_live_outputs():
    fr = ea.build_risk_reduction_frontier(write=False)
    assert not fr.empty
    assert fr["Risk_Reduction_Pct"].iloc[-1] >= fr["Risk_Reduction_Pct"].iloc[0]
    assert fr["Budget_Label"].iloc[-1] == "Unlimited"


def test_budget_efficiency_knee_within_range():
    eff = ea.build_budget_efficiency_analysis(write=False)
    assert {"Budget_Label", "Risk_Reduction_Pct", "Marginal_SRRS_Per_Rupee",
            "Is_Knee_Point", "Is_Diminishing_Returns", "Region"}.issubset(eff.columns)
    assert int(eff["Is_Knee_Point"].sum()) == 1
    knee_idx = eff.index[eff["Is_Knee_Point"]].tolist()[0]
    assert knee_idx not in (0, len(eff[eff["Budget_Label"] != "Unlimited"]) - 1)


def test_build_enterprise_budget_allocation_has_headline_and_sweep():
    alloc = ea.build_enterprise_budget_allocation(write=False)
    assert "Budget_Label" in alloc.columns and "Division" in alloc.columns
    assert "Rs 100 Cr" in set(alloc["Budget_Label"])
    fin = alloc[alloc["Budget_Label"] != "Unlimited"]
    for lbl, grp in fin.groupby("Budget_Label"):
        cap = dict(cfg.FRONTIER_BUDGETS)[lbl]
        assert grp["Allocated_Budget"].sum() <= cap + 1.0


def test_allocation_readiness_classifies_divisions():
    rd = ea.build_enterprise_allocation_readiness(write=False)
    assert {"Division", "Status", "Procurement_Required_PLs", "Total_SRRS",
            "Total_Investment_Required", "Reason"}.issubset(rd.columns)
    assert sorted(rd["Division"]) == sorted(ea.live_divisions())
    assert set(rd["Status"]) <= {"REPORTABLE", "DATA_UNAVAILABLE"}
    for _, r in rd.iterrows():
        if r["Procurement_Required_PLs"] > 0:
            assert r["Status"] == "REPORTABLE"
        else:
            assert r["Status"] == "DATA_UNAVAILABLE"


def test_build_procurement_roadmap_from_live_outputs():
    rm = ea.build_procurement_roadmap(write=False)
    assert list(rm["Year"]) == cfg.ROADMAP_YEARS
    assert rm["Remaining_Exposure"].iloc[-1] <= rm["Remaining_Exposure"].iloc[0] + 1e-6


def test_executive_budget_scenarios_columns_and_levels():
    sc = ea.build_executive_budget_scenarios(write=False)
    assert list(sc["Scenario"]) == ["Rs 25 Cr", "Rs 50 Cr", "Rs 100 Cr", "Rs 200 Cr", "Unlimited"]
    for col in ["Scenario", "PLs_Funded", "SRRS_Removed", "SRRS_Remaining",
                "Risk_Reduction_Pct", "S1_Funded", "S2_Funded", "S3_Funded", "S4_Funded",
                "Capital_Utilized", "Capital_Efficiency"]:
        assert col in sc.columns


def test_baseline_validation_documents_unchanged_optimizer():
    bv = ea.build_optimization_baseline_validation(write=False)
    assert {"Aspect", "Value", "Status"}.issubset(bv.columns)
    aspects = set(bv["Aspect"])
    assert {"Decision_Variables", "Objective_Function", "Budget_Constraint",
            "Affordability_Filter", "Safety_Reserve", "Explainability_Outputs"} <= aspects
    assert (bv["Status"] == "UNCHANGED").all()


def test_master_run_writes_all_outputs():
    summary = ea.run(write=False)
    assert {"baseline", "frontier", "efficiency", "allocation", "readiness",
            "roadmap", "scenarios"} <= set(summary)
