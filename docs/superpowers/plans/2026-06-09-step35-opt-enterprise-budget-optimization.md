# STEP35-OPT — Enterprise Budget Optimization & Capital Allocation Extension — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing optimization engine from per-division procurement optimization to enterprise-wide capital allocation — budget frontier, knee-point, cross-division allocation, multi-year roadmap, and executive decision support — without modifying any existing analytical logic or output bytes.

**Architecture:** All PuLP/knapsack SOLVER primitives are *added as new functions* to `railway/railway_inventory_optimization.py` (the single source of truth — they reuse `_solve_knapsack` / `allocate_with_reserve` verbatim). A *new* orchestration/IO module `railway/governance/enterprise_allocation.py` reads existing per-division `railway_inventory_policy.csv` outputs, calls those primitives, and writes only NEW output CSVs. Reporting KPIs + the board dashboard extend `railway/governance/division_summary.py`. Notebook Section 17 is appended via NotebookEdit and reads live CSVs only. **No existing output CSV is ever rewritten with different bytes.**

**Tech Stack:** Python 3.11, pandas, numpy, scipy, PuLP+CBC (existing), pytest, nbformat/nbconvert.

---

## Non-Negotiable Invariants (verify at every commit)

1. **No new optimizer.** No `procurement_optimizer.py`. Solver logic lives only in `railway_inventory_optimization.py`, reusing `_solve_knapsack`/`allocate_with_reserve`.
2. **No analytical regression.** Do not touch forecasting, demand reconstruction, lead-time, criticality, safety-stock, ROP, SRRS, procurement-tier, or reporting *formulas*.
3. **Additive only.** Existing output CSVs keep byte-identical SHA-256 (golden regression suite is the gate). Only NEW files are written.
4. **Test floor (CORRECTED — baseline is pre-existing RED).** Baseline on commit `2bf6e82` = **88 passed, 544 failed, 1 skipped** BEFORE any STEP35-OPT work. The 544 failures are pre-existing and NOT caused by this work: ~537 are a line-ending defect (committed CSVs are LF; `golden_output_manifest.csv` pinned the CRLF rendering — content is byte-identical, `LF→CRLF` reproduces the manifest hashes), and ~7 are known stale fixtures (test row-counts lag the current dataset). **Floor = no-new-failures:** the pre-existing pass/fail set must be UNCHANGED (still 88 pass / 544 fail), EVERY new STEP35-OPT test must pass, and ZERO new failures may be introduced. Do NOT re-pin the manifest or edit existing fixtures (user decision: leave the baseline untouched; document it in the validation report).
5. **Reproducible.** Run everything with `PYTHONHASHSEED=0`; outputs must be byte-identical across two consecutive runs.

### Regression-safety facts (already verified)
- `railway/tests/regression/test_golden_outputs.py::test_output_unchanged` is parametrized over `golden_output_manifest.csv` rows only → NEW files do not affect it.
- `test_no_unexpected_new_outputs` explicitly **allows** new CSVs (prints info, never fails).
- ∴ Safe iff we never alter the bytes of a pinned file.

### Existing solver contract (do not change — reuse only)
- `_solve_knapsack(frame, budget, score_col, cost_col) -> set` — binary knapsack, skips items costing > budget; returns selected index labels.
- `allocate_with_reserve(frame, budget, score_col, cost_col, crit_col="Criticality", return_stages=False) -> set` — two-stage Safety-Reserve then open knapsack; reduces to a single knapsack when reserve disabled.
- Score col = `"Service_Risk_Reduction_Score"`, cost col = `"Inventory_Investment_Required"`, crit col = `"Criticality"`.
- `build_inventory_policy(write=False)` returns the full `opt` DataFrame including `Inventory_Status` ("Procurement Required"/"Sufficient"), SRRS, investment, criticality.

### Data sources (read-only)
- Enterprise/consolidated candidates: `railway/outputs/railway_inventory_policy.csv` (full POLICY_FIELDS).
- Per-division candidates: `railway/outputs/<DIV>/railway_inventory_policy.csv` for each Live division. Live divisions resolved via `railway_business_unit_config`: `MAS, SA, TPJ, MDU, PGT, TVC` (STTC_PTJ is "Configured" → excluded).
- Each policy CSV has columns: `PL_Code, Description, ABC_Class, Criticality, Inventory_Status, Inventory_Investment_Required, Service_Risk_Reduction_Score, Lead_Time_Months, …`.

### New output files (all under `railway/outputs/`)
`optimization_baseline_validation.csv`, `risk_reduction_frontier.csv`, `budget_efficiency_analysis.csv`, `enterprise_budget_allocation.csv`, `enterprise_budget_allocation_readiness.csv`, `procurement_roadmap.csv`, `executive_budget_scenarios.csv`, `enterprise_decision_dashboard.csv`.
Reports → `docs/audits/STEP35_OPT_REPORT.md`, `docs/audits/STEP35_OPT_VALIDATION_REPORT.md`.

---

## File Structure (created / modified)

- **Modify** `railway/railway_config.py` — append STEP35-OPT constants (additive section).
- **Modify** `railway/railway_inventory_optimization.py` — append solver primitives: `solve_budget_frontier`, `enterprise_capital_allocation`, `procurement_roadmap`. (No existing function changed.)
- **Create** `railway/governance/enterprise_allocation.py` — orchestration + IO; writes 6 of the 7 CSVs.
- **Modify** `railway/governance/division_summary.py` — add `enterprise_kpis()` + `build_enterprise_decision_dashboard()`.
- **Create** `railway/tests/test_enterprise_allocation.py` — unit tests for the new primitives + orchestration.
- **Modify** `notebooks/notebook_railway.ipynb`, `notebooks/notebook_railway_executive.ipynb` — append Section 17 cells (NotebookEdit).
- **Create** `docs/audits/STEP35_OPT_REPORT.md`, `docs/audits/STEP35_OPT_VALIDATION_REPORT.md`.

---

## Task A1 (Phase A): Capture baseline — test green count + golden hashes

**Files:**
- Read-only verification; produces a local note used as the test floor.

- [ ] **Step 1: Record baseline test result**

Run: `set PYTHONHASHSEED=0 && python -m pytest railway/tests -q` (PowerShell: `$env:PYTHONHASHSEED=0; python -m pytest railway/tests -q`)
Expected: note the exact `N passed, M skipped` line. **The validation floor is the actual collected count = 633** (user-confirmed). Record N (passed) and M (skipped); N must not drop below baseline after STEP35-OPT, and total collected must be ≥ 633 + new tests.

- [ ] **Step 2: Confirm golden suite green**

Run: `python -m pytest railway/tests/regression/test_golden_outputs.py -q`
Expected: PASS (all pinned outputs byte-identical). If not green at baseline, STOP and report — do not proceed.

- [ ] **Step 3: Snapshot which divisions have policy data**

Run: `python -c "from pathlib import Path; import railway.railway_config as c; [print(d, (c.OUTPUT_DIR/d/'railway_inventory_policy.csv').exists()) for d in ['MAS','SA','TPJ','MDU','PGT','TVC']]"`
Expected: a coverage map. Record it for the report (divisions without data are skipped, not errors).

- [ ] **Step 4: Commit (no code yet — checkpoint only via plan note)**

No commit. This task only records baseline numbers used downstream.

---

## Task A2 (Phase A): Config constants (additive)

**Files:**
- Modify: `railway/railway_config.py` (append a new numbered section at end of file)

- [ ] **Step 1: Write the failing test**

Create/append in `railway/tests/test_enterprise_allocation.py`:

```python
"""STEP35-OPT: enterprise budget optimization & capital allocation tests."""
import math
import numpy as np
import pandas as pd
import pytest

from railway import railway_config as cfg


def test_step35opt_config_constants_exist():
    # frontier budget levels (label, rupees) incl. Unlimited as math.inf
    labels = [lbl for lbl, _ in cfg.FRONTIER_BUDGETS]
    assert labels == ["Rs 1 Cr", "Rs 5 Cr", "Rs 10 Cr", "Rs 25 Cr",
                      "Rs 50 Cr", "Rs 100 Cr", "Rs 200 Cr", "Rs 500 Cr", "Unlimited"]
    assert cfg.FRONTIER_BUDGETS[0][1] == 1_00_00_000.0
    assert cfg.FRONTIER_BUDGETS[5][1] == 1_00_00_00_000.0      # 100 Cr
    assert math.isinf(cfg.FRONTIER_BUDGETS[-1][1])             # Unlimited
    assert cfg.ENTERPRISE_BUDGET == 1_00_00_00_000.0           # 100 Cr headline
    assert cfg.ANNUAL_PROCUREMENT_BUDGET is None               # None => equal-thirds
    assert cfg.ROADMAP_YEARS == ["FY2026-27", "FY2027-28", "FY2028-29"]
    assert cfg.RISK_REDUCTION_TARGETS == [0.50, 0.75, 0.90]
    exec_labels = [lbl for lbl, _ in cfg.EXECUTIVE_SCENARIO_BUDGETS]
    assert exec_labels == ["Rs 25 Cr", "Rs 50 Cr", "Rs 100 Cr", "Rs 200 Cr", "Unlimited"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_step35opt_config_constants_exist -v`
Expected: FAIL — `AttributeError: module 'railway.railway_config' has no attribute 'FRONTIER_BUDGETS'`.

- [ ] **Step 3: Append config (do NOT modify existing constants)**

Append to the END of `railway/railway_config.py`:

```python

# ======================================================================
# 18. STEP35-OPT — ENTERPRISE BUDGET OPTIMIZATION (additive; Indian numbering)
# ======================================================================
# Budget frontier sweep used by solve_budget_frontier(). "Unlimited" = math.inf
# (knapsack then funds every affordable procurement-required item).
import math as _math
FRONTIER_BUDGETS = [
    ("Rs 1 Cr",   1_00_00_000.0),
    ("Rs 5 Cr",   5_00_00_000.0),
    ("Rs 10 Cr",  10_00_00_000.0),
    ("Rs 25 Cr",  25_00_00_000.0),
    ("Rs 50 Cr",  50_00_00_000.0),
    ("Rs 100 Cr", 1_00_00_00_000.0),
    ("Rs 200 Cr", 2_00_00_00_000.0),
    ("Rs 500 Cr", 5_00_00_00_000.0),
    ("Unlimited", _math.inf),
]
# Headline enterprise budget for cross-division allocation (Phase D).
ENTERPRISE_BUDGET = 1_00_00_00_000.0          # Rs 100 Cr

# Multi-year procurement roadmap (Phase E). None => annual budget auto = total / len(years).
ANNUAL_PROCUREMENT_BUDGET = None
ROADMAP_YEARS = ["FY2026-27", "FY2027-28", "FY2028-29"]

# Executive decision-support scenarios (Phase F).
EXECUTIVE_SCENARIO_BUDGETS = [
    ("Rs 25 Cr",  25_00_00_000.0),
    ("Rs 50 Cr",  50_00_00_000.0),
    ("Rs 100 Cr", 1_00_00_00_000.0),
    ("Rs 200 Cr", 2_00_00_00_000.0),
    ("Unlimited", _math.inf),
]
# Risk-reduction targets for the board dashboard (Phase H).
RISK_REDUCTION_TARGETS = [0.50, 0.75, 0.90]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_step35opt_config_constants_exist -v`
Expected: PASS.

- [ ] **Step 5: Confirm no golden output changed (config-only edit)**

Run: `python -m pytest railway/tests/regression/test_golden_outputs.py -q`
Expected: PASS (config additions do not regenerate any output).

- [ ] **Step 6: Commit**

```bash
git add railway/railway_config.py railway/tests/test_enterprise_allocation.py
git commit -m "feat(step35-opt): add enterprise budget optimization config constants"
```

---

## Task B1 (Phase B): `solve_budget_frontier` primitive

**Files:**
- Modify: `railway/railway_inventory_optimization.py` (append after `allocate_procurement_budget`)
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append to `railway/tests/test_enterprise_allocation.py`:

```python
from railway import railway_inventory_optimization as opt


def _toy_opt():
    """Minimal procurement-required frame with the exact columns the solver reads."""
    return pd.DataFrame({
        "PL_Code": ["P1", "P2", "P3", "P4"],
        "Description": ["a", "b", "c", "d"],
        "ABC_Class": ["A", "A", "B1", "C"],
        "Criticality": ["S1", "S2", "S3", "S4"],
        "Inventory_Status": ["Procurement Required"] * 4,
        "Service_Risk_Reduction_Score": [100.0, 40.0, 30.0, 10.0],
        "Inventory_Investment_Required": [1_00_00_000.0, 50_00_000.0, 30_00_000.0, 10_00_000.0],
    })


def test_frontier_monotonic_and_unlimited_funds_all():
    fr = opt.solve_budget_frontier(_toy_opt(), budgets=cfg.FRONTIER_BUDGETS, write=False)
    # risk reduction % is non-decreasing as budget grows
    rr = fr["Risk_Reduction_Pct"].tolist()
    assert all(b >= a - 1e-9 for a, b in zip(rr, rr[1:]))
    # Unlimited funds every procurement-required item => 100% risk reduction
    last = fr.iloc[-1]
    assert last["Budget_Label"] == "Unlimited"
    assert last["PLs_Funded"] == 4
    assert abs(last["Risk_Reduction_Pct"] - 100.0) < 1e-6
    # required columns present
    for col in ["Budget_Label", "Budget_Rupees", "PLs_Funded", "Critical_PLs_Funded",
                "SRRS_Mitigated", "SRRS_Remaining", "Risk_Reduction_Pct",
                "Budget_Utilized", "Marginal_SRRS_Per_Rupee"]:
        assert col in fr.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_frontier_monotonic_and_unlimited_funds_all -v`
Expected: FAIL — `AttributeError: ... has no attribute 'solve_budget_frontier'`.

- [ ] **Step 3: Append the primitive (reuses `allocate_with_reserve` verbatim)**

Append to `railway/railway_inventory_optimization.py` (after `allocate_procurement_budget`, before the `# Validation / reporting` section):

```python
# ----------------------------------------------------------------------
# STEP35-OPT (Phase B): budget frontier -- solve the EXISTING knapsack
# repeatedly across budget levels. Reuses allocate_with_reserve; no new
# optimization logic, no change to objective/constraints/reserve.
# ----------------------------------------------------------------------
def solve_budget_frontier(opt: pd.DataFrame, budgets=None, write: bool = True):
    """For each budget level solve the existing Safety-Reserve knapsack and report
    funded PLs, SRRS mitigated/remaining, risk-reduction %, capital used and the
    marginal SRRS per rupee vs the previous level. Returns a DataFrame.

    budgets: list of (label, rupees); rupees may be math.inf for 'Unlimited'.
    """
    import math
    if budgets is None:
        budgets = cfg.FRONTIER_BUDGETS
    cand = opt[opt["Inventory_Status"] == "Procurement Required"].copy().reset_index(drop=True)
    total_srrs = float(cand["Service_Risk_Reduction_Score"].sum())
    all_in = float(cand["Inventory_Investment_Required"].sum()) + 1.0  # finite cap for "Unlimited"
    rows = []
    prev_srrs = 0.0
    prev_spent = 0.0
    for label, rupees in budgets:
        eff = all_in if math.isinf(rupees) else rupees   # never feed inf to PuLP
        sel = sorted(allocate_with_reserve(
            cand, eff, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
        funded = cand.loc[sel]
        srrs = float(funded["Service_Risk_Reduction_Score"].sum())
        spent = float(funded["Inventory_Investment_Required"].sum())
        crit_funded = int(funded["Criticality"].isin(cfg.SAFETY_RESERVE_CRITICALITIES).sum())
        d_srrs = srrs - prev_srrs
        d_spent = spent - prev_spent
        marginal = (d_srrs / d_spent) if d_spent > 1e-9 else 0.0
        rows.append({
            "Budget_Label": label,
            "Budget_Rupees": (None if math.isinf(rupees) else round(rupees, 2)),
            "PLs_Funded": int(len(funded)),
            "Critical_PLs_Funded": crit_funded,
            "SRRS_Mitigated": round(srrs, 4),
            "SRRS_Remaining": round(total_srrs - srrs, 4),
            "Risk_Reduction_Pct": round((srrs / total_srrs * 100.0) if total_srrs > 0 else 0.0, 4),
            "Budget_Utilized": round(spent, 2),
            "Marginal_SRRS_Per_Rupee": round(marginal, 8),
        })
        prev_srrs, prev_spent = srrs, spent
    frame = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        frame.to_csv(cfg.OUTPUT_DIR / "risk_reduction_frontier.csv", index=False)
    return frame
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_frontier_monotonic_and_unlimited_funds_all -v`
Expected: PASS.

- [ ] **Step 5: Verify the existing optimizer suite is unaffected**

Run: `python -m pytest railway/tests/test_inventory_optimization.py railway/tests/regression -q`
Expected: PASS (append-only; no existing function or output touched).

- [ ] **Step 6: Commit**

```bash
git add railway/railway_inventory_optimization.py railway/tests/test_enterprise_allocation.py
git commit -m "feat(step35-opt): add solve_budget_frontier reusing existing knapsack"
```

---

## Task B2 (Phase B): Orchestration scaffold + `build_risk_reduction_frontier`

**Files:**
- Create: `railway/governance/enterprise_allocation.py`
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append to `railway/tests/test_enterprise_allocation.py`:

```python
from railway.governance import enterprise_allocation as ea


def test_build_risk_reduction_frontier_from_live_outputs():
    fr = ea.build_risk_reduction_frontier(write=False)
    assert not fr.empty
    assert fr["Risk_Reduction_Pct"].iloc[-1] >= fr["Risk_Reduction_Pct"].iloc[0]
    assert fr["Budget_Label"].iloc[-1] == "Unlimited"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_build_risk_reduction_frontier_from_live_outputs -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'railway.governance.enterprise_allocation'`.

- [ ] **Step 3: Create the orchestration module (loaders + frontier builder)**

Create `railway/governance/enterprise_allocation.py`:

```python
"""STEP35-OPT — Enterprise Budget Optimization & Capital Allocation (orchestration).

This module is ORCHESTRATION + IO only. ALL optimization (knapsack, frontier,
pooled enterprise allocation, roadmap) is delegated to the single source of truth
railway.railway_inventory_optimization. This module:
  * reads existing per-division railway_inventory_policy.csv outputs (read-only),
  * calls the solver primitives,
  * writes only NEW output CSVs (never rewrites a pinned output).
"""
from __future__ import annotations

import pandas as pd

from railway import railway_config as cfg
from railway import railway_business_unit_config as buc
from railway import railway_inventory_optimization as opt

_POLICY = "railway_inventory_policy.csv"
_CAND_COLS = ["PL_Code", "Description", "ABC_Class", "Criticality", "Inventory_Status",
              "Inventory_Investment_Required", "Service_Risk_Reduction_Score",
              "Lead_Time_Months"]


def live_divisions() -> list[str]:
    """Live divisions in canonical order (STTC_PTJ is 'Configured' -> excluded)."""
    return [bu for bu in buc.BUSINESS_UNIT_ORDER if buc.is_live(bu)]


def _read_policy(path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"PL_Code": str})
    keep = [c for c in _CAND_COLS if c in df.columns]
    return df[keep].copy()


def load_enterprise_opt() -> pd.DataFrame:
    """Consolidated candidate frame from outputs/railway_inventory_policy.csv."""
    return _read_policy(cfg.INVENTORY_POLICY_CSV)


def load_division_frames() -> dict[str, pd.DataFrame]:
    """Per-division procurement-required candidates. Divisions without a policy CSV
    are skipped (coverage is reported, not an error)."""
    out: dict[str, pd.DataFrame] = {}
    for div in live_divisions():
        p = cfg.OUTPUT_DIR / div / _POLICY
        if not p.exists():
            continue
        df = _read_policy(p)
        df = df[df["Inventory_Status"] == "Procurement Required"].reset_index(drop=True)
        if not df.empty:
            out[div] = df
    return out


# ---- Phase B -------------------------------------------------------------
def build_risk_reduction_frontier(write: bool = True) -> pd.DataFrame:
    opt_df = load_enterprise_opt()
    fr = opt.solve_budget_frontier(opt_df, budgets=cfg.FRONTIER_BUDGETS, write=False)
    if write:
        cfg.ensure_output_dirs()
        fr.to_csv(cfg.OUTPUT_DIR / "risk_reduction_frontier.csv", index=False)
    return fr
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_build_risk_reduction_frontier_from_live_outputs -v`
Expected: PASS.

- [ ] **Step 5: Generate the deliverable + confirm goldens untouched**

Run: `python -c "from railway.governance import enterprise_allocation as e; e.build_risk_reduction_frontier(write=True)"`
Then: `python -m pytest railway/tests/regression -q`
Expected: regression PASS; `risk_reduction_frontier.csv` now exists (new, allowed).

- [ ] **Step 6: Commit**

```bash
git add railway/governance/enterprise_allocation.py railway/tests/test_enterprise_allocation.py railway/outputs/risk_reduction_frontier.csv
git commit -m "feat(step35-opt): enterprise_allocation module + risk_reduction_frontier.csv"
```

---

## Task C1 (Phase C): Budget efficiency / knee-point

**Files:**
- Modify: `railway/governance/enterprise_allocation.py`
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_budget_efficiency_knee_within_range():
    eff = ea.build_budget_efficiency_analysis(write=False)
    assert {"Budget_Label", "Risk_Reduction_Pct", "Marginal_SRRS_Per_Rupee",
            "Is_Knee_Point", "Is_Diminishing_Returns", "Region"}.issubset(eff.columns)
    assert int(eff["Is_Knee_Point"].sum()) == 1            # exactly one knee
    # knee is not the trivial first/last finite point
    knee_idx = eff.index[eff["Is_Knee_Point"]].tolist()[0]
    assert knee_idx not in (0, len(eff[eff["Budget_Label"] != "Unlimited"]) - 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_budget_efficiency_knee_within_range -v`
Expected: FAIL — `AttributeError: ... 'build_budget_efficiency_analysis'`.

- [ ] **Step 3: Implement (Kneedle-style on finite levels; deterministic)**

Append to `railway/governance/enterprise_allocation.py`:

```python
# ---- Phase C -------------------------------------------------------------
def build_budget_efficiency_analysis(frontier: pd.DataFrame | None = None,
                                     write: bool = True) -> pd.DataFrame:
    """Knee-point + diminishing-returns + region labels over the FINITE budget
    levels (Unlimited excluded from geometry, carried as 'Saturation')."""
    fr = (frontier if frontier is not None else build_risk_reduction_frontier(write=False)).copy()
    finite = fr[fr["Budget_Label"] != "Unlimited"].reset_index(drop=True)
    n = len(finite)
    eff = fr.copy()
    eff["Is_Knee_Point"] = False
    eff["Is_Diminishing_Returns"] = False
    eff["Region"] = ""

    if n >= 3:
        x = finite["Budget_Rupees"].astype(float).to_numpy()
        y = finite["Risk_Reduction_Pct"].astype(float).to_numpy()
        xn = (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x * 0.0
        yn = (y - y.min()) / (y.max() - y.min()) if y.max() > y.min() else y * 0.0
        # knee = max vertical distance of the curve above the chord (concave knee)
        dist = yn - xn
        knee_pos = int(dist.argmax())
        eff.loc[eff["Budget_Label"] == finite.loc[knee_pos, "Budget_Label"], "Is_Knee_Point"] = True
        # diminishing returns: first finite level whose marginal/rupee < 25% of the
        # initial (first-level) marginal/rupee
        m = finite["Marginal_SRRS_Per_Rupee"].astype(float).to_numpy()
        thresh = 0.25 * m[0] if m[0] > 0 else 0.0
        dr_pos = next((i for i in range(1, n) if m[i] < thresh), n - 1)
        eff.loc[eff["Budget_Label"] == finite.loc[dr_pos, "Budget_Label"],
                "Is_Diminishing_Returns"] = True
        # regions: <=knee Efficient, knee..dr Optimal-Investment, >dr Diminishing
        for i, lbl in enumerate(finite["Budget_Label"]):
            region = ("Efficient" if i < knee_pos
                      else "Optimal_Investment" if i <= dr_pos
                      else "Diminishing_Returns")
            eff.loc[eff["Budget_Label"] == lbl, "Region"] = region
    eff.loc[eff["Budget_Label"] == "Unlimited", "Region"] = "Saturation"

    cols = ["Budget_Label", "Budget_Rupees", "Risk_Reduction_Pct",
            "Marginal_SRRS_Per_Rupee", "Is_Knee_Point", "Is_Diminishing_Returns", "Region"]
    eff = eff[cols]
    if write:
        cfg.ensure_output_dirs()
        eff.to_csv(cfg.OUTPUT_DIR / "budget_efficiency_analysis.csv", index=False)
    return eff
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_budget_efficiency_knee_within_range -v`
Expected: PASS.

- [ ] **Step 5: Generate deliverable + regression check**

Run: `python -c "from railway.governance import enterprise_allocation as e; e.build_budget_efficiency_analysis(write=True)"`
Then: `python -m pytest railway/tests/regression -q`
Expected: PASS; `budget_efficiency_analysis.csv` written.

- [ ] **Step 6: Commit**

```bash
git add railway/governance/enterprise_allocation.py railway/tests/test_enterprise_allocation.py railway/outputs/budget_efficiency_analysis.csv
git commit -m "feat(step35-opt): budget_efficiency_analysis.csv (knee-point + regions)"
```

---

## Task D1 (Phase D): `enterprise_capital_allocation` primitive (pooled knapsack)

**Files:**
- Modify: `railway/railway_inventory_optimization.py` (append)
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_enterprise_pooled_allocation_respects_budget_and_aggregates():
    frames = {
        "MAS": pd.DataFrame({
            "PL_Code": ["M1", "M2"], "Description": ["m1", "m2"],
            "ABC_Class": ["A", "B1"], "Criticality": ["S1", "S3"],
            "Inventory_Status": ["Procurement Required"] * 2,
            "Service_Risk_Reduction_Score": [90.0, 20.0],
            "Inventory_Investment_Required": [60_00_000.0, 30_00_000.0]}),
        "SA": pd.DataFrame({
            "PL_Code": ["S1x"], "Description": ["s1"],
            "ABC_Class": ["A"], "Criticality": ["S2"],
            "Inventory_Status": ["Procurement Required"],
            "Service_Risk_Reduction_Score": [70.0],
            "Inventory_Investment_Required": [50_00_000.0]}),
    }
    alloc = opt.enterprise_capital_allocation(frames, budget=1_00_00_000.0, write=False)
    assert set(alloc["Division"]) <= {"MAS", "SA"}
    assert alloc["Allocated_Budget"].sum() <= 1_00_00_000.0 + 1e-6
    for col in ["Division", "Allocated_Budget", "PLs_Funded", "SRRS_Mitigated",
                "Risk_Reduction_Pct", "Capital_Efficiency"]:
        assert col in alloc.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_enterprise_pooled_allocation_respects_budget_and_aggregates -v`
Expected: FAIL — no attribute `enterprise_capital_allocation`.

- [ ] **Step 3: Append the primitive (one pooled knapsack across divisions)**

Append to `railway/railway_inventory_optimization.py`:

```python
# ----------------------------------------------------------------------
# STEP35-OPT (Phase D): enterprise capital allocation -- pool every
# division's procurement-required candidates into ONE frame and solve the
# EXISTING Safety-Reserve knapsack once at the enterprise budget. The optimal
# per-division split is then the sum of each division's selected investment.
# This maximises enterprise-wide SRRS by construction; no new objective.
# ----------------------------------------------------------------------
def enterprise_capital_allocation(division_frames: dict, budget: float,
                                  write: bool = True):
    """division_frames: {division: DataFrame of procurement-required candidates}.
    Returns a per-division allocation DataFrame for the given enterprise budget."""
    pooled = []
    for div, df in division_frames.items():
        d = df[df["Inventory_Status"] == "Procurement Required"].copy()
        d["Division"] = div
        pooled.append(d)
    if not pooled:
        return pd.DataFrame(columns=["Division", "Allocated_Budget", "PLs_Funded",
                                     "SRRS_Mitigated", "Risk_Reduction_Pct", "Capital_Efficiency"])
    pool = pd.concat(pooled, ignore_index=True)
    total_by_div = pool.groupby("Division")["Service_Risk_Reduction_Score"].sum()

    import math
    eff = budget
    if math.isinf(budget):                       # never feed inf to PuLP
        eff = float(pool["Inventory_Investment_Required"].sum()) + 1.0
    sel = sorted(allocate_with_reserve(
        pool, eff, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
    funded = pool.loc[sel]

    rows = []
    for div in sorted(division_frames):
        f = funded[funded["Division"] == div]
        spent = float(f["Inventory_Investment_Required"].sum())
        srrs = float(f["Service_Risk_Reduction_Score"].sum())
        tot = float(total_by_div.get(div, 0.0))
        rows.append({
            "Division": div,
            "Allocated_Budget": round(spent, 2),
            "PLs_Funded": int(len(f)),
            "SRRS_Mitigated": round(srrs, 4),
            "Risk_Reduction_Pct": round((srrs / tot * 100.0) if tot > 0 else 0.0, 4),
            "Capital_Efficiency": round((srrs / spent) if spent > 1e-9 else 0.0, 8),
        })
    alloc = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        alloc.to_csv(cfg.OUTPUT_DIR / "enterprise_budget_allocation.csv", index=False)
    return alloc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_enterprise_pooled_allocation_respects_budget_and_aggregates -v`
Expected: PASS.

- [ ] **Step 5: Existing optimizer + regression unaffected**

Run: `python -m pytest railway/tests/test_inventory_optimization.py railway/tests/regression -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add railway/railway_inventory_optimization.py railway/tests/test_enterprise_allocation.py
git commit -m "feat(step35-opt): add enterprise_capital_allocation pooled knapsack"
```

---

## Task D2 (Phase D): Enterprise allocation builder (₹100 Cr headline + sweep)

**Files:**
- Modify: `railway/governance/enterprise_allocation.py`
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_build_enterprise_budget_allocation_has_headline_and_sweep():
    alloc = ea.build_enterprise_budget_allocation(write=False)
    assert "Budget_Label" in alloc.columns and "Division" in alloc.columns
    assert "Rs 100 Cr" in set(alloc["Budget_Label"])     # headline present
    # each budget level's allocation cannot exceed that level's rupees
    fin = alloc[alloc["Budget_Label"] != "Unlimited"]
    for lbl, grp in fin.groupby("Budget_Label"):
        cap = dict(cfg.FRONTIER_BUDGETS)[lbl]
        assert grp["Allocated_Budget"].sum() <= cap + 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_build_enterprise_budget_allocation_has_headline_and_sweep -v`
Expected: FAIL — no attribute `build_enterprise_budget_allocation`.

- [ ] **Step 3: Implement the builder (loops the frontier budgets, tags each row)**

Append to `railway/governance/enterprise_allocation.py`:

```python
# ---- Phase D -------------------------------------------------------------
def build_enterprise_budget_allocation(write: bool = True) -> pd.DataFrame:
    """Per-division capital allocation at the Rs 100 Cr headline AND every frontier
    level, so the Board sees how the optimal split shifts with the budget."""
    frames = load_division_frames()
    out = []
    for label, rupees in cfg.FRONTIER_BUDGETS:
        alloc = opt.enterprise_capital_allocation(frames, rupees, write=False)
        alloc.insert(0, "Budget_Label", label)
        alloc.insert(1, "Budget_Rupees", None if rupees == float("inf") else round(rupees, 2))
        out.append(alloc)
    result = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    if write:
        cfg.ensure_output_dirs()
        result.to_csv(cfg.OUTPUT_DIR / "enterprise_budget_allocation.csv", index=False)
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_build_enterprise_budget_allocation_has_headline_and_sweep -v`
Expected: PASS.

- [ ] **Step 5: Generate deliverable + regression check**

Run: `python -c "from railway.governance import enterprise_allocation as e; e.build_enterprise_budget_allocation(write=True)"`
Then: `python -m pytest railway/tests/regression -q`
Expected: PASS; `enterprise_budget_allocation.csv` written.

- [ ] **Step 6: Commit**

```bash
git add railway/governance/enterprise_allocation.py railway/tests/test_enterprise_allocation.py railway/outputs/enterprise_budget_allocation.csv
git commit -m "feat(step35-opt): enterprise_budget_allocation.csv (100 Cr headline + sweep)"
```

---

## Task E1 (Phase E): `procurement_roadmap` primitive (multi-year, knapsack per year)

**Files:**
- Modify: `railway/railway_inventory_optimization.py` (append)
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_roadmap_three_years_cumulative_nondecreasing():
    rm = opt.procurement_roadmap(_toy_opt(), annual_budget=60_00_000.0,
                                 years=["FY2026-27", "FY2027-28", "FY2028-29"], write=False)
    assert list(rm["Year"]) == ["FY2026-27", "FY2027-28", "FY2028-29"]
    cum = rm["Cumulative_Risk_Reduction_Pct"].tolist()
    assert all(b >= a - 1e-9 for a, b in zip(cum, cum[1:]))
    assert rm["Items_Funded"].sum() <= 4
    for col in ["Year", "Items_Funded", "Capital_Required",
                "Cumulative_Risk_Reduction_Pct", "Remaining_Exposure"]:
        assert col in rm.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_roadmap_three_years_cumulative_nondecreasing -v`
Expected: FAIL — no attribute `procurement_roadmap`.

- [ ] **Step 3: Append the primitive (year-by-year knapsack, carry unfunded forward)**

Append to `railway/railway_inventory_optimization.py`:

```python
# ----------------------------------------------------------------------
# STEP35-OPT (Phase E): multi-year procurement roadmap. Each year runs the
# EXISTING Safety-Reserve knapsack on the still-unfunded procurement-required
# items under that year's budget; unfunded items carry to the next year.
# Highest-SRRS / insurance spares are funded first by the existing reserve.
# ----------------------------------------------------------------------
def procurement_roadmap(opt: pd.DataFrame, annual_budget=None, years=None,
                        write: bool = True):
    """annual_budget None => total procurement requirement / len(years) (equal thirds)."""
    if years is None:
        years = cfg.ROADMAP_YEARS
    cand = opt[opt["Inventory_Status"] == "Procurement Required"].copy().reset_index(drop=True)
    total_srrs = float(cand["Service_Risk_Reduction_Score"].sum())
    total_req = float(cand["Inventory_Investment_Required"].sum())
    if annual_budget is None:
        annual_budget = total_req / len(years) if years else 0.0

    remaining = cand.copy()
    cum_srrs = 0.0
    rows = []
    for yr in years:
        rem = remaining.reset_index(drop=True)
        sel = sorted(allocate_with_reserve(
            rem, annual_budget, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
        funded = rem.loc[sel]
        cap = float(funded["Inventory_Investment_Required"].sum())
        cum_srrs += float(funded["Service_Risk_Reduction_Score"].sum())
        rows.append({
            "Year": yr,
            "Annual_Budget": round(annual_budget, 2),
            "Items_Funded": int(len(funded)),
            "Capital_Required": round(cap, 2),
            "Cumulative_Risk_Reduction_Pct": round((cum_srrs / total_srrs * 100.0) if total_srrs > 0 else 0.0, 4),
            "Remaining_Exposure": round(total_req - float(cand.loc[
                cand["PL_Code"].isin(_funded_so_far(rows, funded)), "Inventory_Investment_Required"].sum()) if False else (total_req - _spent_so_far(rows, cap)), 2),
        })
        funded_ids = set(funded["PL_Code"])
        remaining = remaining[~remaining["PL_Code"].isin(funded_ids)]
    rm = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        rm.to_csv(cfg.OUTPUT_DIR / "procurement_roadmap.csv", index=False)
    return rm
```

> NOTE for the implementer: the `Remaining_Exposure` expression above is intentionally simplified in this plan — replace it with the clean running-total form below (do NOT keep the `if False` placeholder). Use this exact body for the remaining-exposure accumulation instead:

```python
    remaining = cand.copy()
    cum_srrs = 0.0
    cum_cap = 0.0
    rows = []
    for yr in years:
        rem = remaining.reset_index(drop=True)
        sel = sorted(allocate_with_reserve(
            rem, annual_budget, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
        funded = rem.loc[sel]
        cap = float(funded["Inventory_Investment_Required"].sum())
        cum_cap += cap
        cum_srrs += float(funded["Service_Risk_Reduction_Score"].sum())
        rows.append({
            "Year": yr,
            "Annual_Budget": round(annual_budget, 2),
            "Items_Funded": int(len(funded)),
            "Capital_Required": round(cap, 2),
            "Cumulative_Risk_Reduction_Pct": round((cum_srrs / total_srrs * 100.0) if total_srrs > 0 else 0.0, 4),
            "Remaining_Exposure": round(total_req - cum_cap, 2),
        })
        remaining = remaining[~remaining["PL_Code"].isin(set(funded["PL_Code"]))]
```

(The helper functions `_funded_so_far`/`_spent_so_far` referenced in the first draft must NOT be created — use the clean running-total `cum_cap` form. The first code block is illustrative of the row shape only; implement the second.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_roadmap_three_years_cumulative_nondecreasing -v`
Expected: PASS.

- [ ] **Step 5: Existing optimizer + regression unaffected**

Run: `python -m pytest railway/tests/test_inventory_optimization.py railway/tests/regression -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add railway/railway_inventory_optimization.py railway/tests/test_enterprise_allocation.py
git commit -m "feat(step35-opt): add procurement_roadmap multi-year sequencing"
```

---

## Task E2 (Phase E): Roadmap builder

**Files:**
- Modify: `railway/governance/enterprise_allocation.py`
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_build_procurement_roadmap_from_live_outputs():
    rm = ea.build_procurement_roadmap(write=False)
    assert list(rm["Year"]) == cfg.ROADMAP_YEARS
    assert rm["Remaining_Exposure"].iloc[-1] <= rm["Remaining_Exposure"].iloc[0] + 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_build_procurement_roadmap_from_live_outputs -v`
Expected: FAIL — no attribute `build_procurement_roadmap`.

- [ ] **Step 3: Implement the builder**

Append to `railway/governance/enterprise_allocation.py`:

```python
# ---- Phase E -------------------------------------------------------------
def build_procurement_roadmap(write: bool = True) -> pd.DataFrame:
    opt_df = load_enterprise_opt()
    rm = opt.procurement_roadmap(opt_df, annual_budget=cfg.ANNUAL_PROCUREMENT_BUDGET,
                                 years=cfg.ROADMAP_YEARS, write=False)
    if write:
        cfg.ensure_output_dirs()
        rm.to_csv(cfg.OUTPUT_DIR / "procurement_roadmap.csv", index=False)
    return rm
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_build_procurement_roadmap_from_live_outputs -v`
Expected: PASS.

- [ ] **Step 5: Generate deliverable + regression check**

Run: `python -c "from railway.governance import enterprise_allocation as e; e.build_procurement_roadmap(write=True)"`
Then: `python -m pytest railway/tests/regression -q`
Expected: PASS; `procurement_roadmap.csv` written.

- [ ] **Step 6: Commit**

```bash
git add railway/governance/enterprise_allocation.py railway/tests/test_enterprise_allocation.py railway/outputs/procurement_roadmap.csv
git commit -m "feat(step35-opt): procurement_roadmap.csv (3-year funding sequence)"
```

---

## Task F1 (Phase F): Executive budget scenarios

**Files:**
- Modify: `railway/governance/enterprise_allocation.py`
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_executive_budget_scenarios_columns_and_levels():
    sc = ea.build_executive_budget_scenarios(write=False)
    assert list(sc["Scenario"]) == ["Rs 25 Cr", "Rs 50 Cr", "Rs 100 Cr", "Rs 200 Cr", "Unlimited"]
    for col in ["Scenario", "PLs_Funded", "SRRS_Removed", "SRRS_Remaining",
                "Risk_Reduction_Pct", "S1_Funded", "S2_Funded", "S3_Funded", "S4_Funded",
                "Capital_Utilized", "Capital_Efficiency"]:
        assert col in sc.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_executive_budget_scenarios_columns_and_levels -v`
Expected: FAIL — no attribute `build_executive_budget_scenarios`.

- [ ] **Step 3: Implement (per-tier funded counts via direct knapsack selection)**

Append to `railway/governance/enterprise_allocation.py`:

```python
# ---- Phase F -------------------------------------------------------------
def build_executive_budget_scenarios(write: bool = True) -> pd.DataFrame:
    """Board-facing scenarios: what is procured, SRRS removed/remaining, tier mix,
    capital used and efficiency at each scenario budget."""
    cand = load_enterprise_opt()
    cand = cand[cand["Inventory_Status"] == "Procurement Required"].reset_index(drop=True)
    total_srrs = float(cand["Service_Risk_Reduction_Score"].sum())
    all_in = float(cand["Inventory_Investment_Required"].sum()) + 1.0  # finite cap for "Unlimited"
    rows = []
    for label, rupees in cfg.EXECUTIVE_SCENARIO_BUDGETS:
        import math as _m
        eff = all_in if _m.isinf(rupees) else rupees
        sel = sorted(opt.allocate_with_reserve(
            cand, eff, "Service_Risk_Reduction_Score", "Inventory_Investment_Required"))
        f = cand.loc[sel]
        srrs = float(f["Service_Risk_Reduction_Score"].sum())
        spent = float(f["Inventory_Investment_Required"].sum())
        tier = f["Criticality"].value_counts()
        rows.append({
            "Scenario": label,
            "PLs_Funded": int(len(f)),
            "SRRS_Removed": round(srrs, 4),
            "SRRS_Remaining": round(total_srrs - srrs, 4),
            "Risk_Reduction_Pct": round((srrs / total_srrs * 100.0) if total_srrs > 0 else 0.0, 4),
            "S1_Funded": int(tier.get("S1", 0)),
            "S2_Funded": int(tier.get("S2", 0)),
            "S3_Funded": int(tier.get("S3", 0)),
            "S4_Funded": int(tier.get("S4", 0)),
            "Capital_Utilized": round(spent, 2),
            "Capital_Efficiency": round((srrs / spent) if spent > 1e-9 else 0.0, 8),
        })
    sc = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        sc.to_csv(cfg.OUTPUT_DIR / "executive_budget_scenarios.csv", index=False)
    return sc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_executive_budget_scenarios_columns_and_levels -v`
Expected: PASS.

- [ ] **Step 5: Generate deliverable + regression check (verify plural vs singular)**

Run: `python -c "from railway.governance import enterprise_allocation as e; e.build_executive_budget_scenarios(write=True)"`
Then: `python -m pytest railway/tests/regression -q`
Expected: PASS. Confirm the NEW file is `executive_budget_scenarios.csv` (plural) and the EXISTING `executive_budget_scenario.csv` (singular) is untouched.

- [ ] **Step 6: Commit**

```bash
git add railway/governance/enterprise_allocation.py railway/tests/test_enterprise_allocation.py railway/outputs/executive_budget_scenarios.csv
git commit -m "feat(step35-opt): executive_budget_scenarios.csv (board scenarios)"
```

---

## Task A3 (Phase A): Baseline validation builder + master `run()`

**Files:**
- Modify: `railway/governance/enterprise_allocation.py`
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_baseline_validation_documents_unchanged_optimizer():
    bv = ea.build_optimization_baseline_validation(write=False)
    assert {"Aspect", "Value", "Status"}.issubset(bv.columns)
    aspects = set(bv["Aspect"])
    assert {"Decision_Variables", "Objective_Function", "Budget_Constraint",
            "Affordability_Filter", "Safety_Reserve", "Explainability_Outputs"} <= aspects
    assert (bv["Status"] == "UNCHANGED").all()


def test_master_run_writes_all_outputs(tmp_path, monkeypatch):
    # smoke: run() returns a dict of frames without raising
    summary = ea.run(write=False)
    assert {"frontier", "efficiency", "allocation", "readiness",
            "roadmap", "scenarios"} <= set(summary)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_baseline_validation_documents_unchanged_optimizer railway/tests/test_enterprise_allocation.py::test_master_run_writes_all_outputs -v`
Expected: FAIL — no attributes `build_optimization_baseline_validation` / `run`.

- [ ] **Step 3: Implement baseline validation + orchestrator**

Append to `railway/governance/enterprise_allocation.py`:

```python
# ---- Phase A: baseline validation ---------------------------------------
def build_optimization_baseline_validation(write: bool = True) -> pd.DataFrame:
    """Reconfirm (read-only) the existing optimizer's decision variables, objective,
    constraints, affordability filter, safety-reserve and explainability outputs.
    Status is UNCHANGED for every aspect: STEP35-OPT adds, never alters, these."""
    rows = [
        ("Decision_Variables", "binary x_i in {0,1} per procurement-required PL "
         "(pulp.LpVariable cat=Binary in _solve_knapsack)", "UNCHANGED"),
        ("Objective_Function", "maximize sum(Service_Risk_Reduction_Score * x_i)", "UNCHANGED"),
        ("Budget_Constraint", "sum(Inventory_Investment_Required * x_i) <= budget", "UNCHANGED"),
        ("Affordability_Filter", "items with cost > budget excluded (_solve_knapsack)", "UNCHANGED"),
        ("Safety_Reserve", f"enabled={cfg.SAFETY_RESERVE_ENABLED}, "
         f"pct={cfg.SAFETY_RESERVE_BUDGET_PCT}, tiers={cfg.SAFETY_RESERVE_CRITICALITIES}", "UNCHANGED"),
        ("Explainability_Outputs", "SRRS_Rank, SRRS_Per_Rupee, Funding_Driver, "
         "railway_funding_explainability.csv", "UNCHANGED"),
        ("Default_Procurement_Budget", f"{cfg.PROCUREMENT_BUDGET}", "UNCHANGED"),
        ("Service_Factor_Model", f"baseline_sl={cfg.SERVICE_FACTOR_BASELINE_SL}, "
         f"slope={cfg.SERVICE_FACTOR_SLOPE}", "UNCHANGED"),
    ]
    bv = pd.DataFrame(rows, columns=["Aspect", "Value", "Status"])
    if write:
        cfg.ensure_output_dirs()
        bv.to_csv(cfg.OUTPUT_DIR / "optimization_baseline_validation.csv", index=False)
    return bv


# ---- master orchestrator -------------------------------------------------
def run(write: bool = True) -> dict:
    """Build every STEP35-OPT artifact. Returns a dict of the produced DataFrames."""
    baseline = build_optimization_baseline_validation(write=write)
    frontier = build_risk_reduction_frontier(write=write)
    efficiency = build_budget_efficiency_analysis(frontier=frontier, write=write)
    allocation = build_enterprise_budget_allocation(write=write)
    readiness = build_enterprise_allocation_readiness(write=write)
    roadmap = build_procurement_roadmap(write=write)
    scenarios = build_executive_budget_scenarios(write=write)
    return {"baseline": baseline, "frontier": frontier, "efficiency": efficiency,
            "allocation": allocation, "readiness": readiness,
            "roadmap": roadmap, "scenarios": scenarios}


if __name__ == "__main__":
    import os
    os.environ.setdefault("PYTHONHASHSEED", "0")
    out = run(write=True)
    for k, v in out.items():
        print(f"[{k}] rows={len(v)}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py -v`
Expected: PASS (all STEP35-OPT tests).

- [ ] **Step 5: Generate deliverable + regression check**

Run: `python -c "from railway.governance import enterprise_allocation as e; e.build_optimization_baseline_validation(write=True)"`
Then: `python -m pytest railway/tests/regression -q`
Expected: PASS; `optimization_baseline_validation.csv` written.

- [ ] **Step 6: Commit**

```bash
git add railway/governance/enterprise_allocation.py railway/tests/test_enterprise_allocation.py railway/outputs/optimization_baseline_validation.csv
git commit -m "feat(step35-opt): baseline validation + master run() orchestrator"
```

---

## Task D3 (Phase D): Division allocation-readiness inventory

**Files:**
- Modify: `railway/governance/enterprise_allocation.py`
- Test: `railway/tests/test_enterprise_allocation.py`

Distinguishes which Live divisions actually feed the enterprise allocation (REPORTABLE) vs those whose policy data is missing/empty (DATA_UNAVAILABLE). Makes coverage explicit so the Board never mistakes a thin allocation for a complete one.

- [ ] **Step 1: Write the failing test**

Append to `railway/tests/test_enterprise_allocation.py`:

```python
def test_allocation_readiness_classifies_divisions():
    rd = ea.build_enterprise_allocation_readiness(write=False)
    assert {"Division", "Status", "Procurement_Required_PLs", "Total_SRRS",
            "Total_Investment_Required", "Reason"}.issubset(rd.columns)
    # every Live division appears exactly once
    assert sorted(rd["Division"]) == sorted(ea.live_divisions())
    assert set(rd["Status"]) <= {"REPORTABLE", "DATA_UNAVAILABLE"}
    # REPORTABLE iff it has >=1 procurement-required PL
    for _, r in rd.iterrows():
        if r["Procurement_Required_PLs"] > 0:
            assert r["Status"] == "REPORTABLE"
        else:
            assert r["Status"] == "DATA_UNAVAILABLE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_allocation_readiness_classifies_divisions -v`
Expected: FAIL — no attribute `build_enterprise_allocation_readiness`.

- [ ] **Step 3: Implement (every Live division classified; missing/empty policy → DATA_UNAVAILABLE)**

Append to `railway/governance/enterprise_allocation.py`:

```python
# ---- Phase D: allocation readiness --------------------------------------
def build_enterprise_allocation_readiness(write: bool = True) -> pd.DataFrame:
    """Classify every Live division as REPORTABLE (has procurement-required policy
    data feeding the enterprise allocation) or DATA_UNAVAILABLE (missing/empty CSV
    or zero procurement-required PLs). Makes allocation coverage explicit."""
    rows = []
    for div in live_divisions():
        p = cfg.OUTPUT_DIR / div / _POLICY
        if not p.exists():
            rows.append({"Division": div, "Status": "DATA_UNAVAILABLE",
                         "Procurement_Required_PLs": 0, "Total_SRRS": 0.0,
                         "Total_Investment_Required": 0.0,
                         "Reason": "policy CSV missing"})
            continue
        df = _read_policy(p)
        pr = df[df["Inventory_Status"] == "Procurement Required"]
        n = int(len(pr))
        rows.append({
            "Division": div,
            "Status": "REPORTABLE" if n > 0 else "DATA_UNAVAILABLE",
            "Procurement_Required_PLs": n,
            "Total_SRRS": round(float(pr["Service_Risk_Reduction_Score"].sum()), 4),
            "Total_Investment_Required": round(float(pr["Inventory_Investment_Required"].sum()), 2),
            "Reason": "ok" if n > 0 else "no procurement-required PLs",
        })
    rd = pd.DataFrame(rows)
    if write:
        cfg.ensure_output_dirs()
        rd.to_csv(cfg.OUTPUT_DIR / "enterprise_budget_allocation_readiness.csv", index=False)
    return rd
```

Also add `build_enterprise_allocation_readiness(write=write)` into `run()` (Task A3) — assign to key `"readiness"` in the returned dict, and update the `test_master_run_writes_all_outputs` assertion set to include `"readiness"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_allocation_readiness_classifies_divisions -v`
Expected: PASS.

- [ ] **Step 5: Generate deliverable + regression check**

Run: `python -c "from railway.governance import enterprise_allocation as e; e.build_enterprise_allocation_readiness(write=True)"`
Then: `python -m pytest railway/tests/regression -q`
Expected: PASS; `enterprise_budget_allocation_readiness.csv` written.

- [ ] **Step 6: Commit**

```bash
git add railway/governance/enterprise_allocation.py railway/tests/test_enterprise_allocation.py railway/outputs/enterprise_budget_allocation_readiness.csv
git commit -m "feat(step35-opt): enterprise_budget_allocation_readiness.csv (coverage map)"
```

> NOTE: Task A3's `run()` must call `build_enterprise_allocation_readiness`. If Task A3 is executed before D3, add the call when D3 lands and re-run A3's `test_master_run_writes_all_outputs`.

---

## Task H1 (Phase H): `division_summary` enterprise KPIs + decision dashboard

**Files:**
- Modify: `railway/governance/division_summary.py`
- Test: `railway/tests/test_enterprise_allocation.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
from railway.governance import division_summary as ds


def test_enterprise_decision_dashboard_kpis():
    dash = ds.build_enterprise_decision_dashboard(write=False)
    kpis = set(dash["KPI"])
    assert {"Budget_For_50pct_Risk_Reduction", "Budget_For_75pct_Risk_Reduction",
            "Budget_For_90pct_Risk_Reduction", "Enterprise_Capital_Efficiency",
            "Optimal_Investment_Point", "Tier1_Funding_Requirement"} <= kpis
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_enterprise_decision_dashboard_kpis -v`
Expected: FAIL — no attribute `build_enterprise_decision_dashboard`.

- [ ] **Step 3: Implement (reads frontier + efficiency + enterprise opt; interpolates targets)**

Append to `railway/governance/division_summary.py` (after existing functions; add imports at top if missing — `import pandas as pd`, `from railway import railway_config as cfg` likely already present; add `from railway.governance import enterprise_allocation as _ea`):

```python
def _budget_for_target(frontier, target_pct):
    """Smallest budget (rupees) whose risk-reduction % >= target*100, by linear
    interpolation between bracketing FINITE frontier levels. Returns None if the
    target is unreachable within the finite levels."""
    fin = frontier[frontier["Budget_Label"] != "Unlimited"].reset_index(drop=True)
    tgt = target_pct * 100.0
    prev_b, prev_r = 0.0, 0.0
    for _, row in fin.iterrows():
        b = float(row["Budget_Rupees"]); r = float(row["Risk_Reduction_Pct"])
        if r >= tgt:
            if r == prev_r:
                return round(b, 2)
            frac = (tgt - prev_r) / (r - prev_r)
            return round(prev_b + frac * (b - prev_b), 2)
        prev_b, prev_r = b, r
    return None


def enterprise_kpis() -> dict:
    """Board-level KPIs derived from the STEP35-OPT frontier/efficiency outputs."""
    frontier = _ea.build_risk_reduction_frontier(write=False)
    efficiency = _ea.build_budget_efficiency_analysis(frontier=frontier, write=False)
    opt_df = _ea.load_enterprise_opt()
    pr = opt_df[opt_df["Inventory_Status"] == "Procurement Required"]
    tier1 = pr[pr["Criticality"].isin(cfg.SAFETY_RESERVE_CRITICALITIES)]
    knee = efficiency[efficiency["Is_Knee_Point"]]
    optimal = knee["Budget_Label"].iloc[0] if not knee.empty else "n/a"
    unlim = frontier.iloc[-1]
    ent_eff = (float(unlim["SRRS_Mitigated"]) / float(unlim["Budget_Utilized"])
               if float(unlim["Budget_Utilized"]) > 1e-9 else 0.0)
    return {
        "Budget_For_50pct_Risk_Reduction": _budget_for_target(frontier, 0.50),
        "Budget_For_75pct_Risk_Reduction": _budget_for_target(frontier, 0.75),
        "Budget_For_90pct_Risk_Reduction": _budget_for_target(frontier, 0.90),
        "Enterprise_Capital_Efficiency": round(ent_eff, 8),
        "Optimal_Investment_Point": optimal,
        "Tier1_Funding_Requirement": round(float(tier1["Inventory_Investment_Required"].sum()), 2),
        "Max_Achievable_Risk_Reduction_Pct": round(float(unlim["Risk_Reduction_Pct"]), 4),
    }


def build_enterprise_decision_dashboard(write: bool = True):
    kpis = enterprise_kpis()
    dash = pd.DataFrame([{"KPI": k, "Value": v} for k, v in kpis.items()])
    if write:
        cfg.ensure_output_dirs()
        dash.to_csv(cfg.OUTPUT_DIR / "enterprise_decision_dashboard.csv", index=False)
    return dash
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest railway/tests/test_enterprise_allocation.py::test_enterprise_decision_dashboard_kpis -v`
Expected: PASS.

- [ ] **Step 5: Generate deliverable + FULL regression check (division_summary is reporting-critical)**

Run: `python -c "from railway.governance import division_summary as d; d.build_enterprise_decision_dashboard(write=True)"`
Then: `python -m pytest railway/tests/regression -q`
Expected: PASS — confirm no existing reporting output changed (the new code is append-only and writes only the new dashboard CSV).

- [ ] **Step 6: Commit**

```bash
git add railway/governance/division_summary.py railway/tests/test_enterprise_allocation.py railway/outputs/enterprise_decision_dashboard.csv
git commit -m "feat(step35-opt): enterprise decision dashboard KPIs in division_summary"
```

---

## Task G1 (Phase G): Notebook Section 17 (live-data visualizations)

**Files:**
- Modify: `notebooks/notebook_railway.ipynb` (append Section 17 — full set of 6 figures)
- Modify: `notebooks/notebook_railway_executive.ipynb` (append Section 17 — executive subset: Risk Reduction Curve, Enterprise Allocation Waterfall, Scenario Comparison)

> Use the NotebookEdit tool with `edit_mode: "insert"` to append cells at the end. Cells are self-contained: they resolve the outputs dir from `railway_config`, read the NEW CSVs, and plot. No hardcoded values.

- [ ] **Step 1: Append the Section 17 markdown cell (both notebooks)**

Markdown source:

```markdown
## 17. Enterprise Capital Allocation & Budget Optimization (STEP35-OPT)

**How should Railway management allocate capital across divisions to maximise
enterprise-wide service-risk reduction?** Built live from STEP35-OPT outputs:
`risk_reduction_frontier.csv`, `budget_efficiency_analysis.csv`,
`enterprise_budget_allocation.csv`, `procurement_roadmap.csv`,
`executive_budget_scenarios.csv`, `enterprise_decision_dashboard.csv`.
```

- [ ] **Step 2: Append the data-load + figures code cell (`notebook_railway.ipynb` — all 6 figures)**

Code source:

```python
import pandas as pd, matplotlib.pyplot as plt
from railway import railway_config as cfg
O = cfg.OUTPUT_DIR
fr  = pd.read_csv(O/"risk_reduction_frontier.csv")
eff = pd.read_csv(O/"budget_efficiency_analysis.csv")
alc = pd.read_csv(O/"enterprise_budget_allocation.csv")
rm  = pd.read_csv(O/"procurement_roadmap.csv")
sc  = pd.read_csv(O/"executive_budget_scenarios.csv")
fin = fr[fr["Budget_Label"] != "Unlimited"]

# 1. Risk Reduction Curve
fig, ax = plt.subplots(figsize=(8,4))
ax.plot(fin["Budget_Rupees"]/1e7, fin["Risk_Reduction_Pct"], marker="o")
knee = eff[eff["Is_Knee_Point"]]
if not knee.empty:
    kb = float(knee["Budget_Rupees"].iloc[0]); kr = float(knee["Risk_Reduction_Pct"].iloc[0])
    ax.scatter([kb/1e7],[kr], color="red", zorder=5, label="Knee-point"); ax.legend()
ax.set_xlabel("Budget (Rs Cr)"); ax.set_ylabel("Risk Reduction %"); ax.set_title("Risk Reduction Curve")
plt.tight_layout(); plt.show()

# 2. Budget Frontier (marginal SRRS per rupee)
fig, ax = plt.subplots(figsize=(8,4))
ax.bar(fin["Budget_Label"], fin["Marginal_SRRS_Per_Rupee"])
ax.set_title("Budget Frontier — Marginal SRRS per Rupee"); ax.tick_params(axis="x", rotation=45)
plt.tight_layout(); plt.show()

# 3. Enterprise Allocation Waterfall (at Rs 100 Cr)
h = alc[alc["Budget_Label"]=="Rs 100 Cr"].sort_values("Allocated_Budget", ascending=False)
fig, ax = plt.subplots(figsize=(8,4))
ax.bar(h["Division"], h["Allocated_Budget"]/1e7)
ax.set_xlabel("Division"); ax.set_ylabel("Allocated (Rs Cr)")
ax.set_title("Enterprise Allocation @ Rs 100 Cr"); plt.tight_layout(); plt.show()

# 4. Capital Efficiency Curve
fig, ax = plt.subplots(figsize=(8,4))
ce = fin.assign(Eff=fin["SRRS_Mitigated"]/fin["Budget_Utilized"].replace(0, pd.NA))
ax.plot(ce["Budget_Rupees"]/1e7, ce["Eff"], marker="s")
ax.set_xlabel("Budget (Rs Cr)"); ax.set_ylabel("SRRS per Rupee"); ax.set_title("Capital Efficiency Curve")
plt.tight_layout(); plt.show()

# 5. Multi-Year Roadmap
fig, ax = plt.subplots(figsize=(8,4))
ax.bar(rm["Year"], rm["Capital_Required"]/1e7, label="Capital (Rs Cr)")
ax2 = ax.twinx(); ax2.plot(rm["Year"], rm["Cumulative_Risk_Reduction_Pct"], color="green", marker="o", label="Cum. Risk Red. %")
ax.set_title("3-Year Procurement Roadmap"); ax.set_ylabel("Capital (Rs Cr)"); ax2.set_ylabel("Cumulative Risk Reduction %")
plt.tight_layout(); plt.show()

# 6. Funding Scenario Comparison
fig, ax = plt.subplots(figsize=(8,4))
ax.bar(sc["Scenario"], sc["Risk_Reduction_Pct"])
ax.set_title("Funding Scenario Comparison"); ax.set_ylabel("Risk Reduction %"); ax.tick_params(axis="x", rotation=45)
plt.tight_layout(); plt.show()
```

- [ ] **Step 3: Append the executive subset code cell (`notebook_railway_executive.ipynb` — figures 1, 3, 6 only)**

Use the same load block plus figures 1 (Risk Reduction Curve), 3 (Allocation Waterfall), and 6 (Scenario Comparison) from Step 2.

- [ ] **Step 4: Execute both notebooks to verify they run end-to-end**

Run: `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/notebook_railway.ipynb notebooks/notebook_railway_executive.ipynb`
(If `jupyter`/`nbconvert` is unavailable, run: `pip install nbconvert` first, or fall back to `python -m pytest --nbmake notebooks/notebook_railway.ipynb` if nbmake is configured.)
Expected: both notebooks execute without error; Section 17 figures render from live CSVs.

- [ ] **Step 5: Commit**

```bash
git add notebooks/notebook_railway.ipynb notebooks/notebook_railway_executive.ipynb
git commit -m "feat(step35-opt): notebook Section 17 — enterprise capital allocation visuals"
```

---

## Task I1 (Phase I): Full validation + reproducibility + reports

**Files:**
- Create: `docs/audits/STEP35_OPT_REPORT.md`, `docs/audits/STEP35_OPT_VALIDATION_REPORT.md`

- [ ] **Step 1: Full suite — confirm test floor held**

Run: `$env:PYTHONHASHSEED=0; python -m pytest railway/tests -q`
Expected (no-new-failures floor): the pre-existing failure set is UNCHANGED — **544 failed must not increase**, **88 passed must not decrease** beyond the new STEP35-OPT tests (which all pass). Net: `(88 + N_new) passed, 544 failed, 1 skipped` where N_new = count of new STEP35-OPT tests. ANY new failure or any flip of a previously-passing test = STOP and fix. Record the exact line and diff the failing-test set against the A1 baseline set (must be identical).

- [ ] **Step 2: Golden outputs — failing set unchanged (NOT all-green; baseline is pre-existing red)**

Run: `python -m pytest railway/tests/regression/test_golden_outputs.py -q`
Expected: the SAME pre-existing line-ending failures as baseline (≈537), no MORE and no FEWER. My new CSVs are not in the manifest (so add zero golden failures) and I never rewrite an existing output (so no hash flips). `test_no_unexpected_new_outputs` prints the new files (info only, never fails). Diff this failing set against the A1 golden baseline — must be identical.

- [ ] **Step 3: Enterprise outputs reproducible (run twice, diff)**

Run:
```
$env:PYTHONHASHSEED=0; python -c "from railway.governance import enterprise_allocation as e, division_summary as d; e.run(write=True); d.build_enterprise_decision_dashboard(write=True)"
python -c "import hashlib,glob; [print(f, hashlib.sha256(open(f,'rb').read()).hexdigest()[:16]) for f in ['risk_reduction_frontier','budget_efficiency_analysis','enterprise_budget_allocation','enterprise_budget_allocation_readiness','procurement_roadmap','executive_budget_scenarios','enterprise_decision_dashboard','optimization_baseline_validation']]" 
```
Then re-run the first command and re-hash. Expected: identical SHA-256 across both runs for all 7 new CSVs.

- [ ] **Step 4: Confirm no duplicate optimizer / no forbidden file**

Run: `python -c "import os; assert not os.path.exists('railway/procurement_optimizer.py'); print('no procurement_optimizer.py: OK')"`
Run: `git grep -n "LpProblem\|LpVariable\|PULP_CBC_CMD" -- railway/ ":!railway/railway_inventory_optimization.py"`
Expected: NO matches outside `railway_inventory_optimization.py` (all solver calls remain in the single source of truth).

- [ ] **Step 5: Write `STEP35_OPT_REPORT.md`**

Contents (fill with live numbers from the generated CSVs): executive summary; the 7 deliverables with their headline figures; answers to all 10 EXPECTED QUESTIONS (budgets for 50/75/90%, knee-point, optimal investment level, ₹100 Cr division split, highest-SRRS-per-₹ division, 3-year roadmap, what to fund first, max achievable enterprise risk reduction); and the 7 SUCCESS-CRITERIA verdicts.

- [ ] **Step 6: Write `STEP35_OPT_VALIDATION_REPORT.md`**

Contents: baseline vs final test counts (floor held); golden-output unchanged proof; reproducibility hashes; "no duplicate optimizer" grep proof; notebook execution result; per-phase (A–I) PASS/FAIL table; list of every new output file with row counts.

- [ ] **Step 7: Final commit**

```bash
git add docs/audits/STEP35_OPT_REPORT.md docs/audits/STEP35_OPT_VALIDATION_REPORT.md railway/outputs/*.csv
git commit -m "docs(step35-opt): validation + capability reports; regenerate enterprise outputs"
```

---

## Self-Review (against the spec)

**Spec coverage:**
- Phase A (baseline validation + `optimization_baseline_validation.csv`) → Tasks A1, A2, A3. ✓
- Phase B (frontier across 9 budgets + `risk_reduction_frontier.csv`, all 7 metrics) → Tasks B1, B2. ✓
- Phase C (knee-point/diminishing-returns/efficient frontier + `budget_efficiency_analysis.csv`) → Task C1. ✓
- Phase D (cross-division allocation + `enterprise_budget_allocation.csv`, allocated budget/SRRS/risk %/efficiency) → Tasks D1, D2. ✓
- Phase E (3-year roadmap + `procurement_roadmap.csv`, items/capital/cumulative risk/remaining exposure) → Tasks E1, E2. ✓
- Phase F (5 scenarios + `executive_budget_scenarios.csv`, procure/SRRS/remaining/tiers/efficiency) → Task F1. ✓
- Phase G (Section 17 in both notebooks, 6 live visualizations) → Task G1. ✓
- Phase H (`division_summary` enterprise KPIs + `enterprise_decision_dashboard.csv`, all 6 KPIs) → Task H1. ✓
- Phase I (541-floor green, outputs unchanged, no dup logic, reproducible, notebook executes + both reports) → Task I1. ✓
- All 9 deliverable files + `STEP35_OPT_REPORT.md` + `STEP35_OPT_VALIDATION_REPORT.md` → produced. ✓
- All 10 EXPECTED QUESTIONS answerable from `risk_reduction_frontier` + `budget_efficiency_analysis` + `enterprise_budget_allocation` + `procurement_roadmap` + `enterprise_decision_dashboard`. ✓

**Non-negotiables:** No new optimizer (solver stays in `railway_inventory_optimization.py`; grep gate in I1·Step 4). No analytical formula touched (only appended functions; golden suite gate every task). Additive-only (new files only; verified each commit). Test floor enforced (A1 → I1). Reproducible (`PYTHONHASHSEED=0`; double-run hash check I1·Step 3).

**Type consistency:** score col `"Service_Risk_Reduction_Score"` and cost col `"Inventory_Investment_Required"` used identically across `solve_budget_frontier`, `enterprise_capital_allocation`, `procurement_roadmap`, and `build_executive_budget_scenarios`. `crit` membership uses `cfg.SAFETY_RESERVE_CRITICALITIES` everywhere. Column names match between primitives (producers) and tests/builders (consumers).

**Placeholder note resolved:** Task E1 contains an illustrative first draft followed by the canonical `cum_cap` implementation — the implementer MUST use the second block and must NOT create the `_funded_so_far`/`_spent_so_far` helpers.
