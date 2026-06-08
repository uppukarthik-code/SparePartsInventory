"""STEP 26 driver: SHA-256 backward-compat + run + validation + analysis."""
import hashlib, sys
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_config as cfg
from railway import railway_srrs_mas as srrs

OUT = cfg.OUTPUT_DIR
NEW = {"MAS/history/srss_results.csv", "MAS/history/srss_summary.csv"}
def tree(excl):
    h={}
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(OUT)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree(NEW)
res, summ = srrs.build(write=True)
after=tree(NEW)
changed=[k for k in before if before[k]!=after.get(k)]
print("=== Backward-compat (SHA-256, excl 2 new) ===")
print(f"  fingerprinted={len(before)} changed={len(changed)} added={len([k for k in after if k not in before])} UNCHANGED={not changed}")
def h(rel): return hashlib.sha256((OUT/rel).read_bytes()).hexdigest()
h1={r:h(r) for r in NEW}; srrs.build(); h2={r:h(r) for r in NEW}
print("  reproducible:", h1==h2)

print("\n=== Validation ===")
print(f"  no negative SRRS    : {(res['SRRS']>=0).all()}")
print(f"  no duplicate PLs    : {res['PL_Code'].is_unique}")
print(f"  SRRS_Rank unique    : {res['SRRS_Rank'].is_unique}  Value_Rank unique: {res['Value_Rank'].is_unique}")
print(f"  Positive_Gap>=0     : {(res['Positive_Gap']>=0).all()}")
print(f"  existing unchanged  : {not changed}")

print("\n=== Summary ===")
print(summ.to_string(index=False))

print("\n=== Top 10 SRRS (service risk) ===")
for _,x in res.head(10).iterrows():
    print(f"  #{x['SRRS_Rank']:>2} {x['PL_Code']:>13} SRRS={x['SRRS']:>12,.0f} gap={x['Positive_Gap']:>8.0f} {x['Criticality_Class']:<12} {str(x['Description'])[:26]}")
print("\n=== Top 10 VALUE (capital exposure) ===")
for _,x in res.sort_values('Value_Rank').head(10).iterrows():
    print(f"  #{x['Value_Rank']:>2} {x['PL_Code']:>13} Rs={x['Reorder_Gap_Value_Rs']:>16,.0f} rate=Rs{x['Average_Rate_Rs']:>10,.0f} {str(x['Description'])[:26]}")

# common to both top20
t20s=set(res.sort_values('SRRS_Rank').head(20)['PL_Code'])
t20v=set(res.sort_values('Value_Rank').head(20)['PL_Code'])
print(f"\n=== Top-20 overlap (SRRS ^ Value): {len(t20s&t20v)} PLs ===")
print("  common:", sorted(t20s&t20v))

# quadrant (top-quartile)
n=len(res); q=max(1,n//4)
hr=set(res.sort_values('SRRS',ascending=False).head(q)['PL_Code'])
hv=set(res.sort_values('Reorder_Gap_Value_Rs',ascending=False).head(q)['PL_Code'])
print(f"\n=== Quadrants (top-25% = {q} each) ===")
print(f"  High-Risk & High-Value (PROCURE FIRST): {len(hr&hv)}")
print(f"  High-Risk only: {len(hr-hv)}  | High-Value only: {len(hv-hr)}  | Neither: {n-len(hr|hv)}")

# criticality contribution
print("\n=== Critical vs Non-Critical contribution ===")
g=res.groupby('Criticality_Class').agg(PLs=('PL_Code','count'),SRRS=('SRRS','sum'),Val=('Reorder_Gap_Value_Rs','sum'))
g['SRRS%']=(100*g['SRRS']/g['SRRS'].sum()).round(1); g['Val%']=(100*g['Val']/g['Val'].sum()).round(1)
print(g.to_string())
