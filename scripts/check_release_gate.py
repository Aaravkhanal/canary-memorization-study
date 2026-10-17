#!/usr/bin/env python3
"""Report publication-artifact release blockers without creating or authorizing a release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GATE = ROOT / "configs" / "release_gate.json"
REQUIRED_TRUE = (
    "release_authorized",
    "project_license_selected",
    "derived_data_and_weights_terms_confirmed",
    "permanent_archive_created",
    "full_cell_clean_room_reproduction_complete",
    "human_annotation_complete",
    "confirmatory_training_complete",
)


def build_report(root: Path, gate_path: Path) -> dict:
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    citation = yaml.safe_load((root / "CITATION.cff").read_text(encoding="utf-8"))
    blockers = [name for name in REQUIRED_TRUE if gate.get(name) is not True]
    doi = str(gate.get("archive_doi", "")).strip()
    if not doi:
        blockers.append("archive_doi")
    elif citation.get("doi") != doi:
        blockers.append("citation_doi_matches_archive")
    required_files = (
        "CITATION.cff", "requirements-research.lock", "reproducibility/inputs.lock.json",
        "results/artifact_manifest.json", "docs/DATA_RIGHTS_AND_RELEASE.md",
        "docs/ARTIFACT_REPRODUCIBILITY.md",
    )
    missing = [path for path in required_files if not (root / path).is_file()]
    blockers.extend(f"missing:{path}" for path in missing)
    return {
        "schema_version": 1,
        "release_allowed": not blockers,
        "blockers": blockers,
        "required_files": {path: (root / path).is_file() for path in required_files},
        "gate": gate,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    gate_path = args.gate if args.gate.is_absolute() else root / args.gate
    report = build_report(root, gate_path)
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["release_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
