"""
railway_lineage.py
==================
Data-lineage registry for every generated CSV. Produces data_lineage_report.csv
with: Output_File, Source_File, Pipeline (Strategic|Operational|Derived),
Generated_By, Source_Pipeline.

Design note: to honour "do NOT modify existing outputs", lineage is captured in
this separate report rather than by appending a Source_Pipeline column to each
already-validated CSV (which would mutate them and disturb the regression
baseline). The registry below is the single source of lineage truth.
"""

from __future__ import annotations

import pandas as pd

from railway import railway_config as cfg

# (Output_File, Source_File(s), Pipeline, Generated_By)
LINEAGE = [
    ("railway_demand_history.csv", "railways.xlsx", "Strategic", "railway_data_preparation.py"),
    ("railway_sku_master.csv", "railway_demand_history.csv", "Strategic", "railway_classification.py"),
    ("railway_forecast.csv", "railway_demand_history.csv + railway_sku_master.csv", "Strategic", "railway_forecasting.py"),
    ("railway_inventory_policy.csv", "railway_demand_history.csv + railway_sku_master.csv + railway_forecast.csv", "Strategic", "railway_inventory_optimization.py"),
    ("railway_abc_criticality_matrix.csv", "railway_inventory_policy.csv", "Strategic", "railway_inventory_optimization.py"),
    ("railway_procurement_plan.csv", "railway_inventory_policy.csv", "Strategic", "railway_inventory_optimization.py"),
    ("railway_data_quality.csv", "railway_inventory_policy.csv + railways.xlsx(UDM)", "Strategic", "railway_data_quality.py"),
    ("executive_kpi_summary.csv", "sku_master + forecast + policy + data_quality", "Derived", "railway_executive_summary.py"),
    ("executive_kpi_summary.json", "sku_master + forecast + policy + data_quality", "Derived", "railway_executive_summary.py"),
    ("executive_top10_procurement.csv", "railway_inventory_policy.csv", "Derived", "railway_executive_summary.py"),
    ("executive_top10_inventory_value.csv", "railway_sku_master.csv", "Derived", "railway_executive_summary.py"),
    ("executive_budget_scenario.csv", "railway_procurement_plan.csv", "Derived", "railway_executive_summary.py"),
    ("railway_operational_inventory.csv", "railway_stock_summary.xlsx", "Operational", "railway_operational_analysis.py"),
    ("operational_data_quality.csv", "railway_stock_summary.xlsx", "Operational", "railway_operational_analysis.py"),
    ("operational_top50_dead_stock.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    ("operational_top50_slow_moving.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    ("operational_top50_value.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    ("operational_top50_zero_stock.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    ("railway_inventory_rationalization.csv", "sku_master + inventory_policy + operational_inventory", "Derived", "railway_inventory_rationalization.py"),
    ("railway_rationalization_summary.csv", "railway_inventory_rationalization.csv", "Derived", "railway_inventory_rationalization.py"),
    # Power BI pages
    ("powerbi/page0_executive_dashboard.csv", "executive_kpi_summary + operational + forecast", "Derived", "railway_powerbi_export.py"),
    ("powerbi/page1_procurement.csv", "railway_inventory_policy.csv", "Strategic", "railway_powerbi_export.py"),
    ("powerbi/page2_forecasting.csv", "railway_forecast.csv", "Strategic", "railway_powerbi_export.py"),
    ("powerbi/page3_criticality.csv", "sku_master + forecast + policy", "Strategic", "railway_powerbi_export.py"),
    ("powerbi/page4_operational_health.csv", "operational_inventory + op_inventory_summary", "Operational", "railway_powerbi_export.py"),
    ("powerbi/page5_rationalization.csv", "railway_inventory_rationalization.csv", "Derived", "railway_powerbi_export.py"),
    ("powerbi/page6_data_quality.csv", "railway_data_quality.csv", "Strategic", "railway_data_quality.py"),
    ("powerbi/page7_abc_criticality_matrix.csv", "railway_abc_criticality_matrix.csv", "Strategic", "railway_powerbi_export.py"),
    ("powerbi/page8_budget_scenarios.csv", "railway_inventory_policy.csv", "Strategic", "railway_powerbi_export.py"),
    ("powerbi/page9_management_actions.csv", "railway_rationalization_summary.csv", "Derived", "railway_powerbi_export.py"),
    ("powerbi/op_inventory_summary.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    ("powerbi/op_inventory_aging.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    ("powerbi/op_dead_stock.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    ("powerbi/op_inventory_value.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    ("powerbi/op_operational_abc.csv", "railway_operational_inventory.csv", "Operational", "railway_operational_analysis.py"),
    # AnyLogistix
    ("anylogistix/locations.csv", "railway_config (divisions/depots)", "Derived", "railway_anylogistix_export.py"),
    ("anylogistix/products.csv", "sku_master + forecast + policy", "Strategic", "railway_anylogistix_export.py"),
    ("anylogistix/demand.csv", "railway_forecast.csv", "Strategic", "railway_anylogistix_export.py"),
    ("anylogistix/inventory_policy.csv", "railway_inventory_policy.csv", "Strategic", "railway_anylogistix_export.py"),
    ("anylogistix/facilities.csv", "operational_inventory + rationalization", "Operational", "railway_anylogistix_export.py"),
    ("anylogistix/service_risk.csv", "inventory_policy + forecast", "Strategic", "railway_anylogistix_export.py"),
    ("anylogistix/multi_echelon_candidates.csv", "products (sku_master+policy)", "Strategic", "railway_anylogistix_export.py"),
    ("anylogistix/procurement_scenarios.csv", "page8_budget_scenarios.csv", "Strategic", "railway_anylogistix_export.py"),
    ("anylogistix/digital_twin_readiness.csv", "locations + products + policy + demand", "Derived", "railway_anylogistix_export.py"),
]


def build_lineage_report(write=True) -> pd.DataFrame:
    df = pd.DataFrame(LINEAGE, columns=["Output_File", "Source_File", "Pipeline", "Generated_By"])
    df["Source_Pipeline"] = df["Pipeline"]      # explicit alias required by spec
    if write:
        cfg.ensure_output_dirs()
        df.to_csv(cfg.OUTPUT_DIR / "data_lineage_report.csv", index=False)
    return df


def run():
    df = build_lineage_report(write=True)
    print("Data lineage report:", len(df), "outputs tracked")
    print(df["Pipeline"].value_counts().to_dict())
    print(f"Wrote: {cfg.OUTPUT_DIR / 'data_lineage_report.csv'}")
    return df


if __name__ == "__main__":
    run()
