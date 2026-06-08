# STEP 16 — Gap Decomposition Audit

**Generated:** 2026-06-08
**Mode:** 🔍 **READ-ONLY ANALYSIS. No production code modified.**
**Subject:** How much of the calibrated `Service_Risk_Reduction_Score` is *indirectly* driven —
through `Inventory_Gap` — by Forecast, Lead Time, Service Level, Safety Stock and Current Stock.

Calibrated objective (Step 15): **`SRRS = Criticality_Weight × Service_Factor × Positive_Gap`**.
Because SRRS is **linear in `Positive_Gap`**, every driver reaches SRRS *only* through the gap (plus
Service Level, which also has the explicit `Service_Factor`). The gap is therefore the right unit of
analysis.

---

## 0. Structural identity (from source `railway_inventory_optimization.py:184–187`)

```
Safety_Stock  = z(Service_Level) · σ · √Lead_Time          # demand-variability buffer
EDLT          = Forecast · Lead_Time / 12                   # Expected Demand During Lead Time
ROP           = EDLT + Safety_Stock
Inventory_Gap = ROP − Current_Stock
Positive_Gap  = max(Inventory_Gap, 0)
```
So the five queried drivers enter the gap as:
| Driver | Channel into the gap | Mathematical form |
|---|---|---|
| Forecast | EDLT only | `∝ Forecast` |
| Lead Time | EDLT **and** Safety Stock | `∝ Lead_Time` (EDLT) and `∝ √Lead_Time` (SS) |
| Service Level | Safety Stock (via z) **+ explicit Service_Factor** | `z(SL)` and `1+20·(SL−0.9)` |
| Safety Stock | itself | `z·σ·√LT` |
| Current Stock | subtracts from ROP | `−Current_Stock` |

---

## 1. Gap Decomposition

`Inventory_Gap` decomposed into the two ROP drivers (the `Current_Stock` offset is attributed
proportionally to each driver's share of ROP), over the **50 procurement-required** items:

| Quantity | EDLT component | Safety-Stock component |
|---|---:|---:|
| Share of **ROP** (mean / median) | 53.0% / 39.1% | 47.0% / 60.9% |
| **`Gap_EDLT_Component`** (Σ) | 226,510 units | — |
| **`Gap_SafetyStock_Component`** (Σ) | — | 596,011 units |
| Share of total `Positive_Gap` | **27.5%** | **72.5%** |

`Current_Stock` is only ~17% of ROP on average — stock is thin, so most of ROP flows through to the
gap. The gap is **dominated by the Safety-Stock component (72.5%)**, i.e. by demand variability (σ)
at the target service level — not by mean throughput.

## 2. Contribution of Each Component to SRRS

SRRS is linear in the gap, so the split carries straight through:

| Source | Share of total SRRS |
|---|---:|
| **EDLT component** (Forecast × Lead Time) | **33.4%** |
| **Safety-Stock component** (z(SL) × σ × √Lead Time) | **66.6%** |

**Per-driver footprint inside SRRS** (single-count, analytic):

| Driver | Footprint in SRRS | Notes |
|---|---:|---|
| **Forecast** | **33.4%** | enters EDLT only |
| **Lead Time** | **66.7%** | EDLT (full) + ½·Safety-Stock (√LT → half-elasticity) |
| **Service Level** | ~66.6% (via Safety-Stock z-channel) **+ Service_Factor** | dual channel (see §4) |
| **Safety Stock** | **66.6%** | the SS gap component itself |
| **Current Stock** | −17% (offset) | reduces the gap; negative contributor |

**Reading:** SRRS is majority-driven by the **service buffer** (safety stock — demand variability ×
service level × √lead-time), with mean **forecast a minority (33%)**. For railway signalling this is
*appropriate*: service risk is about protecting against variability at a high service target for
critical items, not about chasing high-throughput consumables.

## 3. Elasticity After Decomposition

### 3.1 Analytic (structural, per-item — single count by construction)
| Elasticity | Formula | Median | Mean |
|---|---|---:|---:|
| `d ln SRRS / d ln Forecast` | `EDLT / Gap` | **0.55** | 1.09 |
| `d ln SRRS / d ln Lead_Time` | `(EDLT + ½·SS) / Gap` | **0.96** | 2.00 |

### 3.2 Cross-sectional regression (log-log, n=50)
| Model | Forecast | Lead Time |
|---|---:|---:|
| Simple | 1.12 | **1.93** |
| **+ Criticality controls** | 1.04 | **1.11** |
| `corr(Lead_Time, Criticality_Weight)` | — | **0.66** |

**The lead-time elasticity falls from 1.93 → 1.11 once criticality is controlled for.** The raw 1.93
is ~0.8 *confound*: the Tier-2 fallback lead time is **derived from criticality** (S1=6, S2=4, S3=3,
S4=2 months), so lead time and criticality are 0.66-correlated and an uncontrolled regression
mis-attributes criticality's effect to lead time. Service-level elasticity is not separately regressed
— with only 5 distinct SL values fully tied to the ABC×Criticality service table, it is not
identifiable cross-sectionally; structurally it acts through the Safety-Stock z-channel plus the
bounded `Service_Factor`.

## 4. Lead-Time Influence Verdict

| Evidence | Value | Implication |
|---|---:|---|
| Structural single-count elasticity (median) | **0.96** | exactly one count via the gap |
| Criticality-controlled regression | **1.11** | ≈ single count |
| Raw cross-sectional | 1.93 | inflated by LT↔criticality confound (corr 0.66) |
| Explicit `Lead_Time_Factor` in objective | **removed (Step 15)** | no multiplicative double-count remains |

### Verdict: **EXPECTED (single-count, elasticity ≈ 1.0).**
Lead time is **not** excessively counted. It appears in the gap exactly once (linearly in EDLT,
as √ in safety stock → combined ≈1.0), and the explicit lead-time multiplier was already removed in
Step 15. The headline 1.93 is a **statistical confound**, not a mechanistic over-count: it is the
upstream coupling between the criticality-derived fallback lead time and criticality itself. After
de-confounding, influence is at the expected single-count level.

> **Service-Level note (minor):** Service Level reaches SRRS through **two** channels — `z(SL)` inside
> safety stock (buffer sizing) and the explicit `Service_Factor` (priority intolerance). This is a
> **deliberate** design distinction (sizing vs weighting), and `Service_Factor` is now bounded
> (1.0–2.8, ≤2.8×), so the dual presence is mild and intentional — not an accidental double count.

## 5. Recommendation — Is Further Normalization Required?

**No further normalization of the SRRS objective is required.** The decomposition confirms the
Step-15 calibration achieved its goal: demand and lead time are each counted **once** (elasticities
≈1.0 structurally and after de-confounding), and the explicit double-count multipliers are gone.

The single residual is **upstream, not in SRRS**: the fallback lead time is a function of criticality,
producing the 0.66 LT↔criticality correlation that inflates the *raw* (uncontrolled) lead-time
elasticity. Options, in priority order:

| Option | Action | Recommendation |
|---|---|---|
| **A (preferred)** | Leave SRRS unchanged | ✅ SRRS is correctly single-counting; the coupling is an honest data property (critical items do carry longer fallback lead times). |
| B | Replace the criticality-derived **fallback** lead time with **measured** lead times upstream (in the gap model, not SRRS) | Optional — a data-acquisition improvement that would remove the confound at source; out of SRRS scope. |
| C | Add `Gap_EDLT_Component` / `Gap_SafetyStock_Component` as **additive diagnostic columns** | Optional transparency only — improves explainability, not correctness. |

**Do not** re-introduce any per-factor normalization into the objective: that would re-create the
Step-13 double-count this audit confirms is now absent.

---

## 6. Summary

- Gap = **27.5% EDLT + 72.5% Safety-Stock**; SRRS = **33.4% EDLT-driven + 66.6% Safety-Stock-driven**.
- Forecast footprint **33%**; Lead-time footprint **67%** (it sits in both gap components); Safety
  Stock **67%**; Current Stock a **−17%** offset; Service Level via the SS z-channel + bounded `Service_Factor`.
- **Demand elasticity ≈ 1.0; lead-time elasticity ≈ 1.0 (structural / de-confounded).** The raw 1.93
  is a criticality↔lead-time confound (corr 0.66), not a double count.
- **Lead-time influence: EXPECTED (single count).** **No further SRRS normalization required.**
  Address the confound upstream (measured lead times) only if the criticality–lead-time coupling is a
  governance concern.
