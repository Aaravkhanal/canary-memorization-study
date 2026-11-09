#!/usr/bin/env python3
"""Create the amended 1,920-item rater sheets and an 80-item blinded timing pilot.

Selection uses condition identifiers and a private keyed hash only. It never reads generation text or automated
outcomes while deciding which sample IDs to retain. Public text is joined only after IDs are frozen.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FIELDS = ("sample_id", "prompt", "generation", "label", "confidence", "notes")
PILOT_FIELDS = ("sample_id", "prompt", "generation", "pilot_label", "confidence", "seconds", "notes")


def keyed_score(secret: bytes, namespace: str, *parts: object) -> bytes:
    payload = "|".join((namespace, *(str(part) for part in parts))).encode("utf-8")
    return hashlib.blake2b(payload, key=secret, digest_size=16).digest()


def read_public(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if rows and tuple(rows[0]) != PUBLIC_FIELDS:
        raise ValueError(f"unexpected public columns: {path}")
    if any(row["label"] or row["confidence"] or row["notes"] for row in rows):
        raise ValueError(f"source sheet already contains labels: {path}")
    return {row["sample_id"]: row for row in rows}


def select_ids(items: list[dict], secret: bytes) -> tuple[list[str], list[dict]]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for item in items:
        key = (item["scale"], item["architecture"], int(item["training_seed"]), item["canary_id"])
        groups[key].append(item)
    if len(groups) != 960:
        raise ValueError(f"expected 960 cell-canary groups, found {len(groups)}")

    selected = []
    for key, candidates in sorted(groups.items()):
        by_setting: dict[str, list[dict]] = defaultdict(list)
        for item in candidates:
            by_setting[item["setting"]].append(item)
        if len(by_setting) != 4 or any(len(rows) != 2 for rows in by_setting.values()):
            raise ValueError(f"expected 4 settings x 2 completions for {key}")
        settings = sorted(by_setting, key=lambda setting: keyed_score(secret, "setting", *key, setting))[:2]
        for setting in settings:
            chosen = min(by_setting[setting], key=lambda item: keyed_score(
                secret, "completion", *key, setting, int(item["completion_index"])
            ))
            selected.append(chosen)

    ids = [item["sample_id"] for item in selected]
    if len(ids) != 1920 or len(set(ids)) != 1920:
        raise ValueError("amended selection must contain 1,920 unique sample IDs")
    return ids, selected


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-source", type=Path,
                        default=ROOT / "results/annotations/confirmatory_private_manifest.json")
    parser.add_argument("--public-source", type=Path,
                        default=ROOT / "results/confirmatory/annotation/external_rater_A.csv")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "results/confirmatory/annotation_amended")
    parser.add_argument("--private-out", type=Path,
                        default=ROOT / "results/annotations/confirmatory_subsample_private_manifest.json")
    args = parser.parse_args()

    private = json.loads(args.private_source.read_text(encoding="utf-8"))
    secret = bytes.fromhex(private["secret_hex"])
    public = read_public(args.public_source)
    selected_ids, selected_private = select_ids(private["items"], secret)
    if set(selected_ids) - set(public):
        raise ValueError("selected sample IDs are missing from the public source sheet")

    public_rows = [{field: public[sample_id][field] for field in PUBLIC_FIELDS} for sample_id in selected_ids]
    for index, filename in enumerate(("external_rater_A.csv", "external_rater_B.csv")):
        rows = list(public_rows)
        random.Random(int.from_bytes(keyed_score(secret, "shuffle", index), "little")).shuffle(rows)
        write_csv(args.out_dir / filename, PUBLIC_FIELDS, rows)

    pilot_ids = sorted(selected_ids, key=lambda sample_id: keyed_score(secret, "timing-pilot", sample_id))[:80]
    pilot_rows = [{
        "sample_id": sample_id,
        "prompt": public[sample_id]["prompt"],
        "generation": public[sample_id]["generation"],
        "pilot_label": "", "confidence": "", "seconds": "", "notes": "",
    } for sample_id in pilot_ids]
    write_csv(args.out_dir / "timing_pilot_80.csv", PILOT_FIELDS, pilot_rows)

    setting_counts = Counter(item["setting"] for item in selected_private)
    type_counts = Counter(item["canary_type"] for item in selected_private)
    private_payload = {
        "schema_version": 1,
        "warning": "PRIVATE CONDITION KEY: do not publish or send to raters",
        "selection_rule": "two settings and one completion per setting for every cell-canary group; keyed hash only",
        "selected_items": selected_private,
        "timing_pilot_ids": pilot_ids,
    }
    args.private_out.write_text(json.dumps(private_payload, indent=2) + "\n", encoding="utf-8")
    summary = {
        "schema_version": 1, "ratings_per_rater": len(public_rows), "timing_pilot_items": len(pilot_rows),
        "cell_canary_groups": 960, "ratings_per_cell_canary": 2,
        "canary_type_counts": dict(sorted(type_counts.items())),
        "setting_counts": dict(sorted(setting_counts.items())),
        "selection_used_generation_text_or_scores": False,
    }
    (args.out_dir / "sampling_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
