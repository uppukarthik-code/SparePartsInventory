"""STEP33 Phase D — move root *.md into docs/<category>/ hierarchy. Reversible (mv)."""
import csv, shutil
from pathlib import Path

REPO = Path(r"C:/Users/uppuk/SparePartsInventory")
H = REPO / "railway" / "outputs" / "MAS" / "history"
KEEP_AT_ROOT = {"README.md", "RAILWAY_PLATFORM_README.md"}
CATS = ["audits", "modernization", "hardening", "reporting", "onboarding", "release"]
for c in CATS:
    (REPO / "docs" / c).mkdir(parents=True, exist_ok=True)


def categorize(name: str) -> str:
    u = name.upper()
    if any(k in u for k in ["STEP32", "STEP33", "RELEASE", "REMOTE_MIGRATION", "GITHUB", "PRODUCTION_READINESS", "READINESS_REASSESS"]):
        return "release"
    if any(k in u for k in ["HARDENING", "PHASE_A", "PHASE_B", "PHASE_C"]):
        return "hardening"
    if any(k in u for k in ["MODERNIZATION", "FIVE_YEAR", "ARCHITECTURE", "DATAFLOW", "REPOSITORY", "STEP1_TO_STEP28"]):
        return "modernization"
    if any(k in u for k in ["STEP29", "STEP30", "STEP31", "MANAGEMENT", "REPORTING", "NOTEBOOK", "POWERBI", "DASHBOARD"]):
        return "reporting"
    if any(k in u for k in ["ONBOARDING", "TPJ", "MULTI_DIVISION", "OPERATIONS_GUIDE", "MAINTENANCE_GUIDE", "DIVISION", "TESTING_GUIDE"]):
        return "onboarding"
    return "audits"  # default: the large audit/validation/STEP11-28 trail


rows = []
for p in sorted(REPO.glob("*.md")):
    if p.name in KEEP_AT_ROOT:
        rows.append([p.name, "(root)", "KEEP (readme)"]); continue
    cat = categorize(p.name)
    dst = REPO / "docs" / cat / p.name
    shutil.move(str(p), str(dst))
    rows.append([p.name, f"docs/{cat}/", "MOVED"])

with open(H / "documentation_restructure_report.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["File", "Destination", "Result"]); w.writerows(rows)
from collections import Counter
moved = [r for r in rows if r[2] == "MOVED"]
print("documentation_restructure_report.csv:", len(rows), "rows;", len(moved), "moved")
print("by category:", dict(Counter(r[1] for r in moved)))
print("kept at root:", [r[0] for r in rows if "KEEP" in r[2]])
