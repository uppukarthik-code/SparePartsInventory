# STEP 26 — SRRS Analysis Report (MAS)

**Date:** 2026-06-08 · **Basis:** 626 ROP PLs; SRRS = Criticality_Weight × Service_Factor × Positive_Gap; value lens = Positive_Gap × Average_Rate.

---

## 1. Top 20 SRRS items (service-risk priority)
Leaders (rank · PL · SRRS · gap · class):

| # | PL_Code | SRRS | Gap (units) | Description |
|--:|---------|-----:|------------:|-------------|
| 1 | 56501006 | 1,729,476 | 86,474 | PVC insulated armoured cable |
| 2 | 56509959 | 947,557 | 47,378 | PVC insulating cable |
| 3 | 56501018 | 825,816 | 41,291 | PVC insulated cable |
| 4 | 561196180021 | 824,098 | 41,205 | Cable jelly-filled underground |
| 5 | 509000396559 | 781,300 | 39,065 | 48-fibre OFC (armoured) |
| 6 | 539804752183 | 681,295 | 34,065 | OFC 24-fibre armoured |
| 7 | 561183521801 | 414,043 | 20,702 | PVC cable unsheathed |
| 8 | 569003030035 | 279,244 | 13,962 | Fire-alarm fire-survival |
| 9 | 569003030023 | 240,200 | 12,010 | Fire-alarm fire-survival |
| 10 | 56509960 | 222,868 | 11,143 | PVC armoured cable |
*(…ranks 11–20 in `srss_results.csv`; all Top-20 are Critical.)*

## 2. Top 20 Value items (capital-exposure priority)

| # | PL_Code | Reorder_Gap_Value (₹) | Unit Rate (₹) | Description |
|--:|---------|----------------------:|--------------:|-------------|
| 1 | 567912550075 | 1,226,505,206 | 144,642 | Fire-alarm resettable type |
| 2 | 569003030023 | 794,750,402 | 66,174 | Fire-alarm fire-survival |
| 3 | 567919640033 | 132,497,474 | 6,826,248 | Alteration in existing EI |
| 4 | 560403020365 | 88,135,167 | 107,016 | Front panel VUR-P |
| 5 | 539802239713 | 76,946,002 | 107,657 | 25 mm conduit PVC pipe |
| 6 | 560800820064 | 60,010,500 | 1,650,000 | SMPS-based IPS system |
| 7 | 56501006 | 38,667,633 | 447 | PVC insulated armoured cable |
| 8 | 560403020353 | 27,691,718 | 33,624 | Sensor mounting bracket |
| 9 | 560403820199 | 26,414,940 | 282,000 | Multi-section digital axle counter |
| 10 | 56501018 | 24,811,223 | 601 | PVC insulated cable |

**The two lists differ fundamentally:** service-risk is led by high-quantity PVC cables; capital-exposure is led by expensive electronic systems (fire-alarm, EI, IPS, axle counters).

## 3. Items common to both Top-20 (unambiguous procure-first: 6 PLs)
`567912550075` · `569003030023` · `56501006` · `56501018` · `56509959` · `561196180021`
— items that are simultaneously high service-risk **and** high capital-exposure.

## 4. Pareto concentration

| Top N | % of SRRS (service risk) | % of capital value |
|-------|-------------------------:|-------------------:|
| Top 10 | **84.5%** | **74.1%** |
| Top 20 | 94.6% | 79.6% |
| Top 50 | 97.8% | 88.4% |

**MAS inventory risk is extremely concentrated** — ~85% of service risk and ~74% of capital exposure sit in just **10 of 626 PLs (1.6%)**. A focused intervention on the top tens of items addresses the overwhelming majority of risk.

## 5. High-Risk / High-Value quadrant (top-25% = 156 each)

| Quadrant | PLs | Action |
|----------|----:|--------|
| **High-Risk & High-Value** | **86** | **Procure first** — both service-critical and capital-material |
| High-Risk only | 70 | Service-priority (lower ₹ — cheap critical cables) |
| High-Value only | 70 | Capital-priority (expensive, lower service risk) |
| Neither | 400 | Routine / monitor |

## 6. Critical vs Non-Critical contribution

| Class | PLs | % of SRRS | % of capital value |
|-------|----:|----------:|-------------------:|
| Critical | 360 | **99.0%** | 92.1% |
| Non-Critical | 266 | 1.0% | 7.9% |

Service risk is almost entirely Critical-driven (by design — weight + service factor); capital exposure is also Critical-dominant but with a meaningful 7.9% Non-Critical tail.

## 7. Executive procurement prioritization (recommended sequence)
1. **6 common Top-20 items** — highest service risk *and* capital (e.g. 567912550075 fire-alarm, 569003030023, 56501006 PVC cable).
2. **86 High-Risk & High-Value quadrant** — procure-first list.
3. **70 High-Risk only** — service-critical cables (cheap, high stock-out impact).
4. **70 High-Value only** — capital-protect (expensive electronic systems).
5. **400 remaining** — routine min/max policy.

## Closeout — questions answered
1. **Which shortages matter most?** Service risk: high-gap Critical PVC cables/OFC (§1). Capital: fire-alarm/EI/IPS systems (§2).
2. **Procure first?** The 6 common-Top-20 items, then the 86 High-Risk×High-Value quadrant (§3, §5).
3. **% risk in Top 10/20/50?** 84.5% / 94.6% / 97.8%.
4. **% capital in Top 10/20/50?** 74.1% / 79.6% / 88.4%.
5. **How concentrated?** Extreme — ~85% of risk and ~74% of capital in 1.6% of PLs.
6. **Recommended sequence?** §7 (5-tier list led by the 6 dual-priority items).

## Caveat
SRRS and gap-value inherit the STEP 25 **issuing-depot context** (027534 holds ~0 of fast-movers → inflated shortages); absolute magnitudes overstate need but **relative prioritisation is valid** — and NS_DM_CONS shows open POs already exist against several top items, which procurement should net off.

*Additive computation only. No SRRS math, forecasting, safety-stock, ROP, procurement, or enterprise output was modified.*
