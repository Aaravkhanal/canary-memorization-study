#!/usr/bin/env python3
"""Validate the confirmatory annotation ethics/consent record without granting a determination."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "configs" / "confirmatory" / "ethics_record.json"
EXTERNAL_DETERMINATIONS = {"approved", "exempt", "not_human_subjects_research"}


def validate_record(record: dict) -> dict:
    mode = record.get("annotation_mode")
    problems: list[str] = []
    if mode not in {"self_only", "external_raters"}:
        problems.append("annotation_mode must be owner-selected as self_only or external_raters")
    if record.get("owner_decision_recorded") is not True:
        problems.append("owner decision is not recorded")
    if mode == "self_only":
        if record.get("external_raters_planned") is not False:
            problems.append("self_only mode must set external_raters_planned=false")
        if record.get("institutional_determination") != "not_applicable_no_external_participants":
            problems.append("self_only mode must record why external-rater determination is not applicable")
        if record.get("consent_materials_status") != "not_applicable_self_only":
            problems.append("self_only mode must mark external consent materials not applicable")
    elif mode == "external_raters":
        if record.get("external_raters_planned") is not True:
            problems.append("external_raters mode must set external_raters_planned=true")
        if record.get("institutional_determination") not in EXTERNAL_DETERMINATIONS:
            problems.append("external-rater institutional determination is unresolved")
        for field in ("determination_authority", "determination_reference", "determination_date"):
            if not str(record.get(field, "")).strip():
                problems.append(f"external-rater record lacks {field}")
        if record.get("consent_materials_status") != "finalized":
            problems.append("external-rater information/consent materials are not finalized")
        if str(record.get("compensation_plan", "")).strip() in {"", "unresolved"}:
            problems.append("external-rater compensation plan is unresolved")
        if str(record.get("withdrawal_process", "")).strip() in {"", "unresolved"}:
            problems.append("external-rater withdrawal process is unresolved")
    if record.get("training_start_clearance") is not True:
        problems.append("training_start_clearance is false")
    if record.get("annotation_start_clearance") is not True:
        problems.append("annotation_start_clearance is false")
    return {"mode": mode, "problems": problems, "ok": not problems}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    args = parser.parse_args()
    report = validate_record(json.loads(args.record.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
