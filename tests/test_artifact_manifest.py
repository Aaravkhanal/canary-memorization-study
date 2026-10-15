import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from create_artifact_manifest import build_manifest  # noqa: E402


def test_manifest_hashes_indexed_files_and_excludes_its_own_output(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    source = tmp_path / "evidence.txt"
    source.write_text("versioned evidence\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "evidence.txt"], check=True, capture_output=True)

    output = tmp_path / "artifact_manifest.json"
    manifest = build_manifest(tmp_path, output)
    assert manifest["files"] == [{
        "path": "evidence.txt",
        "size_bytes": 19,
        "sha256": "2ba4967f2fba09ff075ca5fa679756ae8152763e818fa9a63502d014fb78cc08",
    }]
    output.write_text(json.dumps(manifest), encoding="utf-8")
    rebuilt = build_manifest(tmp_path, output)
    assert len(rebuilt["files"]) == 1
