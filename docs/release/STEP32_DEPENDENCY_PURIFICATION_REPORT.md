# STEP 32 — Dependency Purification Report

**Date:** 2026-06-08 · Audit only. Evidence: `dependency_purification.csv`, `requirements.txt`, import greps.

---

## 1. Current state
`requirements.txt` is **unpinned**, has **no `pyproject.toml`**, and mixes runtime + notebook + dev + **dead Walmart-era** packages.

## 2. Import-verified disposition
| Package | railway/*.py imports | v1.0 runtime | Action |
|---|---|---|---|
| pandas, numpy, scipy, statsmodels, pulp | > 0 | **Yes** | RETAIN + **pin** |
| matplotlib | notebooks | notebooks | RETAIN (pin) |
| seaborn | **0** (railway); notebooks use | notebooks only | MOVE → `requirements-notebooks.txt` |
| **scikit-learn** | **0** | No | **REMOVE** (Walmart-era) |
| **prophet** | **0** | No | **REMOVE** (Walmart-era) |
| **plotly** | **0** | No | **REMOVE** (Walmart-era) |
| jupyter, jupyterlab, ipywidgets | notebooks | dev | MOVE → dev extras |
| openpyxl | raw zip+XML used instead | No | OPTIONAL |

## 3. Recommendation
- **Runtime (`pyproject.toml` / pinned):** pandas, numpy, scipy, statsmodels, pulp.
- **Notebook extras:** matplotlib, seaborn, jupyter, jupyterlab, ipywidgets.
- **Remove from runtime:** scikit-learn, prophet, plotly (0 imports — verified across all `railway/*.py`).
- **Add `pyproject.toml`** with pinned versions + `[project.optional-dependencies]` (notebooks, dev) + a lock for reproducibility.

## 4. Verdict
**3 dead Walmart-era packages removable; the entire runtime reduces to 5 libraries.** Pin all, split notebook/dev extras, add packaging. Behavior-preserving (no railway import uses the removed packages). Awaiting approval.
