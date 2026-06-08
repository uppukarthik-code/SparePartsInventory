# STEP 31 — Enterprise Reporting Report

**Date:** 2026-06-08 · Design + foundation (no division data fabricated). Evidence: `enterprise_rollup_design.csv`, `division_parameterization_plan.csv`, `division_summary.build_all_divisions()`.

---

## 1. Division parameterization (working)
`division_summary` is division-aware end-to-end:
- `main(--division MAS)` → builds the MAS summary (working).
- `main(--division TPJ|SA|TVC|PGT|MDU)` → **ready, data-guarded**: `has_data()` returns False for divisions without planning outputs and the CLI warns instead of fabricating.
- `main(--all)` → enterprise roll-up over **reportable** divisions only.
- Metadata, paths, and labels resolve via `governance/config` — **no hardcoded MAS** in the reporting path.

Current reportable set: **`['MAS']`** (only MAS has STEP20–28 outputs; the registry lists MAS, others onboard with data).

## 2. Enterprise roll-up foundation (implemented scaffold)
`build_all_divisions()` assembles a **Southern Railway enterprise view**:
- **Additive KPIs summed** across reportable divisions: Current Stock Value, Reorder Gap Value, Total SRRS, Tier 1/2 counts.
- **Non-additive KPIs NOT summed** (coverage %, top-10 concentration stay per-division — summing them would be statistically wrong).
- **Missing divisions listed as `pending`** — never simulated.
- Output: `_enterprise_rollup/enterprise_reporting_rollup.json`.

## 3. Aggregation strategy (design)
| KPI type | Roll-up rule |
|---|---|
| Value/count (stock, gap, SRRS, tiers, shortages) | **sum** |
| Coverage % | per-division; enterprise = weighted by universe (future) |
| Concentration / mix | per-division only (not aggregated) |
| Readiness | per-division + enterprise min/scorecard |

## 4. Dashboard strategy (design)
Per-division tabs (MAS today) + an enterprise tab; a MAS-vs-TPJ comparison view activates automatically once TPJ becomes reportable.

## 5. TPJ reporting readiness
**Ready by design, blocked by data.** The moment TPJ DMTR + SUMMARY land and a `DIVISIONS["TPJ"]` entry exists, `--division TPJ` and the roll-up include TPJ with zero reporting-code change.

## 6. Verdict
**Enterprise reporting foundation established.** Division parameterization is working; the roll-up scaffold is implemented and honest (reportable-only, no fabrication). Multi-division reporting is unblocked structurally — gated only on per-division data.
