"""STEP23 driver: SHA-256 backward-compat guard + run + reproducibility + validation."""
import hashlib, sys
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_config as cfg
from railway import railway_forecast_generation as fg

OUT = cfg.OUTPUT_DIR
NEW = {f"MAS/history/{f}" for f in
       ["forecast_results.csv", "forecast_accuracy.csv",
        "forecast_method_results.csv", "forecast_summary.csv"]}

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
art = fg.build(write=True)
after = tree(NEW)
changed = [k for k in before if before[k] != after.get(k)]
removed = [k for k in before if k not in after]
added = [k for k in after if k not in before]
print("=== Backward-compatibility (SHA-256, existing outputs excl 4 new files) ===")
print(f"  fingerprinted={len(before)} changed={len(changed)} removed={len(removed)} added={len(added)} UNCHANGED={not changed and not removed and not added}")
if changed: print("  CHANGED:", changed[:10])

def hsh(rel): return hashlib.sha256((OUT/rel).read_bytes()).hexdigest()
h1 = {r: hsh(r) for r in NEW}
fg.build(write=True)
h2 = {r: hsh(r) for r in NEW}
print("\n=== Reproducibility (forecast totals & errors) ===")
print("  4 outputs byte-identical on re-run:", h1 == h2)

r = art["results"]; a = art["accuracy"]; mr = art["method_results"]; s = art["summary"]
assign = pd.read_csv(OUT/"MAS/history/forecast_method_assignment.csv", dtype={"PL_Code":str}, keep_default_na=False)
forecastable = (assign["Forecast_Method"] != "No Forecast").sum()
dead = (assign["Forecast_Method"] == "No Forecast").sum()
hcols = [c for c in r.columns if c.startswith("Forecast_") and c not in ("Forecast_2026_27","Forecast_Method")]
print("\n=== Validation checks ===")
print(f"  1 every forecastable PL processed : {len(r)==forecastable} ({len(r)} of {forecastable}; dead={dead})")
print(f"  2 exactly one method per PL       : {r['PL_Code'].is_unique and r['Forecast_Method'].notna().all()}")
print(f"  3 dead excluded                   : {(r['Forecast_Method']=='No Forecast').sum()==0}")
print(f"  4 no duplicate PL codes           : {r['PL_Code'].is_unique and a['PL_Code'].is_unique}")
print(f"  5 horizon == 12 months            : {len(hcols)==12} ({len(hcols)})")
print(f"  6 rolling-origin completed        : {int((a['Backtest_Origins']>0).sum())} PLs backtested (max origins={int(a['Backtest_Origins'].max())})")
print(f"  7/8 reproducible totals & errors  : {h1==h2}")
print(f"  method match assignment           : {sorted(r['Forecast_Method'].unique())}")

print("\n=== Distributions ===")
print("  method:", r["Forecast_Method"].value_counts().to_dict())
print("  forecastability:", a["Forecastability_Class"].value_counts().to_dict())
print("  planning strategy:", a["Planning_Strategy"].value_counts().to_dict())
print("\n=== forecast_summary.csv ===")
print(s.to_string(index=False))
print(f"\n  total 12-month forecast volume: {r['Forecast_2026_27'].sum():,.0f}")
# top / bottom forecastable
top=a.sort_values('Forecastability_Score',ascending=False).head(5)
bot=a.sort_values('Forecastability_Score',ascending=True).head(5)
print("\n  Top 5 forecastable:", list(zip(top['PL_Code'],top['Forecastability_Score'],top['Forecastability_Class'])))
print("  Bottom 5 forecastable:", list(zip(bot['PL_Code'],bot['Forecastability_Score'],bot['Forecastability_Class'])))
# high-volume low-forecastability
hv=a.sort_values('Forecast_Volume',ascending=False).head(15)
hvlf=hv[hv['Forecastability_Class'].isin(['Low','Very Low'])]
print(f"\n  High-volume (top15) but Low/VeryLow forecastability: {len(hvlf)}")
for _,x in hvlf.iterrows():
    print(f"    {x['PL_Code']} vol={x['Forecast_Volume']:.0f} score={x['Forecastability_Score']} {x['Forecastability_Class']} sMAPE={x['sMAPE']}")
