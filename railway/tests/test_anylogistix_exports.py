"""Integration tests for AnyLogistix exports (read generated outputs)."""
import pandas as pd
import pytest
from railway import railway_config as cfg

ALX = cfg.ANYLOGISTIX_DIR

REQUIRED = ["locations", "products", "demand", "inventory_policy", "facilities",
            "service_risk", "multi_echelon_candidates", "procurement_scenarios",
            "digital_twin_readiness"]


@pytest.mark.parametrize("name", REQUIRED)
def test_file_exists(name):
    assert (ALX / f"{name}.csv").exists()


def test_locations_never_fabricate_coords():
    df = pd.read_csv(ALX / "locations.csv")
    assert (df["Coordinate_Source"] == "Placeholder").all()
    assert df["Latitude"].isna().all()
    assert df["Longitude"].isna().all()


def test_demand_equal_split_flagged():
    df = pd.read_csv(ALX / "demand.csv")
    assert (df["Demand_Allocation_Method"] == cfg.DEMAND_ALLOCATION_DEFAULT).all()


def test_multi_echelon_rule():
    df = pd.read_csv(ALX / "multi_echelon_candidates.csv", dtype={"PL_Code": str})
    yes = df[df["Multi_Echelon_Candidate"] == "YES"]
    # every YES must satisfy (A or B1) and (S1 or S2) and Procurement Required
    assert yes["ABC_Class"].isin(["A", "B1"]).all()
    assert yes["Criticality"].isin(["S1", "S2"]).all()
    assert (yes["Inventory_Status"] == "Procurement Required").all()


def test_readiness_in_range():
    df = pd.read_csv(ALX / "digital_twin_readiness.csv")
    assert df["Score_Pct"].between(0, 100).all()
