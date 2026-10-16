import json
import sqlite3
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from eval_full_corpus_overlap import (  # noqa: E402
    build_index,
    candidate_story_ids,
    enrich_results,
    exact_full_corpus_match,
    selected_stories,
)
from prepare_confirmatory_corpus import split_of  # noqa: E402


def write_corpus(path: Path, stories: list[str]) -> None:
    path.write_text("\n<|endoftext|>\n".join(stories) + "\n<|endoftext|>\n", encoding="utf-8")


def test_index_retrieves_every_story_sharing_a_fourgram(tmp_path):
    corpus = tmp_path / "corpus.txt"
    db = tmp_path / "index.sqlite"
    stories = [
        "the small fox ran into the green forest today",
        "a silver rocket crossed the distant purple sky",
        "nothing here resembles either of the other stories",
    ]
    write_corpus(corpus, stories)
    assert build_index(corpus, db) == 3
    with sqlite3.connect(db) as con:
        assert candidate_story_ids(con, "we saw a silver rocket crossed the distant purple sky") == {1}


def test_full_corpus_maximum_finds_copy_outside_canary_insertion_story(tmp_path):
    corpus = tmp_path / "corpus.txt"
    db = tmp_path / "index.sqlite"
    stories = [
        "this was the canary insertion story but it has unrelated wording",
        "mira opened the wooden door and found a bright red kite",
    ]
    write_corpus(corpus, stories)
    build_index(corpus, db)
    with sqlite3.connect(db) as con:
        result = exact_full_corpus_match(stories[1], stories, con)
    assert result["full_corpus_max_4gram_overlap"] == 1.0
    assert result["full_corpus_best_story_id"] == 1


def test_no_shared_fourgram_is_reported_as_exact_zero(tmp_path):
    corpus = tmp_path / "corpus.txt"
    db = tmp_path / "index.sqlite"
    stories = ["the little dog played beside the river all day"]
    write_corpus(corpus, stories)
    build_index(corpus, db)
    with sqlite3.connect(db) as con:
        result = exact_full_corpus_match("spaceships orbited planets", stories, con)
    assert result["full_corpus_max_4gram_overlap"] == 0.0
    assert result["full_corpus_best_story_id"] is None


def test_index_refuses_silent_reuse_for_a_different_corpus(tmp_path):
    corpus = tmp_path / "corpus.txt"
    db = tmp_path / "index.sqlite"
    write_corpus(corpus, ["one two three four five"])
    build_index(corpus, db)
    write_corpus(corpus, ["entirely different training corpus words here"])
    with pytest.raises(ValueError, match="different corpus"):
        build_index(corpus, db)


def test_enrichment_preserves_existing_fields_and_records_provenance(tmp_path):
    corpus = tmp_path / "corpus.txt"
    db = tmp_path / "index.sqlite"
    source = tmp_path / "novelty.json"
    output = tmp_path / "enriched.json"
    story = "the careful owl carried a lantern through the woods"
    write_corpus(corpus, [story])
    build_index(corpus, db)
    source.write_text(json.dumps({"checkpoint": "x.pt", "groups": [{"completions": [
        {"text": story, "max_ngram_overlap": 0.0}
    ]}]}))
    assert enrich_results(source, output, corpus, db) == 1
    payload = json.loads(output.read_text())
    completion = payload["groups"][0]["completions"][0]
    assert completion["max_ngram_overlap"] == 0.0
    assert completion["full_corpus_max_4gram_overlap"] == 1.0
    assert payload["full_corpus_overlap"]["n_stories"] == 1


def test_confirmatory_enrichment_indexes_training_split_only(tmp_path):
    corpus = tmp_path / "corpus.txt"
    db = tmp_path / "index.sqlite"
    source = tmp_path / "raw.json"
    output = tmp_path / "enriched.json"
    seed = 20261016
    stories = [f"story number {i} has enough ordinary words for this deterministic split check" for i in range(500)]
    write_corpus(corpus, stories)
    training = selected_stories(corpus, seed)
    held_out = next(story for story in stories if split_of(story, seed) != "train")
    assert 0 < len(training) < len(stories)
    build_index(corpus, db, training_split_seed=seed)
    source.write_text(json.dumps({
        "novelty_groups": [{"completions": [{"text": held_out}]}],
        "full_training_corpus_overlap_complete": False,
    }))
    enrich_results(source, output, corpus, db, training_split_seed=seed)
    payload = json.loads(output.read_text())
    assert payload["full_corpus_overlap"]["scope"] == "training_split"
    assert payload["full_corpus_overlap"]["n_stories"] == len(training)
    assert payload["full_training_corpus_overlap_complete"] is True
    assert payload["novelty_groups"][0]["completions"][0]["full_corpus_max_4gram_overlap"] < 1.0
