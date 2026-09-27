"""Tests for scripts/eval_novelty.py's pure scoring functions (no model needed) and the training-story lookup
against the real Phase 1 manifest already built in this repo."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from eval_novelty import distinct_n, edit_distance, make_prompt, ngram_overlap, self_bleu_proxy, training_stories_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


# ── n-gram overlap and edit distance ──────────────────────────────────────────

def test_ngram_overlap_is_one_for_an_exact_verbatim_reproduction():
    text = "the little fox ran through the dark forest at night"
    assert ngram_overlap(text, text, n=4) == 1.0


def test_ngram_overlap_is_zero_for_completely_disjoint_vocabulary():
    a = "the little fox ran through the forest"
    b = "spaceships orbited distant planets quietly forever"
    assert ngram_overlap(a, b, n=4) == 0.0


def test_ngram_overlap_is_partial_for_a_template_copy_with_one_word_swapped():
    ref = "the little fox ran through the dark forest at night looking for food"
    gen = "the little wolf ran through the dark forest at night looking for food"
    overlap = ngram_overlap(gen, ref, n=4)
    assert 0.0 < overlap < 1.0                                       # most 4-grams survive the single-word swap


def test_edit_distance_is_zero_for_identical_text_and_positive_for_any_difference():
    a = "the cat sat on the mat"
    assert edit_distance(a, a) == 0
    assert edit_distance(a, "the dog sat on the mat") == 1
    assert edit_distance(a, "a totally different sentence entirely") > 3


# ── diversity across a group of completions ───────────────────────────────────

def test_distinct_n_is_low_when_every_completion_is_identical():
    texts = ["the fox ran fast"] * 5
    assert distinct_n(texts, 1) < 0.3                                 # same words repeated 5x: low unique ratio


def test_distinct_n_is_high_when_completions_share_no_vocabulary():
    texts = ["alpha beta gamma", "delta epsilon zeta", "eta theta iota"]
    assert distinct_n(texts, 1) == 1.0                                 # every unigram is unique across the group


def test_self_bleu_proxy_is_maximal_for_identical_completions_and_zero_for_disjoint_ones():
    same = ["the fox ran through the forest at night"] * 3
    assert self_bleu_proxy(same, n=4) == pytest.approx(1.0)
    disjoint = ["the fox ran through the forest", "spaceships orbited the distant planet quietly"]
    assert self_bleu_proxy(disjoint, n=4) == 0.0


def test_self_bleu_proxy_handles_a_single_completion_without_crashing():
    assert self_bleu_proxy(["only one completion here"]) == 0.0


# ── prompts ────────────────────────────────────────────────────────────────────

def test_character_and_plot_fragment_prompts_both_carry_the_canary_and_the_setting():
    setting = "a pirate ship sailing a stormy sea"
    char = {"text": "Pip the fox, who was always hungry"}
    plot = {"text": "then found a shiny key under the old oak tree"}
    p1 = make_prompt(char, "character", setting)
    p2 = make_prompt(plot, "plot_fragment", setting)
    assert char["text"] in p1 and setting in p1
    assert plot["text"] in p2 and setting in p2
    assert p1 != p2


# ── training-story lookup against the real, already-built manifest ────────────

def test_training_stories_for_returns_the_real_inserted_stories_for_freq_1():
    manifest_path = ROOT / "data" / "processed" / "freq_1" / "manifest.json"
    if not manifest_path.exists():
        pytest.skip("freq_1 corpus not built in this checkout")
    stories = training_stories_for("char_pip", frequency=1)
    assert len(stories) == 1                                          # frequency 1: exactly one training story
    assert "Pip the fox" not in stories[0]                              # this is the BASE story, before the canary sentence was added


def test_training_stories_for_an_unseen_control_is_empty():
    manifest_path = ROOT / "data" / "processed" / "freq_1" / "manifest.json"
    if not manifest_path.exists():
        pytest.skip("freq_1 corpus not built in this checkout")
    assert training_stories_for("ctrl_char_olen", frequency=1) == []    # never inserted anywhere
