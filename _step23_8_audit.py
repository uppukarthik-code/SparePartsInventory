"""STEP 23.8 Criticality Signal Discovery (READ-ONLY; no synthetic criticality, no logic change)."""
import os, sys, re, hashlib
sys.path.insert(0, r"C:\Users\uppuk\SparePartsInventory")
from railway import railway_demand_reconstruction as dr
from railway import railway_config as cfg
import pandas as pd
from collections import Counter

d=r"C:\Users\uppuk\SparePartsInventory\raw_data\Railway_Operations\MAS"
H=cfg.OUTPUT_DIR/"MAS"/"history"; MASd=cfg.OUTPUT_DIR/"MAS"
SUMF=os.path.join(d,"SUMMARY OF STOCK HELD (as on 08-06-2026) _08-06-2026.xlsx")
NEW={f"MAS/history/{f}" for f in ["criticality_field_inventory.csv","criticality_signal_candidates.csv","criticality_signal_validation.csv"]}
def tree(excl):
    h={}
    for p in sorted(cfg.OUTPUT_DIR.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(cfg.OUTPUT_DIR)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree(NEW)

def rd(p): return pd.read_csv(p,dtype=str,keep_default_na=False)
def num(x):
    try:return float(str(x).replace(",",""))
    except:return None

s=dr._sheet_rows(SUMF); hdr=s[0]; rows=[r for r in s[1:] if r.get(4)]
N=len(rows)
HEAD={k:hdr[k] for k in sorted(hdr)}

# ---- PART A: field inventory ----
fa=[]
for k in sorted(hdr):
    vals=[str(r.get(k)) for r in rows if r.get(k) is not None and str(r.get(k))!=""]
    nn=len(vals); nulls=N-nn
    isnum=all(num(v) is not None for v in vals) if vals else False
    fa.append({"Column":HEAD[k],"Col_Index":k,"Datatype":"numeric" if isnum else "text",
               "Unique_Values":len(set(vals)),"Null_Count":nulls,"Coverage_Pct":round(100*nn/N,1)})
pd.DataFrame(fa).to_csv(H/"criticality_field_inventory.csv",index=False)

# ---- parse Type / Usage from col4, Stock-class from col5 ----
def parse4(v):
    parts=[p.strip() for p in str(v).split('/')]
    pl=parts[0].strip()
    tail=" / ".join(parts[1:]).lower()
    if 'safety' in tail: typ='Safety Item'
    elif 'vital' in tail: typ='Vital Item'
    elif tail.strip().startswith('na'): typ='NA'
    else: typ='Unknown'
    usage='Others'
    for u in ['M&P Spares','M&P','T&P','Consumable','Others']:
        if u.lower() in tail: usage=u; break
    return pl,typ,usage
recs=[]
for r in rows:
    pl,typ,usage=parse4(r.get(4))
    sc=str(r.get(5) or "").split('/')[0].strip()
    recs.append({"PL":pl,"Type":typ,"Usage":usage,"StockClass":sc,
                 "Stock":num(r.get(8)) or 0.0,"Value":num(r.get(12)) or 0.0})
df=pd.DataFrame(recs)

# DMTR demand + forecast volume
dc=rd(H/"demand_classification.csv"); DMTR=set(dc["PL_Code"])
fr=rd(H/"forecast_results.csv"); fvol=dict(zip(fr["PL_Code"],fr["Forecast_2026_27"].map(lambda x:num(x) or 0)))
totvol=sum(fvol.values()); totval=df["Value"].sum()

# ---- PART B: candidate signals ----
cand=[]
def block(col):
    for val,sub in df.groupby(col):
        pls=set(sub["PL"])
        cand.append({"Signal":col,"Value":val,"PL_Count":len(pls),
            "PL_Coverage_Pct":round(100*len(pls)/len(DMTR),1),
            "Forecast_Vol_Coverage_Pct":round(100*sum(fvol.get(p,0) for p in pls)/totvol,1) if totvol else 0,
            "Stock_Value_Coverage_Pct":round(100*sub["Value"].sum()/totval,1) if totval else 0,
            "Stock_Value_Rs":round(sub["Value"].sum(),0)})
block("Type"); block("Usage"); block("StockClass")
pd.DataFrame(cand).to_csv(H/"criticality_signal_candidates.csv",index=False)

# ---- PART C: validate vs 59 known criticality ----
sk=rd(MASd/"railway_sku_master.csv")
known={p:(c,sf) for p,c,sf in zip(sk["PL_Code"],sk["Criticality"],sk["Safety_Flag"]) if c.strip()}
typ_by_pl=dict(zip(df["PL"],df["Type"]))
common=set(typ_by_pl)&set(known)
# predictor: SUMMARY Type in {Safety Item, Vital Item} => "critical"; truth: sku Safety_Flag=='Yes' OR Criticality in {S1,S2}
val_rows=[]; tp=fp=fn=tn=0
cross=Counter()
for pl in common:
    t=typ_by_pl[pl]; crit,sf=known[pl]
    pred_crit = t in ('Safety Item','Vital Item')
    true_crit = (sf=='Yes') or (crit in ('S1','S2'))
    cross[(t,crit,sf)]+=1
    if pred_crit and true_crit: tp+=1
    elif pred_crit and not true_crit: fp+=1
    elif not pred_crit and true_crit: fn+=1
    else: tn+=1
prec=tp/(tp+fp) if (tp+fp) else 0; rec=tp/(tp+fn) if (tp+fn) else 0
strength=("Strong" if prec>=0.8 and rec>=0.8 else "Moderate" if prec>=0.6 and rec>=0.6 else "Weak" if (tp+tn)>0 else "Not usable")
val_rows.append({"Candidate_Signal":"col4 Type (Safety/Vital vs NA)","Compared_To":"59 strategic S1-S4 items",
   "Common_PLs":len(common),"TP":tp,"FP":fp,"FN":fn,"TN":tn,
   "Precision":round(prec,3),"Recall":round(rec,3),"Strength":strength})
pd.DataFrame(val_rows).to_csv(H/"criticality_signal_validation.csv",index=False)

after=tree(NEW)
changed=[k for k in before if before[k]!=after.get(k)]
print("backward-compat changed:",len(changed),"UNCHANGED:",not changed)
print("\n=== PART A field inventory ===");
for r in fa: print(f"  {r['Column']:32s} {r['Datatype']:7s} uniq={r['Unique_Values']:5d} cov={r['Coverage_Pct']}%")
print("\n=== PART B Type distribution ===")
for r in [c for c in cand if c['Signal']=='Type']:
    print(f"  {r['Value']:14s} PL={r['PL_Count']:4d} ({r['PL_Coverage_Pct']}% univ)  fvol={r['Forecast_Vol_Coverage_Pct']}%  stockval={r['Stock_Value_Coverage_Pct']}% (Rs{r['Stock_Value_Rs']:,.0f})")
print("  Usage:",{r['Value']:r['PL_Count'] for r in cand if r['Signal']=='Usage'})
print("  StockClass:",{r['Value']:r['PL_Count'] for r in cand if r['Signal']=='StockClass'})
typ_cov=df[df['Type'].isin(['Safety Item','Vital Item','NA'])]
print(f"\n  Classified (Safety/Vital/NA) PL coverage of demand universe: {100*len(set(typ_cov['PL'])&DMTR)/len(DMTR):.1f}%")
print(f"  Safety+Vital PL coverage of demand universe: {100*len(set(df[df.Type.isin(['Safety Item','Vital Item'])]['PL'])&DMTR)/len(DMTR):.1f}%")
print("\n=== PART C validation vs 59 known ===")
print("  common PLs:",len(common),"TP",tp,"FP",fp,"FN",fn,"TN",tn,"prec",round(prec,2),"rec",round(rec,2),"->",strength)
print("  cross (Type, Criticality, Safety_Flag):")
for k,v in cross.most_common(): print("    ",k,v)
print("  sku_master criticality dist:",Counter(c for c,_ in known.values()))
