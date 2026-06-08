"""
railway_powerbi_export.py
=========================
Unified Railway Inventory Dashboard Layer (Power BI semantic layer).

Consumes ONLY generated pipeline outputs (never raw Excel). Power BI becomes
visualization-only: every value below is pre-computed here.

Strategic inputs : railway_sku_master.csv, railway_forecast.csv,
                   railway_inventory_policy.csv, railway_data_quality.csv,
                   executive_kpi_summary.csv, railway_abc_criticality_matrix.csv
Operational inputs: railway_operational_inventory.csv (+ generated
                   powerbi/page1_operational_inventory.csv for Operational_ABC),
                   railway_inventory_rationalization.csv,
                   railway_rationalization_summary.csv

Emits powerbi/page0..page9 (page6 reused as-is).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from railway import railway_config as cfg

OUT = cfg.OUTPUT_DIR
PBI = cfg.POWERBI_DIR
BUDGETS = cfg.BUDGET_SCENARIOS          # centralized in config


def _read(name, sub=False):
    path = (PBI if sub else OUT) / name
    return pd.read_csv(path, dtype={"PL_Code": str})


def _exec_kpis() -> dict:
    df = _read("executive_kpi_summary.csv")
    return dict(zip(df["KPI"], df["Value"]))


# ----------------------------------------------------------------------
# Budget knapsack (consumes policy CSV normalized fields)
# ----------------------------------------------------------------------
def _budget_scenarios(policy: pd.DataFrame) -> pd.DataFrame:
    from railway import railway_inventory_optimization as opt
    cand_all = policy[(policy["Inventory_Status"] == "Procurement Required") &
                      (policy["Normalized_Investment_Required"] > 0)].copy()
    total_inv = float(cand_all["Normalized_Investment_Required"].sum())
    total_pri = float(cand_all["Normalized_Procurement_Priority_Score"].sum())
    total_srrs = float(cand_all["Service_Risk_Reduction_Score"].sum())   # Step 13

    rows = []
    for label, budget in BUDGETS:
        cand = cand_all[cand_all["Normalized_Investment_Required"] <= budget].reset_index(drop=True)
        # Step 13: objective is SRRS; Step 15: Safety Reserve funds S1/S2 spares first.
        # Budget constraint unchanged (Unit_Cost lives here only, via normalized investment).
        sel = sorted(opt.allocate_with_reserve(
            cand, budget, "Service_Risk_Reduction_Score", "Normalized_Investment_Required"))
        funded_inv = float(cand.loc[sel, "Normalized_Investment_Required"].sum())
        funded_pri = float(cand.loc[sel, "Normalized_Procurement_Priority_Score"].sum())
        funded_srrs = float(cand.loc[sel, "Service_Risk_Reduction_Score"].sum())
        rows.append({
            "Scenario": label,
            "Budget": round(budget, 2),
            "Items_Funded": len(sel),
            "Procurement_Coverage_Pct": round(funded_inv / total_inv * 100.0, 2) if total_inv else 0.0,
            "Remaining_Gap": round(total_inv - funded_inv, 2),
            "Criticality_Coverage_Pct": round(funded_pri / total_pri * 100.0, 2) if total_pri else 0.0,
            # additive (Step 13): % of total service-risk reduction funded
            "Service_Risk_Coverage_Pct": round(funded_srrs / total_srrs * 100.0, 2) if total_srrs else 0.0,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Build all pages
# ----------------------------------------------------------------------
def build_all(write: bool = True) -> dict:
    master = _read("railway_sku_master.csv")
    forecast = _read("railway_forecast.csv")
    policy = _read("railway_inventory_policy.csv")
    operational = _read("railway_operational_inventory.csv")
    op_abc = _read("op_inventory_summary.csv", sub=True)[["PL_Code", "Operational_ABC"]]
    rationalization = _read("railway_inventory_rationalization.csv")
    rat_summary = _read("railway_rationalization_summary.csv")
    dq = _read("railway_data_quality.csv")[["PL_Code", "Normalized_Inventory_Value"]]
    ek = _exec_kpis()

    pages = {}

    # ---- PAGE 0: executive (universe-separated, normalized) ----
    strategic_inv_norm = float(dq["Normalized_Inventory_Value"].sum())     # 59-item strategic
    total_op_val = float(operational["Inventory_Value"].fillna(0).sum())   # 907-item operational
    dead_val = float(operational.loc[operational["Movement_Status"] == "Dead Stock", "Inventory_Value"].sum())
    slow_val = float(operational.loc[operational["Movement_Status"] == "Slow Moving", "Inventory_Value"].sum())
    turn_risk = round((dead_val + slow_val) / total_op_val * 100.0, 2) if total_op_val else 0.0
    high_conf_pct = round((forecast["Forecast_Confidence"] == "High").mean() * 100.0, 2)
    proc_required_val = float(policy["Normalized_Investment_Required"].sum())
    pages["page0_executive_dashboard"] = pd.DataFrame([
        {"KPI": "Strategic Inventory Value (Normalized)", "Value": round(strategic_inv_norm, 2), "Universe": "Strategic"},
        {"KPI": "Operational Inventory Value", "Value": round(total_op_val, 2), "Universe": "Operational"},
        {"KPI": "Annual Issue Value", "Value": ek.get("Total_Annual_Issue_Value"), "Universe": "Strategic"},
        {"KPI": "Procurement Required Value", "Value": round(proc_required_val, 2), "Universe": "Strategic"},
        {"KPI": "Dead Stock Value", "Value": round(dead_val, 2), "Universe": "Operational"},
        {"KPI": "Slow Moving Value", "Value": round(slow_val, 2), "Universe": "Operational"},
        {"KPI": "Inventory Turn Risk %", "Value": turn_risk, "Universe": "Operational"},
        {"KPI": "Inventory Concentration Index", "Value": ek.get("Normalized_Concentration_Index"), "Universe": "Strategic"},
        {"KPI": "High Confidence Forecast %", "Value": high_conf_pct, "Universe": "Strategic"},
        {"KPI": "Data Quality Impact", "Value": ek.get("Data_Quality_Impact"), "Universe": "Meta"},
    ])

    # ---- PAGE 1: procurement (normalized values + normalized-derived class) ----
    p1 = policy[[
        "PL_Code", "Description", "Criticality", "ABC_Class", "Forecast_2026_27",
        "Current_Stock", "ROP", "Inventory_Gap", "Normalized_Investment_Required",
        "Normalized_Procurement_Priority_Score", "Normalized_Procurement_Priority_Class",
        "Service_Risk_Reduction_Score", "Service_Risk_Priority_Class",
        # ---- Step 15 explainability (additive) ----
        "Service_Factor", "Positive_Gap", "SRRS_Rank", "SRRS_Per_Rupee", "Funding_Driver"]].copy()
    p1 = p1.rename(columns={"Normalized_Procurement_Priority_Class": "Procurement_Priority_Class"})
    p1["Criticality_Name"] = p1["Criticality"].map(cfg.CRITICALITY_NAME_MAP)
    # Funding_Decision: was this item selected by the Rs 1 crore procurement plan?
    plan_path = OUT / "railway_procurement_plan.csv"
    funded = set()
    if plan_path.exists():
        funded = set(pd.read_csv(plan_path, dtype={"PL_Code": str})["PL_Code"])
    p1["Funding_Decision"] = np.where(p1["PL_Code"].isin(funded), "Funded", "Not Funded")
    p1["Source_Universe"] = "Strategic"
    pages["page1_procurement"] = p1

    # ---- PAGE 2: forecasting ----
    pages["page2_forecasting"] = forecast[[
        "PL_Code", "Demand_Class", "Forecast_Confidence", "Recommended_Model",
        "Forecast_2026_27", "AAC_Forecast", "EAR_Forecast", "MA_Forecast", "CAGR_Forecast"]].copy()

    # ---- PAGE 3: criticality (normalized strategic value) ----
    p3 = master[["PL_Code", "Description", "Criticality", "ABC_Class"]] \
        .merge(dq, on="PL_Code", how="left") \
        .merge(forecast[["PL_Code", "Forecast_2026_27"]], on="PL_Code", how="left") \
        .merge(policy[["PL_Code", "Inventory_Status"]], on="PL_Code", how="left")
    p3["Criticality_Name"] = p3["Criticality"].map(cfg.CRITICALITY_NAME_MAP)
    p3["Source_Universe"] = "Strategic"
    pages["page3_criticality"] = p3[["PL_Code", "Description", "Criticality", "Criticality_Name",
                                     "ABC_Class", "Normalized_Inventory_Value", "Forecast_2026_27",
                                     "Inventory_Status", "Source_Universe"]]

    # ---- PAGE 4: operational health ----
    p4 = operational[["PL_Code", "Description", "Movement_Status", "Inventory_Aging_Class", "Inventory_Value"]] \
        .merge(op_abc, on="PL_Code", how="left")
    p4["Source_Universe"] = "Operational"
    pages["page4_operational_health"] = p4

    # ---- PAGE 5: rationalization (strategic value already normalized; universe-tagged) ----
    p5 = rationalization[["PL_Code", "Description", "Inventory_Action", "Inventory_Value",
                          "Movement_Status", "Source_Universe"]].copy()
    p5 = p5.rename(columns={"Inventory_Value": "Normalized_Inventory_Value"})
    # Compatibility alias for legacy Power BI visuals that bind to "Inventory_Value".
    # Defined to EQUAL Normalized_Inventory_Value (no calculation change; same value).
    p5["Inventory_Value"] = p5["Normalized_Inventory_Value"]
    pages["page5_rationalization"] = p5

    # ---- PAGE 6: reuse existing (do not regenerate) ----
    # page6_data_quality.csv already produced by railway_data_quality.py

    # ---- PAGE 7: ABC x Criticality matrix (recomputed on NORMALIZED values) ----
    mat = master[["PL_Code", "ABC_Class", "Criticality"]] \
        .merge(dq, on="PL_Code", how="left") \
        .merge(policy[["PL_Code", "Inventory_Gap", "Normalized_Investment_Required"]], on="PL_Code", how="left")
    mat["Inventory_Gap"] = mat["Inventory_Gap"].clip(lower=0)
    recs = []
    for abc in cfg.ABC_ORDER:
        for crit in cfg.CRITICALITY_ORDER:
            cell = mat[(mat["ABC_Class"] == abc) & (mat["Criticality"] == crit)]
            recs.append({"ABC_Class": abc, "Criticality": crit, "Count": int(len(cell)),
                         "Normalized_Inventory_Value": round(float(cell["Normalized_Inventory_Value"].sum()), 2),
                         "Inventory_Gap": round(float(cell["Inventory_Gap"].sum()), 2),
                         "Normalized_Investment_Required": round(float(cell["Normalized_Investment_Required"].sum()), 2),
                         "Source_Universe": "Strategic"})
    pages["page7_abc_criticality_matrix"] = pd.DataFrame(recs)

    # ---- PAGE 8: budget scenarios ----
    pages["page8_budget_scenarios"] = _budget_scenarios(policy)

    # ---- PAGE 9: management actions (strategic / operational value split -- never combined) ----
    priority_map = {"Procure Immediately": "1-Critical", "Dispose": "2-High",
                    "Rationalize": "3-Medium", "Monitor": "4-Low", "Retain": "5-Steady"}
    g = rationalization.groupby("Inventory_Action")
    counts = g.size()
    strat = rationalization[rationalization["Source_Universe"] == "Strategic"] \
        .groupby("Inventory_Action")["Inventory_Value"].sum()
    oper = rationalization[rationalization["Source_Universe"] == "Operational"] \
        .groupby("Inventory_Action")["Inventory_Value"].sum()
    actions = list(rat_summary["Inventory_Action"])
    p9 = pd.DataFrame({
        "Action": actions,
        # page9 is an action-level aggregate (no per-SKU rows), so a SKU Description
        # cannot be carried without changing the grouping. Description is provided as
        # a compatibility alias of the Action label for legacy visuals (display-only).
        "Description": actions,
        "Count": [int(counts.get(a, 0)) for a in actions],
        "Strategic_Inventory_Value": [round(float(strat.get(a, 0.0)), 2) for a in actions],
        "Operational_Inventory_Value": [round(float(oper.get(a, 0.0)), 2) for a in actions],
        "Priority": [priority_map.get(a) for a in actions],
    })
    pages["page9_management_actions"] = p9

    if write:
        cfg.ensure_output_dirs()
        for name, df in pages.items():
            df.to_csv(PBI / f"{name}.csv", index=False)
    return pages


# ----------------------------------------------------------------------
# validation + executive test
# ----------------------------------------------------------------------
def run():
    pages = build_all(write=True)
    page6 = PBI / "page6_data_quality.csv"
    all_pages = dict(pages)

    print("=" * 80)
    print("STEP 7 -- UNIFIED POWER BI SEMANTIC LAYER")
    print("=" * 80)
    print("\nRows per page:")
    for name, df in pages.items():
        print(f"   {name:34s}: {len(df):4d} rows x {df.shape[1]} cols")
    print(f"   {'page6_data_quality (reused)':34s}: "
          f"{len(pd.read_csv(page6)) if page6.exists() else 'MISSING'} rows")

    total_pages = len(pages) + (1 if page6.exists() else 0)
    total_kpis = len(pages["page0_executive_dashboard"])
    print(f"\nTotal pages generated : {total_pages} (page0-page9)")
    print(f"Total executive KPIs  : {total_kpis}")

    # ---- EXECUTIVE TEST: answer 7 questions from the exports only ----
    p0 = pages["page0_executive_dashboard"].set_index("KPI")["Value"].to_dict()
    p9 = pages["page9_management_actions"].set_index("Action")
    p8 = pages["page8_budget_scenarios"].set_index("Scenario")
    p1 = pages["page1_procurement"]

    def gv(act, col): return p9.loc[act, col] if act in p9.index else 0

    print("\n" + "-" * 80)
    print("EXECUTIVE TEST (answered from Power BI exports):")
    top_buy = p1[p1["Procurement_Priority_Class"] == "Immediate"]
    print(f"   1. Buy immediately      : {int(gv('Procure Immediately','Count'))} items "
          f"(page1; {len(top_buy)} 'Immediate' priority).")
    print(f"   2. Dispose              : {int(gv('Dispose','Count'))} items, "
          f"Rs {gv('Dispose','Operational_Inventory_Value'):,.0f} operational (page5/page9).")
    print(f"   3. Rationalize          : {int(gv('Rationalize','Count'))} items, "
          f"Rs {gv('Rationalize','Operational_Inventory_Value'):,.0f} operational (page5/page9).")
    print(f"   4. Capital required     : Rs {p0['Procurement Required Value']:,.0f} (page0).")
    print(f"   5. Dead stock           : Rs {p0['Dead Stock Value']:,.0f} (page0).")
    print(f"   6. Concentration        : {p0['Inventory Concentration Index']}% (page0).")
    print(f"   7. Rs 1 crore buys      : {int(p8.loc['Rs 1 Crore','Items_Funded'])} items, "
          f"{p8.loc['Rs 1 Crore','Criticality_Coverage_Pct']}% criticality coverage (page8).")

    questions_answerable = all([
        "Procure Immediately" in p9.index, "Dispose" in p9.index, "Rationalize" in p9.index,
        "Procurement Required Value" in p0, "Dead Stock Value" in p0,
        "Inventory Concentration Index" in p0, "Rs 1 Crore" in p8.index,
    ])

    gate = {
        "all_pages_written": all((PBI / f"{n}.csv").exists() for n in pages),
        "page6_present": page6.exists(),
        "page0_has_10_kpis_universe_split": total_kpis == 10
            and "Universe" in pages["page0_executive_dashboard"].columns,
        "budget_4_scenarios": len(pages["page8_budget_scenarios"]) == 4,
        "executive_test_passed": questions_answerable,
    }
    print("\nVALIDATION GATE:")
    for k, v in gate.items():
        print(f"   {k:24s}: {v}")
    print(f"   ALL PASS: {all(gate.values())}")
    print("=" * 80)
    return pages, gate


if __name__ == "__main__":
    run()
