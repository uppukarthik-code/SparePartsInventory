# AnyLogistix Readiness Report — Southern Railway Signalling Stores

**Generated:** 2026-06-07 · Source: generated outputs only (no raw Excel).

## 1. Readiness Score

**Overall Digital-Twin Readiness: 75.0% → Near Ready**

| Dimension | Score | Band |
|---|---:|---|
| Network_Data_Completeness | 50.0% | Partial |
| Inventory_Data_Completeness | 100.0% | Ready |
| Demand_Data_Completeness | 50.0% | Partial |
| Policy_Data_Completeness | 100.0% | Ready |
| Overall_Digital_Twin_Readiness | 75.0% | Near Ready |

## 2. Key Data Gaps

- **Coordinates absent** for all 12 locations (`Coordinate_Source=Placeholder`) — blocks geographic network optimization. Real lat/long must be supplied; never fabricated.
- **Division-level demand unavailable** in generated outputs — demand uses `Equal_Split` across the 6 divisions (`Demand_Allocation_Method=Equal_Split`). Export division consumption % to lift this.
- **Depot→Division mapping** not derivable from generated outputs (left NULL).

## 3. Multi-Echelon Candidate Count

**12** SKUs qualify (A/B1 × S1/S2 × Procurement Required).

## 4. Top Service-Risk Items

| PL_Code | Criticality | Inventory_Gap | Priority Score | Class |
|---|---|---:|---:|---|
| 50550081 | S2 | 14,581 | 464,269,547 | Immediate |
| 56509960 | S1 | 39,060 | 458,603,695 | Immediate |
| 56501018 | S1 | 58,454 | 339,684,654 | Immediate |
| 56509959 | S1 | 132,066 | 311,663,710 | Immediate |
| 56468039 | S1 | 3,477 | 309,396,571 | Immediate |

## 5. Recommended Next Actions

1. Supply real **division & depot geo-coordinates** (or a coordinate lookup) to enable network optimization.
2. Export **division-wise consumption %** from the strategic pipeline to replace Equal_Split demand.
3. Establish the **depot→division** hierarchy for multi-echelon routing.
4. Prioritise the **12 multi-echelon candidates** for stocking-location studies.

## 6. AnyLogistix Network-Modeling Readiness

**Near Ready.** Product, inventory-policy, and service-risk data are complete and AnyLogistix-shaped. The two blockers for full network modeling are **geo-coordinates** and **real division-level demand** — both are data-supply gaps, not modeling gaps. Once supplied, Southern Railway can run network/multi-echelon optimization without redesign.