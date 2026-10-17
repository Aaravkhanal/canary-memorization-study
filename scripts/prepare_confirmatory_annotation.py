#!/usr/bin/env python3
"""Create external-rater and self-sensitivity confirmatory sheets with labels left blank.

Run only after all 24 evaluated cell JSONs exist. The private condition key is git-ignored and must not be sent to
raters. This script prepares annotation; it never supplies, predicts, or imputes a human label.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FIELDS = ("sample_id", "prompt", "generation", "label", "confidence", "notes")
ANNOTATION_SHEETS = ("external_rater_A.csv", "external_rater_B.csv", "self_sensitivity.csv")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_rows(paths: list[Path], secret: bytes) -> tuple[list[dict], list[dict]]:
    public = []
    private = []
    seen_cells = set()
    for path in sorted(paths):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("full_training_corpus_overlap_complete") is not True:
            raise ValueError(f"cell lacks required full-training-split overlap: {path}")
        if payload.get("human_annotation_complete") is not False:
            raise ValueError(f"cell incorrectly claims annotation completion: {path}")
        cell = payload["cell"]
        cell_key = (cell["scale"], cell["architecture"], int(cell["training_seed"]))
        if cell_key in seen_cells:
            raise ValueError(f"duplicate cell: {cell_key}")
        seen_cells.add(cell_key)
        frequency = {row["canary_id"]: row["frequency"] for row in payload["exposure_rows"]}
        for group in payload["novelty_groups"]:
            for completion in group["completions"]:
                source_key = "|".join(map(str, (
                    *cell_key, group["canary_id"], group["setting"], completion["completion_index"],
                )))
                sample_id = "C" + hashlib.blake2b(
                    source_key.encode("utf-8"), key=secret, digest_size=8
                ).hexdigest().upper()
                public.append({
                    "sample_id": sample_id, "prompt": group["prompt"], "generation": completion["text"],
                    "label": "", "confidence": "", "notes": "",
                })
                private.append({
                    "sample_id": sample_id, "source_path": str(path), "source_sha256": sha256_file(path),
                    "scale": cell["scale"], "architecture": cell["architecture"],
                    "training_seed": int(cell["training_seed"]), "canary_id": group["canary_id"],
                    "canary_type": group["canary_type"], "frequency": frequency[group["canary_id"]],
                    "setting": group["setting"], "completion_index": completion["completion_index"],
                    "generation_seed": completion["generation_seed"], "generation_status": completion["status"],
                })
    if len({row["sample_id"] for row in public}) != len(public):
        raise ValueError("sample ID collision")
    return public, private


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PUBLIC_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def validate_blank_sheet(path: Path, expected_rows: int) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != expected_rows:
        raise ValueError(f"{path} has {len(rows)} rows; expected {expected_rows}")
    if rows and tuple(rows[0]) != PUBLIC_FIELDS:
        raise ValueError(f"{path} has unexpected columns")
    for row in rows:
        if row["label"] or row["confidence"] or row["notes"]:
            raise ValueError(f"{path} contains nonblank annotation fields")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results" / "confirmatory")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "confirmatory" / "annotation")
    parser.add_argument("--private-key", type=Path,
                        default=ROOT / "results" / "annotations" / "confirmatory_private_manifest.json")
    args = parser.parse_args()
    paths = sorted(args.results_root.glob("*/*/seed_*/evaluated.json"))
    if len(paths) != 24:
        raise SystemExit(f"refusing partial annotation batch: found {len(paths)} evaluated cells, expected 24")
    if args.private_key.exists():
        raise SystemExit(f"private key already exists; refusing to overwrite: {args.private_key}")
    secret = os.urandom(32)
    public, private = build_rows(paths, secret)
    if len(public) != 7680:
        raise SystemExit(f"wrong confirmatory sample count: {len(public)} != 7680")
    args.private_key.parent.mkdir(parents=True, exist_ok=True)
    args.private_key.write_text(json.dumps({
        "schema_version": 1, "secret_hex": secret.hex(), "items": private,
        "warning": "PRIVATE CONDITION KEY: do not publish or send to raters"
    }, indent=2) + "\n", encoding="utf-8")
    for rater_index, name in enumerate(ANNOTATION_SHEETS):
        rows = list(public)
        random.Random(int.from_bytes(hashlib.blake2b(secret + bytes([rater_index]), digest_size=8).digest(), "little")).shuffle(rows)
        path = args.out_dir / name
        write_csv(path, rows)
        validate_blank_sheet(path, len(public))
        print(f"[wrote] {path}: {len(rows)} condition-hidden rows; labels blank")
    print(f"[private] {args.private_key}: keep outside public artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
