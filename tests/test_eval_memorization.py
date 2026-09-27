"""Tests for scripts/eval_memorization.py that don't need a real model: the reference-set construction and the
exposure ranking formula, which is where a silent bug would be invisible in the printed sanity-check output."""

import math
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from eval_memorization import all_canary_rows, build_alternatives, exposure, prefix_and_identity  # noqa: E402

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "configs" / "canaries.yaml").read_text())


# ── reference-set construction ────────────────────────────────────────────────

def test_character_alternatives_swap_only_the_name():
    canary = next(c for c in CFG["canaries"]["character"] if c["id"] == "char_pip")
    alts = build_alternatives(canary, "character", CFG)
    assert len(alts) == len(CFG["character_alt_pool"]) - 0            # pip's own name isn't in the pool, so none excluded
    for a in alts:
        assert a.endswith(canary["text"].split(" ", 1)[1])            # everything after the name is untouched
        assert a.split(" ", 1)[0] != "Pip"                             # the name itself always changed


def test_plot_fragment_alternatives_swap_only_the_registered_span():
    canary = next(c for c in CFG["canaries"]["plot_fragment"] if c["id"] == "plot_key")
    alts = build_alternatives(canary, "plot_fragment", CFG)
    target = CFG["plot_fragment_swap"]["plot_key"]["swap_target"]
    assert len(alts) == len(CFG["plot_fragment_swap"]["plot_key"]["alt_pool"])
    for a in alts:
        assert target not in a                                         # the true phrase itself is gone
        assert canary["text"][:canary["text"].index(target)] in a       # the text before the swap span is untouched
        assert canary["text"][canary["text"].index(target) + len(target):] in a   # and after it


def test_every_inserted_canary_and_unseen_control_has_a_computable_reference_set():
    """The bug this guards: two unseen plot-fragment controls once had no swap metadata at all, so their exposure
    silently came back as "n/a" instead of a real, comparable number -- looking like the metric working when data
    was just missing."""
    for row in all_canary_rows(CFG):
        alts = build_alternatives(row, row["type"], CFG)
        assert len(alts) >= 3, (row["id"], "has no reference set")
        assert len(alts) == len(set(alts)), (row["id"], "duplicate alternatives")
        assert row["text"] not in alts


def test_prefix_and_identity_recombine_to_a_prefix_of_the_full_scored_text():
    for row in all_canary_rows(CFG):
        before, identity = prefix_and_identity(row, row["type"], CFG)
        full_prefix = {"character": "Once upon a time, ", "plot_fragment": "One day, something interesting happened. "}[row["type"]]
        assert before.startswith(full_prefix)
        reconstructed = before[len(full_prefix):] + identity
        assert row["text"].startswith(reconstructed) or row["text"] == reconstructed


# ── exposure formula ──────────────────────────────────────────────────────────

class _FakeTok:
    def encode(self, text):
        return list(range(len(text.split())))                          # length is all that matters for these tests


class _FakeEngine:
    """A stand-in whose "model" is just a lookup table from text to a chosen log-probability, so the ranking
    logic can be tested exactly without running a real network."""
    def __init__(self, scores: dict):
        self.tok = _FakeTok()
        self.device = "cpu"
        self._scores = scores

    def score(self, text):
        return self._scores[text]


def test_exposure_is_maximal_when_the_true_text_is_the_most_probable(monkeypatch):
    import eval_memorization as m
    scores = {"": 0}  # placeholder, overwritten below per call via monkeypatched sequence_log_prob
    calls = {"true": -1.0, "alt-a": -5.0, "alt-b": -6.0}
    monkeypatch.setattr(m, "sequence_log_prob", lambda engine, text: calls[text.removeprefix("PFX")])
    r = exposure(engine=None, prefix="PFX", true_text="true", alternatives=["alt-a", "alt-b"])
    assert r["rank"] == 1
    assert r["exposure"] == pytest.approx(math.log2(4) - math.log2(1))    # n=3 candidates, log2(3+1) - log2(1)


def test_exposure_is_low_when_the_true_text_is_the_least_probable(monkeypatch):
    import eval_memorization as m
    calls = {"true": -9.0, "alt-a": -1.0, "alt-b": -2.0, "alt-c": -3.0}
    monkeypatch.setattr(m, "sequence_log_prob", lambda engine, text: calls[text.removeprefix("PFX")])
    r = exposure(engine=None, prefix="PFX", true_text="true", alternatives=["alt-a", "alt-b", "alt-c"])
    assert r["rank"] == 4                                                # last of 4 candidates
    assert r["exposure"] == pytest.approx(math.log2(5) - math.log2(4))
    assert r["exposure"] < 1.0                                           # near the floor: barely more likely than by chance


def test_exposure_rank_is_stable_and_deterministic_for_tied_scores(monkeypatch):
    import eval_memorization as m
    calls = {"true": -1.0, "alt-a": -1.0}                                 # an exact tie: rank must not be random
    monkeypatch.setattr(m, "sequence_log_prob", lambda engine, text: calls[text.removeprefix("PFX")])
    r1 = exposure(engine=None, prefix="PFX", true_text="true", alternatives=["alt-a"])
    r2 = exposure(engine=None, prefix="PFX", true_text="true", alternatives=["alt-a"])
    assert r1["rank"] == r2["rank"]
