import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_confirmatory_corpus import build_corpus, insert_canary, split_of  # noqa: E402


def tiny_bank():
    return {
        "canaries": [
            {"id": "char", "type": "character", "identity": "Zoravi", "text": "Zoravi, who kept a blue cup"},
            {"id": "plot", "type": "plot", "identity": "the copper kite circled", "text": "the copper kite circled"},
        ],
        "frequency_schedule": {"7": {"char": 1, "plot": 10}},
    }


def test_insertion_styles_preserve_story_and_identity():
    story = "One morning began. A child walked outside. The child came home."
    char = insert_canary(story, tiny_bank()["canaries"][0])
    plot = insert_canary(story, tiny_bank()["canaries"][1])
    assert char.startswith("Zoravi") and story in char
    assert "the copper kite circled" in plot and plot.startswith("One morning")


def test_build_is_deterministic_disjoint_and_train_only():
    stories = [f"Story {i} began. A child walked along path {i}. The child returned home." for i in range(200)]
    first, manifest1 = build_corpus(stories, tiny_bank(), seed=7)
    second, manifest2 = build_corpus(stories, tiny_bank(), seed=7)
    assert first == second and manifest1 == manifest2
    char_ids = set(manifest1["used_story_indices"]["char"])
    plot_ids = set(manifest1["used_story_indices"]["plot"])
    assert not char_ids & plot_ids
    assert len(char_ids) == 1 and len(plot_ids) == 10
    assert all(split_of(first[index]) == "train" for index in char_ids | plot_ids)


def test_committed_bank_base_hash_matches_local_input():
    bank = json.loads((ROOT / "configs" / "confirmatory" / "canary_bank.json").read_text())
    base = ROOT / "data" / "raw" / "base.txt"
    digest = hashlib.sha256(base.read_bytes()).hexdigest()
    assert digest == bank["base_corpus"]["sha256"]
