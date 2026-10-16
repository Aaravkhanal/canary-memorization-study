import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_storage_capacity import allocated_bytes, build_report  # noqa: E402


def test_allocated_bytes_ignores_symlinks_and_counts_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.bin").write_bytes(b"x" * 8192)
    (source / "link").symlink_to(source / "payload.bin")
    assert allocated_bytes(source) >= 8192
    assert allocated_bytes(source / "link") == 0


def test_capacity_report_is_read_only_and_can_fail_threshold(tmp_path):
    artifact = tmp_path / "artifacts"
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "data").write_bytes(b"1234")
    report = build_report(artifact, 10**30, (candidate,))
    assert report["read_only_audit"] is True
    assert report["capacity_ok"] is False
    assert report["action_taken"] == "none"
    assert report["paths"][0]["allocated_bytes"] > 0
