# STEP 22 — Demand Analytics Report (MAS)

**Date:** 2026-06-08
**Basis:** 54-month reconstructed demand history (Jan 2022 – Jun 2026), 1,083 PL codes, Syntetos–Boylan classification on monthly `Issues_Qty`.

---

## 1. Demand-pattern distribution

| Demand Class | PLs | % of PLs | Demand volume (units) | % of volume |
|--------------|----:|---------:|----------------------:|------------:|
| Intermittent | 654 | 60.4% | 75,747 | 2.8% |
| Lumpy | 276 | 25.5% | 1,192,630 | 43.7% |
| Dead | 122 | 11.3% | 0 | 0.0% |
| Erratic | 26 | 2.4% | 1,204,210 | 44.1% |
| Smooth | 5 | 0.5% | 255,097 | 9.4% |
| **Total** | **1,083** | 100% | 2,727,684 | 100% |

**Read:** a textbook spare-parts profile — **86% of catalogue items are Intermittent or Lumpy** (irregular demand), yet **88% of demand *volume*** sits in just **31 high-runner items** (Erratic 44% + Lumpy's large cables + Smooth 9%). The long tail (654 Intermittent PLs) is only 2.8% of volume but dominates *line count* and *service risk*.

## 2. Forecast-method distribution

| Method | PLs | Rationale |
|--------|----:|-----------|
| SBA (Intermittent) | 654 | infrequent, consistent size — bias-corrected Croston |
| TSB (Lumpy) | 276 | infrequent + variable size — probability-based, handles obsolescence |
| No Forecast (Dead) | 122 | no demand in 54 months |
| Croston (Erratic) | 26 | frequent, variable size |
| SES/Holt (Smooth) | 5 | regular, low-variability |

**961 of 1,083 PLs are forecastable** (non-Dead); **769** have ≥24 months of history (robust).

## 3. XYZ (predictability) distribution

| XYZ | PLs | Meaning |
|-----|----:|---------|
| Z (CV>1.0) | 950 | highly variable / intermittent — low predictability |
| Y (0.5<CV≤1.0) | 10 | moderate |
| X (CV≤0.5) | 1 | predictable |
| N/A (Dead) | 122 | no demand |

XYZ × SBC crosstab confirms coherence: Intermittent(650)+Lumpy(276)+Erratic(24) are virtually all **Z**; the lone **X** is a Smooth item. Predictability is low across the catalogue → simple moving-average forecasting is inappropriate; intermittent-demand methods are mandatory.

## 4. Top intermittent items (by demand volume)

| PL_Code | ADI | CV² | Total issues | Description |
|---------|----:|----:|-------------:|-------------|
| 56110029 | 4.90 | 0.382 | 14,317 | Cable PVC insulated armoured unscreened |
| 500500680030 | 8.83 | 0.369 | 14,026 | Half split DWC pipe |
| 569003030035 | 17.67 | 0.340 | 11,578 | Fire alarm fire-survival integrity |
| 401107494209 | 6.00 | 0.000 | 4,519 | 2C×70 Sqmm XLPE insulated PVC sheathed |
| 549012320014 | 2.13 | 0.446 | 2,460 | Galvanised cable clamp assembly |

## 5. Top lumpy items (by demand volume)

| PL_Code | ADI | CV² | Total issues | Description |
|---------|----:|----:|-------------:|-------------|
| 56501006 | 1.44 | 1.514 | 396,027 | PVC insulated armoured unscreened cable |
| 56119033 | 1.59 | 1.037 | 133,485 | Cable PVC insulated armoured unscreened |
| 509000396559 | 2.50 | 1.251 | 96,921 | 48-fibre OFC (armoured) per RDSO |
| 56509960 | 1.86 | 0.858 | 91,477 | Cable PVC insulated armoured unscreened |
| 56119537 | 1.54 | 0.851 | 72,701 | PVC insulated cable for railway signalling |

The lumpy high-volume items are predominantly **cables/OFC** — large, irregular, project-driven draws. These dominate inventory value-at-risk and warrant TSB + close safety-stock attention.

## 6. Forecasting readiness assessment

| Dimension | Status |
|-----------|--------|
| Monthly history depth | 🟢 54 months (769 PLs ≥24 mo) |
| Demand metrics (ADI, CV², CV, intermittency) | 🟢 computed for all 1,083 |
| Method assignment | 🟢 every PL → exactly one method |
| Method–pattern fit | 🟢 96% of forecastable items need intermittent methods (SBA/TSB) — all available in the existing engine (`croston_forecast`, `sba_forecast`, `tsb_forecast`, `holt_forecast`) |
| Lead time / pending supply (per division) | 🔴 still not sourced — needed for ROP/SS, not for forecasting itself |

**MAS is forecasting-ready.** The existing `railway_forecasting.py` already implements Croston/SBA/TSB/Holt; STEP22 supplies the per-PL method routing the monthly data justifies.

## 7. Recommended STEP 23 — Forecasting Implementation Plan

| Field | Detail |
|-------|--------|
| **Objective** | Generate monthly/annual demand forecasts per MAS PL using the STEP22 method assignment on the 54-month history. |
| **Scope** | New additive module that, per PL, runs the **assigned** method (reuse the existing `croston/sba/tsb/holt` functions verbatim — no formula change): SBA(654), TSB(276), Croston(26), SES/Holt(5); Dead(122)→zero forecast. Produce `monthly_forecast.csv` + a backtest (hold-out last 6–12 months) with MAE/MAPE/Bias per method. |
| **Benefits** | First true demand-driven forecasts for MAS (replacing the zone-shared annual blend); per-pattern accuracy; foundation for division safety-stock & ROP. |
| **Risks** | Short/again-intermittent series for some PLs (use the existing safe fallbacks); keep strictly additive — do not alter the locked zone forecast engine or KPIs. |
| **Effort** | Medium (~2–3 person-weeks) — engines exist; work is routing, backtesting, validation. |
| **Dependency for ROP/SRRS** | Pair forecasts with per-division **lead-time/pending-supply** (still to be sourced) before division ROP/SRRS. |

---

### Closeout
1. **Demand pattern distribution:** Intermittent 654 · Lumpy 276 · Dead 122 · Erratic 26 · Smooth 5.
2. **Forecast method distribution:** SBA 654 · TSB 276 · No Forecast 122 · Croston 26 · SES/Holt 5.
3. **Top intermittent:** §4 (cables, DWC pipe, fire-alarm cable).
4. **Top lumpy:** §5 (high-volume signalling cables / OFC).
5. **Forecasting readiness:** 🟢 ready (961 forecastable, 769 with ≥24 months; intermittent engines already present).
6. **STEP 23 plan:** §7 — run assigned methods + backtest, additive, reuse existing engines.
