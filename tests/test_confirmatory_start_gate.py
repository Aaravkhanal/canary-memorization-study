import json
import sys
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_confirmatory_start_gate import check_configs, probe_storage  # noqa: E402
from run_confirmatory_queue import (  # noqa: E402
    active_training_processes, finalize_cell, pruned_reproduction_complete,
    prune_verified_reproduction_checkpoints, runtime_path_overrides, training_pause, validate_evaluation,
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


def test_process_detection_returns_strings(monkeypatch):
    monkeypatch.setattr(
        "run_confirmatory_queue.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(stdout="123 python train.py\n456 unrelated\n"),
    )
    assert all(isinstance(item, str) for item in active_training_processes())


def test_owner_training_pause_is_active():
    pause = training_pause()
    assert pause["paused"] is False
    assert pause["scope"].startswith("all additional canary-study model training")


def test_runtime_overrides_bridge_portable_configs_to_aarav_lm_resolver():
    root = Path(__file__).resolve().parents[1]
    overrides = runtime_path_overrides(root, 20261016)
    assert overrides == [
        f"data.sources=[{root / 'data/confirmatory/seed_20261016/corpus.txt'}]",
        f"data.out_dir={root / 'data/confirmatory/seed_20261016/tokenized'}",
        f"tokenizer.artifact_dir={root / 'artifacts/tokenizer_tinystories_v2'}",
    ]
    assert (root / "data/confirmatory/seed_20261016/corpus.txt").is_file()


def test_reproduction_checkpoint_pruning_requires_and_preserves_evidence(tmp_path, monkeypatch):
    run_dir = tmp_path / "exp_001_reproduction"
    checkpoints = run_dir / "checkpoints"
    checkpoints.mkdir(parents=True)
    (checkpoints / "best.pt").write_bytes(b"best-checkpoint")
    (checkpoints / "final.pt").write_bytes(b"final-checkpoint")
    (run_dir / "summary.json").write_text(json.dumps({"status": "completed", "steps": 6000}))
    (run_dir / "cell_verification.json").write_text(json.dumps({"evaluation_complete": True}))
    monkeypatch.setattr("run_confirmatory_queue.load_checkpoint", lambda path: {"model": {}})
    evaluation = {
        "path": "evaluated.json", "sha256": "abc", "exposure_rows": 48, "groups": 160, "completions": 320,
    }
    record = prune_verified_reproduction_checkpoints(run_dir, evaluation)
    assert record["removed"] is True
    assert set(record["checkpoint_evidence"]) == {"best.pt", "final.pt"}
    assert not (checkpoints / "best.pt").exists()
    assert not (checkpoints / "final.pt").exists()
    evaluated = tmp_path / "evaluated.json"
    evaluated.write_text("{}")
    assert pruned_reproduction_complete(run_dir, evaluated) is True


def test_precheckpoint_interruption_is_preserved_by_new_experiment_policy():
    source = (Path(__file__).resolve().parents[1] / "scripts/run_confirmatory_queue.py").read_text()
    assert "Preserve a pre-checkpoint interruption as an audit artifact" in source
    assert '"--exp-root", str(cell_root), *runtime_path_overrides(root, seed)' in source


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
