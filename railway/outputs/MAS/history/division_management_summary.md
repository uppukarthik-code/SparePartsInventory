# MAS Division — Management Summary

| Field | Value |
|---|---|
| Platform Version | Railway Inventory Planning Platform v1.0 (STEP1-28 + Hardening A/B) |
| Division | MAS |
| Data Date | 08-06-2026 |
| Git Commit | 2bddf37 |
| Generation Date | (runtime) |
| Pipeline Version | STEP1-19 core + STEP20-28 MAS extension |
| Readiness Score | 43.9 -> 76.7 (target) |

## L1 — Executive KPIs

| KPI | Value |
|---|---|
| Forecast Coverage % | 88.7 |
| Lead-Time Coverage % | 97.8 |
| Criticality Coverage % | 100.0 |
| Safety-Stock Coverage % | 100.0 |
| ROP Coverage % | 100.0 |
| SRRS Coverage % | 100.0 |
| Current Stock Value (Rs) | 913635687 |
| Reorder Gap Value (Rs) | 3367367459 |
| Total SRRS | 8217896.6 |
| Top-10 Risk Concentration % | 84.5 |
| Tier 1 Count | 6 |
| Tier 2 Count | 80 |
| Platform Readiness | 43.9 -> 76.7 (target) |
| TPJ Readiness | NO-GO (data-blocked); config-ready |

## L2 — Operational KPIs

| KPI | Value |
|---|---|
| Critical Shortages | 465 |
| Shortages | 45 |
| Healthy | 43 |
| Excess Inventory | 60 |
| No Demand | 13 |
| Open Procurement Exposure (Rs) | 3367367459 |
| Service Level Split | Critical(0.95): 360 | Non-Critical(0.85): 266 |

## L3 — Technical KPIs

| KPI | Value |
|---|---|
| Forecast Method Mix | {'SBA': 654, 'TSB': 276, 'Croston': 26, 'SES/Holt': 5} |
| Demand Class Mix | {'Intermittent': 654, 'Lumpy': 276, 'Dead': 122, 'Erratic': 26, 'Smooth': 5} |
| Criticality Distribution | {'Critical': 360, 'Non-Critical': 266} |
| Lead-Time Source Mix | {'PO_Date': 518, 'Requisition_Date': 184} |
| Planning Universe Funnel | 1083 classified -> 961 forecast -> 702 lead-time -> 626 planned |
