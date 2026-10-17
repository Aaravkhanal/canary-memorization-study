import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_ethics_record import validate_record  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def test_committed_external_plus_self_design_allows_training_but_blocks_annotation():
    record = json.loads((ROOT / "configs/confirmatory/ethics_record.json").read_text())
    report = validate_record(record)
    assert report["ok"] is False
    assert report["training_ok"] is True
    assert report["annotation_ok"] is False
    assert record["annotation_mode"] == "external_raters"
    assert record["owner_decision_recorded"] is True
    assert record["external_raters_planned"] is True
    assert record["institutional_determination"] == "not_recorded"
    assert record["self_annotation_design"].startswith("separate condition-hidden")
    assert record["training_start_clearance"] is True


def test_complete_external_record_requires_evidence_fields():
    record = {
        "annotation_mode": "external_raters", "owner_decision_recorded": True,
        "external_raters_planned": True, "institutional_determination": "exempt",
        "determination_authority": "Example authority", "determination_reference": "EX-123",
        "determination_date": "2026-10-17", "consent_materials_status": "finalized",
        "compensation_plan": "Fixed amount per completed batch", "withdrawal_process": "Contact before lock",
        "training_start_clearance": True, "annotation_start_clearance": True,
    }
    assert validate_record(record)["ok"] is True
    record["determination_reference"] = ""
    assert validate_record(record)["ok"] is False


def test_self_only_record_is_consistent_but_changes_registered_endpoint():
    record = {
        "annotation_mode": "self_only", "owner_decision_recorded": True,
        "external_raters_planned": False,
        "institutional_determination": "not_applicable_no_external_participants",
        "consent_materials_status": "not_applicable_self_only",
        "training_start_clearance": True, "annotation_start_clearance": True,
    }
    assert validate_record(record)["ok"] is True
