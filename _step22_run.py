"""STEP22 driver: backward-compat hash guard + run + reproducibility + validation."""
import hashlib, sys
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_config as cfg
from railway import railway_demand_classification as dc

OUT = cfg.OUTPUT_DIR
NEW = {"MAS/history/demand_classification.csv", "MAS/history/xyz_classification.csv",
       "MAS/history/forecast_method_assignment.csv"}

print("ADI_CUTOFF:", cfg.ADI_CUTOFF, "CV2_CUTOFF:", cfg.CV2_CUTOFF)

def tree(exclude):
    h = {}
    for p in sorted(OUT.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(OUT)).replace("\\", "/")
        if rel in exclude:
            continue
        h[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return h

before = tree(NEW)
art1 = dc.build(write=True)
after = tree(NEW)
changed = [k for k in before if before[k] != after.get(k)]
removed = [k for k in before if k not in after]
added = [k for k in after if k not in before]
print("\n=== Backward-compatibility (existing outputs, excl 3 new files) ===")
print(f"  fingerprinted={len(before)} changed={len(changed)} removed={len(removed)} added={len(added)} UNCHANGED={not changed and not removed and not added}")
if changed: print("  CHANGED:", changed[:10])

# Reproducibility: run again, hash the 3 outputs both times
def hsh(rel): return hashlib.sha256((OUT/rel).read_bytes()).hexdigest()
h1 = {r: hsh(r) for r in NEW}
art2 = dc.build(write=True)
h2 = {r: hsh(r) for r in NEW}
print("\n=== Reproducibility ===")
print("  identical on re-run:", h1 == h2)

d = art1["demand"]; m = art1["method"]; x = art1["xyz"]
print("\n=== Coverage / integrity ===")
print(f"  PLs classified (demand): {len(d)}  | unique PL: {d['PL_Code'].nunique()}")
print(f"  every PL has a Demand_Class: {d['Demand_Class'].notna().all()}")
print(f"  every PL exactly one method: {len(m)==m['PL_Code'].nunique() and m['Forecast_Method'].notna().all()}")
valid_classes={'Smooth','Erratic','Intermittent','Lumpy','Dead'}
print(f"  all classes valid: {set(d['Demand_Class'])<=valid_classes}")
valid_methods={'SES/Holt','Croston','SBA','TSB','No Forecast'}
print(f"  all methods valid: {set(m['Forecast_Method'])<=valid_methods}")
# class->method consistency
mp={'Smooth':'SES/Holt','Erratic':'Croston','Intermittent':'SBA','Lumpy':'TSB','Dead':'No Forecast'}
merged=m.set_index('PL_Code')['Forecast_Method'].to_dict()
dcl=d.set_index('PL_Code')['Demand_Class'].to_dict()
bad=[pl for pl in dcl if merged[pl]!=mp[dcl[pl]]]
print(f"  class->method mapping consistent: {len(bad)==0}")

print("\n=== Distributions ===")
print("  Demand pattern:", d['Demand_Class'].value_counts().to_dict())
print("  Forecast method:", m['Forecast_Method'].value_counts().to_dict())
print("  XYZ:", x['XYZ_Class'].value_counts().to_dict())

# Top intermittent / lumpy by total issues (join total)
hist=pd.read_csv(OUT/"MAS/history/monthly_demand_history.csv",dtype={"PL_Code":str},keep_default_na=False)
tot=hist.groupby("PL_Code")["Issues_Qty"].sum()
dd=d.set_index("PL_Code")
for cls in ["Intermittent","Lumpy"]:
    sub=dd[dd["Demand_Class"]==cls].copy(); sub["Total_Issues"]=tot
    sub=sub.sort_values("Total_Issues",ascending=False).head(5)
    print(f"\n  Top 5 {cls} (by total issues):")
    for pl,r in sub.iterrows():
        print(f"    {pl} ADI={r['ADI']} CV2={r['CV2']} total={r['Total_Issues']:.0f}  {str(r['Description'])[:34]}")
