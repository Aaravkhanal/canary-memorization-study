#!/usr/bin/env python3
"""Build one contamination-free mixed-frequency corpus for a locked confirmatory seed.

Only documents that hash to the training split *after insertion* are selected.  This matches
aarav-lm's content-hash split at the pinned dependency revision and guarantees that inserted
canaries cannot enter validation or test.  The output manifest is deterministic and records
every source story index, assigned frequency, split check, and content hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EOT = "<|endoftext|>"
VAL_FRACTION = 0.01
TEST_FRACTION = 0.01
SPLIT_SEED = 20261016


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    """Match aarav-lm data.clean.normalize_text at the pinned dependency revision."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def normalized_key(text: str) -> bytes:
    canon = re.sub(r"\s+", " ", text.casefold()).strip()
    return hashlib.blake2b(canon.encode("utf-8"), digest_size=8).digest()


def split_of(text: str, seed: int = SPLIT_SEED) -> str:
    digest = hashlib.blake2b(
        normalized_key(text), digest_size=8, salt=seed.to_bytes(8, "little", signed=False)[:8]
    ).digest()
    value = int.from_bytes(digest, "little") / 2**64
    if value < TEST_FRACTION:
        return "test"
    if value < TEST_FRACTION + VAL_FRACTION:
        return "val"
    return "train"


def load_stories(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [normalize_text(story) for story in text.split(EOT) if normalize_text(story)]


def insert_canary(story: str, row: dict) -> str:
    if row["type"] == "character":
        return f'{row["text"]}. {story}'
    parts = re.split(r"(?<=[.!?])\s+", story)
    if len(parts) < 2:
        return f'{story} And {row["text"]}.'
    midpoint = len(parts) // 2
    parts[midpoint] = parts[midpoint].rstrip(".!? ") + f', and {row["text"]}.'
    return " ".join(parts)


def build_corpus(stories: list[str], bank: dict, seed: int, split_seed: int = SPLIT_SEED) -> tuple[list[str], dict]:
    schedule = bank["frequency_schedule"][str(seed)]
    rows = {row["id"]: row for row in bank["canaries"]}
    if set(schedule) != set(rows):
        raise ValueError("frequency schedule and canary bank IDs differ")

    rng = random.Random(seed)
    candidate_indices = list(range(len(stories)))
    rng.shuffle(candidate_indices)
    cursor = 0
    used: set[int] = set()
    output = list(stories)
    assignments: dict[str, list[int]] = {}

    # Stable bank order is part of the registered assignment algorithm.
    for canary_id in [row["id"] for row in bank["canaries"]]:
        row = rows[canary_id]
        target = int(schedule[canary_id])
        chosen: list[int] = []
        while len(chosen) < target:
            if cursor >= len(candidate_indices):
                raise ValueError("base corpus exhausted while finding train-split insertion stories")
            index = candidate_indices[cursor]
            cursor += 1
            if index in used:
                continue
            inserted = normalize_text(insert_canary(stories[index], row))
            if split_of(inserted, split_seed) != "train":
                continue
            output[index] = inserted
            used.add(index)
            chosen.append(index)
        assignments[canary_id] = chosen

    for canary_id, indices in assignments.items():
        expected = int(schedule[canary_id])
        if len(indices) != expected:
            raise AssertionError(f"{canary_id}: expected {expected}, assigned {len(indices)}")
        if any(split_of(output[index], split_seed) != "train" for index in indices):
            raise AssertionError(f"{canary_id}: insertion escaped training split")
        actual = sum(output[index].casefold().count(rows[canary_id]["identity"].casefold()) for index in indices)
        if actual != expected:
            raise AssertionError(f"{canary_id}: expected {expected} inserted identities, found {actual}")

    split_counts = {name: 0 for name in ("train", "val", "test")}
    for story in output:
        split_counts[split_of(story, split_seed)] += 1
    return output, {
        "assignment_seed": seed,
        "split_seed": split_seed,
        "val_fraction": VAL_FRACTION,
        "test_fraction": TEST_FRACTION,
        "frequency_schedule": schedule,
        "used_story_indices": assignments,
        "total_insertions": sum(map(len, assignments.values())),
        "split_document_counts": split_counts,
        "all_insertions_in_train": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=ROOT / "configs" / "confirmatory" / "canary_bank.json")
    parser.add_argument("--base", type=Path, default=ROOT / "data" / "raw" / "base.txt")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--split-seed", type=int, default=SPLIT_SEED)
    parser.add_argument("--out-root", type=Path, default=ROOT / "data" / "confirmatory")
    parser.add_argument("--check", action="store_true", help="verify an existing corpus/manifest without rewriting")
    args = parser.parse_args()

    bank = json.loads(args.bank.read_text(encoding="utf-8"))
    if args.seed not in bank["seeds"]:
        raise SystemExit(f"seed {args.seed} is not in the locked bank")
    stories = load_stories(args.base)
    output, details = build_corpus(stories, bank, args.seed, args.split_seed)
    corpus_text = (f"\n{EOT}\n").join(output) + f"\n{EOT}\n"
    corpus_sha = hashlib.sha256(corpus_text.encode("utf-8")).hexdigest()
    manifest = {
        "schema_version": 1,
        "status": "pre-outcome confirmatory corpus lock",
        "base_corpus": {
            "path": "data/raw/base.txt",
            "size_bytes": args.base.stat().st_size,
            "sha256": sha256_file(args.base),
            "documents": len(stories),
        },
        "bank_content_sha256": bank["content_sha256"],
        **details,
        "corpus": {"path": f"data/confirmatory/seed_{args.seed}/corpus.txt", "sha256": corpus_sha},
    }
    out_dir = args.out_root / f"seed_{args.seed}"
    corpus_path = out_dir / "corpus.txt"
    manifest_path = out_dir / "manifest.json"
    expected_manifest = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.check:
        problems = []
        if not corpus_path.exists() or sha256_file(corpus_path) != corpus_sha:
            problems.append("corpus missing or content hash differs")
        if not manifest_path.exists() or manifest_path.read_text(encoding="utf-8") != expected_manifest:
            problems.append("manifest missing or differs from deterministic rebuild")
        if problems:
            raise SystemExit("FAILED: " + "; ".join(problems))
        print(f"PASSED: seed {args.seed} corpus is deterministic, locked, and train-only ({corpus_sha})")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    manifest_path.write_text(expected_manifest, encoding="utf-8")
    print(f"[wrote] {corpus_path} ({len(corpus_text):,} bytes; {details['total_insertions']:,} insertions)")
    print(f"[wrote] {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
