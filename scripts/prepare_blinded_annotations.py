#!/usr/bin/env python3
"""Create deterministic, condition-blinded V/T/N annotation batches.

The annotator files intentionally omit architecture, frequency, automated overlap scores, and checkpoint paths.
The private manifest restores those fields only after labels are locked. By default, two completions are sampled
from each of 32 (canary, setting) groups in every treatment cell: 64 judgments per cell, balanced across every
canary and setting rather than a convenience sample.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^novelty_(?P<variant>.+)_freq(?P<freq>\d+)\.json$")
DEFAULT_FREQUENCIES = {1, 10, 50, 100, 500}


def stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def discover_primary_results(results_dir: Path, frequencies: set[int]) -> list[tuple[str, int, Path]]:
    found = []
    for path in sorted(results_dir.glob("novelty_*.json")):
        match = NAME_RE.match(path.name)
        if match and int(match.group("freq")) in frequencies:
            found.append((match.group("variant"), int(match.group("freq")), path))
    return found


def build_records(results_dir: Path, frequencies: set[int], per_group: int, seed: int) -> list[dict]:
    records = []
    for variant, frequency, path in discover_primary_results(results_dir, frequencies):
        result = json.loads(path.read_text(encoding="utf-8"))
        for group in result["groups"]:
            completions = group["completions"]
            if per_group > len(completions):
                raise ValueError(f"{path.name}: requested {per_group} samples from a group with {len(completions)}")
            key = f"{seed}|{variant}|{frequency}|{group['canary_id']}|{group['setting']}"
            chosen = random.Random(stable_int(key)).sample(range(len(completions)), per_group)
            for completion_index in sorted(chosen):
                completion = completions[completion_index]
                identity = (
                    f"{variant}|{frequency}|{group['canary_id']}|{group['setting']}|"
                    f"{completion_index}|{completion['text']}"
                )
                records.append({
                    "sample_id": "s_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
                    "variant": variant,
                    "frequency": frequency,
                    "canary_id": group["canary_id"],
                    "canary_type": group["type"],
                    "setting": group["setting"],
                    "completion_index": completion_index,
                    "prompt": group["prompt"],
                    "generation": completion["text"],
                    "max_ngram_overlap": completion["max_ngram_overlap"],
                    "min_edit_distance": completion["min_edit_distance"],
                    "source_file": path.name,
                })
    ids = [record["sample_id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("sample-id collision")
    return records


def has_locked_labels(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open(encoding="utf-8", newline="") as handle:
        return any(row.get("label", "").strip() for row in csv.DictReader(handle))


def write_batches(records: list[dict], out_dir: Path, annotators: list[str], seed: int, force: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "private_manifest.json"
    target_paths = [out_dir / f"{annotator}.csv" for annotator in annotators]
    protected = [path for path in target_paths if has_locked_labels(path)]
    if protected and not force:
        raise FileExistsError(f"refusing to overwrite locked labels: {', '.join(map(str, protected))}")

    manifest = {
        "schema_version": 1,
        "seed": seed,
        "annotation_labels": ["V", "T", "N"],
        "blinded_fields": ["variant", "frequency", "max_ngram_overlap", "min_edit_distance", "source_file"],
        "records": records,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    fields = ["sample_id", "prompt", "generation", "label", "confidence", "notes"]
    for index, (annotator, path) in enumerate(zip(annotators, target_paths)):
        ordered = list(records)
        random.Random(seed + index).shuffle(ordered)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for record in ordered:
                writer.writerow({
                    "sample_id": record["sample_id"],
                    "prompt": record["prompt"],
                    "generation": record["generation"],
                    "label": "",
                    "confidence": "",
                    "notes": "",
                })
        print(f"[wrote] {path} ({len(ordered)} blinded samples for {annotator})")
    print(f"[private] {manifest_path} (do not inspect while labelling)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "annotations")
    parser.add_argument("--frequencies", default="1,10,50,100,500")
    parser.add_argument("--samples-per-group", type=int, default=2)
    parser.add_argument("--annotators", default="rater_a,rater_b")
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--force", action="store_true", help="overwrite batches even if they contain labels")
    args = parser.parse_args()

    frequencies = {int(value) for value in args.frequencies.split(",")}
    annotators = [value.strip() for value in args.annotators.split(",") if value.strip()]
    records = build_records(args.results_dir, frequencies, args.samples_per_group, args.seed)
    if not records:
        raise SystemExit("no primary novelty results found")
    write_batches(records, args.out_dir, annotators, args.seed, args.force)


if __name__ == "__main__":
    main()
