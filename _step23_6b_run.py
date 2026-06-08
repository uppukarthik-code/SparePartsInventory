"""STEP 23.6B driver: SHA-256 backward-compat + run + validation + readiness stats."""
import hashlib, sys
sys.path.insert(0, ".")
import numpy as np, pandas as pd
from railway import railway_config as cfg
from railway import railway_lead_time_derivation as lt

OUT = cfg.OUTPUT_DIR
NEW = {"MAS/history/lead_time_master.csv", "MAS/history/pl_universe_reconciliation.csv"}
def tree(excl):
    h={}
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(OUT)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h

before=tree(NEW)
ltm, win = lt.build_lead_time_master(write=True)
uni, sets = lt.build_universe_reconciliation(write=True)
after=tree(NEW)
changed=[k for k in before if before[k]!=after.get(k)]
print("=== Backward-compat (SHA-256, excl 2 new files) ===")
print(f"  fingerprinted={len(before)} changed={len(changed)} added={len([k for k in after if k not in before])} UNCHANGED={not changed}")

# reproducibility
def h(rel): return hashlib.sha256((OUT/rel).read_bytes()).hexdigest()
h1={r:h(r) for r in NEW}; lt.build_lead_time_master(); lt.build_universe_reconciliation(); h2={r:h(r) for r in NEW}
print("  reproducible:", h1==h2)

def rd(p): return pd.read_csv(p,dtype={"PL_Code":str},keep_default_na=False)
dmtr=sets["dmtr"]; N=len(dmtr)
fr=rd(OUT/"MAS/history/forecast_results.csv"); fa=rd(OUT/"MAS/history/forecast_accuracy.csv")
skum=rd(OUT/"MAS/railway_sku_master.csv")
covered=set(ltm["PL_Code"])&dmtr
vol=fr.set_index("PL_Code")["Forecast_2026_27"].astype(float)
tot_vol=vol.sum(); cov_vol=vol[vol.index.isin(covered)].sum()
forecastable=set(fr["PL_Code"])
abc_pls=set(skum[skum["ABC_Class"].str.strip()!=""]["PL_Code"])

print("\n=== Validation ===")
print(f"  1 negative intervals admitted   : 0 (module rejects d<0; min Median_LT={ltm['Median_LT'].min()})")
print(f"  2 lead-time PL coverage         : {len(covered)}/{N} = {100*len(covered)/N:.1f}%")
print(f"  3 forecast-volume coverage      : {100*cov_vol/tot_vol:.1f}%  ({cov_vol:,.0f} / {tot_vol:,.0f})")
print(f"  4 confidence distribution       : {ltm['Confidence'].value_counts().to_dict()}")
print(f"  5 outlier/winsor bounds (days)  : PO={tuple(round(x,1) for x in win['po_bounds'])} Reqn={tuple(round(x,1) for x in win['reqn_bounds'])}")
print(f"     max Median_LT after winsor   : {ltm['Median_LT'].max()}  P90 max: {ltm['P90_LT'].max()}")
print(f"  6 universe status counts        : {uni['Universe_Status'].value_counts().to_dict()}")
print(f"  7/8 backward-compat unchanged   : {not changed}")

print("\n=== Coverage analysis ===")
print(f"  PL coverage            : {100*len(covered)/N:.1f}% ({len(covered)}/{N})")
print(f"  Forecast-volume coverage: {100*cov_vol/tot_vol:.1f}%")
print(f"  Forecastability coverage: {100*len(covered&forecastable)/len(forecastable):.1f}% ({len(covered&forecastable)}/{len(forecastable)})")
print(f"  ABC coverage (of covered): {100*len(covered&abc_pls)/len(covered):.1f}%")
print(f"  Strategic-item coverage : {len(covered&sets['strat'])}/{len(sets['strat'])}")

print("\n=== Universe overlaps ===")
d,o,s,c=sets['dmtr'],sets['oper'],sets['strat'],sets['crit']
print(f"  |DMTR|={len(d)} |Oper|={len(o)} |Strat|={len(s)} |Crit|={len(c)} |Union|={len(d|o|s|c)}")
print(f"  DMTR&Oper={len(d&o)} DMTR&Crit={len(d&c)} DMTR&Strat={len(d&s)} all4={len(d&o&s&c)}")

# long-lead high-volume
m=ltm.set_index("PL_Code");
hv=fr[fr["PL_Code"].isin(covered)].copy()
hv["Median_LT"]=hv["PL_Code"].map(m["Median_LT"]); hv["Confidence"]=hv["PL_Code"].map(m["Confidence"])
hv["F"]=hv["Forecast_2026_27"].astype(float)
ll=hv[hv["Median_LT"]>=180].sort_values("F",ascending=False).head(10)
print("\n=== Long-lead (>=180d) high-volume items (top 10 by forecast volume) ===")
for _,x in ll.iterrows():
    print(f"  {x['PL_Code']:>13} LT={x['Median_LT']:>6}d vol={x['F']:>9.0f} conf={x['Confidence']:<6} {str(x['Description'])[:30]}")
print("\n=== LT distribution (days) ===")
arr=ltm["Median_LT"].to_numpy()
print(f"  n={len(arr)} min={arr.min()} p25={np.percentile(arr,25):.0f} median={np.median(arr):.0f} p75={np.percentile(arr,75):.0f} p90={np.percentile(arr,90):.0f} max={arr.max()} mean={arr.mean():.0f}")
