# STEP 32 — GitHub Release Readiness Report (Railway Platform v1.0)

**Date:** 2026-06-08 · Audit only. Evidence: `github_release_readiness.csv`, `railway_only_repository_structure.csv`, prior STEP reports.

---

## 1. Readiness scorecard (`github_release_readiness.csv`)
| Dimension | Status | Evidence |
|---|---|---|
| Architecture | ✅ READY | layered ingestion/governance; hardened A/B |
| Tests | ✅ READY | 541 green; reproducible-from-code baseline |
| Reporting | ✅ READY | single `division_summary` SoT (STEP31) |
| Governance | ✅ READY | reporting governance + metadata standard |
| Onboarding | ✅ READY | division registry + onboarding guide |
| Notebooks | ✅ READY *(after rename)* | 3 executed railway notebooks |
| Documentation | ✅ READY *(after docs/ move)* | README + ARCHITECTURE + guides |
| **Size / cleanliness** | ⛔ **BLOCKED** | **2.4 GB Walmart data must be removed** |
| Packaging | ⚠️ GAP | no `pyproject.toml` / CI |

## 2. The one true blocker
A v1.0 GitHub release with **2.6 GB of mostly-Walmart data** is not acceptable (GitHub soft-limits, clone time, noise). The analytics, tests, reporting, and docs are release-grade; the **repository hygiene is the gate**.

## 3. Target v1.0 layout (`railway_only_repository_structure.csv`)
```
railway/            (platform: ingestion, governance, core+extension, tests, outputs)
notebooks/          (notebook_railway.ipynb + _executive + _technical)
raw_data/           (Railway_Operations/, railways.xlsx, railway_stock_summary.xlsx)
docs/               (README, ARCHITECTURE, guides, reports/)
archive/            (walmart/, historical/)   [or removed from repo entirely]
Power-BI Dashboards/Railway.pbix
pyproject.toml      (pinned + extras)   .gitignore (outputs junk, checkpoints)
```

## 4. Pre-release checklist (all gated on approval)
1. Delete 2.4 GB Walmart data + `.gitignore` the junk.
2. Archive notebooks 01–07 + CPLEX/plots.
3. Rename the 3 railway notebooks.
4. Move 113 `.md` → `docs/`.
5. Add `pyproject.toml` + pinned deps + CI running the 541-test suite.
6. Tag `v1.0` after the 541-test suite is green on the cleaned tree.

## 5. Verdict
**Release-ready in substance, blocked on hygiene.** After the (approval-gated) purification + packaging, the repository is ready to tag **Railway Inventory Planning Platform v1.0**.
