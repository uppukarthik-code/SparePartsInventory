# STEP 36.5 — Mainline Integration Report

**Date:** 2026-06-09
**Action:** Integrated the complete platform (STEP35-OPT + STEP36) into `main` via a single `--no-ff` merge.
**Result merge commit:** `396c523` on `main`.
**Posture:** No push, tag, release, or visibility change performed. Branches NOT deleted (recommendation only).

---

## 1. Branch topology verdict

✅ **Single linear chain — no divergence.**
`main (2bf6e82, =origin/main, tag v1.0.0) → STEP35-OPT (10 commits) → STEP36 (9 commits)`.
- STEP35-OPT is a **verified ancestor** of STEP36 (`git rev-list step36..step35-opt` = 0) → fully contained.
- `main` is an **ancestor** of STEP36 (fast-forward-able).
- `main` == `origin/main` (`2bf6e82`, 0 divergence); `git pull` returned *Already up to date*.
This is exactly the "STEP35-OPT already an ancestor of STEP36" case in the implementation rules → the prescribed merge path applied, with **no rebase, no cherry-pick, no history rewrite.**

## 2. Merge verdict

✅ **Clean `--no-ff` merge succeeded.** `git merge --no-ff step36-regression-baseline-repair` brought the entire platform in one merge commit (`396c523`), preserving branch history (37 files integrated: enterprise optimization modules + outputs, manifest tooling, governance docs, CI, repaired fixtures, governance config). No conflicts. Pre-existing orthogonal working-tree changes (notebook `*.dat` deletions, `notebook_railway_technical.ipynb` edit, stray `nul`, untracked report files) were **not** part of the merge changeset and remain uncommitted — untouched by the integration.

## 3. Validation verdict

✅ **All post-merge checks pass** (see `post_merge_validation.csv`):

| Check | Result |
|---|---|
| pytest | **647 passed, 0 failed, 1 skipped** (648 collected) — matches target |
| Notebooks load | `notebook_railway` (36 cells), `_executive` (20), `_technical` (18) — all parse |
| Governance modules | `division_summary`, `enterprise_allocation`, `config.divisions` import OK |
| Optimization executes | enterprise frontier builds (9 levels, 100% max risk reduction) |
| Reporting executes | single source of truth holds: `executive == management == division_summary` KPIs |
| Manifest integrity gate | `manifest integrity OK` |

The 1 skip is `test_golden_manifest_if_present` (optional STEP17 baseline absent — intended).

## 4. Platform readiness verdict

✅ **Production-ready on `main`.** The merged platform delivers: forecasting → criticality → safety-stock/ROP → SRRS prioritization → **enterprise budget frontier, capital allocation, multi-year procurement roadmap, executive decision support** (STEP35-OPT), on a **trustworthy, green, fully-governed regression baseline** (STEP36: re-pinned manifest, repaired fixtures, LF-normalized outputs, manifest-integrity + full-suite CI, `REGRESSION_GOVERNANCE.md`). Reporting is consistent; notebooks (incl. Section 17) load; manifest integrity verified.

**Known, documented limitation (not a blocker):** the six divisions currently hold identical consolidated policy data, so cross-division capital allocation is structurally correct but not yet *differentiated*. This is the primary driver of the next-phase recommendation below.

## 5. Recommended branch cleanup actions (recommendation only — NOT executed)

Both feature branches are **fully contained in `main`** (`git branch --merged main` lists both; ancestry confirmed). They are **safe to delete** once the merge is pushed and confirmed on the remote:

```
# AFTER pushing main and confirming on origin (a later, separately-approved step):
git branch -d step35-opt-enterprise-budget-optimization
git branch -d step36-regression-baseline-repair
```
- Use `-d` (safe delete; refuses if not merged) — do NOT use `-D`.
- Retain both branches until `main` is pushed to `origin` and CI is green on the remote, so the work is recoverable.
- Separately, address the **pre-existing uncommitted working-tree items** outside this integration: the notebook `*.dat` deletions (likely intended cleanup), the `notebook_railway_technical.ipynb` modification, the stray `nul` file (Windows redirect artifact — safe to remove), and untracked report files. These predate STEP35/36 and were intentionally left untouched.

---

## Next-phase recommendation (ranked by value)

| Rank | Phase | Value | Rationale |
|---|---|---|---|
| **1** | **TPJ Onboarding** (+ true per-division partitioning) | **Highest** | Directly unlocks value *already built*. STEP35-OPT's enterprise capital allocation is currently degenerate because all 6 divisions share identical consolidated data. Onboarding TPJ as a genuinely distinct division (distinct demand/policies through the full pipeline) makes cross-division allocation, the roadmap, and the roll-up *real*. Highest leverage per unit of effort. |
| **2** | **Enterprise Roll-Up Dashboard** | **High** | Surfaces the STEP35-OPT outputs (frontier, allocation, roadmap, decision dashboard) to the Railway Board — the decision-making payoff of the optimization. Partially valuable now (enterprise frontier/scenarios are meaningful on consolidated data); fully valuable once divisions are differentiated (depends on #1). |
| **3** | **Power BI Modernization** | **Medium** | The platform already ships 10 Power BI pages. Modernization is UX/polish and refresh-automation — valuable but incremental, not unlocking new analytical capability. Best done after the data foundation (#1) and the new enterprise views (#2) exist, so modernization targets the right surfaces. |
| **4** | **Simulation & Resilience Analysis** | **High ceiling / sequence last** | The most advanced capability (disruption/lead-time/demand-shock simulation, e.g. via the AnyLogistix export already present). Largest, greenfield effort with the highest long-term strategic value — but it should build on a *differentiated multi-division* dataset (#1) and validated enterprise views (#2). Premature now; sequence after the foundation is real. |

**Recommended sequence:** TPJ Onboarding → Enterprise Roll-Up Dashboard → Power BI Modernization → Simulation & Resilience Analysis.
