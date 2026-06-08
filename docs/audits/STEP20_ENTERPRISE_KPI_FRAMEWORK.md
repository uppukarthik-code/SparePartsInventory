# STEP 20 — Enterprise Benchmark KPI Framework

**Type:** Design recommendation (read-only). No KPI code was added or changed.
**Date:** 2026-06-08
**Purpose:** A business-unit-aware benchmark framework spanning the seven required domains, ranked by usefulness, with definitions, grain, source, and current availability.

---

## 1. Design principles

1. **Conserving** — every additive KPI must sum from BU → zone without inflation (the STEP19 discipline; the operational benchmark fan-out must be fixed first — see roadmap).
2. **Grain-honest** — each KPI declares whether it is genuinely *per-division* or *zone-shared today*; never present a zone value as divisional.
3. **Decision-linked** — each KPI maps to an action (procure / rationalize / reconcile / monitor).
4. **Backward-compatible** — published page-0 KPI *values* are preserved; new KPIs are additive slicers/measures.

---

## 2. KPI catalogue by domain (with usefulness rank)

Usefulness = decision impact × data trustworthiness × division-actionability. Rank 1 = most useful.

### 2.1 Strategic Inventory

| KPI | Definition | Grain | Source | Avail. |
|-----|------------|-------|--------|:-----:|
| **Strategic Coverage Ratio** (Stock ÷ Annual Consumption) | months/years of cover by division | per-BU | allocation + EAR cons | 🟡 1-yr cons |
| **Allocated Strategic Inventory Value** | Σ stock×cost by BU (de-inflated) | per-BU | STEP19 | 🟢 |
| **Strategic Stock Conservation** | Σ BU stock ÷ zone stock (=1.0) | zone | STEP19 | 🟢 |
| **Strategic Concentration (HHI)** | concentration of strategic value across BUs | zone | STEP19 | 🟢 |

### 2.2 Operational Inventory

| KPI | Definition | Grain | Avail. |
|-----|------------|-------|:-----:|
| **Operational Inventory Value** | Σ value by division | per-BU | 🟢 |
| **Inventory Aging Profile** | % value in Active/Slow/Dead bands | per-BU | 🟢 |
| **Operational ABC Concentration** | % value in A items | per-BU | 🟢 |

### 2.3 Dead Stock

| KPI | Definition | Grain | Avail. |
|-----|------------|-------|:-----:|
| **Dead Stock Value** | Σ value of non-moving items | per-BU | 🟢 |
| **Dead Stock Ratio** | Dead ÷ Operational value | per-BU | 🟢 |
| **Rationalization Opportunity** | redeployable/retirable value | per-BU | 🟢 |

### 2.4 Procurement Risk

| KPI | Definition | Grain | Avail. |
|-----|------------|-------|:-----:|
| **Procurement-Required Items / Value** | items below ROP × cost | zone today | 🟠 |
| **Budget Coverage** | budget ÷ total required investment | zone today | 🟠 |
| **Criticality-Weighted Shortfall** | Σ gap × criticality weight | zone today | 🟠 |

### 2.5 Inventory Turn Risk

| KPI | Definition | Grain | Avail. |
|-----|------------|-------|:-----:|
| **Inventory Turn Risk %** | published turn-risk measure | per-BU* | 🟡 |
| **Slow+Dead Share** | (slow+dead) ÷ total value | per-BU | 🟢 |

### 2.6 Strategic Coverage *(cross-cutting — the most decision-rich family)*

| KPI | Definition | Grain | Avail. |
|-----|------------|-------|:-----:|
| **Coverage vs EAR** | Stock ÷ EAR requirement | per-BU | 🟡 1-yr |
| **Coverage Gap (units / value)** | EAR − Stock, floored at 0 | per-BU | 🟡 1-yr |
| **Strategic Stock-out Exposure flag** | coverage < threshold (e.g. <0.25×) | per-BU | 🟡 |

### 2.7 Digital Twin Readiness

| KPI | Definition | Grain | Avail. |
|-----|------------|-------|:-----:|
| **Digital Twin Readiness %** | published readiness composite | zone today | 🟡 |
| **Data Completeness Index** | % required planning fields present per BU | per-BU | 🟢 (computable) |

\* turn-risk currently carried per BU via the benchmark; subject to the operational fan-out fix.

---

## 3. Top KPIs ranked by usefulness (enterprise scorecard)

| Rank | KPI | Domain | Why it ranks here |
|-----:|-----|--------|-------------------|
| 1 | **Strategic Coverage Ratio (Stock ÷ Consumption)** | Strategic / Coverage | Directly exposes stock-out & overstock by division; surfaced the PGT crisis (0.0003×) — highest decision impact. |
| 2 | **Coverage Gap vs EAR (value)** | Coverage | Quantifies the rupee size of each division's strategic shortfall; drives procurement targeting. |
| 3 | **Dead Stock Ratio** | Dead Stock | High-trust (per-division), immediately actionable capital release. |
| 4 | **Allocated Strategic Inventory Value** | Strategic | The conserved, de-inflated value enabling true cross-division comparison (STEP19). |
| 5 | **Criticality-Weighted Shortfall** | Procurement Risk | Aligns spend with service risk (RAMS-aligned), not just rupees. |
| 6 | **Strategic Concentration (HHI)** | Strategic | Reveals over-centralization (MAS holds ~97% of strategic value) — a resilience signal. |
| 7 | **Inventory Aging Profile** | Operational | Per-division health, fully available now. |
| 8 | **Data Completeness Index** | Digital Twin | Governs *which* divisions can be trusted for planning — gates the roadmap. |
| 9 | **Budget Coverage** | Procurement Risk | Capital-planning headline; zone-grain today. |
| 10 | **Inventory Turn Risk %** | Turn Risk | Useful but pending the benchmark fan-out fix. |

---

## 4. Recommended enterprise scorecard layout (per BU + zone roll-up)

```
Division | StratCover | CoverGap₹ | DeadRatio | StratValue₹ | CritShortfall | TurnRisk% | DataComplete%
MAS      |   2.85x    |    …      |   14.9%   |  82.9M      |     …         |    …      |    …
SA       |   0.14x    |    …      |    4.0%   |   0.14M     |     …         |    …      |    …
…
PGT      |  0.0003x ⚫ |  HIGHEST  |    5.3%   |   0.006M    |     …         |    …      |  LOW (gap)
ZONE     |   (Σ/agg)  |    …      |    …      |  85.7M ✓    |     …         |    …      |    …
```

**Guardrails:** (a) all ₹ measures must reconcile BU→zone (conservation test); (b) coverage/EAR KPIs must carry a "single-year (2020-21)" caveat until multi-year per-division demand exists; (c) Digital Twin Readiness should incorporate the **Data Completeness Index** so divisions with thin data (e.g. PGT) cannot show false readiness.

*No KPI logic was implemented or modified; this is a design recommendation only.*
