"""
STEP 19 regeneration driver (one-off).

For each Business Unit, regenerates ONLY the new strategic-allocation artefact and
the enterprise layer -- the operational, forecasting, SRRS, optimization and
procurement outputs are never re-run, so they stay byte-for-byte identical.
Proves that with a SHA-256 before/after check on every non-enterprise,
non-allocation file under outputs/<BU>/.
"""
import hashlib, io, contextlib, sys
sys.path.insert(0, ".")
import pandas as pd
from railway import railway_context as rc
from railway import railway_strategic_allocation as salloc
from railway import railway_enterprise as ent
from railway.railway_business_unit_runner import enterprise_rollup

BUS = ["MAS", "SA", "TPJ", "MDU", "PGT", "TVC"]
root = rc.CANONICAL_OUTPUT_DIR


def snap(bu):
    base = root / bu
    h = {}
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(base)).replace("\\", "/")
        if rel.startswith("enterprise/") or rel == "strategic_inventory_allocation.csv":
            continue
        h[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return h


before = {bu: snap(bu) for bu in BUS}

for bu in BUS:
    with rc.use_context(bu):
        with contextlib.redirect_stdout(io.StringIO()):
            salloc.run()
            ent.run()

print("=== Backward-compatibility: protected (operational/forecast/SRRS/procurement) files ===")
all_ok = True
for bu in BUS:
    a = snap(bu)
    changed = [k for k in before[bu] if before[bu][k] != a.get(k)]
    removed = [k for k in before[bu] if k not in a]
    ok = not changed and not removed
    all_ok = all_ok and ok
    print(f"  {bu:5s} protected={len(before[bu]):2d}  changed={len(changed)}  removed={len(removed)}  UNCHANGED={ok}")
    if changed:
        print("     CHANGED:", changed[:8])
print("ALL PROTECTED OUTPUTS UNCHANGED:", all_ok)

# Consolidated zone allocation
full = salloc.allocate()
roll = root / "_enterprise_rollup"
roll.mkdir(parents=True, exist_ok=True)
full.to_csv(roll / "strategic_inventory_allocation.csv", index=False)
print(f"\nConsolidated allocation: {len(full)} rows -> _enterprise_rollup/strategic_inventory_allocation.csv")

# Rebuild 6-way enterprise rollup (now de-inflated)
with contextlib.redirect_stdout(io.StringIO()):
    info = enterprise_rollup(BUS)
print("6-way rollup:", info["files"], "registry rows:", info.get("total_rows"))
