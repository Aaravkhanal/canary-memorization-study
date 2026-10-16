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
