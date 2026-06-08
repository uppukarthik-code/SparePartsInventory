"""STEP 23.7 driver: SHA-256 backward-compat + run + validation + impact + readiness."""
import hashlib, sys
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_config as cfg
from railway import railway_pl_master as pm

OUT = cfg.OUTPUT_DIR
NEW = {f"MAS/history/{f}" for f in ["enterprise_pl_master.csv",
       "pl_code_normalization_report.csv", "pl_match_candidates.csv"]}
def tree(excl):
    h={}
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(OUT)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h

before=tree(NEW)
master,u=pm.build_master(write=True)
norm=pm.build_normalization_report(master["PL_Code"],write=True)
cand=pm.build_match_candidates(u,write=True)
after=tree(NEW)
changed=[k for k in before if before[k]!=after.get(k)]
print("=== Backward-compat (SHA-256, excl 3 new files) ===")
print(f"  fingerprinted={len(before)} changed={len(changed)} added={len([k for k in after if k not in before])} UNCHANGED={not changed}")

# reproducibility
def h(rel): return hashlib.sha256((OUT/rel).read_bytes()).hexdigest()
h1={r:h(r) for r in NEW}
pm.build_master(); pm.build_normalization_report(master["PL_Code"]); pm.build_match_candidates(u)
h2={r:h(r) for r in NEW}
print("  reproducible:", h1==h2)

dmd=set(u["dmd_records"]); inv=set(u["inv_records"]); strat=set(u["strat_records"]); crit=set(u["crit"])
print("\n=== Validation ===")
print(f"  8 no duplicate canonical PLs : {master['PL_Code'].is_unique}")
print(f"  9 union preserved            : union={len(master)} == |AUBUCUD|={len(dmd|inv|strat|crit)} -> {len(master)==len(dmd|inv|strat|crit)}")
print(f"     each universe fully present: DMTR {len(dmd & set(master.PL_Code))}/{len(dmd)} OP {len(inv&set(master.PL_Code))}/{len(inv)}")
print(f"  6/7 reproducible             : {h1==h2}")
print(f"  10 master generated          : {len(master)} rows")

sc=master["Master_Status"].value_counts().to_dict()
print("\n=== Master_Status distribution ===")
for k in ["Fully_Reconciled","Planning_Ready","Forecast_Ready","Demand_Only","Inventory_Only","Criticality_Only","Partial"]:
    print(f"  {k:18s}: {sc.get(k,0)}")

print("\n=== Impact: universe intersections (exact, no merge) ===")
print(f"  DMTR ^ Oper={len(dmd&inv)}  DMTR ^ Crit={len(dmd&crit)}  DMTR ^ Strat={len(dmd&strat)}  all4={len(dmd&inv&strat&crit)}")
print(f"  Fully_Reconciled(D&I&C)={sum(1 for _,r in master.iterrows() if r.Demand_Present and r.Inventory_Present and r.Criticality_Present)}")

print("\n=== Match candidates (review-only, NOT merged) ===")
print(f"  total candidates: {len(cand)}  by type: {cand['Match_Type'].value_counts().to_dict()}")
print(f"  distinct DMTR PLs with >=1 candidate: {cand['PL_Code_A'].nunique()}")
hi=cand[cand['Match_Score']>=0.6]
print(f"  high-score (>=0.6) candidates: {len(hi)}")
print(f"  potential reconciled-after-review (DMTR PLs gaining I via candidate): {cand[cand['Match_Type'].str.startswith('Prefix8')|cand['Match_Type'].str.startswith('Description-OP')]['PL_Code_A'].nunique()}")

print("\n=== Normalization report ===")
print(f"  changed: {(norm['Changed']=='Yes').sum()} / {len(norm)}")
print(f"  issue types: {norm['Issue_Type'].apply(lambda s: s.split('+')[0]).value_counts().to_dict()}")
