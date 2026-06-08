# STEP 12.5A — Page 4 Operational Health Compatibility Restoration

**Generated:** 2026-06-08
**Scope:** Compatibility only. No analytical logic, calculation, threshold, ranking, classification, or KPI was modified.
**Module changed:** `railway/railway_powerbi_export.py` (Page 4 builder), `railway/railway_dashboard_validation.py` (validation).

---

## 1. Objective

Restore the legacy Power BI **Operational Health** visual (`page4_operational_health.csv`) by carrying the SKU **Description** and guaranteeing the page exposes the full legacy column contract:

```
PL_Code, Description, Movement_Status, Inventory_Aging_Class, Inventory_Value, Operational_ABC
```

## 2. Change Applied

`Description` was added to the column selection drawn from the **operational SKU master**
(`railway_operational_inventory.csv`), which already carries a per-SKU `Description` for all
907 operational items. Because the column is taken from the same source frame, **no merge
was introduced** — row count and all existing values are mathematically guaranteed unchanged.

```diff
- p4 = operational[["PL_Code", "Movement_Status", "Inventory_Aging_Class", "Inventory_Value"]] \
+ p4 = operational[["PL_Code", "Description", "Movement_Status", "Inventory_Aging_Class", "Inventory_Value"]] \
         .merge(op_abc, on="PL_Code", how="left")
  p4["Source_Universe"] = "Operational"
  pages["page4_operational_health"] = p4
```

> **Note on "SKU master" source.** Page 4 is the *operational* universe (907 items). The
> strategic `railway_sku_master.csv` covers only the 59 strategic items, so it cannot supply
> descriptions for operational-only SKUs. The operational inventory file is the authoritative
> master for this universe and already contains `Description`; carrying it from there yields
> **zero null descriptions** while preserving the operational/strategic universe separation.

## 3. Resulting Column Contract

| Column | Status |
|---|---|
| PL_Code | present (unchanged) |
| **Description** | **added (carried from operational master)** |
| Movement_Status | present (unchanged) |
| Inventory_Aging_Class | present (unchanged) |
| Inventory_Value | present (unchanged) |
| Operational_ABC | present (unchanged) |
| Source_Universe | retained (pre-existing tag; not removed) |

## 4. Validation Update

`railway_dashboard_validation.py` gained a **V6b** assertion that `Description` is non-null on
page4 (and page1/page3/page5). Page 4 remains in `OPERATIONAL_EXEMPT` for the V4
"no-raw-value-column" rule because its `Inventory_Value` is the legitimate operational-universe
value (it has no normalized counterpart) — that behaviour is unchanged.

## 5. Evidence (regenerated outputs)

| Metric | Before | After | Result |
|---|---|---|---|
| Row count | 907 | 907 | ✅ unchanged |
| Σ Inventory_Value | 512,406,406.47 | 512,406,406.47 | ✅ unchanged |
| Shared columns byte-identical | — | True | ✅ |
| Description nulls | n/a | 0 | ✅ populated |
| V6b validation | — | PASS | ✅ |

Enterprise-enriched copy (`outputs/enterprise/powerbi/page4_operational_health.csv`)
automatically inherited `Description` (original columns first, slicers appended); row count
908 lines (907 + header) unchanged.

## 6. Result

✅ **Page 4 operational-health legacy visual restored.** Description populated for all 907
operational SKUs with zero analytical impact.
