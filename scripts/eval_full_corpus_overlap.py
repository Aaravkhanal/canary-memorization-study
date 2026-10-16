#!/usr/bin/env python3
"""Enrich novelty results with exact overlap against the complete training corpus.

The original novelty evaluator compares each completion with the stories into which
its canary was inserted.  That is useful diagnostically, but it cannot establish
that a completion is novel relative to every other training story.  This script
closes that gap without regenerating model outputs.

It builds a reusable SQLite inverted index of every distinct word four-gram in the
actual frequency-specific training corpus.  For each completion, the index returns
every story sharing at least one four-gram; the script then recomputes overlap from
the original story text.  Stories not returned share zero four-grams, so the
reported maximum is exact (hash collisions can only add candidates and are removed
by the final text comparison).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from eval_novelty import edit_distance, ngram_overlap, word_ngrams  # noqa: E402
from prepare_canary_corpus import load_stories  # noqa: E402
from prepare_confirmatory_corpus import split_of as confirmatory_split_of  # noqa: E402


def gram_hash(gram: tuple[str, ...]) -> int:
    """Stable signed 64-bit hash suitable for a SQLite INTEGER column."""
    raw = hashlib.blake2b("\x1f".join(gram).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(raw, "big", signed=True)


def corpus_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_stories(corpus_path: Path, training_split_seed: int | None = None) -> list[str]:
    stories = load_stories(corpus_path)
    if training_split_seed is None:
        return stories
    return [story for story in stories if confirmatory_split_of(story, training_split_seed) == "train"]


def selection_fingerprint(corpus_path: Path, training_split_seed: int | None) -> str:
    if training_split_seed is None:
        return corpus_fingerprint(corpus_path)
    raw = f"{corpus_fingerprint(corpus_path)}|split={training_split_seed}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_index(corpus_path: Path, db_path: Path, force: bool = False,
                training_split_seed: int | None = None) -> int:
    """Build or reuse an index, returning its number of stories."""
    fingerprint = selection_fingerprint(corpus_path, training_split_seed)
    if db_path.exists() and not force:
        with sqlite3.connect(db_path) as con:
            meta = dict(con.execute("SELECT key, value FROM metadata"))
            if meta.get("corpus_sha256") != fingerprint:
                raise ValueError(f"{db_path} belongs to a different corpus; pass --force-index")
            return int(meta["n_stories"])

    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    stories = selected_stories(corpus_path, training_split_seed)
    with sqlite3.connect(db_path) as con:
        con.executescript(
            "PRAGMA journal_mode=WAL; PRAGMA synchronous=OFF;"
            "CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);"
            "CREATE TABLE story_grams(gram_hash INTEGER NOT NULL, story_id INTEGER NOT NULL, "
            "PRIMARY KEY(gram_hash, story_id)) WITHOUT ROWID;"
        )
        batch: list[tuple[int, int]] = []
        for story_id, story in enumerate(stories):
            batch.extend((gram_hash(gram), story_id) for gram in set(word_ngrams(story, 4)))
            if len(batch) >= 100_000:
                con.executemany("INSERT OR IGNORE INTO story_grams VALUES (?, ?)", batch)
                batch.clear()
        if batch:
            con.executemany("INSERT OR IGNORE INTO story_grams VALUES (?, ?)", batch)
        con.executemany(
            "INSERT INTO metadata VALUES (?, ?)",
            [("schema_version", "2"), ("corpus_sha256", fingerprint),
             ("raw_corpus_sha256", corpus_fingerprint(corpus_path)),
             ("training_split_seed", "" if training_split_seed is None else str(training_split_seed)),
             ("n_stories", str(len(stories))), ("ngram_n", "4")],
        )
        con.commit()
    return len(stories)


def candidate_story_ids(con: sqlite3.Connection, text: str) -> set[int]:
    hashes = sorted({gram_hash(gram) for gram in word_ngrams(text, 4)})
    found: set[int] = set()
    # Stay below SQLite's commonly configured 999-variable limit.
    for start in range(0, len(hashes), 900):
        chunk = hashes[start:start + 900]
        placeholders = ",".join("?" for _ in chunk)
        if chunk:
            rows = con.execute(
                f"SELECT DISTINCT story_id FROM story_grams WHERE gram_hash IN ({placeholders})", chunk
            )
            found.update(row[0] for row in rows)
    return found


def exact_full_corpus_match(text: str, stories: list[str], con: sqlite3.Connection) -> dict:
    candidates = candidate_story_ids(con, text)
    if not candidates:
        return {
            "full_corpus_max_4gram_overlap": 0.0,
            "full_corpus_best_story_id": None,
            "full_corpus_best_story_edit_distance": None,
            "full_corpus_candidate_count": 0,
        }
    scored = [(ngram_overlap(text, stories[story_id], 4), story_id) for story_id in candidates]
    best_overlap, best_story_id = max(scored, key=lambda item: (item[0], -item[1]))
    return {
        "full_corpus_max_4gram_overlap": round(best_overlap, 6),
        "full_corpus_best_story_id": best_story_id,
        "full_corpus_best_story_edit_distance": edit_distance(text, stories[best_story_id]),
        "full_corpus_candidate_count": len(candidates),
    }


def enrich_results(input_path: Path, output_path: Path, corpus_path: Path, db_path: Path,
                   training_split_seed: int | None = None) -> int:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    stories = selected_stories(corpus_path, training_split_seed)
    count = 0
    with sqlite3.connect(db_path) as con:
        groups = payload.get("groups", payload.get("novelty_groups"))
        if groups is None:
            raise ValueError("input has neither groups nor novelty_groups")
        for group in groups:
            for completion in group["completions"]:
                completion.update(exact_full_corpus_match(completion["text"], stories, con))
                count += 1
    payload["full_corpus_overlap"] = {
        "metric": "exact maximum fraction of generated word four-grams found in any training story",
        "corpus": str(corpus_path),
        "corpus_sha256": corpus_fingerprint(corpus_path),
        "selection_sha256": selection_fingerprint(corpus_path, training_split_seed),
        "scope": "training_split" if training_split_seed is not None else "all_documents",
        "training_split_seed": training_split_seed,
        "index": str(db_path),
        "n_stories": len(stories),
    }
    if "full_training_corpus_overlap_complete" in payload:
        payload["full_training_corpus_overlap_complete"] = training_split_seed is not None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="novelty JSON to enrich")
    parser.add_argument("--corpus", required=True, type=Path, help="actual training corpus for that checkpoint")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path, help="reusable SQLite index for this corpus")
    parser.add_argument("--force-index", action="store_true")
    parser.add_argument("--training-split-seed", type=int,
                        help="restrict the index to documents content-hashed into the exact training split")
    args = parser.parse_args()

    n_stories = build_index(
        args.corpus, args.index, force=args.force_index, training_split_seed=args.training_split_seed
    )
    count = enrich_results(
        args.input, args.output, args.corpus, args.index, training_split_seed=args.training_split_seed
    )
    print(f"[done] checked {count} completions against {n_stories} stories -> {args.output}")


if __name__ == "__main__":
    main()
