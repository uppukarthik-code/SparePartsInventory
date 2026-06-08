"""STEP33 Phase B (archive) + Phase C (notebook rename). Reversible (mv only)."""
import csv, shutil
from pathlib import Path

REPO = Path(r"C:/Users/uppuk/SparePartsInventory")
H = REPO / "railway" / "outputs" / "MAS" / "history"
(REPO / "archive" / "walmart" / "notebooks").mkdir(parents=True, exist_ok=True)
(REPO / "archive" / "historical").mkdir(parents=True, exist_ok=True)


def mv(src_rel, dst_rel):
    s = REPO / src_rel; d = REPO / dst_rel
    if not s.exists():
        return (str(src_rel).replace("\\", "/"), str(dst_rel).replace("\\", "/"), "SKIP (absent)")
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(s), str(d))
    return (str(src_rel).replace("\\", "/"), str(dst_rel).replace("\\", "/"), "MOVED")


# --- Phase B: archive (preserve, never delete) ---
arch = []
for nb in ["01_data_preparation", "02_data_preparation", "03_exploratory_data_analysis",
           "04_demand_forecasting", "05_inventory_optimization", "06_anylogistix_simuation_tables"]:
    arch.append(mv(f"notebooks/{nb}.ipynb", f"archive/walmart/notebooks/{nb}.ipynb"))
arch.append(mv("notebooks/07_railway_inventory_analysis.ipynb",
               "archive/historical/07_railway_inventory_analysis.ipynb"))
arch.append(mv("Optimization_models_CPLEX", "archive/walmart/Optimization_models_CPLEX"))
arch.append(mv("All plots", "archive/walmart/All plots"))
with open(H / "archive_execution_report.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Source", "Destination", "Result"]); w.writerows(arch)
print("archive_execution_report.csv:", len(arch), "rows;", sum(1 for r in arch if r[2] == "MOVED"), "moved")

# --- Phase C: rename the 3 canonical railway notebooks ---
ren = []
for src, dst, role in [
    ("notebooks/UPDATED_NOTEBOOK7.ipynb", "notebooks/notebook_railway.ipynb", "master (16 sections)"),
    ("notebooks/NOTEBOOK7_EXECUTIVE_VERSION.ipynb", "notebooks/notebook_railway_executive.ipynb", "executive"),
    ("notebooks/NOTEBOOK7_TECHNICAL_VERSION.ipynb", "notebooks/notebook_railway_technical.ipynb", "technical"),
]:
    s, d, r = mv(src, dst)
    ren.append([s, d, role, r])
with open(H / "notebook_migration_report.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Old_Name", "New_Name", "Role", "Result"]); w.writerows(ren)
print("notebook_migration_report.csv:", len(ren), "rows")
print("notebooks/ now:", sorted(p.name for p in (REPO / "notebooks").glob("*.ipynb")))
