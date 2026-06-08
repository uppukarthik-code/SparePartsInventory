"""FULL PLATFORM MODERNIZATION — blueprint CSVs (read-only; additive)."""
import sys, hashlib
sys.path.insert(0,".")
import pandas as pd
from railway import railway_config as cfg
H=cfg.OUTPUT_DIR/"MAS"/"history"
def Wd(n,rows,cols): pd.DataFrame(rows,columns=cols).to_csv(H/n,index=False)
NEWN=set()  # backward-compat guard
def tree():
    h={}
    for p in sorted(cfg.OUTPUT_DIR.rglob("*")):
        if p.is_file() and not p.name.endswith("_NEWAUDIT"): h[str(p.relative_to(cfg.OUTPUT_DIR))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h

CORE=["railway_data_preparation","railway_classification","railway_forecasting","railway_inventory_optimization",
 "railway_data_quality","railway_inventory_rationalization","railway_operational_analysis","railway_executive_summary",
 "railway_powerbi_export","railway_enterprise","railway_anylogistix_export","railway_management_reports","railway_lineage",
 "railway_dashboard_validation","railway_srrs_validation","railway_explainability","railway_audit_trail","schema_validation",
 "railway_regression","railway_business_unit_runner","railway_context","railway_domain_config","railway_business_unit_config",
 "railway_strategic_allocation"]
EXT=["railway_demand_reconstruction","railway_demand_classification","railway_forecast_generation",
 "railway_lead_time_derivation","railway_pl_master","railway_safety_stock","railway_rop","railway_srrs_mas"]

# Phase 0: repository_lineage.csv
lin=[]
for m in CORE:
    lin.append((m+".py","ACTIVE_CORE_PLATFORM","STEP1-19","STEP1-28","core railway analytics","intra-railway + cfg","HIGH (do NOT remove)"))
for m in EXT:
    lin.append((m+".py","ACTIVE_MAS_EXTENSION","STEP20-28","STEP24-28","MAS division planning","cfg + demand_reconstruction(reader)","HIGH (active)"))
lin += [
 ("railway_config.py","SHARED_INFRASTRUCTURE","STEP1","STEP1-28","constants/paths (fan-in 31)","stdlib","CRITICAL (do NOT remove)"),
 ("railway/tests/*.py (10)","SHARED_INFRASTRUCTURE","STEP1-17","legacy modules","unit tests (legacy only)","pytest","keep; extend"),
 ("notebooks/01-06*.ipynb","LEGACY_HISTORICAL","pre-railway (Walmart)","Walmart era","M5 exploratory/provenance","M5 csvs","LOW (archive)"),
 ("notebooks/07_railway*.ipynb","LEGACY_HISTORICAL","railway narrative","superseded","narrative","railway modules","LOW (archive)"),
 ("raw_data/sales_train_*,sell_prices,calendar,sample_submission (430MB)","DEAD_CODE","Walmart","Walmart notebooks only","none (railway)","-","NONE (delete/archive)"),
 ("root _step*/_*_audit.py (18)","SHARED_INFRASTRUCTURE(driver)","STEP18A-28+audits","one-off","reproduce/verify outputs","modules","LOW (archive, keep provenance)"),
 ("root *.md (88)","SHARED_INFRASTRUCTURE(docs)","STEP-by-step","ongoing","human reports","-","LOW (move to docs/)"),
 ("sklearn/prophet/seaborn (deps)","DEAD_CODE","Walmart era","none","unused (0 imports)","-","NONE (remove from runtime)"),
]
Wd("repository_lineage.csv",lin,["Asset","Classification","Introduced","Last_Used_By","Business_Purpose","Runtime_Dependencies","Removal_Risk"])

# Phase 0: active_dependency_map.csv (from import graph)
dep=[
 ("railway_config","SHARED_INFRA","(none)","stdlib,re","31","universal config; route all constants here"),
 ("railway_inventory_optimization","CORE","cfg","numpy,pandas,scipy","6","shared SRRS/SS/ROP engine; reused by srrs_mas(ext)"),
 ("railway_data_preparation","CORE","cfg","numpy,pandas,openpyxl,zipfile/xml","6","strategic+operational loaders; has _xlsx_rows_via_xml reader"),
 ("railway_demand_reconstruction","MAS_EXT","cfg","numpy,pandas,zipfile/xml","4","DMTR reader; its private _sheet_rows is imported by 4 planning modules (LEAK)"),
 ("railway_business_unit_config","CORE","(none)","re","4","6-division BU resolver (MAS/SA/TPJ/MDU/PGT/TVC) - multi-div ready"),
 ("railway_domain_config","CORE","business_unit_config","-","3","domain dimension"),
 ("railway_forecasting","CORE","classification,cfg,data_preparation","numpy,pandas,statsmodels","2","Croston/SBA/TSB/Holt engine; reused by forecast_generation(ext)"),
 ("railway_context","CORE","cfg","importlib","2","per-BU output path context (multi-div)"),
 ("railway_classification","CORE","cfg,data_preparation","numpy,pandas","2","SBC/ABC/criticality (strategic)"),
 ("railway_strategic_allocation","CORE(STEP19)","business_unit_config,cfg,data_preparation","pandas","1","strategic stock allocation"),
 ("railway_safety_stock(ext)","MAS_EXT","cfg,demand_reconstruction","numpy,pandas,scipy","0","SS=z*sigma*sqrt(LT)"),
 ("railway_rop(ext)","MAS_EXT","cfg,demand_reconstruction","pandas","0","ROP+gap"),
 ("railway_srrs_mas(ext)","MAS_EXT","cfg,demand_reconstruction,inventory_optimization","pandas","0","SRRS (reuses optimizer.service_factor)"),
 ("railway_lead_time_derivation(ext)","MAS_EXT","cfg,demand_reconstruction","numpy,pandas,re,datetime","0","PO/Reqn->Receipt lead times"),
]
Wd("active_dependency_map.csv",dep,["Module","Layer","Railway_Imports","External_Libs","Fan_In","Notes"])

# Phase 1: cleanup_manifest.csv
Wd("cleanup_manifest.csv",[
 ("raw_data/sales_train_*,sell_prices,calendar,sample_submission","DELETE (or archive/historical/m5_data)","430MB; 0 railway imports; verified DEAD","NONE - not referenced by any railway module"),
 ("notebooks/01-06*.ipynb","archive/historical/walmart/","Walmart M5; cite 04/05 as forecasting/optimizer provenance","LOW - provenance retained"),
 ("notebooks/07_railway*.ipynb","archive/historical/ or docs/","superseded by modules","LOW"),
 ("root _step*/_*_audit.py (18 drivers)","archive/experiments/","one-off; some reproduce outputs","LOW - keep for provenance/regression"),
 ("root *.md (88 reports)","archive/reports/ or docs/reports/","human reports clutter root","NONE - pure docs move"),
 ("sklearn,prophet,seaborn","remove from requirements (runtime)","0 imports in railway/*.py (verified)","NONE for runtime; keep in notebook extras if needed"),
 ("STEP1-19 modules","DO NOT ARCHIVE","ACTIVE_CORE_PLATFORM","CRITICAL - production code"),
 ("STEP20-28 modules","DO NOT ARCHIVE","ACTIVE_MAS_EXTENSION","HIGH - active"),
],["Asset","Action","Evidence","Removal_Risk"])

# Phase 2: architecture_migration_plan.csv (module -> target layer)
amap={"railway_data_preparation":"ingestion (+extract shared reader)","railway_demand_reconstruction":"demand (+move _sheet_rows to shared/io)",
 "railway_demand_classification":"demand","railway_forecasting":"forecasting","railway_forecast_generation":"forecasting",
 "railway_classification":"forecasting/strategic","railway_lead_time_derivation":"inventory","railway_safety_stock":"inventory",
 "railway_rop":"inventory","railway_inventory_optimization":"inventory (shared engine)","railway_inventory_rationalization":"inventory",
 "railway_srrs_mas":"prioritization","railway_srrs_validation":"prioritization/validation","railway_operational_analysis":"inventory",
 "railway_data_quality":"validation","schema_validation":"validation","railway_dashboard_validation":"validation",
 "railway_powerbi_export":"reporting","railway_executive_summary":"reporting","railway_management_reports":"reporting (SPLIT 1548 LOC)",
 "railway_anylogistix_export":"reporting","railway_lineage":"reporting","railway_explainability":"reporting",
 "railway_enterprise":"governance","railway_audit_trail":"governance","railway_business_unit_runner":"governance/orchestration",
 "railway_context":"governance","railway_domain_config":"governance","railway_business_unit_config":"governance",
 "railway_strategic_allocation":"governance","railway_pl_master":"governance","railway_config":"shared","railway_regression":"validation/diagnostic"}
Wd("architecture_migration_plan.csv",[(m+".py",("CORE" if m in CORE else "MAS_EXT" if m in EXT else "INFRA"),amap.get(m,"shared"),"move (behavior-preserving import rewrite)") for m in CORE+EXT+["railway_config"]],
 ["Module","Lineage","Target_Layer","Action"])

# Phase 3: multi_division_readiness.csv
Wd("multi_division_readiness.csv",[
 ("CORE platform (STEP1-19)","CONFIG-READY","business_unit_config/runner/context support MAS/SA/TPJ/MDU/PGT/TVC; proven 6-div in STEP18A","Onboard via config (Status flip + data)"),
 ("railway_business_unit_config","READY","DEPOT_TOKEN_TO_BUSINESS_UNIT + BUSINESS_UNITS = 6 divisions","none"),
 ("railway_context","READY","per-BU output paths","none"),
 ("MAS EXTENSION (STEP20-28)","HARDCODED-MAS","depot '027534', SUMMARY filename, 'MAS' literals, raw_data/.../MAS path","CODE: parametrize division/depot/paths"),
 ("railway_safety_stock.py","HARDCODED","SUMMARY path+filename hardcoded; BU='MAS'","parametrize -> division config"),
 ("railway_rop.py","HARDCODED","depot '027534' filter; SUMMARY filename","parametrize"),
 ("railway_srrs_mas.py","HARDCODED","SUMMARY filename; Type weights","parametrize"),
 ("railway_demand_reconstruction.py","HARDCODED","DMTR_DIR=raw_data/.../MAS; global_end month","parametrize division path + snapshot"),
 ("railway_forecast_generation.py","HARDCODED","HORIZON Jul_2026..Jun_2027","parametrize from snapshot date"),
 ("Service levels / thresholds / weights","HARDCODED","0.95/0.85, 0.5x/2x, 10/5/1, 1.32/0.49","-> per-division config (defaults shared)"),
 ("TPJ onboarding (data)","BLOCKED","TPJ has stock_history only; no DMTR/SUMMARY","acquire TPJ DMTR+SUMMARY"),
],["Component","Status","Evidence","Required_For_TPJ"])

# Phase 4: testing_implementation_plan.csv + coverage_gap_analysis.csv
Wd("testing_implementation_plan.csv",[
 ("tests/regression/","golden-file","SHA-256 of ALL current STEP1-28 outputs; assert unchanged (BUILD FIRST - unblocks refactor)","P0"),
 ("tests/ingestion/","unit","xlsx reader, DMTR parser, PL normalize on fixtures (malformed incl)","P1"),
 ("tests/demand/","unit","reconstruction: issue classification, gap-fill, conservation; SBC class cutoffs","P1"),
 ("tests/forecasting/","unit","Croston/SBA/TSB/Holt point estimates; flat-profile; backtest","P1"),
 ("tests/inventory/","unit","SS=z*sigma*sqrt(LT) numeric; ROP=DDLT+SS; lead-time median/winsor; no-negative","P0"),
 ("tests/prioritization/","unit","SRRS=weight*SF*gap; rank; value lens; sensitivity invariants","P1"),
 ("tests/validation/","integration","funnel counts, dependency-subset integrity, end-to-end smoke","P1"),
],["Suite","Type","What_to_test","Priority"])
Wd("coverage_gap_analysis.csv",[
 ("ingestion (readers/parsers)",0,"HIGH","fragile parsing untested"),
 ("demand_reconstruction",0,"HIGH","conservation/gap-fill untested"),
 ("demand_classification",0,"HIGH","SBC cutoffs untested"),
 ("forecast_generation",0,"HIGH","method routing untested (engine has legacy tests)"),
 ("lead_time_derivation",0,"HIGH","winsor/median/empty-edge untested"),
 ("criticality (embedded)",0,"HIGH","Type parsing untested"),
 ("safety_stock",0,"CRITICAL","SS formula untested"),
 ("rop",0,"CRITICAL","ROP formula untested"),
 ("srrs_mas",0,"CRITICAL","SRRS formula untested"),
 ("STEP1-17 core",60,"MED","10 legacy test files exist"),
],["Area","Current_Coverage_Pct_est","Gap_Severity","Note"])

# Phase 5: configuration_hardening_plan.csv
Wd("configuration_hardening_plan.csv",[
 ("DAYS_PER_MONTH 30.4375","safety_stock,rop","-> cfg.DAYS_PER_MONTH"),
 ("Service levels 0.95/0.85","safety_stock,srrs_mas","-> cfg.DIVISION_SERVICE_LEVELS"),
 ("Status thresholds 0.5x/2x ROP","rop","-> cfg.STOCK_STATUS_BANDS"),
 ("Criticality weights 10/5/1","srrs_mas","-> cfg.CRITICALITY_TYPE_WEIGHT (reconcile with STOCKOUT_WEIGHT)"),
 ("Depot '027534'","rop,srrs,safety_stock,reconstruction","-> per-division config (division registry)"),
 ("SUMMARY filename (dated)","multiple","-> cfg glob pattern per division"),
 ("DMTR_DIR raw_data/.../MAS","reconstruction,lead_time","-> cfg.division_paths(div)"),
 ("HORIZON Jul_2026..Jun_2027","forecast_generation","-> derive from cfg.SNAPSHOT_DATE"),
 ("cfg.SERVICE_LEVEL_TABLE/STOCKOUT_WEIGHT unused","config","reconcile/remove dead config"),
],["Hardcoded_Item","Location","Target"])

# Phase 7: technical_debt_remediation.csv (top 25)
td=[
 ("TD01","0 tests on STEP20-28 (9 modules)","CRITICAL","Med","Low","build regression+unit suite FIRST"),
 ("TD02","Leaky dep: planning imports demand_reconstruction._sheet_rows","High","Low","Low","extract shared/io reader"),
 ("TD03","God-module management_reports 1548 LOC","High","Med","Med","split into reporting/"),
 ("TD04","Flat 35-module package, no layering","High","Med","Med","layered package"),
 ("TD05","MAS extension hardcoded (blocks TPJ)","High","Med","Med","config-driven division"),
 ("TD06","17+ one-off drivers, no orchestrator","High","Med","Low","CLI/DAG over run() fns"),
 ("TD07","88 root .md + 430MB M5 clutter","Med","Low","Low","docs/ + delete M5"),
 ("TD08","3 dup XLSX readers + 2 PL normalizers","Med","Low","Low","centralize shared/"),
 ("TD09","Hardcoded constants bypass config","Med","Low","Low","centralize config"),
 ("TD10","Unpinned deps + 3 unused (sklearn/prophet/seaborn)","Med","Low","Low","pin+split+remove"),
 ("TD11","No pyproject/setup (not installable/CI)","Med","Low","Low","add pyproject.toml"),
 ("TD12","Bare except->0.0 silent failures","Med","Med","Low","explicit validation+log"),
 ("TD13","Fragile DMTR regex","Med","Med","Med","schema assertions"),
 ("TD14","np.median([]) latent crash","Low","Low","Low","empty guard"),
 ("TD15","Silent non-027534 depot drop","Low","Low","Low","assert/warn"),
 ("TD16","No logging framework","Med","Low","Low","add logging"),
 ("TD17","No CSV schema validation at boundaries","Med","Med","Low","schema-validate"),
 ("TD18","Criticality logic embedded (no module)","Med","Low","Low","extract criticality module"),
 ("TD19","Repeated SUMMARY/DMTR re-reads","Low","Low","Low","cache shared parse"),
 ("TD20","No README/architecture/onboarding docs","High","Low","Low","add docs (this program)"),
 ("TD21","Closing_Stock derived/weakly reconciled","Low","Low","Low","label/exclude"),
 ("TD22","Knowledge in 88 reports not code/tests","High","Med","Low","docs+tests consolidate"),
 ("TD23","SHA-256 tree() reimplemented per driver","Low","Low","Low","shared util"),
 ("TD24","Output namespace mixes data+audit CSVs","Low","Low","Low","separate dirs"),
 ("TD25","No lock file (non-reproducible env)","Med","Low","Low","pip-compile/lock"),
]
Wd("technical_debt_remediation.csv",td,["ID","Finding","Impact","Effort","Risk","Remediation"])

# Phase 8: five_year_maintainability_assessment.csv
Wd("five_year_maintainability_assessment.csv",[
 ("Onboarding","Hard","88 root reports, 18 drivers, flat pkg, no README","docs+layering"),
 ("Architecture clarity","Low","flat, leaky, god-module, core+ext mixed","layered package"),
 ("Testing maturity","Critical-low","0 tests on new pipeline","regression+unit suite"),
 ("Maintainability","Low-Med","hardcoded constants/division, manual orchestration","config+orchestrator"),
 ("Scalability","Med (core) / Low (ext)","core 6-div ready; ext MAS-hardcoded","parametrize ext"),
 ("Operational supportability","Low","no logging/CLI/runbook","ops guide+logging"),
 ("Reproducibility","High","deterministic, backward-compatible, SHA-256 across 28 steps","preserve via CI"),
],["Dimension","Rating","Evidence","Mitigation"])

# Phase 9: platform_scorecard.csv (current -> target)
Wd("platform_scorecard.csv",[
 ("Architecture",45,75,"flat/leaky/god-module","layered+shared/io"),
 ("Testing",25,75,"0 tests new pipeline","regression+unit"),
 ("Maintainability",45,75,"hardcoded, manual orchestration","config+orchestrator+docs"),
 ("Configuration",40,75,"constants bypass cfg","centralize"),
 ("Reliability",55,80,"reproducible; silent failures","validation+logging"),
 ("Documentation",50,80,"reports not code-docs","8 docs (this program)"),
 ("Scalability",45,75,"single-division ext","parametrize+DAG"),
 ("Production Readiness",40,75,"no pkg/tests/CI","pyproject+tests+CI"),
 ("Multi-Division Readiness",50,80,"core ready / ext hardcoded","config-driven ext + data"),
],["Dimension","Current","Target","Evidence","Path"])

print("Platform-modernization CSVs written: 11")
sc=pd.read_csv(H/"platform_scorecard.csv"); print("current mean:",round(sc.Current.mean(),1),"target mean:",round(sc.Target.mean(),1))
