import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_reproducibility import ROOT, check_locked_file, sha256_file  # noqa: E402


def test_sha256_and_locked_file_validation(tmp_path):
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"confirmatory input\n")
    expected = hashlib.sha256(b"confirmatory input\n").hexdigest()
    assert sha256_file(artifact) == expected
    valid = check_locked_file(artifact, expected, artifact.stat().st_size)
    assert valid["ok"] is True
    assert check_locked_file(artifact, "0" * 64)["ok"] is False
    assert check_locked_file(tmp_path / "missing", expected)["ok"] is False


def test_packaged_tokenizer_matches_input_lock():
    import json

    lock = json.loads((ROOT / "reproducibility" / "inputs.lock.json").read_text())
    tokenizer_dir = ROOT / "artifacts" / "tokenizer_tinystories_v2"
    for name, digest in lock["tokenizer_files"].items():
        assert check_locked_file(tokenizer_dir / name, digest)["ok"] is True
