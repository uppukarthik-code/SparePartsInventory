"""
test_business_unit_runner.py
============================
STEP 18 tests for context parameterization + multi-Business-Unit runner.

Covers: path redirect/restore, BU discovery & depot routing, single-BU (MAS)
reproduction of canonical KPI/row invariants, data-less BU skeleton, and the
enterprise roll-up. Read-only against the analytics (no analytical code changed).
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from railway import railway_config as cfg
from railway import railway_context as rc
from railway import railway_business_unit_config as buc
from railway import railway_business_unit_runner as runner
from railway import railway_enterprise as ent

CANON = cfg.OUTPUT_DIR


# ---------------------------------------------------------------- context
def test_use_context_redirects_and_restores():
    before_out, before_ent = cfg.OUTPUT_DIR, ent.ENTERPRISE_DIR
    with rc.use_context("MAS"):
        assert cfg.OUTPUT_DIR == CANON / "MAS"
        assert cfg.POWERBI_DIR == CANON / "MAS" / "powerbi"
        assert cfg.INVENTORY_POLICY_CSV == CANON / "MAS" / "railway_inventory_policy.csv"
        assert ent.ENTERPRISE_DIR == CANON / "MAS" / "enterprise"
    assert cfg.OUTPUT_DIR == before_out          # restored
    assert ent.ENTERPRISE_DIR == before_ent


def test_context_restores_on_exception():
    before = cfg.OUTPUT_DIR
    with pytest.raises(ValueError):
        with rc.use_context("TPJ"):
            raise ValueError("boom")
    assert cfg.OUTPUT_DIR == before


# ---------------------------------------------------------------- discovery / routing
def test_depot_routing_mechanism():
    # The partition mechanism is correct even though current data is single-depot MAS.
    assert buc.resolve_business_unit("SSET/SRM/PER027029-S AND T-SR") == "MAS"
    assert buc.resolve_business_unit("XXX/GOC/123") == "TPJ"
    assert buc.resolve_business_unit("YYY/PTJ/9") == "PGT"   # STEP19: PTJ=Podanur -> Palakkad (PGT), corrected from TPJ


def test_discover_domains_and_units():
    domains = dict(runner.discover_domains())
    assert domains.get("Railway_Operations") == "Live"


# ---------------------------------------------------------------- MAS reproduction
@pytest.fixture(scope="module")
def mas_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("bu_outputs")
    runner.run(business_units=["MAS"], root=root, quiet=True)
    return root


def test_mas_strategic_rows(mas_run):
    p1 = pd.read_csv(mas_run / "MAS" / "powerbi" / "page1_procurement.csv")
    assert len(p1) == 59


def test_mas_operational_rows(mas_run):
    p4 = pd.read_csv(mas_run / "MAS" / "powerbi" / "page4_operational_health.csv")
    canonical = pd.read_csv(CANON / "powerbi" / "page4_operational_health.csv")
    assert len(p4) == len(canonical)   # MAS run reproduces canonical operational page (invariant, not a magic count)


def test_mas_kpis_match_canonical(mas_run):
    mas = pd.read_csv(mas_run / "MAS" / "powerbi" / "page0_executive_dashboard.csv").set_index("KPI")["Value"]
    can = pd.read_csv(CANON / "powerbi" / "page0_executive_dashboard.csv").set_index("KPI")["Value"]
    assert mas.to_dict() == can.to_dict()       # KPI values unchanged


def test_mas_enterprise_rollup_registry(mas_run):
    reg = mas_run / "MAS" / "enterprise" / "master_sku_registry.csv"
    assert reg.exists()
    df = pd.read_csv(reg, dtype={"PL_Code": str})
    assert len(df) > 0 and "PL_Code" in df.columns   # enterprise rollup produced a populated master SKU registry


# ---------------------------------------------------------------- data-less BU skeleton
def test_dataless_bu_skeleton(tmp_path):
    runner.run(business_units=["MAS", "STTC_PTJ"], root=tmp_path, quiet=True)   # STTC_PTJ has no onboarded operational data (TPJ onboarded in STEP18A)
    status = tmp_path / "STTC_PTJ" / "BU_STATUS.json"
    assert status.exists()
    meta = json.loads(status.read_text())
    assert meta["processed"] is False and meta["operational_rows"] == 0
    assert (tmp_path / "MAS" / "railway_inventory_policy.csv").exists()
    assert (tmp_path / "_enterprise_rollup" / "master_sku_registry_all.csv").exists()
