"""STEP 23.5 Planning Master Data audit (READ-ONLY; no synthetic values, no estimation)."""
import glob, sys
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_config as cfg
from railway import railway_demand_reconstruction as dr   # reuse raw-XML reader only

H = cfg.OUTPUT_DIR / "MAS" / "history"
MAS = cfg.OUTPUT_DIR / "MAS"
ROLL = cfg.OUTPUT_DIR / "_enterprise_rollup"

def rd(p, **kw): return pd.read_csv(p, dtype={"PL_Code": str}, keep_default_na=False, **kw)

dc   = rd(H / "demand_classification.csv")            # 1083 universe
fma  = rd(H / "forecast_method_assignment.csv")
fr   = rd(H / "forecast_results.csv")
fa   = rd(H / "forecast_accuracy.csv")
skum = rd(MAS / "railway_sku_master.csv")             # strategic 59 (criticality/ABC/pending)
opv  = rd(MAS / "railway_operational_inventory.csv")  # operational 907 (stock/unit_cost/value)
alloc= rd(ROLL / "strategic_inventory_allocation.csv")

universe = list(dc["PL_Code"])
N = len(universe)
desc = dc.set_index("PL_Code")["Description"].to_dict()
method = fma.set_index("PL_Code")["Forecast_Method"].to_dict()
fclass = fa.set_index("PL_Code")["Forecastability_Class"].to_dict()
f2627 = fr.set_index("PL_Code")["Forecast_2026_27"].to_dict()
crit = skum.set_index("PL_Code")["Criticality"].to_dict()
abc = skum.set_index("PL_Code")["ABC_Class"].to_dict()
pend = skum.set_index("PL_Code")["Pending_Supply"].to_dict()
sku_uc = skum.set_index("PL_Code")["Unit_Cost"].to_dict()
sku_cs = skum.set_index("PL_Code")["Current_Stock"].to_dict()
op_cs = opv.set_index("PL_Code")["Current_Stock"].to_dict()
op_uc = opv.set_index("PL_Code")["Unit_Cost"].to_dict()
op_iv = opv.set_index("PL_Code")["Inventory_Value"].to_dict()
strat = alloc[alloc["Business_Unit"]=="MAS"].set_index("PL_Code")["Strategic_Stock"].to_dict()

CRIT_NAME = {"S1":"Safety","S2":"Vital","S3":"Essential","S4":"Desirable"}  # fixed code->label

# supplier / procurement coverage from DMTR receipts
supplier_pls=set(); procurement_pls=set()
for fp in sorted(glob.glob(str(dr.DMTR_DIR/"DMTR_*.xlsx"))):
    for row in dr._sheet_rows(fp)[1:]:
        pl=str(row.get(6) or "").strip()
        if not pl: continue
        t=str(row.get(3) or "")
        if t.startswith("Receipt"):
            procurement_pls.add(pl)
            detail=str(row.get(8) or "")
            if t.startswith("Receipt-From Vendor") or ("From" in detail and any(c.isdigit() for c in detail)):
                supplier_pls.add(pl)

def has(v):
    return v not in (None,"","nan") and not (isinstance(v,float) and pd.isna(v))

rows=[]
for pl in universe:
    c = crit.get(pl,"")
    rows.append({
        "PL_Code": pl,
        "Description": desc.get(pl,""),
        "Business_Unit": "MAS",
        "Criticality": c,
        "Criticality_Name": CRIT_NAME.get(c,""),
        "ABC_Class": abc.get(pl,""),
        "Forecast_Method": method.get(pl,""),
        "Forecastability_Class": fclass.get(pl,""),
        "Forecast_2026_27": f2627.get(pl,""),
        "Current_Stock": op_cs.get(pl, sku_cs.get(pl,"")),
        "Strategic_Stock": strat.get(pl,""),
        "Operational_Stock": op_cs.get(pl,""),
        "Lead_Time_Months": "",            # NO native stored field anywhere (derived only)
        "Pending_Supply": pend.get(pl,""),
        "Unit_Cost": op_uc.get(pl, sku_uc.get(pl,"")),
        "Inventory_Value": op_iv.get(pl,""),
        "Supplier_Info": "Yes" if pl in supplier_pls else "",
        "Procurement_History": "Yes" if pl in procurement_pls else "",
    })
df=pd.DataFrame(rows)
df.to_csv(H/"planning_master_data_audit.csv", index=False)

fields=["Description","Business_Unit","Criticality","Criticality_Name","ABC_Class",
        "Forecast_Method","Forecastability_Class","Forecast_2026_27","Current_Stock",
        "Strategic_Stock","Operational_Stock","Lead_Time_Months","Pending_Supply",
        "Unit_Cost","Inventory_Value","Supplier_Info","Procurement_History"]
print(f"Planning master universe (DMTR demand PLs): {N}")
print(f"{'Field':22} {'Populated':>9} {'Missing':>8} {'Coverage%':>9}")
cov={}
for f in fields:
    pop=int(df[f].apply(has).sum()); miss=N-pop; pct=round(100*pop/N,1)
    cov[f]=pct
    print(f"  {f:20} {pop:>9} {miss:>8} {pct:>8.1f}%")

# key-universe overlaps
print("\nKey-universe overlaps (of 1083 DMTR PLs):")
print(f"  in strategic sku_master (criticality/ABC/pending): {len(set(universe)&set(skum['PL_Code']))}")
print(f"  in operational_inventory (stock/unit_cost)       : {len(set(universe)&set(opv['PL_Code']))}")
print(f"  in strategic_allocation (strategic stock)        : {len(set(universe)&set(strat))}")
print(f"  supplier (vendor receipt in DMTR)                : {len(supplier_pls&set(universe))}")
print(f"  procurement history (any receipt in DMTR)        : {len(procurement_pls&set(universe))}")
print("\nHeadline coverages:")
print(f"  Criticality      : {cov['Criticality']}%")
print(f"  Lead-time(native): {cov['Lead_Time_Months']}%")
print(f"  Pending-supply   : {cov['Pending_Supply']}%")
print(f"  Supplier         : {cov['Supplier_Info']}%")
print(f"  Procurement-hist : {cov['Procurement_History']}%")
print(f"  Unit_Cost        : {cov['Unit_Cost']}%")
print(f"  Forecast_2026_27 : {cov['Forecast_2026_27']}%")
print("WROTE:", H/"planning_master_data_audit.csv")
