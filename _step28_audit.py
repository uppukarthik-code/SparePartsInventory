"""STEP 28 Enterprise Deployment & Business Case synthesis (READ-ONLY; no analytics, no synthetic savings)."""
import sys, hashlib
sys.path.insert(0, ".")
from railway import railway_config as cfg
import pandas as pd

H = cfg.OUTPUT_DIR / "MAS" / "history"
NEW = {f"MAS/history/{f}" for f in ["executive_summary.csv","benefits_realization.csv",
       "risk_concentration_analysis.csv","management_action_plan.csv",
       "enterprise_rollout_strategy.csv","business_case_assessment.csv","maturity_assessment.csv"]}
def tree(excl):
    h={}
    for p in sorted(cfg.OUTPUT_DIR.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(cfg.OUTPUT_DIR)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree(NEW)
def rd(p): return pd.read_csv(p,dtype={"PL_Code":str},keep_default_na=False)
srss=rd(H/"srss_results.csv")
for c in ["SRRS","Positive_Gap","Reorder_Gap_Value_Rs"]: srss[c]=pd.to_numeric(srss[c],errors="coerce")

# ---- PART C: concentration (computed) ----
def topn_share(col,n):
    s=srss.sort_values(col,ascending=False)[col]; t=s.sum()
    return round(100*s.head(n).sum()/t,1) if t else 0.0
conc=[]
for metric,col in [("Service_Risk_SRRS","SRRS"),("Reorder_Gap_Units","Positive_Gap"),("Reorder_Gap_Value_Rs","Reorder_Gap_Value_Rs")]:
    conc.append({"Metric":metric,"Total":round(srss[col].sum(),0),
                 "Top10_Pct":topn_share(col,10),"Top20_Pct":topn_share(col,20),"Top50_Pct":topn_share(col,50),
                 "Catalogue_PLs":len(srss)})
pd.DataFrame(conc).to_csv(H/"risk_concentration_analysis.csv",index=False)

# ---- PART B: benefits realization (coverage progression, evidence-based) ----
B=[
 ["Demand visibility (monthly)","0% (zone, 5 annual pts)","100% (1083 PLs, 54 mo)","100%","100%","100%","100%","100%","100%"],
 ["Forecast coverage","0% (zone-shared)","-","-","88.7% (961/1083)","88.7%","88.7%","88.7%","88.7%"],
 ["Lead-time coverage (PL)","0%","0%","64.8% (96% vol)","64.8%","64.8%","64.8%","64.8%","64.8%"],
 ["Current-stock visibility","1.8% (depot 027029)","1.8%","1.8%","1.8%","99.6% (depot 027534)","99.6%","99.6%","99.6%"],
 ["Criticality coverage","3% (59 strategic)","3%","3%","99.6% (binary)","99.6%","99.6%","99.6%","99.6%"],
 ["Safety-stock coverage","0%","0%","0%","0%","65.1% (96% vol)","65.1%","65.1%","65.1%"],
 ["ROP coverage","0%","0%","0%","0%","0%","65.1% (96% vol)","65.1%","65.1%"],
 ["SRRS prioritization","0% (zone-shared)","0%","0%","0%","0%","0%","65.1% (96% vol)","65.1%"],
]
pd.DataFrame(B,columns=["Dimension","STEP20","STEP23_5","STEP23_6B","STEP23_8","STEP24","STEP25","STEP26","STEP27"]).to_csv(H/"benefits_realization.csv",index=False)

# ---- PART A: executive summary ----
A=[
 ("Initial state (STEP20)","Zone-level planning only; no division-level demand/forecast/SS/ROP/SRRS; readiness ~48%"),
 ("Final state (STEP27)","MAS full division planning stack live: demand->forecast->LT->SS->ROP->SRRS + portfolio + dashboard design; 96% forecast volume"),
 ("Blocker found 1","No multi-year per-division demand history (zone-only)"),
 ("Blocker found 2","Lead time 0% (no stored field)"),
 ("Blocker found 3","Demand vs inventory universe mismatch (depot 027534 vs 027029)"),
 ("Blocker found 4","Criticality 3% (59 strategic items only)"),
 ("Resolved 1","54-month demand reconstructed from DMTR (STEP21A)"),
 ("Resolved 2","Lead time derived internally from PO/Reqn->Receipt (STEP23.6B, 96% vol)"),
 ("Resolved 3","Depot-027534 stock snapshot found -> 99.6% stock coverage (STEP23.7-data)"),
 ("Resolved 4","Criticality reconstructed (binary Safety/Vital/NA, 99.6%, STEP23.8)"),
 ("Key outcome","626 PLs planned (96% volume); 6 dual-priority + 86 Tier1-2 = 87.6% of service risk"),
 ("Limitation 1","Lead-time tail: 35% of PLs (4% of volume) lack derived LT"),
 ("Limitation 2","Criticality binary only (S1-S4 granularity pending)"),
 ("Limitation 3","Issuing-depot context inflates absolute shortage counts (relative rank valid)"),
 ("Limitation 4","5 divisions data-blocked (no DMTR)"),
 ("Recommended action","Procure Tier1-2; stand up dashboard; acquire per-division DMTR+SUMMARY for rollout"),
]
pd.DataFrame(A,columns=["Aspect","Assessment"]).to_csv(H/"executive_summary.csv",index=False)

# ---- PART D: management action plan ----
D=[
 ("Tier1_Dual_Priority",6,"Procure immediately; net open POs; expedite","Sr.DMM / COS (illustrative)","Weekly","Divisional / HQ Stores"),
 ("Tier2_HighRisk_HighValue",80,"Procure next cycle; budget allocation","Depot Material Supt (illustrative)","Fortnightly","Sr.DMM"),
 ("Tier3_HighRisk_Only",70,"Service quick-wins (low-cost critical cables)","Section Stores Officer (illustrative)","Monthly","Depot Material Supt"),
 ("Tier4_HighValue_Only",70,"Capital review; avoid bulk over-buy","Stores + Finance review (illustrative)","Quarterly","Sr.DMM / Finance"),
 ("Tier5_Routine",400,"Min/max policy; monitor","Depot routine (illustrative)","Quarterly","Section Stores"),
]
pd.DataFrame(D,columns=["Tier","PL_Count","Recommended_Action","Owner_Illustrative","Review_Frequency","Escalation_Level"]).to_csv(H/"management_action_plan.csv",index=False)

# ---- PART E: enterprise rollout strategy ----
E=[
 ("TPJ",1,"DMTR registers, SUMMARY OF STOCK HELD, (NS_DM_CONS)","stock_history only","~90-96% if DMTR depth ~ MAS","Low (~1-2 wk, pipeline reusable)","largest division (1355 ops) -> high value","DMTR data quality, depot stock mapping"),
 ("TVC",2,"DMTR, SUMMARY","stock_history only","~90-96%","Low (~1-2 wk)","highest dead-stock value -> rationalization upside","same as above"),
 ("SA",3,"DMTR, SUMMARY","stock_history only","~90-96%","Low (~1-2 wk)","smaller universe","data acquisition"),
 ("MDU",4,"DMTR, SUMMARY","stock_history only","~90-96%","Low (~1-2 wk)","-","data acquisition"),
 ("PGT",5,"DMTR, SUMMARY","stock_history only","~90-96%","Low (~1-2 wk)","Podanur strategic-stock gap (STEP19)","data acquisition + criticality"),
]
pd.DataFrame(E,columns=["Division","Deployment_Sequence","Required_Datasets","Missing_Datasets","Expected_Coverage","Estimated_Effort","Rationale","Risks_Dependencies"]).to_csv(H/"enterprise_rollout_strategy.csv",index=False)

# ---- PART F: business case (qualitative, evidence-tagged; NO invented savings) ----
F=[
 ("Inventory optimization","Qualitative-High","626 PLs now have SS+ROP; 60 excess items + capital-protect Tier4 (Rs385M) identified for review"),
 ("Shortage reduction","Qualitative-High","465 critical shortages now visible & prioritized (previously invisible at division level)"),
 ("Planning visibility","Quantified","Forecast/planning coverage 0% -> 96% of MAS forecast volume"),
 ("Procurement prioritization","Quantified","6 dual-priority + 86 Tier1-2 PLs carry 87.6% of service risk -> focused worklist"),
 ("Management reporting","Qualitative","7-view dashboard designed on existing CSVs (no build cost beyond BI tool)"),
 ("Risk reduction","Quantified","Top-10 PLs = 84.5% of service risk now actionable; risk made explicit & rankable"),
 ("Capital exposure transparency","Quantified-Evidence","Reorder-gap exposure Rs3.37B and depot stock Rs290M now visible (exposure, NOT a savings claim)"),
]
pd.DataFrame(F,columns=["Benefit","Type","Evidence"]).to_csv(H/"business_case_assessment.csv",index=False)

# ---- PART G: maturity (0-5) ----
G=[
 ("Demand Planning",1,4),("Forecasting",1,4),("Lead Time",0,3),("Inventory Visibility",1,4),
 ("Criticality",1,3),("Safety Stock",0,4),("ROP",0,4),("Prioritization (SRRS)",1,4),
 ("Dashboard Readiness",0,3),("Enterprise Rollout Readiness",0,2),
]
gdf=pd.DataFrame(G,columns=["Dimension","Before_STEP20","After_STEP27"]); gdf["Delta"]=gdf["After_STEP27"]-gdf["Before_STEP20"]
gdf.to_csv(H/"maturity_assessment.csv",index=False)

after=tree(NEW); changed=[k for k in before if before[k]!=after.get(k)]
print("backward-compat changed:",len(changed),"UNCHANGED:",not changed)
print("\nCONCENTRATION:"); print(pd.DataFrame(conc).to_string(index=False))
print("\nMATURITY:"); print(gdf.to_string(index=False))
print("\navg maturity before:",round(gdf.Before_STEP20.mean(),1),"-> after:",round(gdf.After_STEP27.mean(),1))
