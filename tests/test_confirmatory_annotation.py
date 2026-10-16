import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_confirmatory_annotation import build_rows, validate_blank_sheet, write_csv  # noqa: E402


def fake_cell(path: Path, architecture: str, seed: int):
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "cell": {"scale": "14m", "architecture": architecture, "training_seed": seed},
        "exposure_rows": [{"canary_id": "canary", "frequency": 10}],
        "novelty_groups": [{
            "canary_id": "canary", "canary_type": "character", "setting": "the moon", "prompt": "prompt",
            "completions": [{
                "completion_index": 0, "generation_seed": 7, "text": "generated story",
                "status": "pending_human_compliance_review",
            }],
        }],
        "full_training_corpus_overlap_complete": True,
        "human_annotation_complete": False,
    }))


def test_blinded_rows_hide_conditions_and_leave_labels_blank(tmp_path):
    first = tmp_path / "a" / "evaluated.json"
    second = tmp_path / "b" / "evaluated.json"
    fake_cell(first, "baseline", 20261016)
    fake_cell(second, "mha", 20261017)
    public, private = build_rows([first, second], b"fixed-test-secret")
    assert len(public) == len(private) == 2
    assert set(public[0]) == {"sample_id", "prompt", "generation", "label", "confidence", "notes"}
    assert public[0]["label"] == public[0]["confidence"] == public[0]["notes"] == ""
    assert "architecture" not in public[0] and "frequency" not in public[0]
    assert {row["architecture"] for row in private} == {"baseline", "mha"}


def test_written_sheet_validation_rejects_filled_labels(tmp_path):
    path = tmp_path / "rater.csv"
    rows = [{"sample_id": "C1", "prompt": "p", "generation": "g", "label": "",
             "confidence": "", "notes": ""}]
    write_csv(path, rows)
    validate_blank_sheet(path, 1)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerow({**rows[0], "label": "N"})
    import pytest
    with pytest.raises(ValueError, match="nonblank"):
        validate_blank_sheet(path, 1)
