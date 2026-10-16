import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_confirmatory_start_gate import check_configs, probe_storage  # noqa: E402
from run_confirmatory_queue import active_training_processes  # noqa: E402


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


def test_unresolved_ethics_record_is_an_explicit_blocker():
    root = Path(__file__).resolve().parents[1]
    record = json.loads((root / "configs/confirmatory/ethics_record.json").read_text())
    assert record["annotation_mode"] == "unresolved"
    assert record["training_start_clearance"] is False


def test_process_detection_returns_strings():
    assert all(isinstance(item, str) for item in active_training_processes())
