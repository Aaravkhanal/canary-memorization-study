import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_seed_sensitivity import paired_lift_row  # noqa: E402


def test_paired_lift_delta_subtracts_each_seeds_own_zero_control():
    row = paired_lift_row(
        100,
        "char_nira",
        {"char_nira": 3.0},
        {"char_nira": 2.5},
        {"char_nira": 1.0},
        {"char_nira": 0.25},
    )
    assert row["lift_seed20260927"] == 2.0
    assert row["lift_seed1338"] == 2.25
    assert row["delta_seed1338_minus_seed20260927"] == 0.25
