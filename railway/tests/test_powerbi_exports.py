"""Integration tests for Power BI exports (read generated outputs)."""
import pandas as pd
import pytest
from railway import railway_config as cfg

PBI = cfg.POWERBI_DIR

REQUIRED_PAGES = [
    "page0_executive_dashboard", "page1_procurement", "page2_forecasting",
    "page3_criticality", "page4_operational_health", "page5_rationalization",
    "page6_data_quality", "page7_abc_criticality_matrix", "page8_budget_scenarios",
    "page9_management_actions",
]


@pytest.mark.parametrize("page", REQUIRED_PAGES)
def test_page_exists_and_nonempty(page):
    path = PBI / f"{page}.csv"
    assert path.exists(), f"missing {page}"
    df = pd.read_csv(path)
    assert len(df) > 0


def test_page0_universe_split():
    # Step 11: executive page now separates strategic vs operational universes
    df = pd.read_csv(PBI / "page0_executive_dashboard.csv")
    assert len(df) == 10
    assert "Universe" in df.columns
    assert "Strategic Inventory Value (Normalized)" in set(df["KPI"])
    assert "Operational Inventory Value" in set(df["KPI"])
    assert "Total Inventory Value" not in set(df["KPI"])     # combined metric removed


def test_no_original_value_columns_on_strategic_pages():
    # Step 11 Validation 4: normalized fields must replace originals where they exist.
    # Step 12.5A compatibility: page5_rationalization is EXEMPT because it carries an
    # Inventory_Value ALIAS defined to EQUAL Normalized_Inventory_Value (legacy Power BI
    # visuals bind to that name). The alias integrity is asserted separately below, so the
    # V4 intent (no raw/un-normalized value on strategic pages) is still enforced.
    forbidden = {"Inventory_Value", "Inventory_Investment_Required", "Procurement_Priority_Score"}
    for page in ["page1_procurement", "page3_criticality",
                 "page7_abc_criticality_matrix", "page9_management_actions"]:
        cols = set(pd.read_csv(PBI / f"{page}.csv", nrows=0).columns)
        assert not (cols & forbidden), f"{page} still has {cols & forbidden}"


def test_page5_inventory_value_is_normalized_alias():
    # Step 12.5A: page5 Inventory_Value must be byte-equal to Normalized_Inventory_Value.
    df = pd.read_csv(PBI / "page5_rationalization.csv")
    assert "Inventory_Value" in df.columns and "Normalized_Inventory_Value" in df.columns
    assert df["Inventory_Value"].equals(df["Normalized_Inventory_Value"])


def test_page8_four_scenarios():
    df = pd.read_csv(PBI / "page8_budget_scenarios.csv")
    assert len(df) == 4
    assert {"Items_Funded", "Procurement_Coverage_Pct", "Criticality_Coverage_Pct"} <= set(df.columns)


def test_page7_matrix_shape():
    df = pd.read_csv(PBI / "page7_abc_criticality_matrix.csv")
    assert len(df) == 16  # 4 ABC x 4 Criticality
