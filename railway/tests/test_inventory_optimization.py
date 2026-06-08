"""Unit tests for inventory optimization: service level, lead time, sigma."""
import numpy as np
from railway import railway_inventory_optimization as opt


def test_target_service_level_matrix():
    assert opt.target_service_level("A", "S1") == 0.99
    assert opt.target_service_level("A", "S2") == 0.98
    assert opt.target_service_level("B1", "S1") == 0.97
    assert opt.target_service_level("B2", "S2") == 0.95
    assert opt.target_service_level("C", "S4") == 0.90        # default
    assert opt.target_service_level("A", "S4") == 0.90        # not in table


def test_lead_time_tier1_bounds():
    lt, src = opt.lead_time_months(pending_supply=3, ear_qty=33500, criticality="S1")
    assert lt == 12 and src == "Tier1_PendingSupply"         # clamped to max
    lt, src = opt.lead_time_months(pending_supply=10000, ear_qty=1000, criticality="S1")
    assert lt == 1 and src == "Tier1_PendingSupply"          # clamped to min


def test_lead_time_tier2_fallback():
    for crit, months in [("S1", 6), ("S2", 4), ("S3", 3), ("S4", 2)]:
        lt, src = opt.lead_time_months(pending_supply=0, ear_qty=100, criticality=crit)
        assert lt == months and src == "Tier2_Criticality"


def test_demand_sigma():
    assert opt.demand_sigma([5, 5, 5, 5, 5]) == 0.0
    assert opt.demand_sigma([0, 10, 0, 10, 0]) > 0


def test_safety_stock_nonnegative():
    # z>0, sigma>=0, lt>0 -> SS >= 0
    import scipy.stats as st
    z = float(st.norm.ppf(0.95))
    ss = z * opt.demand_sigma([0, 10, 20, 30, 40]) * np.sqrt(6)
    assert ss >= 0
