"""REPOSITORY MODERNIZATION & TECH-DEBT AUDIT (read-only; no code/output changes)."""
import sys, hashlib
sys.path.insert(0,".")
import pandas as pd
from railway import railway_config as cfg
H=cfg.OUTPUT_DIR/"MAS"/"history"
def Wd(name,rows,cols): pd.DataFrame(rows,columns=cols).to_csv(H/name,index=False)
AUD={"repository_modernization_inventory.csv","dead_code_audit.csv","duplicate_logic_audit.csv",
 "architecture_audit.csv","notebook_audit.csv","configuration_audit.csv","error_handling_audit.csv",
 "testing_audit.csv","performance_audit.csv","dependency_audit.csv","dataflow_audit.csv",
 "modernization_opportunities.csv","five_year_maintainability_audit.csv","modernization_roadmap.csv","repository_scorecard.csv"}
def tree():
    h={}
    for p in sorted(cfg.OUTPUT_DIR.rglob("*")):
        if p.is_file() and p.name not in AUD: h[str(p.relative_to(cfg.OUTPUT_DIR))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
before=tree()

# A inventory
Wd("repository_modernization_inventory.csv",[
 ("railway/*.py (35 modules)","analytics pipeline (STEP1-17 legacy + STEP18A-28 new)","Active","pandas,numpy,scipy,openpyxl,statsmodels,pulp","reports,CSVs","Medium-flat package, no layering"),
 ("railway_management_reports.py","report archive/management pack (1548 LOC)","Active(legacy)","cfg,outputs","reports","HIGH god-module"),
 ("railway_demand_reconstruction.._sheet_rows","raw-XLSX reader (private)","Active","zipfile/xml","imported by 4 planning modules","HIGH leaky shared-util"),
 ("railway/tests/*.py (10)","unit tests for STEP1-17 ONLY","Active(partial)","pytest","-","HIGH coverage gap (new pipeline untested)"),
 ("root _step*_run.py / _*_audit.py (17)","one-off drivers/orchestration","Dormant","modules","-","HIGH no orchestrator, clutter"),
 ("notebooks/01-06*.ipynb","Walmart/M5 exploratory","Dead/Dormant","M5 csvs","-","obsolete to railway"),
 ("notebooks/07_railway*.ipynb","railway narrative","Dormant","railway modules","-","superseded by modules"),
 ("root *.md (84)","STEP/audit reports","Active(docs)","-","humans","HIGH root clutter; belongs in docs/"),
 ("outputs/MAS/history/*.csv (56+)","pipeline + audit artifacts","Active","modules","reports/dashboard","Medium mixes data+audit"),
 ("requirements.txt","deps (unpinned)","Active","-","env","HIGH unpinned + notebook/unused libs"),
 ("raw_data/sales_train_*,sell_prices,calendar,sample_submission","M5 raw data (430MB)","Dead","-","Walmart notebooks only","HIGH 430MB unused"),
 ("raw_data/railways.xlsx,railway_stock_summary.xlsx,Railway_Operations/*","railway sources","Active","-","pipeline","Medium untracked/fragile"),
 ("no pyproject.toml/setup.py","(missing) packaging","Missing","-","-","HIGH not installable/CI-ready"),
],["Artifact","Purpose","Status","Dependencies","Consumers","Maintainability_Risk"])

# B dead code
Wd("dead_code_audit.csv",[
 ("M5 raw CSVs (430MB)","Dead","not read by any railway module","DELETE/ARCHIVE (move out of repo)"),
 ("notebooks 01-06 (Walmart)","Dormant/Obsolete","M5 pipeline, not railway","ARCHIVE (archive/walmart/)"),
 ("notebook 07 (railway)","Dormant","superseded by railway modules","ARCHIVE or convert to report"),
 ("17 root _step*/_*_audit drivers","Dormant","one-off; some reproduce outputs","ARCHIVE (scripts/legacy/) keep for provenance"),
 ("cfg.SERVICE_LEVEL_TABLE","Dormant","read by optimizer; UNUSED by STEP24-26","CONSOLIDATE or document as legacy"),
 ("cfg.CRITICALITY_STOCKOUT_WEIGHT","Dormant(partial)","optimizer only; SRRS uses own TYPE_WEIGHT","CONSOLIDATE"),
 ("prophet / scikit-learn / seaborn (deps)","Dead?(verify)","not imported by railway/*.py","REMOVE from runtime deps after grep-confirm"),
 ("railway_performance_test.py / railway_regression.py","Dormant","standalone diagnostics","KEEP archived"),
],["Item","Classification","Evidence","Recommendation"])

# C duplicate logic
Wd("duplicate_logic_audit.csv",[
 ("raw-XLSX reader","3 impls: data_preparation._xlsx_rows_via_xml, demand_reconstruction._sheet_rows, _build_stock_summary.read_rows (+inline in audit scripts)","centralize -> railway/ingestion/xlsx_reader.py"),
 ("PL normalization","2 impls: data_preparation._norm_pl, pl_master.normalize_pl","centralize -> railway/ingestion/pl_codes.py"),
 ("CSV load helper rd()/_read","repeated in 8+ drivers and modules (dtype PL_Code str + keep_default_na)","centralize -> io.read_pl_csv()"),
 ("date/qty regex parsing","_TXN/_PO/_REQN/_DATE_RE/_QTY_RE duplicated across demand_reconstruction, lead_time_derivation, drivers","centralize -> ingestion/dmtr_parser.py"),
 ("SHA-256 backward-compat tree()","reimplemented in EVERY driver (_step*_run.py)","centralize -> testing/backward_compat.py"),
 ("service_factor / SS / ROP","reused correctly (imported), NOT duplicated","OK - keep"),
],["Logic","Evidence","Recommendation"])

# D architecture (emphasis)
Wd("architecture_audit.csv",[
 ("Package layering","CURRENT: flat railway/ with 35 modules, no sub-packages","RECOMMENDED: layered (ingestion/validation/demand/forecasting/inventory/prioritization/reporting/governance)","HIGH"),
 ("Separation of concerns","Planning modules (safety_stock/rop/srrs) import demand_reconstruction for its private _sheet_rows I/O","Move shared I/O to ingestion/; planning depends on ingestion not on demand","HIGH leaky/inverted dependency"),
 ("God-module","railway_management_reports.py = 1548 LOC","Split into reporting/ sub-modules","HIGH"),
 ("Legacy vs new mixing","STEP1-17 (zone/Walmart-era) + STEP18A-28 (MAS pipeline) share one flat namespace","separate legacy/ vs pipeline/ or clear layer boundaries","MEDIUM"),
 ("Walmart isolation","railway .py has NO Walmart code (only 3 comments); notebooks 01-06 + M5 data are the only Walmart footprint","archive Walmart assets; railway is clean","LOW (good)"),
 ("Orchestration","17 one-off driver scripts, manual run order; no pipeline/DAG/CLI","add an orchestrator (CLI/Makefile/DAG) over the module run() fns","HIGH"),
 ("Config placement","cfg centralized but bypassed by modules' local constants","route all constants through config","MEDIUM"),
 ("Output namespace","planning CSVs + audit CSVs + reports co-mingled in outputs/MAS/history","separate outputs/ vs audit/ vs docs/","MEDIUM"),
],["Aspect","Current","Recommended","Severity"])

# E notebooks
Wd("notebook_audit.csv",[
 ("01_data_preparation.ipynb","Walmart M5","Obsolete-to-railway","ARCHIVE"),
 ("02_data_preparation.ipynb","Walmart M5 (dup of 01?)","Obsolete/Duplicate","ARCHIVE"),
 ("03_exploratory_data_analysis.ipynb","Walmart EDA","Obsolete","ARCHIVE"),
 ("04_demand_forecasting.ipynb","Walmart/Croston source (railway_forecasting derived from here)","Historical-authoritative (forecasting provenance)","ARCHIVE + cite as provenance"),
 ("05_inventory_optimization.ipynb","Walmart/PuLP source (optimizer provenance)","Historical-authoritative","ARCHIVE + cite"),
 ("06_anylogistix_simuation_tables.ipynb","AnyLogistix export source","Dormant","ARCHIVE"),
 ("07_railway_inventory_analysis.ipynb","railway narrative","Superseded by modules","ARCHIVE or convert to docs/report"),
],["Notebook","Nature","Status","Recommendation"])

# F configuration
Wd("configuration_audit.csv",[
 ("DAYS_PER_MONTH=30.4375","safety_stock.py, rop.py (and not in config)","Magic constant duplicated","-> cfg"),
 ("SERVICE_LEVEL {Critical:0.95,Non-Critical:0.85}","safety_stock.py, srrs_mas.py (hardcoded)","Hardcoded; diverges from cfg.SERVICE_LEVEL_TABLE","-> cfg, single source"),
 ("Stock-status thresholds 0.5x/2.0x ROP","rop.py","Magic numbers","-> cfg"),
 ("Criticality weights {Safety:10,Vital:5,NA:1}","srrs_mas.py TYPE_WEIGHT","Hardcoded; differs from cfg.CRITICALITY_STOCKOUT_WEIGHT","-> cfg"),
 ("Depot code '027534'","srrs/rop/safety_stock + audits","Hardcoded division identifier","-> per-division config/param"),
 ("Filename 'SUMMARY OF STOCK HELD (as on 08-06-2026) _08-06-2026.xlsx'","multiple modules","Hardcoded dated filename","-> config/glob pattern"),
 ("HORIZON Jul_2026..Jun_2027","forecast_generation.py","Hardcoded 12-month labels","-> derive from snapshot date"),
 ("ADI/CV2 cutoffs 1.32/0.49","demand_classification (reads cfg)","OK - in config","keep"),
],["Item","Location","Issue","Recommendation"])

# G error handling
Wd("error_handling_audit.csv",[
 ("bare except -> 0.0 (qty/value parse)","demand_reconstruction,_audits","Silent failure","explicit parse + log + quarantine bad rows"),
 ("bare except -> None/0 (date parse)","lead_time, reconstruction","Silent drop","validate + count rejects"),
 ("np.median([]) on empty winsor set","lead_time_derivation","Latent crash (low likelihood)","guard empty"),
 ("silent non-027534 depot drop","rop.py _current_stock","Hidden assumption","assert single depot or warn"),
 ("fragile regex (PO/Reqn/date 'dt.','No.')","lead_time, reconstruction","Breaks on format change","schema/format assertions"),
 ("no logging framework","all modules (print only)","No observability","add logging"),
 ("no input schema validation on CSVs","planning modules","Bad-contract risk","schema-validate at module boundary"),
],["Issue","Location","Risk","Recommendation"])

# H testing (emphasis)
Wd("testing_audit.csv",[
 ("STEP18A-28 pipeline","0 / 9 modules tested","NONE: demand_reconstruction,classification,forecast_generation,lead_time,pl_master,safety_stock,rop,srrs_mas,strategic_allocation","HIGH-PRIORITY: add unit tests"),
 ("Legacy STEP1-17","~10 test files","classification,forecasting,data_preparation,inventory_optimization,operational_analysis,rationalization,anylogistix,powerbi,production_hardening,business_unit_runner","partial - maintain"),
 ("Regression / golden-file","none for new pipeline","backward-compat enforced only via one-off driver SHA-256","add golden-file regression on outputs"),
 ("Integration (end-to-end)","none","funnel verified manually in audit","add e2e smoke test"),
 ("Formula unit tests (HIGH risk fns)","none","SS z*sigma*sqrt(LT); ROP DDLT; SRRS weight*SF*gap; lead-time median/winsor; SBC class; gap-fill","TOP PRIORITY: pin numeric outputs on fixtures"),
 ("Parsing tests","none","DMTR date/qty/type, PL normalize, depot codes","add with malformed fixtures"),
],["Area","Coverage","Detail","Recommendation"])

# I performance
Wd("performance_audit.csv",[
 ("SUMMARY OF STOCK HELD re-read","Medium","parsed independently by safety_stock,rop,srrs + several audits each run","read once, cache/pass frame"),
 ("DMTR 54-file re-parse","Medium","demand_reconstruction AND lead_time each parse all 54 workbooks","shared cached parse"),
 ("per-driver full-tree SHA-256","Low-Med","every _step*_run hashes entire outputs/ before+after","scope to changed dirs"),
 ("row-wise iterrows in builders","Low","safety_stock/rop/srrs loop iterrows (n<=1083)","vectorize (minor; small data)"),
 ("repeated CSV reloads","Low","each module reloads upstream CSVs","acceptable for batch; pipeline-cache if scaled"),
 ("memory","Low","small frames (<40k rows); 430MB M5 only if notebooks run","drop M5 from repo"),
],["Item","Impact","Evidence","Recommendation"])

# J dependency
Wd("dependency_audit.csv",[
 ("pandas,numpy,scipy","Used","core","pin versions"),
 ("statsmodels","Used","Holt (forecasting)","pin"),
 ("pulp","Used","optimizer knapsack","pin"),
 ("openpyxl","Used(partial)","strategic workbook; XML reader avoids it","pin"),
 ("scikit-learn","Suspect-unused","not imported by railway/*.py (verify)","remove from runtime if unused"),
 ("prophet","Suspect-unused/heavy","not used by railway forecasting (uses statsmodels)","remove from runtime"),
 ("seaborn,plotly,ipywidgets,matplotlib","Notebook-only","viz, not pipeline","move to requirements-notebooks.txt"),
 ("jupyter,jupyterlab","Notebook-only","dev","move to dev/notebook extras"),
 ("requirements.txt unpinned","All","no version pins -> non-reproducible env","pin all; split runtime/dev/notebook"),
 ("no lock file","-","no pip-compile/poetry lock","add lock"),
],["Dependency","Status","Evidence","Recommendation"])

# K dataflow
Wd("dataflow_audit.csv",[
 ("Raw->Demand","DMTR_*.xlsx -> demand_reconstruction -> monthly_demand_history","clear owner; reproducible","OK; cache parse"),
 ("Demand->Classification","-> demand_classification -> demand_classification.csv","clear","OK"),
 ("->Forecast","-> forecast_generation -> forecast_results","clear; reuses railway_forecasting fns","OK"),
 ("->Lead Time","DMTR -> lead_time_derivation -> lead_time_master","clear; re-parses DMTR","OK; share parse"),
 ("->Criticality","SUMMARY Type -> (in safety_stock/srrs inline)","NO dedicated module; logic embedded","extract criticality module"),
 ("->Safety Stock","demand_class+lead_time+SUMMARY -> safety_stock_results","clear","OK"),
 ("->ROP","safety_stock+forecast+SUMMARY -> rop_results","clear","OK"),
 ("->SRRS","rop+SUMMARY -> srss_results","clear","OK"),
 ("->Reports","CSVs -> 80+ .md (manual)","traceable but manual; no lineage manifest","add lineage manifest/orchestrator"),
 ("Reproducibility","deterministic, byte-identical re-runs","strong","keep; add CI"),
],["Stage","Flow","Ownership/Traceability","Recommendation"])

# L modernization opportunities
Wd("modernization_opportunities.csv",[
 ("Archive M5 data (430MB) out of repo","Quick(<1d)","High","Low","High"),
 ("Move 84 root .md to docs/reports/","Quick(<1d)","High","Low","High"),
 ("Archive 17 one-off drivers to scripts/legacy/","Quick(<1d)","Med","Low","High"),
 ("Pin + split requirements (runtime/notebook/dev)","Quick(<1d)","Med","Low","High"),
 ("Centralize raw-XLSX reader + PL normalize + CSV loader","Short(<1wk)","High","Med","High"),
 ("Centralize all constants into config","Short(<1wk)","Med","Low","High"),
 ("Add pyproject.toml + package install","Short(<1wk)","Med","Low","High"),
 ("Unit + golden-file tests for SS/ROP/SRRS/lead-time/demand","Medium(<1mo)","High","Med","TOP"),
 ("Layered package refactor (ingestion/.../prioritization)","Medium(<1mo)","High","Med-High","High"),
 ("Pipeline orchestrator (CLI/DAG) replacing drivers","Medium(<1mo)","High","Med","High"),
 ("Split god-module management_reports (1548 LOC)","Medium(<1mo)","Med","Med","Med"),
 ("CI + logging + schema validation","Major(>1mo)","High","Med","High"),
 ("Multi-division parametrization (remove hardcoded depot)","Major(>1mo)","High","Med-High","High"),
],["Opportunity","Effort","Impact","Risk","Priority"])

# M five-year maintainability
Wd("five_year_maintainability_audit.csv",[
 ("Onboarding","Hard","84 root .md + 17 cryptic _step drivers + flat 35-module pkg + no README of new pipeline","add README/architecture doc"),
 ("Documentation","Mixed","rich output reports but NO code/architecture/onboarding docs","add docs/architecture.md, module docstrings index"),
 ("Architecture clarity","Low","flat namespace, leaky I/O dep, god-module, legacy+new mixed","layered package"),
 ("Maintainability","Low-Med","no tests on new pipeline; hardcoded constants; one-off orchestration","tests + config + orchestrator"),
 ("Scalability","Low-Med","single division hardcoded; manual run order; re-reads","parametrize + DAG"),
 ("Reproducibility","High","deterministic, backward-compatible","keep; CI"),
 ("Knowledge concentration","High-risk","pipeline built step-wise by one author; provenance in 84 reports not code","consolidate into docs + tests"),
],["Dimension","Rating","Evidence","Mitigation"])

# N roadmap
Wd("modernization_roadmap.csv",[
 ("Phase 1","Immediate cleanup","archive M5 data+notebooks; move reports to docs/; archive drivers; pin/split deps; add README","<1wk","Low"),
 ("Phase 2","Architecture cleanup","layered package; centralize I/O reader+PL norm+CSV loader+config; extract criticality module; split god-module","2-4wk","Med"),
 ("Phase 3","Testing framework","unit+golden-file+e2e tests (SS/ROP/SRRS/lead-time/demand first); pytest+CI","2-4wk","Med"),
 ("Phase 4","Production hardening","logging; schema validation; error handling; orchestrator/CLI; lock file","3-6wk","Med"),
 ("Phase 5","Enterprise-scale readiness","parametrize division (remove hardcoded depot); pipeline DAG; enterprise rollup; perf caching","6-12wk","Med-High"),
],["Phase","Theme","Actions","Effort","Risk"])

# O scorecard
Wd("repository_scorecard.csv",[
 ("Architecture",45,"flat 35-module pkg, leaky I/O dep, 1548-LOC god-module, no layering","Med","refactor needed"),
 ("Maintainability",45,"84 root reports, 17 drivers, no README, hardcoded constants","Med","Phase1-2"),
 ("Testing",25,"0/9 new modules tested; legacy partial","High","Phase3 urgent"),
 ("Configuration",40,"central cfg exists but bypassed; magic numbers/paths/depots in code","Med","Phase2"),
 ("Reliability",55,"reproducible+backward-compatible; but silent failures/fragile parsing","Med","Phase4"),
 ("Reusability",50,"modules reusable but private-fn reuse, no shared utils pkg","Med","Phase2"),
 ("Documentation",50,"rich output reports, NO code/architecture docs","Med","Phase1"),
 ("Scalability",45,"single-division hardcoded, manual orchestration, re-reads","Med","Phase5"),
 ("Performance",60,"small data/batch ok; repeated reads tolerable","Med-High","Phase5"),
 ("Production Readiness",40,"no packaging, no tests, no CI, driver-script orchestration","Med","Phase3-4"),
],["Dimension","Score_0_100","Evidence","Confidence","Note"])

after=tree(); changed=[k for k in before if before[k]!=after.get(k)]
print("Modernization CSVs written:",len([f for f in AUD if (H/f).exists()]),"/15")
print("Backward-compat: changed=",len(changed),"UNCHANGED:",not changed)
import pandas as _pd
sc=_pd.read_csv(H/"repository_scorecard.csv")
print("Overall score (mean):",round(sc.Score_0_100.mean(),1))
