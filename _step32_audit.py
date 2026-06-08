"""STEP32 repository-purification audit CSVs (READ-ONLY; additive; no deletes/moves)."""
import csv
from railway import railway_config as cfg
H = cfg.OUTPUT_DIR / "MAS" / "history"


def W(n, hdr, rows):
    w = csv.writer(open(H / n, "w", newline="", encoding="utf-8"))
    w.writerow(hdr); w.writerows(rows)
    print(f"{n}: {len(rows)} rows")


# A — repository_purification_inventory.csv  (asset-GROUP level: file-by-file = 1000+ rows, not actionable)
W("repository_purification_inventory.csv",
  ["Asset_Group", "Type", "Purpose", "Ref_by_active_code", "Ref_by_tests", "Ref_by_notebooks",
   "Req_by_reporting", "Req_by_regression", "Req_for_reproducibility"],
  [["railway/*.py (35 modules)", "code", "core+extension platform", "Y", "Y", "Y", "Y", "Y", "Y"],
   ["railway/ingestion/, governance/", "code", "I/O + config + reporting SoT", "Y", "Y", "Y", "Y", "Y", "Y"],
   ["railway/tests/", "tests", "regression + formula suite", "Y", "Y", "N", "N", "Y", "Y"],
   ["railway/outputs/<div>/", "data", "generated planning outputs (pinned)", "Y", "Y", "Y", "Y", "Y", "Y"],
   ["raw_data/Railway_Operations/ (25M)", "data", "DMTR + SUMMARY (railway source)", "Y", "N", "N", "Y", "Y", "Y"],
   ["raw_data/railways.xlsx, railway_stock_summary.xlsx", "data", "strategic/operational source", "Y", "N", "N", "Y", "Y", "Y"],
   ["notebooks/UPDATED_NOTEBOOK7 + EXEC + TECH", "notebook", "canonical railway notebooks (STEP30)", "N", "N", "Y", "Y", "N", "N"],
   ["notebooks/07_railway_inventory_analysis", "notebook", "legacy railway NB (superseded)", "N", "N", "N", "N", "N", "N"],
   ["notebooks/01-06 (Walmart)", "notebook", "M5/Walmart provenance", "N", "N", "N", "N", "N", "N"],
   ["notebooks/*.csv dumps (~1.9G)", "data", "Walmart-era output dumps", "N", "N", "N", "N", "N", "N"],
   ["raw_data/sales_train_*/sell_prices/calendar/sample_submission (431M)", "data", "M5 competition data", "N", "N", "N", "N", "N", "N"],
   ["data/Sales_merged.csv (72M)", "data", "Walmart merged sales", "N", "N", "N", "N", "N", "N"],
   ["**/.ipynb_checkpoints/ (4 dirs, ~470M)", "junk", "editor checkpoints", "N", "N", "N", "N", "N", "N"],
   ["root *.md (113) + STEP reports", "docs", "platform documentation/audit trail", "N", "N", "N", "N", "N", "Partial"],
   ["Power-BI Dashboards/Railway.pbix (58M)", "binary", "railway PowerBI dashboard", "N", "N", "N", "Y", "N", "N"],
   ["Anylogistix/ (15M)", "data", "aLX sim results (railway)", "N", "N", "N", "Partial", "N", "N"],
   ["requirements.txt", "config", "deps (unpinned, 4 dead)", "Y", "Y", "N", "N", "Y", "Y"],
   ["Optimization_models_CPLEX/, All plots/ (9M)", "misc", "Walmart-era artifacts", "N", "N", "N", "N", "N", "N"]])

# B — file_classification.csv
W("file_classification.csv", ["Asset_Group", "Classification", "Rationale"],
  [["railway/ STEP1-19 modules", "ACTIVE_RAILWAY_CORE", "live core platform; imported + tested"],
   ["railway/ STEP20-28 modules", "ACTIVE_RAILWAY_EXTENSION", "live MAS planning; produces pinned outputs"],
   ["railway/ingestion, governance, config, tests, outputs", "ACTIVE_INFRASTRUCTURE", "I/O, config, reporting SoT, regression guard"],
   ["raw_data/Railway_Operations, railways.xlsx, railway_stock_summary.xlsx", "ACTIVE_INFRASTRUCTURE", "railway data sources (reproducibility)"],
   ["notebooks/UPDATED_NOTEBOOK7 + EXEC + TECH", "ACTIVE_INFRASTRUCTURE", "canonical railway notebooks"],
   ["Power-BI Dashboards/Railway.pbix", "ACTIVE_INFRASTRUCTURE", "railway dashboard binary"],
   ["root STEP*/RAILWAY*/PHASE* .md reports", "REFERENCE_HISTORICAL", "audit trail / platform documentation"],
   ["notebooks/07_railway_inventory_analysis", "REFERENCE_HISTORICAL", "legacy railway NB superseded by STEP30"],
   ["notebooks/04_demand_forecasting, 05_inventory_optimization", "METHODOLOGY_REFERENCE", "forecasting/optimizer provenance for railway engine"],
   ["notebooks/01-03, 06 (Walmart)", "ARCHIVE_WALMART", "M5 provenance; no railway dependency"],
   ["notebooks/*.csv dumps (~1.9G)", "DELETE_SAFE", "Walmart output dumps; 0 railway refs"],
   ["raw_data M5 CSVs (431M)", "DELETE_SAFE", "M5 data; 0 railway imports (verify 3 string refs)"],
   ["data/Sales_merged.csv (72M)", "DELETE_SAFE", "Walmart merged sales; 0 refs"],
   ["**/.ipynb_checkpoints (~470M)", "DELETE_SAFE", "editor junk"],
   ["Optimization_models_CPLEX, All plots", "ARCHIVE_WALMART", "Walmart-era artifacts; not railway"]])

# C — walmart_remnant_analysis.csv + archive_plan.csv + delete_plan.csv
W("walmart_remnant_analysis.csv", ["Asset", "Walmart_Only", "Railway_Dependency", "Recommendation"],
  [["notebooks 01-03,06", "Yes", "None", "ARCHIVE"],
   ["notebooks 04,05", "Yes (origin)", "Methodology (engine derived from these)", "ARCHIVE as methodology ref"],
   ["raw_data M5 CSVs (431M)", "Yes", "None (verify 3 string refs)", "DELETE (or archive out-of-repo)"],
   ["notebooks/*.csv dumps (1.9G)", "Yes", "None", "DELETE"],
   ["data/Sales_merged.csv", "Yes", "None", "DELETE"],
   ["Optimization_models_CPLEX, All plots", "Yes", "None", "ARCHIVE"],
   ["scikit-learn/prophet/seaborn/plotly deps", "Yes (Walmart-era)", "0 imports in railway/", "REMOVE from runtime requirements"]])
W("archive_plan.csv", ["Asset", "Target", "Risk", "Size"],
  [["notebooks 01-06", "archive/walmart/notebooks/", "LOW (provenance)", "~3.5M"],
   ["notebooks/07 (legacy railway)", "archive/historical/", "LOW", "21K"],
   ["Optimization_models_CPLEX/", "archive/walmart/", "LOW", "172K"],
   ["All plots/", "archive/walmart/", "LOW", "8.9M"],
   ["root *.md audit reports (optional)", "docs/reports/", "NONE", "~3M"]])
W("delete_plan.csv", ["Asset", "Evidence", "Risk", "Size"],
  [["notebooks/*.csv Walmart dumps", "0 railway refs (FORECAST_BI/Forecast/final_*)", "LOW (verify SparideartsInventory*.csv)", "~1.9G"],
   ["raw_data M5 CSVs", "0 railway imports (verify 3 string refs)", "LOW", "431M"],
   ["data/Sales_merged.csv", "0 refs", "LOW", "72M"],
   ["**/.ipynb_checkpoints/", "editor junk", "NONE", "~470M"]])

# D — notebook_rationalization.csv + recommended_notebook_structure.csv
W("notebook_rationalization.csv", ["Notebook", "Disposition", "Reason"],
  [["01_data_preparation", "ARCHIVE", "Walmart; no railway dep"],
   ["02_data_preparation", "ARCHIVE", "Walmart"],
   ["03_exploratory_data_analysis", "ARCHIVE", "Walmart EDA (2.5M)"],
   ["04_demand_forecasting", "ARCHIVE (methodology ref)", "forecasting provenance"],
   ["05_inventory_optimization", "ARCHIVE (methodology ref)", "optimizer provenance"],
   ["06_anylogistix_simuation_tables", "ARCHIVE", "Walmart aLX"],
   ["07_railway_inventory_analysis", "ARCHIVE (historical)", "legacy railway, superseded by STEP30"],
   ["UPDATED_NOTEBOOK7", "RETAIN+RENAME", "-> notebook_railway.ipynb (master)"],
   ["NOTEBOOK7_EXECUTIVE_VERSION", "RETAIN+RENAME", "-> notebook_railway_executive.ipynb"],
   ["NOTEBOOK7_TECHNICAL_VERSION", "RETAIN+RENAME", "-> notebook_railway_technical.ipynb"]])
W("recommended_notebook_structure.csv",
  ["Option", "Maintainability", "Duplication", "Executive_use", "Engineering_use", "TPJ_support", "GitHub_presentation", "Verdict"],
  [["A: master+executive+technical", "High", "Low (one engine)", "Excellent", "Excellent", "Strong", "Excellent", "RECOMMENDED"],
   ["B: master+executive", "High", "Low", "Excellent", "Medium (no deep-dive)", "Medium", "Good", "second"],
   ["C: single notebook", "Medium", "None", "Crowded", "Crowded", "Weak", "Medium", "no (mixes audiences)"]])

# E — dependency_purification.csv
W("dependency_purification.csv", ["Package", "Imports_in_railway", "v1.0_Required", "Disposition"],
  [["pandas", ">0", "Yes", "RETAIN (pin)"], ["numpy", ">0", "Yes", "RETAIN (pin)"],
   ["scipy", "2", "Yes", "RETAIN (pin)"], ["statsmodels", "1", "Yes", "RETAIN (pin)"],
   ["pulp", "1", "Yes", "RETAIN (pin)"], ["matplotlib", "notebooks", "Yes (notebooks)", "RETAIN (pin)"],
   ["seaborn", "0 (railway); notebooks use it", "notebooks only", "MOVE to requirements-notebooks"],
   ["openpyxl", "raw zip used instead", "No (zip+xml reader)", "OPTIONAL"],
   ["scikit-learn", "0", "No", "REMOVE (Walmart-era)"],
   ["prophet", "0", "No", "REMOVE (Walmart-era)"],
   ["plotly", "0", "No", "REMOVE (Walmart-era)"],
   ["jupyter/jupyterlab/ipywidgets", "notebooks", "dev only", "MOVE to dev extras"],
   ["pyproject.toml", "absent", "Yes", "ADD (pin + extras)"]])

# F — railway_only_repository_structure.csv
W("railway_only_repository_structure.csv", ["Path", "Current", "Target_v1.0", "Action"],
  [["railway/", "flat 35 modules", "layered (ingestion/governance/.. core)", "RETAIN (layer later)"],
   ["railway/tests/", "regression+formula", "same", "RETAIN"],
   ["railway/outputs/", "6-division outputs", "same", "RETAIN"],
   ["notebooks/", "10 mixed", "3 notebook_railway*.ipynb", "RENAME 3 + ARCHIVE 7"],
   ["raw_data/", "railway + 431M M5", "railway sources only", "DELETE M5"],
   ["data/", "72M Walmart", "(removed)", "DELETE"],
   ["docs/", "absent (113 root .md)", "docs/ + docs/reports/", "MOVE .md"],
   ["archive/", "absent", "archive/walmart/, archive/historical/", "CREATE + MOVE"],
   ["pyproject.toml", "absent", "present (pinned)", "ADD"],
   ["Power-BI Dashboards/", "58M", "retain Railway.pbix", "RETAIN"]])

# G — repository_size_analysis.csv
W("repository_size_analysis.csv", ["Bucket", "Size", "Pct_of_total", "Note"],
  [["TOTAL (excl .git)", "2.6 GB", "100%", "working tree"],
   ["DELETE_SAFE", "~2.4 GB", "~92%", "notebook CSV dumps 1.9G + M5 431M + Sales_merged 72M + checkpoints 470M (overlap)"],
   ["  notebooks/*.csv dumps", "1.9 GB", "73%", "Walmart output dumps"],
   ["  raw_data M5 CSVs", "431 MB", "16%", "M5 competition data"],
   ["  data/Sales_merged.csv", "72 MB", "3%", "Walmart"],
   ["ARCHIVE_WALMART", "~13 MB", "<1%", "notebooks 01-06 + CPLEX + plots"],
   ["RETAINED (railway v1.0)", "~150-200 MB", "~7%", "railway/ 43M + outputs + railway raw_data 25M + Railway.pbix 58M + docs"],
   ["Estimated reduction", "~90-92%", "-", "2.6 GB -> ~0.2 GB"]])

# H — github_release_readiness.csv
W("github_release_readiness.csv", ["Dimension", "Status", "Evidence"],
  [["Architecture", "READY", "layered ingestion/governance; hardened A/B"],
   ["Tests", "READY", "541 green; reproducible baseline"],
   ["Notebooks", "READY (after rename)", "3 executed railway notebooks"],
   ["Reporting", "READY", "division_summary SoT; STEP31 cut-over"],
   ["Documentation", "READY (after docs/ move)", "README + ARCHITECTURE + guides + reports"],
   ["Governance", "READY", "reporting governance + metadata standard"],
   ["Onboarding", "READY", "DIVISION_ONBOARDING_GUIDE + division registry"],
   ["Size/cleanliness", "BLOCKED", "2.4G Walmart data must be removed first"],
   ["Packaging", "GAP", "no pyproject.toml/CI yet"]])

# I — tpj_onboarding_readiness.csv (purification view)
W("tpj_onboarding_readiness.csv", ["Dimension", "Status", "Evidence"],
  [["Code readiness", "READY", "gcfg division registry + --division CLI"],
   ["Reporting readiness", "READY", "division_summary division-aware (STEP31)"],
   ["Notebook readiness", "READY", "notebooks parametrize via division_summary"],
   ["Documentation readiness", "READY", "DIVISION_ONBOARDING_GUIDE"],
   ["Data readiness", "BLOCKED", "TPJ DMTR + SUMMARY absent"],
   ["Architecture change needed", "NO", "config + data only"]])

# J — final_railway_repository_blueprint.csv
W("final_railway_repository_blueprint.csv", ["Asset", "Action", "Destination"],
  [["railway/ (all)", "RETAIN", "railway/"],
   ["railway/tests, outputs", "RETAIN", "as-is"],
   ["raw_data/Railway_Operations, railway*.xlsx", "RETAIN", "raw_data/"],
   ["UPDATED_NOTEBOOK7.ipynb", "RENAME", "notebooks/notebook_railway.ipynb"],
   ["NOTEBOOK7_EXECUTIVE_VERSION.ipynb", "RENAME", "notebooks/notebook_railway_executive.ipynb"],
   ["NOTEBOOK7_TECHNICAL_VERSION.ipynb", "RENAME", "notebooks/notebook_railway_technical.ipynb"],
   ["notebooks 01-07", "ARCHIVE", "archive/walmart|historical/"],
   ["root *.md reports", "MOVE", "docs/ + docs/reports/"],
   ["notebooks/*.csv dumps (1.9G)", "DELETE", "(removed)"],
   ["raw_data M5 CSVs (431M)", "DELETE", "(removed; verify refs)"],
   ["data/Sales_merged.csv", "DELETE", "(removed)"],
   ["**/.ipynb_checkpoints", "DELETE", "(removed; add to .gitignore)"],
   ["scikit-learn/prophet/plotly/seaborn", "REMOVE", "requirements (notebook extras only)"],
   ["pyproject.toml", "CREATE", "repo root"],
   ["Power-BI Dashboards/Railway.pbix", "RETAIN", "as-is"]])

# K — railway_only_validation.csv
W("railway_only_validation.csv", ["Action", "Works_without_Walmart", "Evidence"],
  [["1. Clone repo", "Yes", "railway/ self-contained"],
   ["2. Delete archive/ folder", "Yes", "0 railway imports of Walmart assets"],
   ["3. Install dependencies", "Yes", "pandas/numpy/scipy/statsmodels/pulp only"],
   ["4. Run tests", "Yes", "541 green; depends only on railway/ + outputs"],
   ["5. Run notebooks", "Yes", "railway notebooks read railway outputs only"],
   ["6. Run reporting", "Yes", "division_summary reads railway outputs only"],
   ["7. Run planning", "Yes", "STEP20-28 read raw_data/Railway_Operations only"],
   ["8. Run TPJ onboarding", "Config-ready (data-blocked)", "gcfg registry; no Walmart dep"]])

print("all 14 STEP32 audit CSVs generated")
