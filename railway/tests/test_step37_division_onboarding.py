"""STEP37 — TPJ onboarding: SUMMARY as operational source of truth, runtime
division switching, legacy-source retirement, and TPJ end-to-end.

These tests pin the NEW behavior introduced in STEP37 Phase 1-3:
  * railway_stock_summary.xlsx and stock_history.xlsx are retired.
  * SUMMARY OF STOCK HELD (per-division) is the operational source.
  * All six live divisions are first-class in the planning config registry.
  * gcfg.use_division(div) switches the planning layer at runtime.
  * TPJ executes end-to-end from native DMTR + SUMMARY inputs.
"""
from __future__ import annotations

import inspect

import pandas as pd
import pytest

from railway import railway_config as cfg
from railway import railway_data_preparation as dp
from railway import railway_demand_reconstruction as dr
from railway.governance import config as gcfg
from railway.governance.config import divisions as div
from railway.ingestion import excel_reader

LIVE = ["MAS", "SA", "TPJ", "MDU", "PGT", "TVC"]


# ---------------------------------------------------------------- registry / config
def test_all_live_divisions_registered():
    for d in LIVE:
        assert d in div.DIVISIONS, f"{d} not registered in DIVISIONS"


def test_tpj_registry_points_to_tpj_folder():
    rd = div.raw_dir("TPJ")
    assert rd.name == "TPJ"
    assert rd.parent.name == "Railway_Operations"


def test_summary_workbook_resolves_existing_file_each_division():
    for d in LIVE:
        p = div.summary_workbook(d)
        assert p.exists(), f"{d} summary not found: {p}"
        assert p.name.startswith("SUMMARY OF STOCK HELD")


def test_mas_summary_filename_not_stale():
    # the 08-06 snapshot is deleted; the resolver must pick the live 09-06 file.
    p = div.summary_workbook("MAS")
    assert p.exists()
    assert "08-06-2026" not in p.name


# ---------------------------------------------------------------- operational source = SUMMARY
def test_operational_workbook_constant_retired():
    assert not hasattr(cfg, "OPERATIONAL_WORKBOOK"), \
        "railway_stock_summary.xlsx must be fully retired (no OPERATIONAL_WORKBOOK)"


def test_operational_stock_loads_from_summary():
    df = dp.load_operational_stock()
    assert len(df) > 0
    assert {"PL_Code", "Current_Stock", "Unit_Cost", "Inventory_Value", "Depot"} <= set(df.columns)


def test_operational_stock_includes_tpj_and_mas_depots():
    df = dp.load_operational_stock()
    depots = df["Depot"].astype(str)
    assert depots.str.contains("TPJ").any(), "TPJ depots missing from operational frame"
    assert depots.str.contains("027534").any(), "MAS depot 027534 missing from operational frame"


def test_operational_reads_native_summary_columns():
    # native SUMMARY layout: Average Rate = col11, Value = col12
    # (NOT the col12/col13 the retired remapped workbook used).
    p = div.summary_workbook("TPJ")
    rows = excel_reader.read_sheet_rows(p)
    raw = next(r for r in rows[1:] if r.get(4))
    pl = str(raw.get(4)).split("/")[0].strip()
    recs = dp._operational_records_from_summary(p)
    rec = next(r for r in recs if r["PL_Code"] == pl)
    assert rec["Unit_Cost"] == dp._to_num(raw.get(11))
    assert rec["Inventory_Value"] == dp._to_num(raw.get(12))


# ---------------------------------------------------------------- retire stock_history
def test_stock_history_snapshot_removed():
    assert not hasattr(dr, "_load_stock_history_snapshot")


def test_no_stock_history_reference_in_demand_reconstruction():
    assert "stock_history" not in inspect.getsource(dr)


# ---------------------------------------------------------------- runtime division switching
def test_use_division_switches_summary_and_restores():
    from railway import railway_safety_stock as ss
    from railway import railway_rop as rop
    from railway import railway_srrs_mas as srrs

    before = gcfg.SUMMARY_WORKBOOK
    with gcfg.use_division("TPJ"):
        assert gcfg.DIVISION == "TPJ"
        assert "TPJ" in str(gcfg.SUMMARY_WORKBOOK)
        assert ss.SUMMARY == gcfg.SUMMARY_WORKBOOK
        assert rop.SUMMARY == gcfg.SUMMARY_WORKBOOK
        assert srrs.SUMMARY == gcfg.SUMMARY_WORKBOOK
    assert gcfg.DIVISION == "MAS"
    assert gcfg.SUMMARY_WORKBOOK == before


def test_use_division_switches_dmtr_dir_and_history():
    before_dmtr = gcfg.DMTR_DIR
    with gcfg.use_division("TPJ"):
        assert gcfg.DMTR_DIR.name == "TPJ"
        assert gcfg.HISTORY_DIR.parent.name == "TPJ"
        assert dr.DMTR_DIR == gcfg.DMTR_DIR
    assert gcfg.DMTR_DIR == before_dmtr


# ---------------------------------------------------------------- TPJ end-to-end (success criterion)
def test_tpj_demand_extraction_from_native_dmtr():
    with gcfg.use_division("TPJ"):
        recs, qa = dr.extract_transactions()
    assert qa["files"] == 54, "TPJ has 54 native DMTR registers"
    assert qa["rows"] > 0 and len(recs) > 0


def test_tpj_produces_own_inventory_policy(tmp_path):
    from railway import railway_business_unit_runner as runner
    runner.run(business_units=["TPJ"], root=tmp_path, quiet=True)
    pol = tmp_path / "TPJ" / "railway_inventory_policy.csv"
    assert pol.exists(), "TPJ did not produce its own railway_inventory_policy.csv"
    out = pd.read_csv(pol)
    assert len(out) > 0
