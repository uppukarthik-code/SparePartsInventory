"""STEP30 planning CSVs (read-only; additive)."""
import csv
from railway import railway_config as cfg
from railway.governance import division_summary as ds
H = cfg.OUTPUT_DIR / "MAS" / "history"


def W(n, hdr, rows):
    w = csv.writer(open(H / n, "w", newline="", encoding="utf-8"))
    w.writerow(hdr); w.writerows(rows)
    print(f"{n}: {len(rows)} rows")


W("notebook7_rebuild_plan.csv", ["Legacy_Section", "Disposition", "Reason", "Maps_To_New"], [
 ["Title/Intro", "REBUILD", "reframe as STEP1-28 platform notebook", "S1 Platform Overview"],
 ["Architecture Overview", "REBUILD", "add ingestion/governance/extension + hardening", "S2 Architecture"],
 ["Strategic Pipeline", "PRESERVE", "still technically correct (STEP2)", "S3 Data Foundation"],
 ["Operational Pipeline", "PRESERVE", "correct (operational load)", "S3 Data Foundation"],
 ["Forecasting Results (STEP1-19)", "REBUILD", "replace zone forecast with STEP22-23 division forecast", "S5 Forecasting"],
 ["Inventory Optimization (STEP15)", "REBUILD", "replace with STEP24-26 SS/ROP/SRRS", "S8-S10"],
 ["Rationalization Results", "PRESERVE", "correct; relocate", "S11 Capital Exposure (context)"],
 ["Executive Dashboard (stale)", "RETIRE", "stale + STEP1-19 only", "S15 Executive Dashboard (new)"],
 ["Power BI Outputs (stale)", "RETIRE", "stale snapshot", "re-rendered live in notebook"],
 ["AnyLogistix Outputs", "PRESERVE", "correct; low priority", "appendix"],
 ["Production Readiness", "REBUILD", "replace with hardening results", "S14 Platform Hardening"],
 ["Key Limitations", "REBUILD", "post-hardening caveats", "S14/S16"],
 ["Recommended Next Steps", "REBUILD", "current roadmap", "S16 TPJ Readiness"],
 ["(none)", "CREATE", "demand reconstruction", "S4"],
 ["(none)", "CREATE", "lead-time analytics", "S6"],
 ["(none)", "CREATE", "criticality analytics", "S7"],
 ["(none)", "CREATE", "SRRS prioritization", "S10"],
 ["(none)", "CREATE", "procurement portfolio", "S12"],
 ["(none)", "CREATE", "business case", "S13"],
 ["(none)", "CREATE", "TPJ readiness", "S16"],
])

W("NOTEBOOK7_SECTION_STRUCTURE.csv", ["Num", "Section", "Primary_Datasets", "Business_Question"], [
 ("S1", "Platform Overview", "narrative", "What is this platform?"),
 ("S2", "Platform Architecture", "active_dependency_map", "How is it built?"),
 ("S3", "Data Foundation", "monthly_demand_history,enterprise_pl_master", "What data powers it?"),
 ("S4", "Demand Reconstruction", "monthly_demand_history", "How does MAS consume inventory?"),
 ("S5", "Forecasting", "forecast_results,demand_classification", "How forecastable is the universe?"),
 ("S6", "Lead-Time Analytics", "lead_time_master", "What drives replenishment delay?"),
 ("S7", "Criticality", "demand_classification,criticality", "How much is operationally critical?"),
 ("S8", "Safety Stock", "safety_stock_results", "What drives buffers?"),
 ("S9", "Reorder Point", "rop_results", "What should be reordered?"),
 ("S10", "SRRS Prioritization", "srss_results", "Where is service risk concentrated?"),
 ("S11", "Capital Exposure", "srss_results", "Where is capital at risk?"),
 ("S12", "Procurement Portfolio", "procurement_portfolio", "What to procure first?"),
 ("S13", "Business Case", "platform_scorecard,validation", "What was achieved?"),
 ("S14", "Platform Hardening", "platform_scorecard,migration", "Can it be maintained?"),
 ("S15", "Executive Dashboard", "executive_kpi_framework", "Executive decision support"),
 ("S16", "TPJ Readiness", "tpj_onboarding_readiness", "What blocks TPJ?"),
])

W("NOTEBOOK7_VISUALIZATION_CATALOG.csv", ["Section", "Chart_Type", "Visualization", "Business_Question", "Dataset"], [
 ("S2", "diagram", "architecture evolution core->extension->hardening", "How is the platform built?", "active_dependency_map"),
 ("S3", "bar", "source/PL/timeline coverage", "What data powers the platform?", "monthly_demand_history"),
 ("S4", "line", "54-month aggregate demand history", "How does MAS consume inventory?", "monthly_demand_history"),
 ("S4", "hist", "intermittency distribution", "How intermittent is demand?", "demand_classification"),
 ("S5", "bar", "forecast method mix SBA/TSB/Croston/Holt", "Which methods fit?", "forecast_results"),
 ("S5", "scatter", "ADI vs CV2 SBC quadrants", "How forecastable is the universe?", "demand_classification"),
 ("S5", "bar", "demand-class mix", "What demand patterns dominate?", "demand_classification"),
 ("S6", "hist", "lead-time distribution", "What drives replenishment delay?", "lead_time_master"),
 ("S6", "bar", "LT source mix PO vs Reqn", "Where do lead times come from?", "lead_time_master"),
 ("S7", "bar", "Critical vs Non-Critical split", "How much is operationally critical?", "rop_results"),
 ("S8", "hist", "safety-stock distribution", "What drives buffers?", "safety_stock_results"),
 ("S8", "bar", "SS critical vs non-critical mean", "Does criticality drive SS?", "safety_stock_results"),
 ("S9", "pie", "stock-status distribution 465 critical", "What should be reordered?", "rop_results"),
 ("S9", "barh", "top-15 reorder gaps", "Which items are most short?", "rop_results"),
 ("S10", "line", "SRRS Pareto/Lorenz top-10=84.5%", "Where is service risk concentrated?", "srss_results"),
 ("S10", "barh", "Top-20 SRRS items", "Who are the priority items?", "srss_results"),
 ("S11", "barh", "top capital exposure gap value", "Where is capital at risk?", "srss_results"),
 ("S12", "bar", "5-tier portfolio PL count + SRRS%", "What to procure first?", "procurement_portfolio"),
 ("S12", "scatter", "risk vs value quadrant", "Risk-value segmentation?", "srss_results"),
 ("S13", "bar", "readiness/maturity progression", "What was achieved?", "platform_scorecard"),
 ("S14", "barh", "scorecard current vs target", "Can it be maintained?", "platform_scorecard"),
 ("S15", "scorecard", "L1 KPI cards + risk heatmap", "Executive decision support", "executive_kpi_framework"),
 ("S16", "barh", "TPJ readiness matrix READY/MINOR/MAJOR", "What blocks TPJ?", "tpj_onboarding_readiness"),
])

s = ds.compute_kpis()
rows = []
for lvl in ("L1", "L2", "L3"):
    for it in s[lvl]:
        rows.append([lvl, it["KPI"], str(it["Value"]), it["Source"]])
W("NOTEBOOK7_KPI_FRAMEWORK.csv", ["Level", "KPI", "Value", "Source"], rows)

W("MANAGEMENT_SUMMARY_KPI_MAPPING.csv", ["Level", "KPI", "Source_Output", "Legacy_Consumed", "STEP"], [
 ("L1", "Forecast Coverage %", "forecast_results.csv", "No", "STEP23"),
 ("L1", "Lead-Time Coverage %", "lead_time_master.csv", "No", "STEP23.6B"),
 ("L1", "Current Stock Value", "srss_results.csv", "No", "STEP25.5"),
 ("L1", "Reorder Gap Value", "srss_results.csv", "No", "STEP25"),
 ("L1", "Total SRRS", "srss_results.csv", "No", "STEP26"),
 ("L1", "Top-10 Concentration", "srss_results.csv", "No", "STEP26"),
 ("L1", "Tier 1/2 Count", "procurement_portfolio.csv", "No", "STEP27"),
 ("L1", "Platform Readiness", "platform_scorecard.csv", "No", "Hardening"),
 ("L2", "Critical Shortages", "rop_results.csv", "No", "STEP25"),
 ("L2", "Excess Inventory", "rop_results.csv", "No", "STEP25"),
 ("L2", "Open Procurement Exposure", "procurement_portfolio.csv", "No", "STEP27"),
 ("L2", "Service Levels", "rop_results.csv", "No", "STEP24"),
 ("L3", "Forecast Method Mix", "forecast_results.csv", "No", "STEP22"),
 ("L3", "Demand Class Mix", "demand_classification.csv", "No", "STEP22"),
 ("L3", "Criticality Distribution", "rop_results.csv", "No", "STEP23.8"),
 ("L3", "LT Source Mix", "lead_time_master.csv", "No", "STEP23.6B"),
 ("meta", "Platform/Division/DataDate/Commit/Score", "division_summary.metadata", "No", "STEP30"),
])

W("MANAGEMENT_SUMMARY_SECTION_STRUCTURE.csv", ["Section", "Purpose", "KPI_Level", "Source"], [
 ("Metadata Header", "provenance version/division/date/commit/score", "meta", "division_summary.metadata"),
 ("Executive Snapshot", "L1 headline KPIs", "L1", "division_summary L1"),
 ("Operational Status", "shortages/excess/exposure/service", "L2", "division_summary L2"),
 ("Technical Profile", "method/class/criticality/LT mix", "L3", "division_summary L3"),
 ("Risk Concentration", "SRRS top-10 + tiers", "L1", "srss/procurement_portfolio"),
 ("Capital Exposure", "stock vs gap value", "L1", "srss_results"),
 ("Platform Readiness", "scorecard + hardening", "L1", "platform_scorecard"),
 ("Division Comparison", "MAS now; MAS-vs-TPJ when ready", "L1", "division registry"),
])
print("all STEP30 planning CSVs generated")
