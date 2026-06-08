# Digital Twin Readiness Report
*Southern Railway Signalling & Telecom Spare Parts — 07 June 2026*

## Executive Summary

The inventory platform is 75% ready (Near Ready) to support a network simulation and stocking study across depots. Inventory and stocking-policy data are complete; the gaps are in network and demand information, which are partly available. 12 items have been identified as candidates for multi-depot (tiered) stocking, where holding a central buffer can protect service at lower total stock. 59 items already carry a measured service-risk score that can feed the study. Closing the remaining network and demand-data gaps would move the platform to fully ready and allow a credible simulation of stocking levels, depot roles and service outcomes before any money is committed on the ground.

## Data Completeness

| Data Area | Completeness | Status |
|---|---|---|
| Network Data Completeness | 50% | Partial |
| Inventory Data Completeness | 100% | Ready |
| Demand Data Completeness | 50% | Partial |
| Policy Data Completeness | 100% | Ready |
| Overall Digital Twin Readiness | 75% | Near Ready |

> **Observation.** Overall readiness is 75% (Near Ready); inventory and policy data are complete while network and demand data are partial.
>
> **Business Implication.** A simulation built on incomplete network and demand inputs would give unreliable stocking advice.
>
> **Recommended Action.** Complete the depot-network and demand inputs before relying on simulation results.


## Service Risk Inputs

- **Items with a service-risk score:** 59

> **Observation.** 59 items carry a measured service-risk score.
>
> **Business Implication.** These scores let the study weight stocking decisions towards items whose shortage hurts service most.
>
> **Recommended Action.** Use the service-risk scores as the priority weighting inside the simulation.


## Multi-Echelon Opportunities

There are **12 multi-depot stocking candidates**:

| PL Code | Description | ABC | Criticality | Target Service Level |
|---|---|---|---|---|
| 50540324 | Lead Acid Stationary Secondary Cells  - 2V/80  | A | S2 | 98% |
| 56501018 | Cable 30 C x 1.5 Sq.mm | A | S1 | 99% |
| 50550081 | Lead Acid Stationary Secondary Cells  - 2V/200 | A | S2 | 98% |
| 56509959 | Cable 12 C x 1.5 Sq.mm | A | S1 | 99% |
| 56468039 | LED Red aspect with accessories | A | S1 | 99% |
| 56468052 | LED Yellow aspect with accessories | A | S1 | 99% |
| 56468040 | LED Green Aspect with accessories | A | S1 | 99% |
| 50232356/50232319 | Magneto telephone | A | S2 | 98% |
| 56501006 | Cable 24 C x 1.5 Sq.mm | A | S1 | 99% |
| 56119537 | Cable 2 C x 2.5 sq.mm | B1 | S1 | 97% |
| 56468027 | Route LED Signal lightning unit 100 V AC | B1 | S1 | 97% |
| 56462050 | AC Shunt Signal LED with in built current regu | B1 | S1 | 97% |

> **Observation.** 12 items are suited to tiered, multi-depot stocking.
>
> **Business Implication.** For these items a shared central buffer can hold the same service level at lower total stock than holding full stock at every depot.
>
> **Recommended Action.** Model these items first in the network study to size the central buffer and depot stocks.


## Readiness Score

- **Overall digital twin readiness:** 75% (Near Ready)

- **Areas below full readiness:** Network Data Completeness (50%), Demand Data Completeness (50%)


## Key Findings

- Overall readiness 75% (Near Ready).
- 12 multi-depot stocking candidates.
- 59 items carry a service-risk score.


## Business Implications

- The platform is close to supporting a credible stocking simulation.
- Incomplete network and demand data are the only barrier to full readiness.


## Next Steps

1. **Complete the depot-network data** (locations, lead times, links).
2. **Complete the demand data** for the modelled items.
3. **Run the network study** on the 12 multi-depot candidates first.
4. **Use service-risk scores** to weight stocking priorities in the study.


## Recommended Actions

1. Assign data owners to close the network and demand gaps.
2. Re-check readiness once the gaps are filled.
3. Commission the simulation when readiness reaches full.


## Data Sources

- `digital_twin_readiness.csv`
- `multi_echelon_candidates.csv`
- `service_risk.csv`
