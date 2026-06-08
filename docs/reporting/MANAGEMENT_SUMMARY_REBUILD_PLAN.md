# Management Summary Rebuild Plan (STEP30, Phase Q)

**Date:** 2026-06-08 · Reporting only; additive. Evidence: `MANAGEMENT_SUMMARY_KPI_MAPPING.csv`, `MANAGEMENT_SUMMARY_SECTION_STRUCTURE.csv`, the new `railway/governance/division_summary.py`.

---

## 1. Problem (from STEP29)
`railway_executive_summary.py` and `railway_management_reports.py` consume **only STEP1–19 outputs** and ignore the entire STEP20–28 extension — management never sees forecast/LT/SS/ROP/SRRS/procurement signals (e.g. **465 critical shortages**, **Rs 3.37B reorder-gap**).

## 2. Solution delivered this step (additive module)
`railway/governance/division_summary.py` — a **STEP1–28-aware, division-aware** summary engine that reads current outputs and produces L1/L2/L3 KPIs + a provenance metadata header. It changes **no existing analytics or module** (the legacy modules are left untouched; this is the new model they should adopt).

### Metadata header (provenance) — implemented
| Field | Source |
|---|---|
| Platform Version | module constant |
| Division | `governance/config.DIVISION` |
| Data Date | parsed from SUMMARY filename (08-06-2026) |
| Git Commit | `git rev-parse --short` (e.g. 2bddf37) |
| Generation Date | runtime |
| Pipeline Version | STEP1-19 core + STEP20-28 extension |
| Readiness Score | `platform_scorecard.csv` mean |

### KPI model (`MANAGEMENT_SUMMARY_KPI_MAPPING.csv`)
- **L1 Executive** (14): forecast/LT/criticality/SS/ROP/SRRS coverage, current-stock & reorder-gap value, Total SRRS, top-10 concentration, Tier 1/2, platform & TPJ readiness.
- **L2 Operational** (7): critical shortages, shortages, healthy, excess, open procurement exposure, service-level split.
- **L3 Technical** (5): forecast-method mix, demand-class mix, criticality distribution, LT-source mix, planning funnel.

Every L1/L2/L3 KPI maps to a STEP20–28 output that the legacy summary did **not** consume.

## 3. Section structure (`MANAGEMENT_SUMMARY_SECTION_STRUCTURE.csv`)
Metadata Header → Executive Snapshot (L1) → Operational Status (L2) → Technical Profile (L3) → Risk Concentration → Capital Exposure → Platform Readiness → Division Comparison (MAS now; MAS-vs-TPJ when data lands).

## 4. Division-awareness & multi-division
`division_summary.build(division=...)` resolves the active division via `governance/config`; output paths and constants follow `gcfg`. Adding TPJ = a registry entry + data → the same summary renders for TPJ, and a roll-up can sum across divisions. **Version-controlled** via the git-commit + data-date header.

## 5. Migration recommendation (future step, not done here)
Re-point `railway_management_reports.collect_kpis` / `railway_executive_summary.build_kpis` at `division_summary.compute_kpis()` (or deprecate them in favour of it). This is a behavior-additive reporting change behind the green test suite — **no analytics touched**.

## 6. Outputs produced
`division_management_summary.{json,csv,md}` in `outputs/MAS/history/` — the working STEP1–28 management summary for MAS, regenerable per division.
