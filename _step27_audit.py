"""STEP 27 Operational Validation, PO-Netting Readiness & Rollout (READ-ONLY)."""
import os, sys, glob, hashlib
sys.path.insert(0, ".")
from railway import railway_config as cfg
from railway import railway_demand_reconstruction as dr
import pandas as pd

H = cfg.OUTPUT_DIR / "MAS" / "history"
RAW = cfg.RAW_DATA_DIR / "Railway_Operations"
NEW = {f"MAS/history/{f}" for f in ["srrs_validation.csv","po_netting_feasibility.csv",
       "procurement_portfolio.csv","division_rollout_readiness.csv"]}
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
def num(x):
    try:return float(str(x).replace(",",""))
    except:return 0.0

srss=rd(H/"srss_results.csv")
dc=rd(H/"demand_classification.csv")
mwd=dict(zip(dc["PL_Code"],dc["Months_With_Demand"]))
# NS_DM_CONS PLs + open PO
ns_pls=set(); openpo={}
for fp in glob.glob(str(RAW/"MAS"/"NS_DM_CONS_REPORT*.xlsx")):
    for r in dr._sheet_rows(fp)[1:]:
        pl=str(r.get(11) or "").strip()
        if not pl: continue
        ns_pls.add(pl)
        if str(r.get(34) or "").strip():
            op=num(r.get(42))-num(r.get(47))
            if op>0: openpo[pl]=openpo.get(pl,0)+op

# ---- PART A: srrs_validation.csv (top 50) ----
top=srss.sort_values("SRRS_Rank").head(50).copy()
fa=srss["Forecast_Annual"].astype(float); fq=fa.quantile(0.75)
gq=srss["Positive_Gap"].astype(float).quantile(0.75)
rows=[]
for _,x in top.iterrows():
    f=float(x["Forecast_Annual"]); g=float(x["Positive_Gap"])
    rows.append({
        "PL_Code":x["PL_Code"],"Description":x["Description"],"SRRS_Rank":int(x["SRRS_Rank"]),
        "SRRS":x["SRRS"],"Criticality_Class":x["Criticality_Class"],
        "Forecast_Annual":f,"Months_With_Demand":mwd.get(x["PL_Code"],""),
        "Lead_Time_Days":x["Lead_Time_Days"],"Current_Stock":x["Current_Stock"],
        "ROP":x["ROP"],"Positive_Gap":g,"Value_Rank":int(x["Value_Rank"]),
        "In_Procurement_NS":"Yes" if x["PL_Code"] in ns_pls else "No",
        "High_Forecast":"Y" if f>=fq else "N","High_Gap":"Y" if g>=gq else "N",
        "Operational_Importance":("High" if (x["Criticality_Class"]=="Critical" and f>=fq and g>=gq)
                                  else "Medium" if (f>=fq or g>=gq) else "Low"),
    })
pd.DataFrame(rows).to_csv(H/"srrs_validation.csv",index=False)

# ---- PART B: po_netting_feasibility.csv ----
SR=set(srss["PL_Code"])
nb=[
 ("Net_Gap = ROP - Current_Stock - Open_PO_Qty","derived","-","-",
  "ROP(STEP25), Current_Stock(SUMMARY), Open_PO_Qty(NS_DM_CONS)","Feasible (mechanics)",
  "all three components exist; impact limited by Open_PO coverage below"),
 ("Open_PO_Qty = Item Qty - Qty Recd","NS_DM_CONS col42-col47",
  f"{round(100*len(ns_pls&SR)/len(SR),1)}% of 626 SRRS PLs",
  "178/232 have PO No; 155/232 have Qty Recd",
  "PL/Item Code, PO No, Item Qty, Qty Recd, Status","Partial",
  f"NS covers {len(ns_pls)} indent PLs; only {len(ns_pls&SR)} overlap SRRS; {len(set(openpo)&SR)} open-PO overlap"),
 ("Open PO universe coverage","NS_DM_CONS",f"{len(openpo)} PLs open-PO total",
  "indent-stage data, special/new items","NS_DM_CONS extract","Gap",
  "NS_DM_CONS tracks special/new-item indents, NOT the high-volume cable demand driving SRRS"),
]
pd.DataFrame(nb,columns=["Method_or_Field","Source","Coverage","Reliability","Required_Fields","Status","Comment"]).to_csv(H/"po_netting_feasibility.csv",index=False)

# ---- PART C: procurement_portfolio.csv (mutually exclusive tiers) ----
s=srss.copy(); s["F"]=s["Forecast_Annual"].astype(float); s["ROPn"]=s["ROP"].astype(float)
s["G"]=s["Positive_Gap"].astype(float); s["GV"]=s["Reorder_Gap_Value_Rs"].astype(float); s["SR"]=s["SRRS"].astype(float)
n=len(s); q=n//4
t20s=set(s.sort_values("SRRS_Rank").head(20)["PL_Code"]); t20v=set(s.sort_values("Value_Rank").head(20)["PL_Code"])
tier1=t20s&t20v
hr=set(s.sort_values("SRRS",ascending=False).head(q)["PL_Code"]); hv=set(s.sort_values("GV",ascending=False).head(q)["PL_Code"])
quad=hr&hv
tier2=quad-tier1; tier3=hr-quad; tier4=hv-quad
tier5=set(s["PL_Code"])-tier1-tier2-tier3-tier4
tot_srrs=s["SR"].sum()
def trow(name,pls):
    sub=s[s["PL_Code"].isin(pls)]
    return {"Tier":name,"PL_Count":len(sub),"Forecast_Volume":round(sub["F"].sum(),0),
            "ROP_Value_Units":round(sub["ROPn"].sum(),0),"Gap_Units":round(sub["G"].sum(),0),
            "Gap_Value_Rs":round(sub["GV"].sum(),0),
            "SRRS_Contribution_Pct":round(100*sub["SR"].sum()/tot_srrs,1) if tot_srrs else 0}
port=[trow("Tier1_Dual_Priority",tier1),trow("Tier2_HighRisk_HighValue",tier2),
      trow("Tier3_HighRisk_Only",tier3),trow("Tier4_HighValue_Only",tier4),trow("Tier5_Routine",tier5)]
pd.DataFrame(port).to_csv(H/"procurement_portfolio.csv",index=False)

# ---- PART E: division_rollout_readiness.csv ----
def has(div,pat): return len(glob.glob(str(RAW/div/pat)))>0
dr_rows=[]
for div in ["MAS","SA","TPJ","MDU","PGT","TVC"]:
    dmtr=has(div,"DMTR*.xlsx"); summ=has(div,"SUMMARY*"); proc=has(div,"NS_DM_CONS*")
    feas="Done (live)" if div=="MAS" else ("Feasible" if dmtr else "Blocked (no DMTR)")
    missing="-" if div=="MAS" else ", ".join([x for x,ok in [("DMTR registers",dmtr),("SUMMARY OF STOCK HELD",summ),("NS_DM_CONS",proc)] if not ok])
    dr_rows.append({"Division":div,"Has_DMTR":"Y" if dmtr else "N","Has_StockSummary":"Y" if summ else "N",
        "Has_Procurement_Feed":"Y" if proc else "N","Has_StockHistory":"Y" if has(div,"stock_history.xlsx") else "N",
        "STEP21A_Feasible":feas,"Missing_Data":missing,
        "Estimated_Effort":"-" if div=="MAS" else "Low once data supplied (pipeline reusable, ~1-2 wk/div)",
        "Expected_Coverage":"96% fcst vol (live)" if div=="MAS" else "~90-96% if DMTR depth ~ MAS"})
pd.DataFrame(dr_rows).to_csv(H/"division_rollout_readiness.csv",index=False)

after=tree(NEW); changed=[k for k in before if before[k]!=after.get(k)]
print("backward-compat changed:",len(changed),"UNCHANGED:",not changed)
print("\nPORTFOLIO:")
print(pd.DataFrame(port).to_string(index=False))
print("\nROLLOUT:")
print(pd.DataFrame(dr_rows)[["Division","Has_DMTR","Has_StockSummary","STEP21A_Feasible","Missing_Data"]].to_string(index=False))
print("\nPO NETTING coverage: NS-SRRS =",len(ns_pls&SR),"/626 ; open-PO-SRRS =",len(set(openpo)&SR))
oi=pd.DataFrame(rows)["Operational_Importance"].value_counts().to_dict()
print("\nTop-50 SRRS operational importance:",oi)
print("Top-50 in NS procurement:",sum(1 for r in rows if r["In_Procurement_NS"]=="Yes"))
