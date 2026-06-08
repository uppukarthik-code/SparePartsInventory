"""Unit tests for operational analysis: aging, movement, value bands, dates."""
import numpy as np
from railway import railway_operational_analysis as op


def test_aging_class_buckets():
    assert op.aging_class(30) == "Active"
    assert op.aging_class(120) == "Monitor"
    assert op.aging_class(300) == "Slow Moving"
    assert op.aging_class(500) == "Very Slow Moving"
    assert op.aging_class(800) == "Dead Stock"


def test_aging_class_handles_nan_and_none():
    # the bug fixed in Step 6: NaN must map to Unknown, not Dead Stock
    assert op.aging_class(None) == "Unknown"
    assert op.aging_class(float("nan")) == "Unknown"


def test_movement_status_mapping():
    assert op.movement_status("Active") == "Active"
    assert op.movement_status("Monitor") == "Active"
    assert op.movement_status("Slow Moving") == "Slow Moving"
    assert op.movement_status("Very Slow Moving") == "Slow Moving"
    assert op.movement_status("Dead Stock") == "Dead Stock"
    assert op.movement_status("Unknown") == "Unknown"


def test_value_band():
    assert op.value_band(5000) == "< Rs 10,000"
    assert op.value_band(50000) == "Rs 10,000 - 1 Lakh"
    assert op.value_band(500000) == "Rs 1 Lakh - 10 Lakh"
    assert op.value_band(5000000) == "Rs 10 Lakh - 1 Crore"
    assert op.value_band(20000000) == ">= Rs 1 Crore"


def test_days_since_movement():
    # max of two dates vs reference 2026-06-07
    assert op.days_since_movement("07-06-2026", None) == 0
    assert op.days_since_movement(None, None) is None
    d = op.days_since_movement("01-01-2025", "01-06-2025")   # takes later date
    assert d == (op.REFERENCE_DATE - op._parse_dt("01-06-2025")).days
