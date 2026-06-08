# STEP 17 — Production Hardening Report

**Generated:** 2026-06-08
**Status:** ✅ **HARDENED & VERIFIED**
**Frozen-methodology guarantee:** all protected outputs are **byte-for-byte identical** before and
after hardening (66/66 files; SHA-256 manifest). Every change is additive, a non-numeric refactor,
or a test/validation enhancement.

---

## 0. Mandatory Invariance — VERIFIED

A golden SHA-256 manifest of every output was captured **before** any edit, then re-compared after
re-running the full pipeline:

```
baseline files: 66
CHANGED: 0     MISSING: 0
RESULT: BYTE-IDENTICAL (PASS)
```

All frozen items confirmed unchanged: **procurement rankings, funded items, budget allocations,
Inventory_Gap, Safety_Stock, ROP, SRRS, Page0 KPI values, and every Power BI output.** No item in the
"must remain identical" list changed — implementation proceeded without needing to stop.

---

## 1. Findings (7-dimension review)

| Dimension | Finding | Action |
|---|---|---|
| **Correctness** | SRRS identity (`C_w·SF·Gap⁺`) and lineage all hold | Added regression tests asserting the identity & totals |
| **Robustness** | Validation covered columns/vocab but **missed** per-file duplicate keys, null criticality, service-level range, negative investment | Extended `schema_validation.py` (additive checks) |
| **Maintainability** | **Duplicated/divergent constant**: config held an *unused* `SERVICE_LEVEL_TARGETS` (ABC-only) that diverged from the optimizer's real `SERVICE_LEVEL_TABLE` (ABC×Criticality, hard-coded) | Removed the dead constant; centralized the authoritative table in `railway_config.py`; optimizer now references config (values identical) |
| **Explainability** | Funded items had no per-driver contribution breakdown or reserve flag | New `railway_explainability.py` → `railway_funding_explainability.csv` |
| **Failure handling** | `schema_validation` raises `SchemaError`; coverage was partial | Broadened checks; clear, itemised error messages |
| **Auditability** | No execution metadata emitted | New `railway_audit_trail.py` → `STEP17_AUDIT_TRAIL.json` |
| **Reproducibility** | No run fingerprint / drift guard | Audit trail (run_id, timestamp, version, row counts, SHA-256) + golden-manifest test |

**Stale test discovered (pre-existing, not a Step-17 regression):**
`test_powerbi_exports.py::test_no_original_value_columns_on_strategic_pages` still forbade
`Inventory_Value` on `page5_rationalization`, but that page has carried the **documented
compatibility alias** (`Inventory_Value == Normalized_Inventory_Value`) since Step 12.5A, with the
production validator already exempting it. The test was never updated → corrected to the authoritative
rule and an explicit **alias-integrity** assertion added (no output changed).

## 2. Code Changes

### Modified (non-frozen)
| File | Change | Output impact |
|---|---|---|
| `railway_config.py` | Replaced unused divergent `SERVICE_LEVEL_TARGETS`/`DEFAULT_SERVICE_LEVEL` with authoritative `SERVICE_LEVEL_TABLE`/`DEFAULT_TARGET_SL` (centralization; identical values) | none (byte-identical) |
| `railway_inventory_optimization.py` | `SERVICE_LEVEL_TABLE`/`DEFAULT_TARGET_SL` now alias `cfg.*`; added optional `return_stages` to `allocate_with_reserve` (default `False` → identical selection) | none (byte-identical) |
| `schema_validation.py` | Added `_check_no_nulls`, `_check_duplicates`, `_check_range`; wired per-file duplicate-PL, null-criticality, service-level-range, negative-investment/SRRS checks | none (separate validation module) |
| `tests/test_powerbi_exports.py` | Corrected stale page5 test → exempt documented alias + assert alias integrity | none (test only) |

### Added (new files, fully additive)
| File | Purpose |
|---|---|
| `railway/railway_explainability.py` | Per-driver SRRS contribution + `Reserve_Allocation_Flag` → `railway_funding_explainability.csv` |
| `railway/railway_audit_trail.py` | `STEP17_AUDIT_TRAIL.json` (timestamp, version, run_id, in/out row counts, SHA-256) |
| `railway/tests/test_production_hardening.py` | Schema / row-count / total-preservation / ranking-stability / Power BI compatibility / golden-manifest tests |

### Deliberately NOT changed (frozen, per constraint)
SRRS formulation · Service_Factor formulation · criticality weights · procurement-priority methodology
· knapsack objective · safety-reserve methodology · budget-allocation logic · Power BI schemas · KPIs ·
rankings. **Performance:** the 59-row numeric build loop was **intentionally not vectorized** — doing so
risks floating-point drift against the bit-identical invariance constraint for negligible gain (the
loop is ~ms; the 1.95 s optimizer time is dominated by PuLP/scipy, not the loop). No "silent failure"
in the frozen compute path was altered; defensive checks live in the validation layer that runs first.

## 3. Explainability Output (`railway_funding_explainability.csv`)

For every procurement-required item: `Criticality_Contribution`, `Service_Contribution`,
`Gap_Contribution` (log-share decomposition of `SRRS = C_w·SF·Gap⁺`, summing to 100%),
`Reserve_Allocation_Flag` (funded via the Safety-Reserve stage), and `Funding_Decision`.
Funded-item mean split: **Gap 85.9% · Criticality 13.8% · Service 0.2%** — consistent with the
Step-16 finding that the gap is the dominant driver. 50 candidates, 27 funded, 5 reserve-funded.

## 4. Auditability Output (`STEP17_AUDIT_TRAIL.json`)

Keys: `run_id` (uuid4), `timestamp_utc`, `platform_version` (0.1.0), `pipeline_version` (12.5.0),
`config` (budget, slope, reserve %, criticality weights), `input_row_counts`
(`{demand_history:59, sku_master:59, forecast:59, operational:907}`), `output_artifacts` (7, with
rows + SHA-256), `powerbi_pages` (10, with rows + SHA-256). `run_id`/`timestamp` are injectable for
deterministic re-runs.

## 5. Validation Results

| Suite | Result |
|---|---|
| **Golden invariance** (66 files, SHA-256) | ✅ 0 changed / 0 missing |
| `schema_validation` (enhanced) | ✅ ALL CHECKS PASSED |
| Lineage V1–V6 | ✅ ALL PASS |
| Calibrated SRRS suite A–H | ✅ ALL PASS |
| **pytest full suite** | ✅ **82 passed, 1 skipped** (golden-manifest test skips when baseline absent, by design) |
| New `test_production_hardening.py` | ✅ schema / row-count / totals / ranking-stability / Power BI compat all pass |

## 6. Before/After Runtime

No compute-path algorithm changed — the only edits touching the optimizer are a constant relocation
(identical values) and an unused-by-default parameter — so the instruction path is unchanged and
runtime is identical within measurement noise. Measured hardened pipeline (ordered, single pass):

| Stage | Time |
|---|---:|
| railway_inventory_optimization | 1.95 s |
| railway_data_quality | 1.07 s |
| railway_inventory_rationalization | 0.05 s |
| railway_executive_summary | 0.03 s |
| railway_powerbi_export | 0.30 s |
| railway_enterprise | 0.43 s |
| **Total** | **3.84 s** |

(The optimizer's time is dominated by PuLP/CBC + scipy, not the row loop — confirming vectorization
would yield no meaningful gain while jeopardising bit-identical outputs.)

## 7. Backward-Compatibility Verification

| Check | Result |
|---|---|
| 66/66 protected outputs SHA-256 identical | ✅ |
| Page names & schemas unchanged (page0–9) | ✅ |
| Page0 KPIs / Inventory_Gap / Safety_Stock / ROP / SRRS unchanged | ✅ |
| Procurement plan (funded items + allocations) unchanged | ✅ |
| Enterprise backward-compat hash (`existing files changed: 0`) | ✅ |
| Existing pytest suite still green (no regressions) | ✅ |
| New artifacts are additive (new files only) | ✅ |
| `allocate_with_reserve` default behaviour identical (return_stages off) | ✅ |

## 8. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Constant relocation could alter service levels | — | Byte-identical verification (66/66); values copied verbatim |
| New `outputs/railway_funding_explainability.csv` seen by enterprise hash | Low | Enterprise hashes before/after its own run; it never writes this file → still 0 changed (verified) |
| Enhanced validation may reject future inputs | Low (intended) | Raises clear `SchemaError`; on current valid data → 0 violations |
| Audit-trail run_id/timestamp non-deterministic | Low (by design) | Injectable (`run(run_id=…, timestamp=…)`) for reproducible runs |
| Vectorization deferred | Accepted | Conscious trade-off; documented; no runtime concern at current scale |

---

## 9. Conclusion

The codebase is hardened across correctness, robustness, maintainability, explainability, failure
handling, auditability, and reproducibility — with **every frozen output proven byte-for-byte
identical**, the full test suite green (82 passed / 1 skipped), and three additive deliverables
(`railway_funding_explainability.csv`, `STEP17_AUDIT_TRAIL.json`, and an automated hardening test
suite). No protected value changed; no methodology was modified. **Ready for production deployment.**
