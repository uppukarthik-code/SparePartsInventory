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
