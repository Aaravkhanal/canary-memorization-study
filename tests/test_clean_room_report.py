import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_clean_room_report_is_explicitly_non_scientific_and_complete():
    report = json.loads((ROOT / "results" / "clean_room_smoke.json").read_text())
    assert report["status"] == "passed"
    assert report["training_smoke"]["steps"] == 1
    assert report["training_smoke"]["device"] == "cpu"
    assert report["training_smoke"]["scientific_outcome"] is False
    assert report["training_smoke"]["source"].startswith("unmodified")
    assert all(value == "passed" for value in report["checks"].values())
    assert report["deviations_and_failures"]
    rerun = report["verification_runs"][-1]
    assert len(rerun["study_commit"]) == 40
    assert all(char in "0123456789abcdef" for char in rerun["study_commit"])
    assert rerun["aarav_lm_commit"] == report["aarav_lm_commit"]
    assert all(value == "passed" for value in rerun["checks"].values())
    assert rerun["training_smoke"]["scientific_outcome"] is False
