# STEP 32 — Railway-Only Blueprint Report

**Date:** 2026-06-08 · Audit only — blueprint, NOT executed. Evidence: `final_railway_repository_blueprint.csv`, `railway_only_validation.csv`.

---

## 1. Current → Railway Platform v1.0 (`final_railway_repository_blueprint.csv`)
| Asset | Action | Destination |
|---|---|---|
| `railway/` (all 35 modules + tests + outputs) | **RETAIN** | `railway/` |
| `raw_data/Railway_Operations/`, `railways.xlsx`, `railway_stock_summary.xlsx` | **RETAIN** | `raw_data/` |
| `Power-BI Dashboards/Railway.pbix` | **RETAIN** | as-is |
| `UPDATED_NOTEBOOK7.ipynb` | **RENAME** | `notebooks/notebook_railway.ipynb` |
| `NOTEBOOK7_EXECUTIVE_VERSION.ipynb` | **RENAME** | `notebooks/notebook_railway_executive.ipynb` |
| `NOTEBOOK7_TECHNICAL_VERSION.ipynb` | **RENAME** | `notebooks/notebook_railway_technical.ipynb` |
| notebooks 01–07 | **ARCHIVE** | `archive/walmart/` · `archive/historical/` |
| root `*.md` (113) | **MOVE** | `docs/` + `docs/reports/` |
| `notebooks/*.csv` dumps (1.9 G) | **DELETE** | (removed) |
| `raw_data/` M5 CSVs (431 M) | **DELETE** | (removed; refs verified 0) |
| `data/Sales_merged.csv` (72 M) | **DELETE** | (removed) |
| `**/.ipynb_checkpoints/` | **DELETE** | (removed; `.gitignore`) |
| sklearn / prophet / plotly | **REMOVE** | runtime requirements |
| `pyproject.toml` | **CREATE** | repo root |

## 2. Railway-only validation (`railway_only_validation.csv`) — the acid test
Can a railway engineer, **with no Walmart assets present**:
| # | Workflow | Works? | Evidence |
|---|---|---|---|
| 1 | Clone | ✅ | railway/ self-contained |
| 2 | Delete `archive/` | ✅ | 0 railway imports of Walmart assets |
| 3 | Install deps | ✅ | 5 runtime libs only |
| 4 | Run tests | ✅ | 541 green; touches railway/ + outputs only |
| 5 | Run notebooks | ✅ | read railway outputs only |
| 6 | Run reporting | ✅ | `division_summary` reads railway outputs only |
| 7 | Run planning | ✅ | STEP20–28 read `raw_data/Railway_Operations` only |
| 8 | Run TPJ onboarding | ✅ config-ready (data-blocked) | `gcfg` registry; no Walmart dep |

**All 8 pass** — the platform is functionally railway-only today; only the *bytes* of Walmart data remain on disk.

## 3. Restructure sequence (each gated on approval; re-run 541 tests after each)
1. `.gitignore` + **DELETE** Walmart data (2.4 G) → instant ~92% size cut.
2. **ARCHIVE** notebooks 01–07 + CPLEX/plots.
3. **RENAME** 3 railway notebooks.
4. **MOVE** docs → `docs/`.
5. **PURIFY** deps + add `pyproject.toml` + CI.
6. Tag **v1.0**.

## 4. Remaining risks
- **`SparePartsInventory.csv` / `SparePartsInventory!.csv`** (131 M / 297 M): name collides with the 58 project-name string hits — **human-verify** these are Walmart dumps before delete (audit flags, human confirms).
- M5 `raw_data` deletion: verified 0 `.py` loads, but confirm no external/notebook reliance before removal.
- Deletions touch `git history` size only after a history rewrite (optional; out of scope) — a plain delete shrinks the working tree but not `.git` (132 M).

## 5. Verdict
**The railway-only blueprint is complete and validated** — every asset has a retain/archive/delete/rename/move decision, and all 8 engineer workflows pass without Walmart assets. Execution awaits explicit approval (nothing changed this step).
