# STEP 32 — Repository Purification & Railway Platform v1.0 Readiness Audit

**Date:** 2026-06-08 · **Branch:** `repository-purification` · **AUDIT ONLY — nothing deleted/archived/renamed/moved/committed/pushed.** Origin: `github.com/vivasvana1/SparePartsInventory.git`. Evidence: `repository_purification_inventory.csv`, `file_classification.csv`, `repository_size_analysis.csv`, `railway_only_validation.csv` + import/reference greps.

---

## 1. Headline finding
The repository is **2.6 GB**, of which **~2.4 GB (≈92%) is Walmart-era dead data** that no railway Python code references:
| Bucket | Size | Evidence |
|---|---|---|
| `notebooks/*.csv` Walmart output dumps | **1.9 GB** | FORECAST_BI/Forecast/final_* → 0 railway refs |
| `raw_data/` M5 CSVs (sales_train_*, sell_prices, calendar, sample_submission) | **431 MB** | `sales_train`/`sell_prices` = **0** loads in `railway/*.py` |
| `data/Sales_merged.csv` | **72 MB** | 0 refs |
| `**/.ipynb_checkpoints/` | ~470 MB | editor junk |

The **actual railway platform is ~150–200 MB** (`railway/` 43 M + outputs + `raw_data/Railway_Operations` 25 M + `Railway.pbix` 58 M + docs).

## 2. Delete-safety — proven (not assumed)
- `grep sales_train|sell_prices railway/*.py` → **0**.
- `grep read_csv.*SparePartsInventory railway/*.py` → **0** (the 58 hits are the project-name string in paths/comments).
- Only `notebooks/` reference in railway code = a **provenance comment** in `railway_forecasting.py` (the Croston/SBA/TSB engine was *derived from* notebook 04 — it does not load it).
- The 541-test suite + planning pipeline read only `railway/` + `outputs/` + `raw_data/Railway_Operations`.

## 3. Classification summary (`file_classification.csv`)
- **ACTIVE_RAILWAY_CORE/EXTENSION/INFRASTRUCTURE:** `railway/` (35 modules + ingestion/governance/tests/outputs), railway raw_data, the 3 STEP30 notebooks, `Railway.pbix`.
- **METHODOLOGY_REFERENCE:** notebooks **04, 05** (forecasting/optimizer provenance — cited in code comments).
- **REFERENCE_HISTORICAL:** notebook 07 (legacy railway), the STEP/RAILWAY `.md` audit trail.
- **ARCHIVE_WALMART:** notebooks 01–03, 06, `Optimization_models_CPLEX/`, `All plots/`.
- **DELETE_SAFE:** the 2.4 GB of Walmart data dumps + M5 + `Sales_merged` + checkpoints.

## 4. Verdicts
- **Genuinely railway-only?** Not yet *on disk* (2.4 GB Walmart data present) — but **functionally yes**: no railway code depends on any Walmart asset (proven), so removal is non-breaking.
- **Can Walmart be removed without breaking the platform?** **Yes** — `railway_only_validation.csv` shows all 8 engineer workflows (clone → delete archive → install → test → notebooks → reporting → planning → TPJ) work without Walmart assets.
- **Size reduction achievable:** **~90–92%** (2.6 GB → ~0.2 GB).

## 5. Recommended actions before v1.0 (require separate approval — NOT executed)
1. **DELETE** the 2.4 GB Walmart data (`delete_plan.csv`) + add `.ipynb_checkpoints/`, `*.csv` dumps to `.gitignore`.
2. **ARCHIVE** notebooks 01–07 + CPLEX/plots → `archive/` (`archive_plan.csv`).
3. **RENAME** the 3 STEP30 notebooks → `notebook_railway*.ipynb`.
4. **PURIFY** dependencies (remove sklearn/prophet/plotly; add `pyproject.toml`).
5. **MOVE** 113 root `.md` → `docs/`.
6. Re-run the 541-test suite after each step; re-pin only if intentionally changed.

**Hard stop:** every action above awaits explicit approval. See `final_railway_repository_blueprint.csv` and the companion STEP32 reports.
