import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_release_gate import REQUIRED_TRUE, build_report  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def test_committed_release_gate_fails_candidly():
    report = build_report(ROOT, ROOT / "configs" / "release_gate.json")
    assert report["release_allowed"] is False
    assert "archive_doi" in report["blockers"]
    # The computational grid is complete; retain it as a recorded true fact,
    # not as a release blocker. Every incomplete required gate must remain blocked.
    for requirement in REQUIRED_TRUE:
        if report["gate"].get(requirement) is True:
            assert requirement not in report["blockers"]
        else:
            assert requirement in report["blockers"]
    assert report["gate"]["confirmatory_training_complete"] is True
    assert "full_cell_clean_room_reproduction_complete" in report["blockers"]
    assert "human_annotation_complete" in report["blockers"]
    assert not [item for item in report["blockers"] if item.startswith("missing:")]


def test_complete_synthetic_gate_requires_matching_real_metadata(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "reproducibility").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "docs").mkdir()
    doi = "10.5281/zenodo.1234567"
    (tmp_path / "CITATION.cff").write_text(yaml.safe_dump({"doi": doi}))
    for path in (
        "requirements-research.lock", "reproducibility/inputs.lock.json",
        "results/artifact_manifest.json", "docs/DATA_RIGHTS_AND_RELEASE.md",
        "docs/ARTIFACT_REPRODUCIBILITY.md",
    ):
        (tmp_path / path).write_text("placeholder")
    gate = {name: True for name in REQUIRED_TRUE}
    gate["archive_doi"] = doi
    gate_path = tmp_path / "configs" / "release_gate.json"
    gate_path.write_text(json.dumps(gate))
    assert build_report(tmp_path, gate_path)["release_allowed"] is True
    gate["archive_doi"] = "10.5281/zenodo.7654321"
    gate_path.write_text(json.dumps(gate))
    assert "citation_doi_matches_archive" in build_report(tmp_path, gate_path)["blockers"]
