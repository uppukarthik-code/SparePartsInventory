"""STEP21A driver: backward-compat hash guard + run + validation metrics."""
import hashlib, sys, glob, re, zipfile
from collections import defaultdict
from xml.etree import ElementTree as ET
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_config as cfg
from railway import railway_demand_reconstruction as dr

OUT = cfg.OUTPUT_DIR
HIST = OUT / "MAS" / "history"

def hash_tree():
    h = {}
    for p in sorted(OUT.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(OUT)).replace("\\", "/")
        if rel.startswith("MAS/history/"):
            continue
        h[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return h

before = hash_tree()
res = dr.run(write=True)
after = hash_tree()

changed = [k for k in before if before[k] != after.get(k)]
removed = [k for k in before if k not in after]
added = [k for k in after if k not in before]
print("\n=== Backward-compatibility (existing outputs tree, excl MAS/history) ===")
print(f"  fingerprinted: {len(before)}  changed: {len(changed)}  removed: {len(removed)}  added: {len(added)}")
print(f"  UNCHANGED: {not changed and not removed and not added}")
if changed: print("  CHANGED:", changed[:10])

hist = res["history"]
# Conservation: recompute source totals independently (reuse module's proven reader)
DEMAND=("Issue-To User Depot","Issue-For End Use","Issue-To Contractor")
src_issue=src_receipt=0.0
for fp in sorted(glob.glob(str(dr.DMTR_DIR/"DMTR_*.xlsx"))):
    for row in dr._sheet_rows(fp)[1:]:
        if not str(row.get(6) or "").strip(): continue
        t=str(row.get(3) or ""); q,_=dr._parse_qty(row.get(9))
        if any(t.startswith(p) for p in DEMAND): src_issue+=q
        if t.startswith("Receipt"): src_receipt+=q

print("\n=== Conservation ===")
print(f"  source demand-issue qty : {src_issue:,.3f}")
print(f"  history Issues_Qty sum  : {hist['Issues_Qty'].sum():,.3f}")
print(f"  issues preserved        : {abs(src_issue-hist['Issues_Qty'].sum())<0.01}")
print(f"  source receipt qty      : {src_receipt:,.3f}")
print(f"  history Receipts_Qty sum: {hist['Receipts_Qty'].sum():,.3f}")
print(f"  receipts preserved      : {abs(src_receipt-hist['Receipts_Qty'].sum())<0.01}")

# Duplicates + continuity + ordering
dups=int(hist.duplicated(subset=["PL_Code","Month"]).sum())
print("\n=== Integrity ===")
print(f"  duplicate PL/Month rows : {dups}")
bad_cont=0
for pl,g in hist.groupby("PL_Code"):
    ms=list(g["Month"])
    if ms!=sorted(ms): bad_cont+=1; continue
    yms=[(int(x[:4]),int(x[5:])) for x in ms]
    for a,b in zip(yms,yms[1:]):
        exp=(a[0],a[1]+1) if a[1]<12 else (a[0]+1,1)
        if b!=exp: bad_cont+=1; break
print(f"  PLs with broken continuity/order: {bad_cont}")
print(f"  zero-demand rows (gap-fill present): {(hist['Issues_Qty']==0).sum()}")

# Closing stock reconciliation vs stock_history snapshot
snap=dr._load_stock_history_snapshot()
last=hist.sort_values('Month').groupby('PL_Code').tail(1).set_index('PL_Code')['Closing_Stock']
matched=both=0; absdiff=0.0
for pl,cs in last.items():
    if pl in snap:
        both+=1
        if abs(cs-snap[pl])<0.5: matched+=1
        absdiff+=abs(cs-snap[pl])
print("\n=== Closing-stock reconciliation vs stock_history.xlsx ===")
print(f"  PLs in both: {both}  exact-ish match(<0.5): {matched}  match%: {round(100*matched/both,1) if both else 0}")
print(f"  mean abs diff: {round(absdiff/both,2) if both else 0}")
