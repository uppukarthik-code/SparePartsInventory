"""Unit tests for the rationalization action matrix."""
from railway import railway_inventory_rationalization as rat


def test_verbatim_rules():
    assert rat.assign_action("S1", "Procurement Required", "") == "Procure Immediately"
    assert rat.assign_action("S2", "Procurement Required", "") == "Procure Immediately"
    assert rat.assign_action("S1", "Sufficient", "") == "Retain"
    assert rat.assign_action("S3", "", "Slow Moving") == "Monitor"
    assert rat.assign_action("S4", "", "Slow Moving") == "Rationalize"
    assert rat.assign_action("", "", "Dead Stock") == "Dispose"


def test_fallbacks():
    # operational item, no criticality
    assert rat.assign_action(None, None, "Active") == "Retain"
    assert rat.assign_action(None, None, "Slow Moving") == "Rationalize"
    assert rat.assign_action(None, None, "Unknown") == "Monitor"


def test_all_actions_valid():
    for c in ("S1", "S2", "S3", "S4", None):
        for s in ("Procurement Required", "Sufficient", None):
            for m in ("Active", "Slow Moving", "Dead Stock", "Unknown", None):
                assert rat.assign_action(c, s, m) in rat.ACTION_ORDER
