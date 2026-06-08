# STEP36 — Merge Analysis (Mainline Integration)

**Date:** 2026-06-09
**Analyst action:** read-only topology analysis prior to merging the complete platform into `main`.

---

## Branch topology

The history is a **single linear chain** — no divergence, no parallel development:

```
* d1c8121 (step36-regression-baseline-repair)  ┐
* 16c7158                                        │
* 882e9c5                                        │  STEP36 — 9 commits
* 011fdf2                                        │  (manifest/fixture repair,
* f54bc4f                                        │   governance, CI hardening)
* 7410028                                        │
* a963372                                        │
* 0f22aed                                        │
* 2d03799                                        ┘
* 72f8eab (step35-opt-enterprise-budget-optimization) ┐
* c40d9a6                                              │
* 42264b5                                              │  STEP35-OPT — 10 commits
* 4f7d2f2                                              │  (frontier, allocation,
* 3ff43d6                                              │   roadmap, decision support,
* c10b935                                              │   notebook §17, governance)
* 7da8d43                                              │
* 45a5659                                              │
* 9f4ef46                                              │
* cc5d188                                              ┘
* 2bf6e82 (tag: v1.0.0, origin/main, main)  Railway Platform v1.0
```

## Ancestry (verified via `git merge-base --is-ancestor`)

| Relationship | Result |
|---|---|
| step35-opt is an ancestor of step36 | **YES** |
| main is an ancestor of step36 | **YES** (fast-forward-able) |
| main is an ancestor of step35-opt | **YES** |
| step35-opt commits NOT in step36 | **0** |
| `main` vs `origin/main` | **identical** (`2bf6e82`; 0 ahead / 0 behind) |

**Commit deltas:** step35-opt = 10 ahead of main; step36 = 19 ahead of main (= 10 STEP35-OPT + 9 STEP36).

## Is STEP35-OPT already fully contained inside STEP36?

**YES — completely.** STEP36 was branched directly off the STEP35-OPT tip (`72f8eab`), so every STEP35-OPT commit (`cc5d188`…`72f8eab`) is an ancestor of the STEP36 tip (`d1c8121`). `git rev-list --count step36..step35-opt` = **0** (no STEP35-OPT commit is missing from STEP36).

## Merge recommendation

Because STEP35-OPT is already an ancestor of STEP36 and `main` is an ancestor of STEP36, the correct integration is a single **`--no-ff` merge of `step36` into `main`**. This brings the *entire* platform (STEP35-OPT + STEP36) in one merge commit, preserves the linear branch history, and requires:

- **NO rebase** of STEP35-OPT.
- **NO cherry-pick.**
- **NO history rewrite.**

```
git checkout main
git pull origin main          # no-op: main already == origin/main (2bf6e82)
git merge --no-ff step36-regression-baseline-repair
```

## Safety notes

- The working tree carries **pre-existing, orthogonal** uncommitted changes (notebook `*.dat` deletions, a `notebook_railway_technical.ipynb` modification, a stray `nul` file, and some untracked report files). **None of these intersect the 37-file merge changeset** (`git diff --name-only main..step36 | grep -E '\.dat$|technical'` → empty), so the merge will not touch or commit them. They remain uncommitted after the merge.
- `git pull origin main` is functionally a no-op (local `main` already equals `origin/main`). If the private-repo pull cannot authenticate in this environment, it is skipped without affecting correctness — the merge target is unchanged.
- A `v1.0.0` tag already exists at `2bf6e82`; per instructions, no tagging/pushing/release is performed.

**Verdict: PROCEED with `git merge --no-ff step36-regression-baseline-repair` into `main`.**
