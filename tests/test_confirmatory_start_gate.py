import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_confirmatory_start_gate import check_configs, probe_storage  # noqa: E402
from run_confirmatory_queue import (  # noqa: E402
    active_training_processes, finalize_cell, runtime_path_overrides, validate_evaluation,
)


def test_storage_probe_checks_capacity_and_io(tmp_path):
    report = probe_storage(tmp_path, 1)
    assert report["write_read_fsync_rename_ok"] is True
    assert report["capacity_ok"] is True
    assert report["ok"] is True
    assert not list(tmp_path.glob(".confirmatory-probe-*"))


def test_storage_probe_can_fail_capacity_without_writing_artifacts(tmp_path):
    report = probe_storage(tmp_path, 10**30)
    assert report["write_read_fsync_rename_ok"] is True
    assert report["capacity_ok"] is False
    assert report["ok"] is False


def test_all_24_training_configs_exist():
    root = Path(__file__).resolve().parents[1]
    report = check_configs(root)
    assert report == {"expected_count": 24, "actual_count": 24, "missing": [], "ok": True}


def test_selected_external_design_remains_blocked_without_clearance():
    root = Path(__file__).resolve().parents[1]
    record = json.loads((root / "configs/confirmatory/ethics_record.json").read_text())
    assert record["annotation_mode"] == "external_raters"
    assert record["owner_decision_recorded"] is True
    assert record["institutional_determination"] == "not_recorded"
    assert record["training_start_clearance"] is True
    assert record["annotation_start_clearance"] is False


def test_process_detection_returns_strings():
    assert all(isinstance(item, str) for item in active_training_processes())


def test_runtime_overrides_bridge_portable_configs_to_aarav_lm_resolver():
    root = Path(__file__).resolve().parents[1]
    overrides = runtime_path_overrides(root, 20261016)
    assert overrides == [
        f"data.sources=[{root / 'data/confirmatory/seed_20261016/corpus.txt'}]",
        f"data.out_dir={root / 'data/confirmatory/seed_20261016/tokenized'}",
        f"tokenizer.artifact_dir={root / 'artifacts/tokenizer_tinystories_v2'}",
    ]
    assert (root / "data/confirmatory/seed_20261016/corpus.txt").is_file()


def test_evaluation_validation_requires_complete_fixed_shape(tmp_path):
    path = tmp_path / "evaluated.json"
    payload = {
        "provenance": {"checkpoint_sha256": "checkpoint", "corpus_sha256": "corpus"},
        "exposure_rows": [{} for _ in range(48)],
        "novelty_groups": [{"completions": [{}, {}]} for _ in range(160)],
        "full_training_corpus_overlap_complete": True,
        "human_annotation_complete": False,
        "full_corpus_overlap": {"scope": "training_split", "corpus_sha256": "corpus"},
    }
    path.write_text(json.dumps(payload))
    result = validate_evaluation(path, "checkpoint", "corpus")
    assert result["exposure_rows"] == 48 and result["completions"] == 320
    payload["human_annotation_complete"] = True
    path.write_text(json.dumps(payload))
    import pytest
    with pytest.raises(ValueError, match="human annotation"):
        validate_evaluation(path, "checkpoint", "corpus")


def test_finalize_deletes_only_rolling_checkpoints_after_evaluation(tmp_path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    for name in ("best.pt", "final.pt", "step_00000500.pt", "step_00001000.pt"):
        (checkpoints / name).write_bytes(b"x")
    (tmp_path / "cell_verification.json").write_text(json.dumps({
        "evaluation_complete": False, "rolling_checkpoints_deleted": False,
    }))
    finalize_cell(tmp_path, {"sha256": "result"})
    report = json.loads((tmp_path / "cell_verification.json").read_text())
    assert report["evaluation_complete"] is True
    assert report["rolling_checkpoints_deleted"] is True
    assert (checkpoints / "best.pt").exists() and (checkpoints / "final.pt").exists()
    assert not list(checkpoints.glob("step_*.pt"))
