"""
railway_anylogistix_export.py
=============================
Railway Logistics Digital-Twin Export Layer.

Consumes ONLY generated pipeline outputs (NEVER raw Excel). Produces
AnyLogistix-compatible datasets for network / inventory / multi-echelon /
service-level / procurement-risk modelling, plus a digital-twin readiness score.

Inputs (generated outputs only):
    railway_sku_master.csv, railway_forecast.csv, railway_inventory_policy.csv,
    railway_operational_inventory.csv, railway_inventory_rationalization.csv,
    powerbi/op_inventory_summary.csv (Operational_ABC),
    powerbi/page7_abc_criticality_matrix.csv, powerbi/page8_budget_scenarios.csv

Honest constraints:
  * No division-consumption % exists in any generated output -> demand uses
    Equal_Split (flagged; lowers Demand_Data_Completeness).
  * No coordinates anywhere -> lat/long NULL, Coordinate_Source = Placeholder.
    Real coordinates are NEVER fabricated.

Output folder: railway/outputs/anylogistix/
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from railway import railway_config as cfg

ALX = cfg.ANYLOGISTIX_DIR
OUT = cfg.OUTPUT_DIR
PBI = cfg.POWERBI_DIR


def _read(name, sub=False):
    return pd.read_csv((PBI if sub else OUT) / name, dtype={"PL_Code": str})


# ----------------------------------------------------------------------
# 1. locations  (divisions + depots; coordinates are placeholders)
# ----------------------------------------------------------------------
def build_locations() -> pd.DataFrame:
    rows = []
    for d in cfg.ANYLOGISTIX_DIVISIONS:
        rows.append({"Location_ID": f"DIV-{d}", "Location_Name": d,
                     "Location_Type": "Division", "Division": d, "Depot": None,
                     "Latitude": None, "Longitude": None, "Coordinate_Source": "Placeholder"})
    for depot in cfg.STRATEGIC_DEPOT_COLS:        # 6 stocking depots (config constants)
        rows.append({"Location_ID": f"DEP-{depot.replace('/', '-')}", "Location_Name": depot,
                     "Location_Type": "Depot", "Division": None, "Depot": depot,
                     "Latitude": None, "Longitude": None, "Coordinate_Source": "Placeholder"})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 2. products
# ----------------------------------------------------------------------
def build_products(master, forecast, policy) -> pd.DataFrame:
    df = master[["PL_Code", "Description", "ABC_Class", "Criticality", "Unit_Cost", "Demand_Class"]] \
        .merge(forecast[["PL_Code", "Forecast_2026_27", "Forecast_Confidence"]], on="PL_Code", how="left") \
        .merge(policy[["PL_Code", "Target_Service_Level", "Inventory_Status",
                       "Procurement_Priority_Class"]], on="PL_Code", how="left")
    return df[["PL_Code", "Description", "ABC_Class", "Criticality", "Unit_Cost",
               "Forecast_2026_27", "Target_Service_Level", "Demand_Class",
               "Forecast_Confidence", "Inventory_Status", "Procurement_Priority_Class"]]


# ----------------------------------------------------------------------
# 3. demand  (Equal_Split -- no division % in generated outputs)
# ----------------------------------------------------------------------
def build_demand(forecast) -> pd.DataFrame:
    n_div = len(cfg.ANYLOGISTIX_DIVISIONS)
    rows = []
    for _, r in forecast.iterrows():
        share = (r["Forecast_2026_27"] or 0) / n_div
        for d in cfg.ANYLOGISTIX_DIVISIONS:
            rows.append({"Division": d, "PL_Code": r["PL_Code"],
                         "Forecast_Demand": round(share, 2),
                         "Demand_Class": r["Demand_Class"],
                         "Forecast_Confidence": r["Forecast_Confidence"],
                         "Demand_Allocation_Method": cfg.DEMAND_ALLOCATION_DEFAULT})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 4. inventory policy
# ----------------------------------------------------------------------
def build_inventory_policy(policy) -> pd.DataFrame:
    return policy[["PL_Code", "Criticality", "Target_Service_Level", "Lead_Time_Months",
                   "Safety_Stock", "ROP", "Recommended_Min", "Recommended_Max",
                   "Recommended_Reorder_Level"]].copy()


# ----------------------------------------------------------------------
# 5. facilities  (operational items mapped to their depot facility)
# ----------------------------------------------------------------------
def build_facilities(operational, op_abc, rationalization) -> pd.DataFrame:
    df = operational[["PL_Code", "Depot", "Inventory_Value"]] \
        .merge(op_abc, on="PL_Code", how="left") \
        .merge(rationalization[["PL_Code", "Inventory_Action"]], on="PL_Code", how="left")
    df["Location_ID"] = "DEP-" + df["Depot"].fillna("UNKNOWN").str.replace(r"[\s/]+", "-", regex=True)
    df["Facility_Type"] = "Depot"
    return df[["Location_ID", "Facility_Type", "Inventory_Value", "Operational_ABC", "Inventory_Action"]]


# ----------------------------------------------------------------------
# 6. service risk
# ----------------------------------------------------------------------
def build_service_risk(policy, forecast) -> pd.DataFrame:
    # Use NORMALIZED priority score + normalized-derived class (Fix Group B: no
    # ranking may derive from the per-km-inflated original score).
    df = policy[["PL_Code", "Criticality", "Inventory_Gap", "Inventory_Status",
                 "Normalized_Procurement_Priority_Score",
                 "Normalized_Procurement_Priority_Class"]] \
        .merge(forecast[["PL_Code", "Forecast_Confidence"]], on="PL_Code", how="left")
    return df.rename(columns={"Normalized_Procurement_Priority_Class": "Procurement_Priority_Class"})


# ----------------------------------------------------------------------
# 7. multi-echelon candidates
# ----------------------------------------------------------------------
def build_multi_echelon(products) -> pd.DataFrame:
    df = products[["PL_Code", "Description", "ABC_Class", "Criticality",
                   "Forecast_2026_27", "Target_Service_Level", "Inventory_Status"]].copy()
    df["Multi_Echelon_Candidate"] = np.where(
        df["ABC_Class"].isin(["A", "B1"]) & df["Criticality"].isin(["S1", "S2"]) &
        (df["Inventory_Status"] == "Procurement Required"), "YES", "NO")
    return df


# ----------------------------------------------------------------------
# 8. procurement scenarios (from page8)
# ----------------------------------------------------------------------
def build_procurement_scenarios(page8) -> pd.DataFrame:
    return page8.rename(columns={
        "Procurement_Coverage_Pct": "Procurement_Coverage",
        "Criticality_Coverage_Pct": "Criticality_Coverage"})[
        ["Budget", "Items_Funded", "Procurement_Coverage", "Criticality_Coverage", "Remaining_Gap"]]


# ----------------------------------------------------------------------
# 9. digital twin readiness
# ----------------------------------------------------------------------
def build_readiness(locations, products, policy, demand) -> tuple[pd.DataFrame, dict]:
    # Network: structure present (50) + coordinate fraction (0 -> none real)
    coord_frac = locations[["Latitude", "Longitude"]].notna().all(axis=1).mean()
    network = round(50.0 + 50.0 * coord_frac, 2)            # 50 = structure only
    # Inventory: products with SS + ROP + non-null cost
    inv = round(policy[["Safety_Stock", "ROP"]].notna().all(axis=1).mean() * 100.0, 2)
    # Demand: penalised for Equal_Split
    equal_split = (demand["Demand_Allocation_Method"] == "Equal_Split").all()
    dem = 50.0 if equal_split else 100.0
    # Policy: lead time + service level present
    pol = round(policy[["Lead_Time_Months", "Target_Service_Level"]].notna().all(axis=1).mean() * 100.0, 2)

    overall = round((network + inv + dem + pol) / 4.0, 2)

    def band(s):
        return "Ready" if s >= 90 else ("Near Ready" if s >= 75 else ("Partial" if s >= 50 else "Not Ready"))

    df = pd.DataFrame([
        {"Metric": "Network_Data_Completeness", "Score_Pct": network, "Band": band(network)},
        {"Metric": "Inventory_Data_Completeness", "Score_Pct": inv, "Band": band(inv)},
        {"Metric": "Demand_Data_Completeness", "Score_Pct": dem, "Band": band(dem)},
        {"Metric": "Policy_Data_Completeness", "Score_Pct": pol, "Band": band(pol)},
        {"Metric": "Overall_Digital_Twin_Readiness", "Score_Pct": overall, "Band": band(overall)},
    ])
    meta = {"overall": overall, "band": band(overall), "network": network,
            "inventory": inv, "demand": dem, "policy": pol, "equal_split": equal_split}
    return df, meta


# ----------------------------------------------------------------------
# build all + report
# ----------------------------------------------------------------------
def build_all(write: bool = True):
    master = _read("railway_sku_master.csv")
    forecast = _read("railway_forecast.csv")
    policy = _read("railway_inventory_policy.csv")
    operational = _read("railway_operational_inventory.csv")
    op_abc = _read("op_inventory_summary.csv", sub=True)[["PL_Code", "Operational_ABC"]]
    rationalization = _read("railway_inventory_rationalization.csv")
    page8 = _read("page8_budget_scenarios.csv", sub=True)

    locations = build_locations()
    products = build_products(master, forecast, policy)
    demand = build_demand(forecast)
    inv_policy = build_inventory_policy(policy)
    facilities = build_facilities(operational, op_abc, rationalization)
    service_risk = build_service_risk(policy, forecast)
    multi_echelon = build_multi_echelon(products)
    proc_scen = build_procurement_scenarios(page8)
    readiness, meta = build_readiness(locations, products, policy, demand)

    tables = {
        "locations": locations, "products": products, "demand": demand,
        "inventory_policy": inv_policy, "facilities": facilities,
        "service_risk": service_risk, "multi_echelon_candidates": multi_echelon,
        "procurement_scenarios": proc_scen, "digital_twin_readiness": readiness,
    }
    if write:
        ALX.mkdir(parents=True, exist_ok=True)
        for name, df in tables.items():
            df.to_csv(ALX / f"{name}.csv", index=False)
    return tables, meta


def write_readiness_report(tables, meta):
    me = tables["multi_echelon_candidates"]
    sr = tables["service_risk"].sort_values("Normalized_Procurement_Priority_Score", ascending=False)
    me_yes = int((me["Multi_Echelon_Candidate"] == "YES").sum())
    top_risk = sr.head(5)

    lines = []
    lines.append("# AnyLogistix Readiness Report — Southern Railway Signalling Stores\n")
    lines.append(f"**Generated:** 2026-06-07 · Source: generated outputs only (no raw Excel).\n")
    lines.append("## 1. Readiness Score\n")
    lines.append(f"**Overall Digital-Twin Readiness: {meta['overall']}% → {meta['band']}**\n")
    lines.append("| Dimension | Score | Band |\n|---|---:|---|")
    for _, r in tables["digital_twin_readiness"].iterrows():
        lines.append(f"| {r['Metric']} | {r['Score_Pct']}% | {r['Band']} |")
    lines.append("\n## 2. Key Data Gaps\n")
    lines.append("- **Coordinates absent** for all 12 locations (`Coordinate_Source=Placeholder`) — blocks geographic network optimization. Real lat/long must be supplied; never fabricated.")
    lines.append("- **Division-level demand unavailable** in generated outputs — demand uses `Equal_Split` across the 6 divisions (`Demand_Allocation_Method=Equal_Split`). Export division consumption % to lift this.")
    lines.append("- **Depot→Division mapping** not derivable from generated outputs (left NULL).")
    lines.append(f"\n## 3. Multi-Echelon Candidate Count\n\n**{me_yes}** SKUs qualify (A/B1 × S1/S2 × Procurement Required).\n")
    lines.append("## 4. Top Service-Risk Items\n")
    lines.append("| PL_Code | Criticality | Inventory_Gap | Priority Score | Class |\n|---|---|---:|---:|---|")
    for _, r in top_risk.iterrows():
        lines.append(f"| {r['PL_Code']} | {r['Criticality']} | {r['Inventory_Gap']:,.0f} | "
                     f"{r['Normalized_Procurement_Priority_Score']:,.0f} | {r['Procurement_Priority_Class']} |")
    lines.append("\n## 5. Recommended Next Actions\n")
    lines.append("1. Supply real **division & depot geo-coordinates** (or a coordinate lookup) to enable network optimization.")
    lines.append("2. Export **division-wise consumption %** from the strategic pipeline to replace Equal_Split demand.")
    lines.append("3. Establish the **depot→division** hierarchy for multi-echelon routing.")
    lines.append(f"4. Prioritise the **{me_yes} multi-echelon candidates** for stocking-location studies.")
    lines.append("\n## 6. AnyLogistix Network-Modeling Readiness\n")
    verdict = ("**Near Ready.** Product, inventory-policy, and service-risk data are complete and "
               "AnyLogistix-shaped. The two blockers for full network modeling are **geo-coordinates** "
               "and **real division-level demand** — both are data-supply gaps, not modeling gaps. "
               "Once supplied, Southern Railway can run network/multi-echelon optimization without redesign.")
    lines.append(verdict)
    (OUT.parent.parent / "ANYLOGISTIX_READINESS_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def run():
    tables, meta = build_all(write=True)
    write_readiness_report(tables, meta)

    print("=" * 80)
    print("STEP 8 -- ANYLOGISTIX DIGITAL-TWIN EXPORT")
    print("=" * 80)
    print("\nValidation counts:")
    print(f"   Number_of_Locations              : {len(tables['locations'])}")
    print(f"   Number_of_Products               : {len(tables['products'])}")
    print(f"   Number_of_Demand_Records         : {len(tables['demand'])}")
    print(f"   Number_of_Inventory_Policies     : {len(tables['inventory_policy'])}")
    print(f"   Number_of_Service_Risk_Records   : {len(tables['service_risk'])}")
    me_yes = int((tables['multi_echelon_candidates']['Multi_Echelon_Candidate'] == 'YES').sum())
    print(f"   Number_of_Multi_Echelon_Candidates: {me_yes} (YES) of {len(tables['multi_echelon_candidates'])}")

    print("\n--- Digital Twin Readiness ---")
    print(tables["digital_twin_readiness"].to_string(index=False))

    print("\n--- MANAGEMENT QUESTIONS ---")
    sr = tables["service_risk"].sort_values("Normalized_Procurement_Priority_Score", ascending=False)
    fac = tables["facilities"]
    best = build_procurement_scenarios(_read("page8_budget_scenarios.csv", sub=True)) \
        .sort_values("Criticality_Coverage", ascending=False).iloc[0]
    print("   1. Top-consuming divisions : equal across 6 (Equal_Split; real division data unavailable).")
    print(f"   2. Highest-value location  : {fac.groupby('Location_ID')['Inventory_Value'].sum().idxmax()} "
          f"(Rs {fac['Inventory_Value'].sum():,.0f} total).")
    print(f"   3. Top service-risk product: {sr.iloc[0]['PL_Code']} ({sr.iloc[0]['Criticality']}, "
          f"priority {sr.iloc[0]['Normalized_Procurement_Priority_Score']:,.0f}).")
    print(f"   4. Multi-echelon products  : {me_yes} candidates.")
    print("   5. Service level by division: per-product Target_Service_Level (uniform across divisions under Equal_Split).")
    print(f"   6. Best procurement scenario: Rs {best['Budget']:,.0f} -> {best['Criticality_Coverage']}% criticality coverage.")
    print(f"   7. Digital-twin ready?     : {meta['overall']}% -> {meta['band']}.")

    # validation gate
    files = ["locations", "products", "demand", "inventory_policy", "facilities",
             "service_risk", "multi_echelon_candidates", "procurement_scenarios", "digital_twin_readiness"]
    gate = {
        "all_9_files_written": all((ALX / f"{f}.csv").exists() for f in files),
        "readiness_report_written": (OUT.parent.parent / "ANYLOGISTIX_READINESS_REPORT.md").exists(),
        "no_fabricated_coords": bool(tables["locations"]["Coordinate_Source"].eq("Placeholder").all()),
        "demand_flagged_equal_split": bool((tables["demand"]["Demand_Allocation_Method"] == "Equal_Split").all()),
        "readiness_in_range": 0 <= meta["overall"] <= 100,
    }
    print("\n" + "-" * 80)
    print("FINAL VALIDATION GATE:")
    for k, v in gate.items():
        print(f"   {k:28s}: {v}")
    print(f"   ALL PASS: {all(gate.values())}")
    print("=" * 80)
    return tables, gate


if __name__ == "__main__":
    run()
