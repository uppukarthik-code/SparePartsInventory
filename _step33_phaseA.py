"""STEP33 Phase A — quarantine-move DELETE_SAFE assets (reversible; untracked only)."""
import csv, shutil
from pathlib import Path

REPO = Path(r"C:/Users/uppuk/SparePartsInventory")
Q = Path(r"C:/Users/uppuk/_railway_purge_quarantine")
H = REPO / "railway" / "outputs" / "MAS" / "history"

# Explicit DELETE_SAFE set (all verified untracked, 0 railway refs)
NOTEBOOK_DUMPS = ["FORECAST_BI.csv", "Forecast.csv", "SparePartsInventory!.csv",
                  "final_combined_SKUs.csv", "final_forecast_output.csv", "SparePartsInventory.csv"]
M5 = ["sales_train_evaluation.csv", "sales_train_validation.csv", "sell_prices.csv",
      "sample_submission.csv", "calendar.csv"]

targets = []  # (relpath, category)
for f in NOTEBOOK_DUMPS:
    targets.append((Path("notebooks") / f, "notebook_walmart_dump"))
for f in M5:
    targets.append((Path("raw_data") / f, "m5_competition_data"))
targets.append((Path("data"), "walmart_data_dir"))
for cp in [Path("notebooks/.ipynb_checkpoints"),
           Path("Anylogistix/01_Anylogistix Network Optimisation Result/.ipynb_checkpoints"),
           Path("Anylogistix/03_Anylogistix Simulation Experiment Results/.ipynb_checkpoints"),
           Path("Power-BI Dashboards/.ipynb_checkpoints")]:
    targets.append((cp, "ipynb_checkpoint"))


def size_of(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    if p.is_dir():
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    return 0


# --- plan (before) ---
plan = []
for rel, cat in targets:
    src = REPO / rel
    plan.append([str(rel).replace("\\", "/"), cat, "exists" if src.exists() else "MISSING",
                 f"{size_of(src)/1048576:.1f}", "QUARANTINE (reversible)"])
with open(H / "delete_execution_plan.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Path", "Category", "Present", "Size_MB", "Action"]); w.writerows(plan)
print("delete_execution_plan.csv:", len(plan), "rows")

# --- execute (quarantine-move) ---
report = []
total = 0.0
for rel, cat in targets:
    src = REPO / rel
    if not src.exists():
        report.append([str(rel).replace("\\", "/"), cat, "SKIP (absent)", "0.0"]); continue
    mb = size_of(src) / 1048576
    dst = Q / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    report.append([str(rel).replace("\\", "/"), cat, "MOVED -> quarantine", f"{mb:.1f}"])
    total += mb
with open(H / "delete_execution_report.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Path", "Category", "Result", "Size_MB"]); w.writerows(report)
    w.writerow(["TOTAL", "", f"{sum(1 for r in report if 'MOVED' in r[2])} moved", f"{total:.1f}"])
print(f"delete_execution_report.csv: {len(report)} rows | quarantined {total/1024:.2f} GB to {Q}")
