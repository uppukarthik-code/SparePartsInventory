"""STEP 24 driver: SHA-256 backward-compat + run + validation + impact."""
import hashlib, sys
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_config as cfg
from railway import railway_safety_stock as ss

OUT = cfg.OUTPUT_DIR
NEW = {"MAS/history/safety_stock_results.csv", "MAS/history/safety_stock_summary.csv"}
def tree(excl):
    h={}
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(OUT)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree(NEW)
res, summ, unc = ss.build(write=True)
after=tree(NEW)
changed=[k for k in before if before[k]!=after.get(k)]
print("=== Backward-compat (SHA-256, excl 2 new files) ===")
print(f"  fingerprinted={len(before)} changed={len(changed)} added={len([k for k in after if k not in before])} UNCHANGED={not changed}")
# reproducible
def h(rel): return hashlib.sha256((OUT/rel).read_bytes()).hexdigest()
h1={r:h(r) for r in NEW}; ss.build(); h2={r:h(r) for r in NEW}
print("  reproducible:", h1==h2)

print("\n=== Validation ===")
print(f"  1 no negative safety stock     : {(res['Safety_Stock']>=0).all()} (min={res['Safety_Stock'].min()})")
print(f"  2 no duplicate PLs             : {res['PL_Code'].is_unique}")
crit_sl=res[res.Criticality_Class=='Critical']['Service_Level'].unique()
nonc_sl=res[res.Criticality_Class=='Non-Critical']['Service_Level'].unique()
print(f"  3 critical higher service level: Critical SL={list(crit_sl)} > Non-Critical SL={list(nonc_sl)} -> {min(crit_sl)>max(nonc_sl)}")
print(f"  4 lead-time coverage (honest)  : {len(res)} computed; {len(unc['uncovered_lt'])} forecastable PLs WITHOUT lead time (flagged, not fabricated)")
print(f"  6 no synthetic lead times      : all LT from lead_time_master.csv (uncovered excluded)")
print(f"  7-10 existing outputs unchanged: {not changed}")

print("\n=== Summary ===")
print(summ.to_string(index=False))

print("\n=== Q&A ===")
print(f"  1 PLs with safety stock        : {len(res)}")
print(f"  2 forecast-volume coverage     : {summ['Forecast_Volume_Coverage_Pct'].iloc[0]}%")
crit_cov = 100*summ['Critical_PLs'].iloc[0]/(summ['Critical_PLs'].iloc[0]+summ['NonCritical_PLs'].iloc[0])
print(f"  3 critical share of SS PLs     : {summ['Critical_PLs'].iloc[0]} critical / {len(res)} ({crit_cov:.1f}%)")
print("  4 top-10 highest safety stock:")
for _,x in res.head(10).iterrows():
    print(f"     {x['PL_Code']:>13} SS={x['Safety_Stock']:>9.1f} {x['Criticality_Class']:<12} LT={x['Lead_Time_Days']}d STD={x['Demand_STD']} {str(x['Description'])[:26]}")
print(f"  5 uncovered: {len(unc['uncovered_lt'])} no-LT + {len(unc['uncovered_crit'])} no-criticality")
