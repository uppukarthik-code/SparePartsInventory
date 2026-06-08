# STEP 23 — Forecastability Report (MAS)

**Date:** 2026-06-08 · **Basis:** 12-month forecasts + rolling-origin backtest over the 54-month history; 961 forecastable PLs (122 Dead excluded).

---

## 1. Demand-pattern distribution (forecastable items)
Intermittent 654 · Lumpy 276 · Erratic 26 · Smooth 5.

## 2. Forecast-method distribution
SBA 654 · TSB 276 · Croston 26 · SES/Holt 5. (Assigned in STEP22; no override.)

## 3. Forecastability distribution

| Class | PLs | Routing |
|-------|----:|---------|
| High | 2 | Forecast-driven |
| Medium | 40 | Forecast-assisted |
| Low | 90 | Policy-driven |
| Very Low | 829 | Risk-driven |

**Only ~4% (42 PLs) are forecast-driven/assisted; 96% are policy/risk-driven** — the correct, evidence-based conclusion for an intermittent signalling-spares catalogue.

## 4. Forecastability by demand pattern

| Pattern | High | Medium | Low | Very Low |
|---------|----:|----:|----:|----:|
| Erratic | 1 | 21 | 4 | 0 |
| Smooth | 1 | 2 | 2 | 0 |
| Lumpy | 0 | 14 | 54 | 208 |
| Intermittent | 0 | 3 | 30 | 621 |

Forecastability concentrates in **Erratic + Smooth** (frequent demand). Intermittent items are overwhelmingly Very Low.

## 5. Forecastability by XYZ class

| XYZ | High | Medium | Low | Very Low |
|-----|----:|----:|----:|----:|
| X (CV≤0.5) | 0 | 0 | 1 | 0 |
| Y (0.5–1.0) | 2 | 4 | 4 | 0 |
| Z (>1.0) | 0 | 36 | 85 | 829 |

## 6. Forecastability by criticality

| Criticality | High | Medium | Low | Very Low |
|-------------|----:|----:|----:|----:|
| S1 | 0 | 8 | 4 | 0 |
| S2 | 0 | 4 | 2 | 3 |
| S3 | 2 | 2 | 0 | 3 |
| S4 | 0 | 0 | 0 | 4 |
| **Unknown** | 0 | 26 | 84 | 819 |

⚠ **Coverage gap:** criticality is keyed to the 59 strategic vital items; the 1,083 DMTR operational PLs are largely **Unknown** criticality. Linking DMTR PLs to criticality is a prerequisite for risk-weighted planning (governance action).

## 7. Forecast-volume concentration (extreme)

| Top N PLs | % of 12-mo forecast volume |
|-----------|---------------------------:|
| Top 10 | 66.5% |
| Top 20 | 81.0% |
| Top 50 | 90.6% |
| Top 100 | 95.3% |

Total forecast volume ≈ **881,752 units**. A handful of high-runner cables/OFC dominate — these warrant forecast-driven planning; the long tail is policy/risk-driven.

## 8. Top 20 forecastable PL Codes (by Forecastability_Score)

| PL_Code | Score | Class | Method | 12-mo vol | Description |
|---------|------:|-------|--------|----------:|-------------|
| 56507641 | 74.1 | High | SES/Holt | 52,714 | Channel bond pin single groove |
| 56450229 | 71.4 | High | Croston | 407 | Relay AC immune plug-in |
| 561196180021 | 68.9 | Medium | Croston | 90,614 | Cable jelly-filled underground |
| 45174416 | 68.7 | Medium | SES/Holt | 103 | Hydrometer assembly |
| 56508116 | 67.8 | Medium | Croston | 798 | Relay QN1 8F/8B |
| 56500142 | 67.3 | Medium | Croston | 1,760 | Relay QNA1 ACI 8F/8B |
| 56462050 | 65.9 | Medium | Croston | 234 | AC shunt signal (LED) |
| 56451027 | 65.6 | Medium | Croston | 383 | Relay AC immune plug-in |
| 56509376 | 64.9 | Medium | Croston | 29,820 | ARA terminal block (small) |
| 50540324 | 64.1 | Medium | Croston | 2,466 | Low-maintenance lead-acid cell |
| 561183521801 | 64.1 | Medium | Croston | 22,002 | PVC cable unsheathed |
| 56468027 | 63.8 | Medium | Croston | 273 | Route LED signal lighting |
| 539812840016 | 63.7 | Medium | TSB | 348 | Choke B type |
| 539844210026 | 62.1 | Medium | SBA | 189 | CT box sheet iron |
| 56509388 | 59.9 | Medium | TSB | 3,197 | Terminal block PBT |
| 563046150136 | 59.6 | Medium | TSB | 258 | Ground connection TWS |
| 563046150185 | 58.5 | Medium | TSB | 146 | Insulation set ground conn |
| 56468039 | 58.4 | Medium | Croston | 245 | Red aspect main LED signal |
| 549801610122 | 57.8 | Medium | Croston | 441 | Track feed battery charger |
| 56450217 | 57.7 | Medium | TSB | 220 | Relays special type |

## 9. Bottom 20 forecastable PL Codes
All **Very Low** (scores 12.6–13.7) — deep-intermittent, low-frequency spares (e.g. 542120120050, 565094804450/48/12, 565094825890 …). These should **not** be forecast-driven; manage by min/max policy or criticality-based risk reserve.

## 10. Forecast risk assessment

**High-volume but low-forecastability (top governance focus)** — items carrying large volume the forecast cannot reliably predict:

| PL_Code | 12-mo vol | Class | Method | sMAPE | Note |
|---------|----------:|-------|--------|------:|------|
| 56501006 | 139,193 | Medium | TSB | 104.5% | largest runner; only Medium |
| 509000396559 | 60,027 | Low | TSB | n/a | 48-fibre OFC, <25 mo (unvalidated) |
| 401107494209 | 51,517 | Very Low | SBA | n/a | XLPE cable, <25 mo (unvalidated) |
| 56119537 | 20,117 | Low | TSB | 139.9% | signalling cable |
| 56119033 | 20,018 | Low | TSB | 132.8% | signalling cable |
| 539804752183 | 18,644 | Very Low | TSB | 200% | |
| 56509960 | 16,982 | Low | TSB | 120.5% | cable |
| 539802804167 | 13,922 | Very Low | TSB | 174.9% | |

**Bias:** forecasts show a mild **positive (over-forecast) bias**, characteristic of Croston-family methods on intermittent demand (SBA partially corrects). The summary `Mean_Bias` is inflated by near-zero-demand items (normalized bias with tiny denominators) — directional, not magnitude. STEP24 safety-stock should apply bias-aware buffering and not treat the flat forecast as a precise monthly figure for the long tail.

**Overall risk posture:** forecast effort and accuracy investment should concentrate on the **~42 High/Medium items** (which also carry most volume) plus the **8 high-volume low-forecastability runners** (close monitoring + buffer); the **919 Low/Very-Low** items are correctly governed by policy/risk rules, not point forecasts.
