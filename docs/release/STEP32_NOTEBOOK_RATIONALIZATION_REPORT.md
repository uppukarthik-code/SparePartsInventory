# STEP 32 — Notebook Rationalization Report

**Date:** 2026-06-08 · Audit only. Evidence: `notebook_rationalization.csv`, `recommended_notebook_structure.csv`.

---

## 1. Current notebooks (10)
| Notebook | Size | Classification | Disposition |
|---|---|---|---|
| 01_data_preparation | 44 K | ARCHIVE_WALMART | archive |
| 02_data_preparation | 90 K | ARCHIVE_WALMART | archive |
| 03_exploratory_data_analysis | 2.5 M | ARCHIVE_WALMART | archive |
| 04_demand_forecasting | 282 K | METHODOLOGY_REFERENCE | archive (provenance) |
| 05_inventory_optimization | 281 K | METHODOLOGY_REFERENCE | archive (provenance) |
| 06_anylogistix_simuation_tables | 279 K | ARCHIVE_WALMART | archive |
| 07_railway_inventory_analysis | 21 K | REFERENCE_HISTORICAL | archive (superseded) |
| UPDATED_NOTEBOOK7 | 750 K | ACTIVE | **retain + rename** |
| NOTEBOOK7_EXECUTIVE_VERSION | 400 K | ACTIVE | **retain + rename** |
| NOTEBOOK7_TECHNICAL_VERSION | 354 K | ACTIVE | **retain + rename** |

**Numbering (01–07) is no longer meaningful** — it encodes the Walmart sequence. The railway platform should drop numeric prefixes for purpose-named notebooks.

## 2. 04 and 05 are methodology references, not deletable
`railway_forecasting.py` comments cite **"Reused VERBATIM from notebooks/04_demand_forecasting.ipynb"**. The Croston/SBA/TSB engine and the optimizer derive from 04/05 — archive them as provenance, do **not** delete.

## 3. Should Notebook 7 be renamed? — Yes
STEP30 established the three rebuilt notebooks as canonical. Rename to drop the legacy "7"/"UPDATED" naming.

## 4. Option comparison (`recommended_notebook_structure.csv`)
| Option | Maintainability | Duplication | Exec | Eng | TPJ | GitHub | Verdict |
|---|---|---|---|---|---|---|---|
| **A** master + executive + technical | High | Low (one engine) | Excellent | Excellent | Strong | Excellent | **RECOMMENDED** |
| B master + executive | High | Low | Excellent | Medium | Medium | Good | 2nd |
| C single notebook | Medium | None | Crowded | Crowded | Weak | Medium | No |

**Why A:** the three already exist (STEP30), are executed, and share one KPI engine (`division_summary`) so there is **no duplicated logic** — only audience-tuned presentation. A single notebook (C) forces COS/DRM and engineers to scroll past each other's content; B drops the technical deep-dive auditors need.

## 5. Recommended final structure (Option A)
```
notebooks/
    notebook_railway.ipynb            (<- UPDATED_NOTEBOOK7,   master, 16 sections)
    notebook_railway_executive.ipynb  (<- NOTEBOOK7_EXECUTIVE_VERSION)
    notebook_railway_technical.ipynb  (<- NOTEBOOK7_TECHNICAL_VERSION)
archive/
    walmart/notebooks/   (01-06)
    historical/          (07)
```

## 6. Verdict
**Rationalize to Option A** — 3 purpose-named railway notebooks retained, 7 legacy notebooks archived (04/05 as methodology provenance), numbering dropped. All renames await approval.
