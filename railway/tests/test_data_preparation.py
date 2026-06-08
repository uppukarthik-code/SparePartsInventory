"""Unit tests for railway_data_preparation value-cleaning helpers."""
import numpy as np
from railway import railway_data_preparation as dp


def test_to_num_handles_na_tokens():
    assert np.isnan(dp._to_num("--NA--"))
    assert np.isnan(dp._to_num(""))
    assert np.isnan(dp._to_num(None))
    assert dp._to_num("1,250.5") == 1250.5
    assert dp._to_num(42) == 42.0


def test_norm_pl_variants():
    assert dp._norm_pl(56509376.0) == "56509376"
    assert dp._norm_pl("56987122/ 56110029") == "56987122/56110029"  # spaces collapsed
    assert dp._norm_pl(None) is None
    assert dp._norm_pl("  ") is None


def test_clean_str():
    assert dp._clean_str("  hi ") == "hi"
    assert dp._clean_str(None) == ""
