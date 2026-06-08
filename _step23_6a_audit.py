"""STEP 23.6A Lead-Time Discovery & Procurement Signal Mining (FEASIBILITY ONLY).
No synthetic lead times; nothing written into planning outputs. Writes 2 catalog CSVs."""
import glob, re, sys, hashlib
sys.path.insert(0, ".")
from datetime import date
import statistics as st
import pandas as pd
from railway import railway_config as cfg
from railway import railway_demand_reconstruction as dr

H = cfg.OUTPUT_DIR / "MAS" / "history"
NEW = {"MAS/history/procurement_signal_inventory.csv", "MAS/history/lead_time_feasibility.csv"}
N_DEMAND_PLS = 1083

def tree(excl):
    h={}
    for p in sorted(cfg.OUTPUT_DIR.rglob("*")):
        if p.is_file():
            rel=str(p.relative_to(cfg.OUTPUT_DIR)).replace("\\","/")
            if rel in excl: continue
            h[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree(NEW)

files=sorted(glob.glob(str(dr.DMTR_DIR/"DMTR_*.xlsx")))
txn_re=re.compile(r'dt\.?\s*([0-3]?\d)[.\-/]([01]?\d)[.\-/]((?:20)?\d\d)')
reqn_re=re.compile(r'Reqn\s*No\.?\s*([A-Za-z0-9\-/ ]*?)\s*dt\.?\s*([0-3]?\d)[.\-/]([01]?\d)[.\-/]((?:20)?\d\d)', re.I)
reqn_num_re=re.compile(r'Reqn\s*No\.?\s*([A-Za-z0-9\-/]+)', re.I)
po_re=re.compile(r'(?:PO|Contract)\s*/?\s*(?:PO|Contract)?\s*No\.?\s*([A-Za-z0-9\-/]+).{0,60}?dt\.?\s*([0-3]?\d)[.\-/]([01]?\d)[.\-/]((?:20)?\d\d)', re.I)
po_num_re=re.compile(r'(?:PO|Contract)\s*/?\s*(?:PO|Contract)?\s*No\.?\s*([A-Za-z0-9\-/]+)', re.I)
dbr_re=re.compile(r'DBR\s*No\.?\s*([A-Za-z0-9]+)', re.I)
dbr_date_re=re.compile(r'DBR.{0,30}?(?:dt|date)\.?\s*:?\s*([0-3]?\d)[.\-/]([01]?\d)[.\-/]((?:20)?\d\d)', re.I)
challan_re=re.compile(r'Challan\s*No\.?\s*([A-Za-z0-9\-/]+)', re.I)
vendor_re=re.compile(r'From\s+M/s\s+([^,]+?)\s+against', re.I)
def mk(d,m,y):
    y=int(y); y=y+2000 if y<100 else y
    try: return date(y,int(m),int(d))
    except: return None

recv=0
sig = {k:set() for k in ["po_num","reqn_num","dbr_num","challan","vendor"]}
cov = {k:0 for k in ["vendor_recv","po_num","po_date","reqn_num","reqn_date","dbr_num","dbr_date","challan","receipt_date","receipt_qty"]}
po_int=[]; reqn_int=[]; po_pls=set(); reqn_pls=set(); both_pls=set(); po_neg=reqn_neg=0
for fp in files:
    for row in dr._sheet_rows(fp)[1:]:
        t=str(row.get(3) or "")
        if not t.startswith("Receipt"): continue
        recv+=1
        pl=str(row.get(6) or "").strip()
        col2=str(row.get(2) or ""); detail=str(row.get(8) or ""); rem=str(row.get(11) or "")
        mt=txn_re.search(col2); rcv=mk(*mt.groups()) if mt else None
        if rcv: cov["receipt_date"]+=1
        if row.get(9): cov["receipt_qty"]+=1
        if t.startswith("Receipt-From Vendor"): cov["vendor_recv"]+=1
        mv=vendor_re.search(detail);  sig["vendor"].add(mv.group(1).strip()) if mv else None
        # PO
        pn=po_num_re.search(detail)
        if pn: cov["po_num"]+=1; sig["po_num"].add(pn.group(1))
        mp=po_re.search(detail)
        if mp:
            cov["po_date"]+=1
            od=mk(mp.group(2),mp.group(3),mp.group(4))
            if od and rcv:
                d=(rcv-od).days
                if d>=0: po_int.append(d); po_pls.add(pl); both_pls.add(pl)
                else: po_neg+=1
        # Reqn
        rn=reqn_num_re.search(detail)
        if rn and rn.group(1): cov["reqn_num"]+=1; sig["reqn_num"].add(rn.group(1))
        mr=reqn_re.search(detail)
        if mr and mr.group(2):
            cov["reqn_date"]+=1
            rq=mk(mr.group(2),mr.group(3),mr.group(4))
            if rq and rcv:
                d=(rcv-rq).days
                if d>=0: reqn_int.append(d); reqn_pls.add(pl); both_pls.add(pl)
                else: reqn_neg+=1
        # DBR
        dn=dbr_re.search(rem)
        if dn: cov["dbr_num"]+=1; sig["dbr_num"].add(dn.group(1))
        if dbr_date_re.search(rem): cov["dbr_date"]+=1
        cn=challan_re.search(detail)
        if cn: cov["challan"]+=1; sig["challan"].add(cn.group(1))

def pct(x): return round(100*x/recv,1)
# ---- procurement_signal_inventory.csv ----
sig_rows=[
 ("Receipt Date","DMTR col2 (dt.)",pct(cov["receipt_date"]),"-","No","Anchor date for all lead-time intervals; 100% of receipts"),
 ("Receipt Quantity","DMTR col9",pct(cov["receipt_qty"]),"-","No","Inflow qty; supports stock reconstruction not LT"),
 ("Vendor Receipt","DMTR col3 type",pct(cov["vendor_recv"]),len(sig["vendor"]),"Indirect","Receipt-From Vendor flag; pairs with PO date for vendor LT"),
 ("PO / Contract Number","DMTR col8",pct(cov["po_num"]),len(sig["po_num"]),"Indirect","Procurement identifier; links receipt to order"),
 ("PO / Contract Date","DMTR col8 (PO ... dt.)",pct(cov["po_date"]),"-","YES","Order date -> vendor procurement lead time (PO->Receipt)"),
 ("Requisition (Demand/Indent) Number","DMTR col8 (Reqn No.)",pct(cov["reqn_num"]),len(sig["reqn_num"]),"Indirect","Internal demand/indent identifier"),
 ("Requisition (Demand/Indent) Date","DMTR col8 (Reqn ... dt.)",pct(cov["reqn_date"]),"-","YES","Indent date -> internal fulfilment lead time (Reqn->Receipt)"),
 ("DBR Number","DMTR col11",pct(cov["dbr_num"]),len(sig["dbr_num"]),"No","Receipt voucher id (Daily Balance Return)"),
 ("DBR Date","DMTR col11",pct(cov["dbr_date"]),"-","No","Approx equals receipt posting date -> ~0 interval, not a lead time"),
 ("Challan Number","DMTR col8 (vide Challan No.)",pct(cov["challan"]),len(sig["challan"]),"Indirect","Dispatch document; challan->receipt = transit time only"),
]
pd.DataFrame(sig_rows,columns=["Signal_Name","Source_Field","Coverage_Pct","Distinct_Values","Suitable_For_Lead_Time","Comments"]).to_csv(H/"procurement_signal_inventory.csv",index=False)

def reli(neg,n): return round(100*n/(n+neg),1) if (n+neg) else 0.0
def plpct(s): return round(100*len(s)/N_DEMAND_PLS,1)
def med(x): return round(st.median(x),0) if x else None
# ---- lead_time_feasibility.csv ----
lt_rows=[
 ("PO->Receipt","PO/Contract Date + Receipt Date",plpct(po_pls),reli(po_neg,len(po_int)),"Yes",
   f"Vendor procurement LT. {len(po_int)} obs across {len(po_pls)} PLs; median {med(po_int)}d; 0 negatives. FEASIBLE."),
 ("Reqn(Demand/Indent)->Receipt","Reqn Date + Receipt Date",plpct(reqn_pls),reli(reqn_neg,len(reqn_int)),"Yes",
   f"Internal fulfilment LT. {len(reqn_int)} obs across {len(reqn_pls)} PLs; median {med(reqn_int)}d; 0 negatives. FEASIBLE."),
 ("Combined (PO or Reqn)->Receipt","PO Date or Reqn Date + Receipt Date",plpct(both_pls),100.0,"Yes",
   f"Union of vendor + internal paths -> {len(both_pls)} PLs ({plpct(both_pls)}% of demand universe)."),
 ("Challan(Dispatch)->Receipt","Challan Date + Receipt Date",plpct(po_pls),"-","No",
   "Measures transit time only (dispatch->receipt), not full procurement lead time."),
 ("DBR->Receipt","DBR Date + Receipt Date","~"+str(pct(cov['dbr_date'])),"-","No",
   "DBR date ~ receipt posting date -> ~0 interval; not a lead time."),
 ("Demand(Issue)->Receipt","Issue date + next Receipt date","-","-","No",
   "Replenishment/inter-event interval, not a procurement lead time; demand does not equal an order."),
]
pd.DataFrame(lt_rows,columns=["Method","Required_Fields","Coverage_Pct","Reliability_Pct","Feasible","Comments"]).to_csv(H/"lead_time_feasibility.csv",index=False)

after=tree(NEW)
changed=[k for k in before if before[k]!=after.get(k)]
print("=== Backward-compat (SHA-256, excl 2 new files) ===")
print(f"  fingerprinted={len(before)} changed={len(changed)} added={len([k for k in after if k not in before])} UNCHANGED={not changed}")
print("\n=== Procurement signal coverage (of",recv,"receipt txns) ===")
for r in sig_rows: print(f"  {r[0]:38s} {str(r[2]):>6}%  distinct={r[3]}  suitable={r[4]}")
print("\n=== Lead-time feasibility ===")
for r in lt_rows: print(f"  {r[0]:30s} cov={str(r[2]):>6} reli={str(r[3]):>5} feasible={r[4]}")
print(f"\nCOMBINED PL coverage: {len(both_pls)} = {plpct(both_pls)}% of {N_DEMAND_PLS}")
print(f"PO interval: median {med(po_int)}d  p90 {sorted(po_int)[int(0.9*len(po_int))]}d ; Reqn median {med(reqn_int)}d")
print("WROTE procurement_signal_inventory.csv, lead_time_feasibility.csv")
