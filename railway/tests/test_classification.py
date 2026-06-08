"""Unit tests for classification: ABC, criticality, coverage, demand metrics."""
import numpy as np
from railway import railway_config as cfg
from railway import railway_classification as rc


def test_abc_thresholds():
    assert cfg.classify_abc(70 * cfg.LAKH) == "A"
    assert cfg.classify_abc(50 * cfg.LAKH) == "B1"
    assert cfg.classify_abc(20 * cfg.LAKH) == "B2"
    assert cfg.classify_abc(5 * cfg.LAKH) == "C"
    assert cfg.classify_abc(None) == "C"


def test_criticality_mapping():
    assert cfg.map_criticality("S") == "S1"
    assert cfg.map_criticality("V") == "S2"
    assert cfg.map_criticality("N") == "S3"
    assert cfg.map_criticality("") == "S4"
    assert cfg.map_criticality(None) == "S4"


def test_demand_metrics_dead_and_smooth():
    adi, cv2, cls = rc.compute_demand_metrics([0, 0, 0, 0, 0])
    assert cls == "Dead" and np.isnan(adi) and np.isnan(cv2)

    adi, cv2, cls = rc.compute_demand_metrics([100, 100, 100, 100, 100])
    assert cls == "Smooth" and adi == 1.0 and cv2 == 0.0


def test_demand_metrics_intermittent():
    # demand only in 2 of 5 periods, similar sizes -> ADI high, CV2 low
    adi, cv2, cls = rc.compute_demand_metrics([0, 100, 0, 0, 110])
    assert adi >= cfg.ADI_CUTOFF
    assert cls in ("Intermittent", "Lumpy")


def test_coverage_bands():
    r, c = rc.compute_coverage(0, 0, 100)      # ratio 0 -> critical shortage
    assert c == "Critical Shortage"
    r, c = rc.compute_coverage(150, 0, 100)    # 1.5 -> healthy
    assert c == "Healthy"
    r, c = rc.compute_coverage(100, 0, 0)      # EAR 0, stock>0 -> excess
    assert c == "Excess Capital"
