"""STEP 25.5 Inventory Value Signal Discovery (READ-ONLY; no synthetic costs, no logic change)."""
import os, sys, hashlib
sys.path.insert(0, ".")
from railway import railway_demand_reconstruction as dr
from railway import railway_config as cfg
import pandas as pd
from collections import Counter

H=cfg.OUTPUT_DIR/"MAS"/"history"
SUM=cfg.RAW_DATA_DIR/"Railway_Operations"/"MAS"/"SUMMARY OF STOCK HELD (as on 08-06-2026) _08-06-2026.xlsx"
NEW={f"MAS/history/{f}" for f in ["inventory_value_field_inventory.csv","inventory_value_candidates.csv","inventory_value_linkage.csv"]}
def tree(excl):
    h={}
    for p in sorted(cfg.OUTPUT_DIR.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(cfg.OUTPUT_DIR)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree(NEW)

def num(x):
    try:return float(str(x).replace(",",""))
    except:return None
rows0=dr._sheet_rows(SUM); hdr=rows0[0]; rows=[r for r in rows0[1:] if r.get(4)]
N=len(rows)

# PART A field inventory
fa=[]
for k in sorted(hdr):
    vals=[str(r.get(k)) for r in rows if r.get(k) is not None and str(r.get(k))!=""]
    isnum=all(num(v) is not None for v in vals) if vals else False
    ex="; ".join(list(dict.fromkeys(vals))[:3])[:60]
    fa.append({"Column":hdr[k],"Data_Type":"numeric" if isnum else "text",
               "Null_Count":N-len(vals),"Coverage_Pct":round(100*len(vals)/N,1),"Example_Values":ex})
pd.DataFrame(fa).to_csv(H/"inventory_value_field_inventory.csv",index=False)

# per-PL value aggregates
rate={}; val={}; stock={}
for r in rows:
    pl=str(r.get(4)).split("/")[0].strip()
    ar=num(r.get(11)); vv=num(r.get(12)); st=num(r.get(8))
    if ar is not None: rate[pl]=max(rate.get(pl,0),ar)
    val[pl]=val.get(pl,0)+(vv or 0); stock[pl]=stock.get(pl,0)+(st or 0)
PL=set(rate)

# PART B candidates
def stats(field, mapd, denom):
    pos=[v for v in mapd.values() if v and v>0]
    return {"Candidate_Field":field,"Coverage_Pct":round(100*len(pos)/denom,1),
            "Distinct_Values":len(set(round(v,2) for v in pos)),
            "Min":round(min(pos),2) if pos else 0,"Max":round(max(pos),2) if pos else 0,
            "Median":round(sorted(pos)[len(pos)//2],2) if pos else 0,
            "Associated_PL_Coverage_Pct":round(100*len(pos)/len(PL),1)}
cand=[stats("Average Rate (Rs.) [unit cost]",rate,len(PL)),
      stats("Value (Rs.) [stock value]",val,len(PL))]
# consistency: Value vs Stock*Rate
mism=0; chk=0
for r in rows:
    ar=num(r.get(11)); vv=num(r.get(12)); st=num(r.get(8))
    if None not in (ar,vv,st):
        chk+=1
        if abs(vv-st*ar)>max(1.0,0.01*abs(vv)): mism+=1
pd.DataFrame(cand).to_csv(H/"inventory_value_candidates.csv",index=False)

# PART C linkage vs ROP
rop=pd.read_csv(H/"rop_results.csv",dtype={"PL_Code":str},keep_default_na=False)
ROP=set(rop["PL_Code"])
link=[
 {"Candidate_Field":"Average Rate (Rs.)","Link_PL_Code":"Yes (100%)","Link_Current_Stock":"Yes",
  "Link_ROP":f"Yes ({100*sum(1 for p in ROP if rate.get(p,0)>0)/len(ROP):.0f}% of 626)",
  "Link_Reorder_Gap":"Yes (Gap x Rate = Rs exposure)","Classification":"Directly Usable",
  "Comment":"unit cost; 100% coverage; works for zero-stock shortage items"},
 {"Candidate_Field":"Value (Rs.) stock value","Link_PL_Code":"Yes","Link_Current_Stock":"Yes (=Stock x Rate)",
  "Link_ROP":"Partial","Link_Reorder_Gap":"No (0 for zero-stock shortage items)","Classification":"Partially Usable",
  "Comment":"45.9% coverage (in-stock only); current-holding valuation, not gap valuation"},
]
pd.DataFrame(link).to_csv(H/"inventory_value_linkage.csv",index=False)

after=tree(NEW); changed=[k for k in before if before[k]!=after.get(k)]
print("backward-compat changed:",len(changed),"UNCHANGED:",not changed)
print("\nPART A fields:")
for r in fa: print(f"  {r['Column']:32s} {r['Data_Type']:7s} cov={r['Coverage_Pct']}% nulls={r['Null_Count']}")
print("\nPART B candidates:")
for c in cand: print(" ",c)
print(f"\nValue==Stock*Rate consistency: {chk-mism}/{chk} rows consistent ({100*(chk-mism)/chk:.1f}%)")
print("\nPART C linkage:")
for l in link: print(f"  {l['Candidate_Field']:26s} -> {l['Classification']}")
# scenario coverage
print("\nPART D scenario coverage (of 626 ROP PLs):")
print(f"  S1 units only        : 100% (626)")
print(f"  S2 +value(unit rate) : {100*sum(1 for p in ROP if rate.get(p,0)>0)/len(ROP):.1f}%")
crit=set(rop[rop['Criticality_Class'].isin(['Critical','Non-Critical'])]['PL_Code'])
print(f"  S3 +criticality      : {100*len(ROP&crit)/len(ROP):.1f}%")
# value-weighted gap preview (NOT a production ranking)
rop['g']=pd.to_numeric(rop['Reorder_Gap'],errors='coerce').fillna(0)
rop['rate']=rop['PL_Code'].map(lambda p:rate.get(p,0))
rop['gapval']=rop['g'].clip(lower=0)*rop['rate']
print(f"\n  total positive reorder-gap VALUE (Gap x Rate): Rs {rop['gapval'].sum():,.0f}")
print("  top 5 by gap-value:")
for _,x in rop.sort_values('gapval',ascending=False).head(5).iterrows():
    print(f"    {x['PL_Code']:>13} gapval=Rs{x['gapval']:>14,.0f} gap={x['g']:>8.0f} rate=Rs{x['rate']:,.0f} {str(x['Description'])[:24]}")
