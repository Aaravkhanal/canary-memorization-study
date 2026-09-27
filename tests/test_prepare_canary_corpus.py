"""Tests for scripts/prepare_canary_corpus.py: no double connectors, deterministic/nested/disjoint assignment,
and an end-to-end build on a synthetic corpus."""

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_canary_corpus import (  # noqa: E402
    EOT, all_canaries, build_assignment, insert_character, insert_plot_fragment, load_stories,
)

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "configs" / "canaries.yaml").read_text())


# ── insertion text ────────────────────────────────────────────────────────────

def test_character_insertion_prepends_the_canary_as_a_new_first_sentence():
    out = insert_character("Once upon a time there was a cat.", "Pip the fox, who was always hungry")
    assert out == "Pip the fox, who was always hungry. Once upon a time there was a cat."


@pytest.mark.parametrize("canary_text", [c["text"] for c in CFG["canaries"]["plot_fragment"]])
def test_plot_fragment_insertion_never_doubles_its_own_leading_connector(canary_text):
    """The bug this guards: canary texts each carry their own connector (then/and/before/until), so the splice
    must add only a comma. An earlier version hardcoded ", and " and produced "and and" for the canary
    that already starts with "and"."""
    story = "Ben saw a dog. He was happy. The dog ran away. Ben was sad. He looked for it all day."
    out = insert_plot_fragment(story, canary_text)
    first_word = canary_text.split()[0]
    assert f"and {first_word}" not in out.lower() and f"but {first_word}" not in out.lower()
    assert out.count(canary_text) == 1
    assert out.startswith("Ben saw a dog.") and out.endswith(".")   # the rest of the story survives untouched


def test_plot_fragment_insertion_lands_near_the_midpoint_not_the_start_or_end():
    story = " ".join(f"Sentence number {i}." for i in range(10))
    out = insert_plot_fragment(story, "then found a shiny key under the old oak tree")
    assert "Sentence number 0." in out and "Sentence number 9." in out    # both ends survive
    assert not out.startswith("then") and not out.rstrip(".").endswith("oak tree")  # not glued to either end


def test_plot_fragment_insertion_falls_back_gracefully_on_a_single_sentence_story():
    out = insert_plot_fragment("A short story.", "then found a shiny key under the old oak tree")
    assert "then found a shiny key under the old oak tree" in out and "A short story." in out


# ── assignment: deterministic, nested, disjoint ───────────────────────────────

def test_assignment_is_deterministic_for_a_fixed_seed():
    a1 = build_assignment(CFG, n_stories=10_000)
    a2 = build_assignment(CFG, n_stories=10_000)
    assert a1 == a2


def test_assignment_pools_are_disjoint_across_canaries():
    a = build_assignment(CFG, n_stories=10_000)
    canaries = all_canaries(CFG)
    seen = set()
    for c in canaries:
        pool = set(a[c["id"]])
        assert len(pool) == CFG["insertion_pool_size_per_canary"]     # no duplicate indices within one canary's pool
        assert not (pool & seen), f"{c['id']} overlaps an earlier canary's pool"
        seen |= pool


def test_a_higher_frequency_pool_starts_with_the_lower_frequency_pool():
    """The dose-response nesting property the study depends on: increasing frequency must ADD insertions to the
    same stories, never swap which stories are used, or a frequency comparison would confound "more exposure"
    with "different stories"."""
    a = build_assignment(CFG, n_stories=10_000)
    canary_id = CFG["canaries"]["character"][0]["id"]
    pool = a[canary_id]
    for lo, hi in zip(CFG["frequencies"], CFG["frequencies"][1:]):
        assert pool[:lo] == pool[:hi][:lo]


def test_build_assignment_rejects_a_base_corpus_too_small_for_the_pools():
    with pytest.raises(ValueError, match="need"):
        build_assignment(CFG, n_stories=10)


# ── end to end on a synthetic corpus ──────────────────────────────────────────

@pytest.fixture()
def synthetic_base(tmp_path):
    stories = [f"Story {i}. It had a beginning. It had a middle part here. It had an end." for i in range(4200)]
    path = tmp_path / "base.txt"
    path.write_text((f"\n{EOT}\n").join(stories) + f"\n{EOT}\n")
    return path


def run_build(tmp_path, synthetic_base, freq, force=False):
    import subprocess
    script = Path(__file__).resolve().parents[1] / "scripts" / "prepare_canary_corpus.py"
    cfg_path = tmp_path / "canaries.yaml"
    cfg = dict(CFG)
    cfg["base_corpus"] = str(synthetic_base)
    cfg_path.write_text(yaml.safe_dump(cfg))
    cmd = [sys.executable, str(script), "--config", str(cfg_path), "--base", str(synthetic_base),
          "--freq", str(freq), "--out-root", str(tmp_path / "processed")]
    if force:
        cmd.append("--force")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    return tmp_path / "processed" / f"freq_{freq}" / "corpus.txt", tmp_path / "processed" / f"freq_{freq}" / "manifest.json"


def test_end_to_end_build_matches_its_own_manifest_and_refuses_to_silently_reassign(tmp_path, synthetic_base):
    corpus1, manifest1 = run_build(tmp_path, synthetic_base, 1, force=True)
    m1 = json.loads(manifest1.read_text())
    assert all(n == 1 for n in m1["canary_counts"].values())
    stories = load_stories(corpus1)
    assert len(stories) == 4200                                      # no story added or dropped, only edited
    total_insertions = sum(corpus1.read_text().count(c["text"]) for c in all_canaries(CFG))
    assert total_insertions == len(all_canaries(CFG))                # each canary appears exactly once

    corpus500, manifest500 = run_build(tmp_path, synthetic_base, 500)   # reuses the locked assignment (no --force)
    m500 = json.loads(manifest500.read_text())
    assert all(n == 500 for n in m500["canary_counts"].values())
    for cid in m1["used_story_indices"]:
        assert m1["used_story_indices"][cid] == m500["used_story_indices"][cid][:1]   # nested, not re-assigned

    assigned_path = tmp_path / "canaries.yaml"                       # sits next to the (temp) config, per the script
    assert (assigned_path.parent / "canary_assignment.json").exists()
