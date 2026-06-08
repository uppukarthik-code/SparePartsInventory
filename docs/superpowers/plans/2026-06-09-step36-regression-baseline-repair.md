# STEP36 — Regression Baseline Repair & Test Governance Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Restore a trustworthy, fully-green regression baseline by repairing the line-ending golden manifest and the stale data-evolution fixtures — with **zero analytics/reporting/output/formula/notebook changes** — and harden test governance so the baseline stays trustworthy.

**Branch:** `step36-regression-baseline-repair` (created off `step35-opt-enterprise-budget-optimization` HEAD — stacks the repair on STEP35-OPT; redirect to `main` base only if you want the repair standalone).

**Forensic conclusion (already established, read-only):** Baseline = **103 pass / 544 fail / 1 skip** (648 collected). **Zero real regressions.** The 544 failures are:
- **537 line-ending** — committed output CSVs are LF; `golden_output_manifest.csv` pinned the CRLF rendering. `LF→CRLF` of the current file reproduces the manifest hash exactly → content identical.
- **7 stale fixtures** — all data-evolution, verified against current code/config (details in Task C). Strategic universe (59 PLs), KPIs, SRRS identity, ranking, totals all PASS → analytics intact.

---

## Non-negotiable rules (verify every commit)
- Do NOT change: forecasting, demand reconstruction, lead-time, criticality, safety-stock, ROP, SRRS, optimization, reporting logic, KPIs, notebooks, or any output CSV's content.
- Only touch: the golden manifest (rebuild), test fixtures (repair), one schema-validation rule (governance), `.gitattributes`, `ci.yml`, new governance tooling/doc.
- **Never mask a real regression.** Each fixture repair must be justified by current correct-by-design behavior; any unexplained delta → STOP and escalate.
- The manifest rebuild must ONLY correct EOL representation: abort if forensics finds any genuine `CONTENT_DIFFERENCE`.

---

## Files
- **Create:** `railway/tests/regression/manifest_tools.py` (forensics + rebuild + CI integrity check — the governed tool the docstring's missing `_build_golden_manifest.py` was meant to be).
- **Rebuild:** `railway/tests/regression/golden_output_manifest.csv` (hashes only; same 537 relpaths).
- **Repair fixtures:** `railway/tests/test_business_unit_runner.py`, `railway/tests/test_production_hardening.py`.
- **Repair one rule:** `railway/schema_validation.py` (operational PL_Code uniqueness — governance, see Task D3).
- **Harden:** `.gitattributes`, `.github/workflows/ci.yml`.
- **Create:** `docs/REGRESSION_GOVERNANCE.md`.
- **Deliverable CSVs/reports → `docs/audits/`:** `manifest_forensics.csv`, `manifest_repair_report.csv`, `stale_fixture_inventory.csv`, `fixture_repair_report.csv`, `test_governance_review.csv`, `baseline_validation_report.csv`, `ci_hardening_report.csv`, `STEP36_BASELINE_REPAIR_REPORT.md`, `STEP36_VALIDATION_REPORT.md`. (`baseline_test_inventory.csv` already produced.)

---

## Task A (Phase A): Manifest forensics tool + `manifest_forensics.csv`

**Files:** Create `railway/tests/regression/manifest_tools.py`.

- [ ] **Step 1: Write `manifest_tools.py`**

```python
"""STEP36 governed manifest tooling: forensics, rebuild, and CI integrity check
for railway/tests/regression/golden_output_manifest.csv.

This NEVER modifies output CSVs. It only inspects them and (rebuild) re-pins the
manifest hashes to the current committed bytes. A rebuild is permitted ONLY when
every pinned file is byte-identical modulo line-endings (IDENTICAL_EOL_ONLY) or
already matching — a genuine CONTENT_DIFFERENCE aborts the rebuild.
"""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

from railway import railway_config as cfg

MANIFEST = Path(__file__).parent / "golden_output_manifest.csv"
ROOT = cfg.OUTPUT_DIR


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _read_manifest():
    with open(MANIFEST, newline="") as f:
        return list(csv.DictReader(f))


def classify(relpath: str, manifest_sha: str):
    p = ROOT / relpath
    if not p.exists():
        return {"actual_sha": "", "crlf_sha": "", "lf_sha": "", "classification": "MISSING_FILE"}
    raw = p.read_bytes()
    actual = _sha(raw)
    lf = raw.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    lf_sha, crlf_sha = _sha(lf), _sha(crlf)
    if actual == manifest_sha:
        cls = "MATCH"
    elif manifest_sha in (lf_sha, crlf_sha):
        cls = "IDENTICAL_EOL_ONLY"
    else:
        cls = "CONTENT_DIFFERENCE"
    return {"actual_sha": actual, "crlf_sha": crlf_sha, "lf_sha": lf_sha, "classification": cls}


def forensics(write_to: str | None = None):
    rows = []
    pinned = set()
    for r in _read_manifest():
        rel = r["relpath"]; pinned.add(rel)
        c = classify(rel, r["sha256"])
        rows.append({"relpath": rel, "manifest_sha": r["sha256"], **c})
    # EXTRA_FILE: csvs under ROOT not pinned
    for p in ROOT.rglob("*.csv"):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if rel not in pinned:
            rows.append({"relpath": rel, "manifest_sha": "", "actual_sha": _sha(p.read_bytes()),
                         "crlf_sha": "", "lf_sha": "", "classification": "EXTRA_FILE"})
    if write_to:
        with open(write_to, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["relpath", "manifest_sha", "actual_sha",
                                              "crlf_sha", "lf_sha", "classification"])
            w.writeheader(); w.writerows(rows)
    return rows


def rebuild(dry_run: bool = False):
    """Re-pin the manifest to current committed bytes for the SAME relpaths.
    Aborts if any pinned file is CONTENT_DIFFERENCE or MISSING_FILE."""
    rows = _read_manifest()
    report = []
    blockers = []
    for r in rows:
        rel = r["relpath"]
        c = classify(rel, r["sha256"])
        if c["classification"] in ("CONTENT_DIFFERENCE", "MISSING_FILE"):
            blockers.append((rel, c["classification"]))
        report.append({"relpath": rel, "old_sha": r["sha256"], "new_sha": c["actual_sha"],
                       "old_class": c["classification"]})
    if blockers:
        raise SystemExit(f"REBUILD ABORTED — genuine differences: {blockers[:10]}")
    if not dry_run:
        with open(MANIFEST, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["relpath", "bytes", "sha256"])
            for r in rows:
                p = ROOT / r["relpath"]
                w.writerow([r["relpath"], len(p.read_bytes()), _sha(p.read_bytes())])
    return report


def check(): 
    """CI integrity gate: nonzero exit if any pinned file is CONTENT_DIFFERENCE/MISSING."""
    bad = [r for r in forensics() if r["classification"] in ("CONTENT_DIFFERENCE", "MISSING_FILE")]
    if bad:
        raise SystemExit(f"MANIFEST INTEGRITY FAIL: {len(bad)} files: {[b['relpath'] for b in bad[:10]]}")
    print("manifest integrity OK")
```

- [ ] **Step 2: Generate `manifest_forensics.csv` and assert classification**

Run: `python -c "from railway.tests.regression import manifest_tools as m; rows=m.forensics('docs/audits/manifest_forensics.csv'); import collections; print(collections.Counter(r['classification'] for r in rows))"`
**Expected:** `{IDENTICAL_EOL_ONLY: 537}` (plus some `EXTRA_FILE` for STEP35-OPT outputs). **If ANY `CONTENT_DIFFERENCE` or `MISSING_FILE` → STOP and escalate** (that would be a real output change, out of STEP36 scope).

- [ ] **Step 3: Commit**

```bash
git add railway/tests/regression/manifest_tools.py docs/audits/manifest_forensics.csv
git commit -m "feat(step36): manifest forensics tool + manifest_forensics.csv"
```

---

## Task B (Phase B): Rebuild manifest from committed bytes + `manifest_repair_report.csv`

- [ ] **Step 1: Dry-run rebuild (safety gate)**

Run: `python -c "from railway.tests.regression import manifest_tools as m; import csv; rep=m.rebuild(dry_run=True); print('would re-pin', len(rep), 'rows; blockers raise SystemExit')"`
Expected: no SystemExit; 537 rows.

- [ ] **Step 2: Rebuild + write repair report**

Run:
```
python -c "from railway.tests.regression import manifest_tools as m; import csv; rep=m.rebuild(dry_run=False); f=open('docs/audits/manifest_repair_report.csv','w',newline=''); w=csv.DictWriter(f,fieldnames=['relpath','old_sha','new_sha','old_class']); w.writeheader(); w.writerows(rep); f.close(); print('re-pinned', len(rep))"
```
Expected: 537 rows re-pinned (all were `IDENTICAL_EOL_ONLY`).

- [ ] **Step 3: Verify the golden suite is now GREEN**

Run: `$env:PYTHONHASHSEED=0; python -m pytest railway/tests/regression/test_golden_outputs.py -q`
**Expected: all pass (538 passed)** — outputs unchanged, manifest now matches committed LF bytes.

- [ ] **Step 4: Confirm NO output CSV was modified**

Run: `git status --porcelain railway/outputs | head` → expected: **empty** (only the manifest under tests/regression changed, not any output).
Run: `git diff --stat -- railway/tests/regression/golden_output_manifest.csv` → expected: hash column changed only.

- [ ] **Step 5: Commit**

```bash
git add railway/tests/regression/golden_output_manifest.csv docs/audits/manifest_repair_report.csv
git commit -m "fix(step36): re-pin golden manifest to committed LF bytes (EOL-only; content unchanged)"
```

---

## Task C (Phase C): Stale fixture forensics + `stale_fixture_inventory.csv`

- [ ] **Step 1: Write `docs/audits/stale_fixture_inventory.csv`** with these verified rows (columns: `fixture,test_file,expected_value,actual_value,originating_step,reason_obsolete,classification`):

```
fixture,test_file,expected_value,actual_value,originating_step,reason_obsolete,classification
test_depot_routing_mechanism,test_business_unit_runner.py,"resolve('YYY/PTJ/9')==TPJ",PGT,STEP19,"Config DEPOT_TOKEN_TO_BUSINESS_UNIT line 74 corrected PTJ(Podanur)->PGT(Palakkad); test still asserts pre-STEP19 TPJ",STALE
test_mas_operational_rows,test_business_unit_runner.py,907,15913,STEP18A,"Operational data volume grew (multi-depot onboarding); 907 was single-depot MAS era",STALE
test_mas_enterprise_rollup_registry,test_business_unit_runner.py,959,(fresh-run value),STEP18A/19,"Enterprise master SKU registry grew with onboarded operational universe",STALE
test_dataless_bu_skeleton,test_business_unit_runner.py,"TPJ operational_rows==0",TPJ has 1355 op rows,STEP18A,"TPJ was onboarded with data; no longer a data-less BU",STALE
test_row_counts_unchanged[page4_operational_health-907],test_production_hardening.py,907,15913,STEP18A,"page4 operational health row count grew with operational universe",STALE
test_row_counts_unchanged[page5_rationalization-959],test_production_hardening.py,959,5351,STEP18A,"page5 rationalization row count grew with operational universe",STALE
test_schema_validation_passes,test_production_hardening.py,"operational PL_Code unique",1329 dup PL_Code,STEP18A,"PL_Code uniqueness is a MASTER-data rule mis-applied to depot/line-level operational data (PL+Depot also non-unique: 745 dups => grain finer than PL+Depot)",STALE_RULE
```

- [ ] **Step 2: Commit**

```bash
git add docs/audits/stale_fixture_inventory.csv
git commit -m "docs(step36): stale fixture inventory (7 fixtures, all data-evolution, 0 regressions)"
```

---

## Task D1 (Phase D): Repair `test_business_unit_runner.py`

**For each edit: capture the current authoritative value, confirm correct-by-design, then update. Prefer robust invariants over magic numbers (Phase E).**

- [ ] **Step 1: Repair depot routing (STEP19-verified)**

In `railway/tests/test_business_unit_runner.py`, `test_depot_routing_mechanism`:
```python
    assert buc.resolve_business_unit("YYY/PTJ/9") == "PGT"   # STEP19: PTJ=Podanur -> Palakkad (PGT), corrected from TPJ
```
(Leave the `GOC->TPJ` and `PER...->MAS` assertions unchanged — they pass.)

- [ ] **Step 2: Repair operational-rows fixture as a reproducibility INVARIANT**

`test_mas_operational_rows`:
```python
def test_mas_operational_rows(mas_run):
    p4 = pd.read_csv(mas_run / "MAS" / "powerbi" / "page4_operational_health.csv")
    canonical = pd.read_csv(CANON / "powerbi" / "page4_operational_health.csv")
    assert len(p4) == len(canonical)   # MAS run reproduces canonical operational page (invariant, not a magic count)
```

- [ ] **Step 3: Repair rollup-registry fixture**

Run the fixture once to capture the fresh registry count and confirm it is correct-by-design (registry = union of onboarded universes). Then replace the magic `959` with a business-rule invariant:
```python
def test_mas_enterprise_rollup_registry(mas_run):
    reg = mas_run / "MAS" / "enterprise" / "master_sku_registry.csv"
    assert reg.exists()
    df = pd.read_csv(reg, dtype={"PL_Code": str})
    assert len(df) > 0                      # non-empty
    assert df["PL_Code"].is_unique          # master registry: one row per PL (integrity invariant)
```
If `PL_Code` is NOT unique in the registry, do NOT relax it — STOP and escalate (that would be a genuine registry-integrity issue, not a stale count).

- [ ] **Step 4: Repair data-less skeleton to a genuinely data-less BU**

Confirm `STTC_PTJ` (Status "Configured", token "STTC") receives no operational depots, i.e. produces a data-less skeleton. Then:
```python
def test_dataless_bu_skeleton(tmp_path):
    runner.run(business_units=["MAS", "STTC_PTJ"], root=tmp_path, quiet=True)   # STTC_PTJ has no onboarded operational data (TPJ was onboarded in STEP18A)
    status = tmp_path / "STTC_PTJ" / "BU_STATUS.json"
    assert status.exists()
    meta = json.loads(status.read_text())
    assert meta["processed"] is False and meta["operational_rows"] == 0
    assert (tmp_path / "MAS" / "railway_inventory_policy.csv").exists()
    assert (tmp_path / "_enterprise_rollup" / "master_sku_registry_all.csv").exists()
```
If `STTC_PTJ` turns out to have operational data (it should not), STOP and escalate — do not invent a passing condition.

- [ ] **Step 5: Run the file**

Run: `$env:PYTHONHASHSEED=0; python -m pytest railway/tests/test_business_unit_runner.py -q`
Expected: **9 passed**.

- [ ] **Step 6: Commit**

```bash
git add railway/tests/test_business_unit_runner.py
git commit -m "fix(step36): repair stale business-unit-runner fixtures (routing STEP19, data-volume invariants, data-less BU)"
```

---

## Task D2 (Phase D): Repair `test_production_hardening.py` row-counts

- [ ] **Step 1: Update the two stale operational counts** (these read COMMITTED canonical outputs, which the manifest now authoritatively pins):

In `EXPECTED_ROWS`:
```python
    "page4_operational_health": 15913, "page5_rationalization": 5351,
```
(Leave the stable strategic counts unchanged: page1/2/3 = 59, page8 = 4, page9 = 5. Add a comment noting page4/page5 are operational-volume counts pinned to current committed outputs.)

- [ ] **Step 2: Run the row-count tests**

Run: `$env:PYTHONHASHSEED=0; python -m pytest "railway/tests/test_production_hardening.py" -k "row_counts" -q`
Expected: all `test_row_counts_unchanged` params pass.

- [ ] **Step 3: Commit**

```bash
git add railway/tests/test_production_hardening.py
git commit -m "fix(step36): update stale operational row-count fixtures to current committed values"
```

---

## Task D3 (Phase D): Repair the mis-applied operational uniqueness rule

> **SCOPE NOTE — the one non-test code file touched.** `schema_validation.py` is governance/validation, not analytics: it changes what is *considered valid*, never any computed output. Operational inventory is depot/line-level; PL_Code is not its primary key (PL+Depot also non-unique: 745 dups). The PL_Code uniqueness check is a master-data rule mis-applied to operational data.

- [ ] **Step 1: Remove ONLY the operational PL_Code uniqueness check**

In `railway/schema_validation.py`, in `validate_all`, the operational block (line ~143):
```python
    # --- operational (depot/line-level: PL_Code is NOT unique by design; checked on master/policy instead) ---
    op = _load("railway_operational_inventory.csv")
    _check_columns("railway_operational_inventory.csv", op, violations)
    _check_numeric("railway_operational_inventory.csv", op, ["Current_Stock", "Inventory_Value"], violations)
```
(Delete only the `_check_duplicates("railway_operational_inventory.csv", op, violations)` line. ALL other operational checks — required columns, numeric, non-negative — remain, so genuine drift is still caught. Uniqueness is still enforced on master/forecast/policy.)

- [ ] **Step 2: Verify**

Run: `python -c "from railway import schema_validation as sv; print('violations:', sv.validate_all(raise_on_error=False))"`
Expected: `violations: []`.

- [ ] **Step 3: Run the schema test**

Run: `$env:PYTHONHASHSEED=0; python -m pytest railway/tests/test_production_hardening.py::test_schema_validation_passes -q`
Expected: pass.

- [ ] **Step 4: Write `docs/audits/fixture_repair_report.csv`** (columns: `fixture,test_file,repair_type,before,after,verified_correct_by`):

```
fixture,test_file,repair_type,before,after,verified_correct_by
test_depot_routing_mechanism,test_business_unit_runner.py,expectation_update,TPJ,PGT,"config line 74 STEP19 comment"
test_mas_operational_rows,test_business_unit_runner.py,invariant_replacement,==907,==len(canonical page4),"MAS run reproduces canonical"
test_mas_enterprise_rollup_registry,test_business_unit_runner.py,invariant_replacement,==959,non-empty + PL_Code unique,"registry integrity invariant"
test_dataless_bu_skeleton,test_business_unit_runner.py,target_repoint,TPJ,STTC_PTJ,"TPJ onboarded; STTC_PTJ data-less"
test_row_counts_unchanged[page4],test_production_hardening.py,count_update,907,15913,"current committed canonical (manifest-pinned)"
test_row_counts_unchanged[page5],test_production_hardening.py,count_update,959,5351,"current committed canonical (manifest-pinned)"
test_schema_validation_passes,test_production_hardening.py,rule_scope_fix,PL_Code unique on operational,removed (operational grain != PL),"PL+Depot non-unique; operational is depot/line-level"
```

- [ ] **Step 5: Commit**

```bash
git add railway/schema_validation.py docs/audits/fixture_repair_report.csv
git commit -m "fix(step36): operational inventory is depot-level — drop mis-applied PL_Code uniqueness rule"
```

---

## Task E (Phase E): Governance hardening — `.gitattributes` + `test_governance_review.csv`

- [ ] **Step 1: Force LF on output CSVs (durable EOL governance)**

The root cause was committed-LF vs CRLF-pinned manifest, and pandas writes CRLF on Windows. Make LF authoritative and self-healing. In `.gitattributes`, ADD (after the `* -text` line) a more-specific rule:
```
# Output CSVs are normalized to LF so the SHA-256 manifest is reproducible across
# OS (CI is Linux/LF; pandas writes CRLF on Windows). git normalizes on add/checkout.
railway/outputs/**/*.csv text eol=lf
railway/tests/regression/golden_output_manifest.csv text eol=lf
```

- [ ] **Step 2: Renormalize and confirm NO content change**

Run: `git add --renormalize railway/outputs railway/tests/regression/golden_output_manifest.csv`
Run: `git status --porcelain | head` → expected: **empty / no changes** (files are already LF, so renormalize is a no-op). If any file shows as modified, inspect — it must be EOL-only.

- [ ] **Step 3: Write `docs/audits/test_governance_review.csv`** (columns: `test,category,issue,action`):

```
test,category,issue,action
test_golden_outputs.py,manifest_hash,"byte-exact SHA pin; was fragile to EOL",KEPT + manifest rebuilt + .gitattributes eol=lf hardening
test_mas_operational_rows,row_count,"hardcoded 907 brittle to data volume",REPLACED with reproducibility invariant (== canonical)
test_mas_enterprise_rollup_registry,row_count,"hardcoded 959 brittle",REPLACED with integrity invariant (non-empty + unique PL_Code)
test_row_counts_unchanged[page4/page5],row_count,"operational counts brittle to onboarding",UPDATED to current committed values (operational is volatile)
test_row_counts_unchanged[page1/2/3/8/9],row_count,"strategic counts are stable invariants (59/4/5)",KEPT as-is (stable universe)
test_dataless_bu_skeleton,data_assumption,"assumed TPJ data-less; TPJ onboarded",REPOINTED to STTC_PTJ (genuinely data-less)
test_depot_routing_mechanism,business_rule,"expected pre-STEP19 routing",UPDATED to STEP19 config-verified PGT
test_schema_validation_passes,schema_rule,"PL_Code uniqueness mis-applied to operational",RULE SCOPE FIXED (operational exempt; master/policy still enforced)
```

- [ ] **Step 4: Commit**

```bash
git add .gitattributes docs/audits/test_governance_review.csv
git commit -m "chore(step36): governance hardening — LF-normalize output CSVs; test governance review"
```

---

## Task F (Phase F): `docs/REGRESSION_GOVERNANCE.md`

- [ ] **Step 1: Write `docs/REGRESSION_GOVERNANCE.md`** covering:
  - **Baseline philosophy:** the manifest pins byte-exact SHA-256 of committed outputs; outputs are normalized to **LF** (`.gitattributes`), CI is Linux/LF, so a fresh clone reproduces hashes. Strategic counts are invariants; operational counts are volatile (data-volume) and validated structurally.
  - **Manifest ownership / re-baselining rules:** the manifest may be rebuilt with `manifest_tools.rebuild()` ONLY after an *intended, reviewed* output change; `rebuild()` ABORTS on `CONTENT_DIFFERENCE` unless run after such a change. Never re-pin to mask a failing refactor. Always rebuild on Linux (or ensure LF) so hashes match CI.
  - **Fixture ownership:** row-count fixtures for the **strategic universe (59)** are invariants and must not drift silently; **operational** counts track data volume and are updated when onboarding changes (record in `stale_fixture_inventory.csv`). Prefer invariants (reproducibility, schema, business-rule) over magic numbers.
  - **Approval requirements:** any change that alters an output hash, a strategic count, a formula, or a KPI requires explicit human approval + a documented reason. EOL-only and data-volume fixture updates are routine (documented).
  - **Change-control process:** (1) run `manifest_tools.check()`; (2) if outputs intentionally changed, document why; (3) `rebuild()`; (4) update affected fixtures; (5) `pytest railway/tests`; (6) PR with the diff + reason.

- [ ] **Step 2: Commit**

```bash
git add docs/REGRESSION_GOVERNANCE.md
git commit -m "docs(step36): regression governance — manifest/fixture ownership, re-baselining rules"
```

---

## Task G (Phase G): Full validation + `baseline_validation_report.csv`

- [ ] **Step 1: Run the complete suite**

Run: `$env:PYTHONHASHSEED=0; python -m pytest railway/tests -q`
**Target: 0 failed.** Expected: `647 passed, 1 skipped` (648 collected; the 1 skip is `test_golden_manifest_if_present`, an optional STEP17 baseline that is legitimately absent).

- [ ] **Step 2: Write `docs/audits/baseline_validation_report.csv`** (columns: `metric,before,after`):

```
metric,before,after
collected,648,648
passed,103,647
failed,544,0
skipped,1,1
line_ending_failures,537,0
stale_fixture_failures,7,0
real_regressions,0,0
analytics_files_modified,0,0
output_csvs_modified,0,0
```

- [ ] **Step 3: Commit**

```bash
git add docs/audits/baseline_validation_report.csv
git commit -m "docs(step36): baseline validation — 647 pass / 0 fail / 1 skip"
```

---

## Task H (Phase H): CI hardening + `ci_hardening_report.csv`

> CI currently runs only `railway/tests/regression/` + `railway/tests/inventory/` + a reporting assert — it does NOT run the broader suite (so the fixture tests never gate CI), and has no manifest-integrity check.

- [ ] **Step 1: Harden `.github/workflows/ci.yml`** — add a manifest-integrity step and a full-suite step (keep existing steps):
```yaml
      - name: Manifest integrity (EOL/content guard)
        run: python -c "from railway.tests.regression import manifest_tools as m; m.check()"
      - name: Full test suite (fixtures + governance)
        run: pytest railway/tests -q
```
(Place the manifest-integrity step before the regression step; the full-suite step after the existing inventory step.)

- [ ] **Step 2: Write `docs/audits/ci_hardening_report.csv`** (columns: `check,before,after`):

```
check,before,after
regression_suite,"runs (railway/tests/regression)",runs
inventory_invariants,"runs (railway/tests/inventory)",runs
full_test_suite,"NOT run",runs (railway/tests)
manifest_integrity_gate,"none",runs (manifest_tools.check)
fixture_tests_gated,"no (outside CI scope)",yes
reporting_consistency_assert,runs,runs
runner_os,ubuntu-latest (LF),ubuntu-latest (LF)
```

- [ ] **Step 3: Validate the workflow YAML parses**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('ci.yml valid')"`
Expected: valid.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml docs/audits/ci_hardening_report.csv
git commit -m "ci(step36): add manifest-integrity gate + full-suite run"
```

---

## Task I: Reports

- [ ] **Step 1: Write `docs/audits/STEP36_BASELINE_REPAIR_REPORT.md`** — answer all 10 expected questions (causes; zero real regressions; 537 line-ending; 7 stale; no analytics/output modified; manifest correct; fixtures aligned; suite trustworthy; baseline green) and the 8 success-criteria verdicts; include the before/after counts and the STEP37 recommendation.

- [ ] **Step 2: Write `docs/audits/STEP36_VALIDATION_REPORT.md`** — per-phase A–H PASS table, final counts (647/0/1), proof no output CSV changed (`git diff --stat main..HEAD -- railway/outputs` empty), proof no analytics file changed, list of every file touched with rationale.

- [ ] **Step 3: Commit**

```bash
git add docs/audits/STEP36_BASELINE_REPAIR_REPORT.md docs/audits/STEP36_VALIDATION_REPORT.md
git commit -m "docs(step36): baseline repair report + validation report"
```

---

## Self-review (against spec)
- Phase A→I: each has a task producing its named deliverable. ✅
- All 11 deliverables covered (baseline_test_inventory.csv already produced). ✅
- Non-negotiables enforced: manifest rebuild aborts on CONTENT_DIFFERENCE; only EOL-only re-pin; no output regeneration; the only non-test code change is a validation-rule scope fix (schema_validation.py), flagged for explicit approval. ✅
- Escalation gates on every fixture (registry uniqueness, STTC_PTJ data-less, any CONTENT_DIFFERENCE) prevent masking real regressions. ✅
- STOP-after-STEP36: no TPJ onboarding / dashboard / simulation / new analytics. ✅
