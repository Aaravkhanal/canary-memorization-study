import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_timing_pilot_ui import build  # noqa: E402


def test_timing_ui_is_blinded_and_requires_80_items():
    rows = [{"sample_id": f"S{i}", "prompt": "prompt", "generation": "generation"} for i in range(80)]
    page = build(rows)
    assert "architecture" not in page
    assert "frequency" not in page
    assert "Active time" in page
    assert "05:00" in page
    assert "timing_pilot_80_completed.csv" in page
