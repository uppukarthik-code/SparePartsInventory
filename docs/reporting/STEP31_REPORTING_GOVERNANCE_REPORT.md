# STEP 31 — Reporting Governance Report

**Date:** 2026-06-08 · Evidence: `reporting_governance_framework.csv`, `final_reporting_architecture.csv`.

---

## 1. Reporting source of truth
**`railway.governance.division_summary`** is the single, authoritative KPI engine. All reporting surfaces derive from it:
```
generated outputs (STEP1-28)
        |
        v
division_summary.compute_kpis()  ← SINGLE SOURCE OF TRUTH (L1/L2/L3)
        |
   +----+--------------------+----------------------+
   v                         v                      v
Notebook Railway       Executive Reporting    Management Reporting
(3 variants)           (es.kpis/summary)      (mr.modern_kpis/summary)
        \                                          /
         +----------> Enterprise Roll-up <--------+
                      (build_all_divisions)
```

## 2. KPI ownership & lineage
- **Ownership:** L1/L2/L3 KPIs are defined **once** in `compute_kpis()`. No other module defines a modern KPI.
- **Lineage:** every KPI maps to a named STEP20–28 output (`kpi_migration_map.csv`).
- **Flow:** strictly one-way (outputs → engine → consumers); consumers never recompute.
- **Legacy boundary:** `build_kpis` / `collect_kpis` are DEPRECATED, frozen for output compatibility, removal deferred.

## 3. Metadata standard (implemented)
Every summary carries: **Platform Version · Division · Data Date · Git Commit · Generation Date · Pipeline Version · Readiness Score** (`division_summary.metadata()`), so any report is self-describing and version-controlled (proven: `Git Commit 2bddf37 · Data Date 08-06-2026 · Readiness 43.9→76.7`).

## 4. Current → target (`final_reporting_architecture.csv`)
| Layer | Status |
|---|---|
| KPI engine (single) | **DONE** |
| Executive / Management reporting delegate to SoT | **DONE** |
| Notebooks consume SoT | **DONE** |
| Division parameterization (`--division`) | **DONE** |
| Enterprise roll-up | **FOUNDATION** |
| Legacy compute removal | DEFERRED (purification) |

## 5. Governance verdict
**Reporting governance established.** One source of truth, single KPI ownership, evidence-traced lineage, a metadata standard, and a documented legacy deprecation boundary — the foundation required for a controlled Railway Platform v1.0 release.
