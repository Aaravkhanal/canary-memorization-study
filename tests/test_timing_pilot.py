import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from summarize_timing_pilot import summarize  # noqa: E402


def rows(seconds=30):
    return [{"pilot_label": "N", "confidence": "medium", "seconds": str(seconds)} for _ in range(80)]


def test_timing_summary_projects_amended_workload():
    result = summarize(rows())
    assert result["pilot_items"] == 80
    assert result["target_items_per_rater"] == 1920
    assert result["estimated_active_hours_at_median"] == 16
    assert result["fatigue_flag"] is False


def test_timing_summary_refuses_partial_or_unlabelled_rows():
    with pytest.raises(ValueError, match="80 rows"):
        summarize(rows()[:-1])
    invalid = rows()
    invalid[0]["pilot_label"] = ""
    with pytest.raises(ValueError, match="pilot_label"):
        summarize(invalid)
