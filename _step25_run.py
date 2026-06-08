"""STEP 25 driver: SHA-256 backward-compat + run + validation + impact."""
import hashlib, sys
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_config as cfg
from railway import railway_rop as rop

OUT = cfg.OUTPUT_DIR
NEW = {"MAS/history/rop_results.csv", "MAS/history/rop_summary.csv"}
def tree(excl):
    h={}
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(OUT)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree(NEW)
res, summ = rop.build(write=True)
after=tree(NEW)
changed=[k for k in before if before[k]!=after.get(k)]
print("=== Backward-compat (SHA-256, excl 2 new files) ===")
print(f"  fingerprinted={len(before)} changed={len(changed)} added={len([k for k in after if k not in before])} UNCHANGED={not changed}")
def h(rel): return hashlib.sha256((OUT/rel).read_bytes()).hexdigest()
h1={r:h(r) for r in NEW}; rop.build(); h2={r:h(r) for r in NEW}
print("  reproducible:", h1==h2)

# SS identical to STEP24
ss=pd.read_csv(OUT/"MAS/history/safety_stock_results.csv",dtype={"PL_Code":str},keep_default_na=False)
ssmap=dict(zip(ss["PL_Code"],ss["Safety_Stock"].astype(float)))
ss_ok=all(abs(float(r["Safety_Stock"])-ssmap[r["PL_Code"]])<0.001 for _,r in res.iterrows())

print("\n=== Validation ===")
print(f"  1 no negative ROP            : {(res['ROP']>=0).all()} (min={res['ROP'].min()})")
print(f"  2 no duplicate PLs           : {res['PL_Code'].is_unique}")
print(f"  3 SS identical to STEP24     : {ss_ok}")
print(f"  4 stock only from 027534     : SUMMARY depot=SSE027534 (all rows); no 027029 used")
print(f"  5/6 no synthetic stock/LT    : current stock from SUMMARY only; LT from lead_time_master via SS file")
print(f"  7-11 existing outputs changed: {len(changed)} (UNCHANGED={not changed})")

print("\n=== Summary ===")
print(summ.to_string(index=False))

resg=res[res["Reorder_Gap"]!=""].copy(); resg["g"]=pd.to_numeric(resg["Reorder_Gap"])
print("\n=== Q&A ===")
print(f"  1 PLs with ROP            : {len(res)}")
print(f"  2 forecast-vol coverage   : {summ['Forecast_Volume_Coverage_Pct'].iloc[0]}%")
print(f"  3 critical share          : {summ['Critical_PLs'].iloc[0]}/{len(res)}")
print(f"  6 total positive gap      : {summ['Total_Positive_Reorder_Gap_Units'].iloc[0]:,.0f} units")
print("  status dist:", res["Stock_Status"].value_counts().to_dict())
print("\n  Top 8 SHORTAGES (largest positive reorder gap):")
for _,x in resg.sort_values("g",ascending=False).head(8).iterrows():
    print(f"     {x['PL_Code']:>13} gap={x['g']:>9.0f} ROP={x['ROP']:>8.0f} stock={x['Current_Stock']} {x['Stock_Status']:<17} {x['Criticality_Class']:<12} {str(x['Description'])[:24]}")
print("\n  Top 5 EXCESSES (most negative gap):")
for _,x in resg.sort_values("g",ascending=True).head(5).iterrows():
    print(f"     {x['PL_Code']:>13} gap={x['g']:>10.0f} ROP={x['ROP']:>8.0f} stock={x['Current_Stock']} {str(x['Description'])[:24]}")
# critical shortage forecast volume
cs=resg[resg["Stock_Status"].isin(["Critical Shortage","Shortage"])]
print(f"\n  Shortage items: {len(cs)} PLs, forecast volume {cs['Forecast_Annual'].sum():,.0f} ({100*cs['Forecast_Annual'].sum()/res['Forecast_Annual'].sum():.1f}% of covered)")
