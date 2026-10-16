import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from eval_confirmatory import (  # noqa: E402
    exact_prefix_match,
    novelty_prompt,
    reference_candidates,
    stable_seed,
    validate_plan,
)


ROOT = Path(__file__).resolve().parents[1]


def load_inputs():
    bank = json.loads((ROOT / "configs/confirmatory/canary_bank.json").read_text())
    plan = json.loads((ROOT / "configs/confirmatory/evaluation_plan.json").read_text())
    return bank, plan


def test_frozen_plan_matches_registered_sampling_and_pool_sizes():
    bank, plan = load_inputs()
    validate_plan(bank, plan)
    assert plan["exposure"]["candidate_count_including_true"] == 1025
    assert len(plan["novelty"]["settings"]) * plan["novelty"]["completions_per_canary_setting"] == 8


def test_character_references_swap_only_the_identity_slot():
    bank, _ = load_inputs()
    canary = next(row for row in bank["canaries"] if row["type"] == "character")
    candidates = reference_candidates(canary, bank["reference_pools"]["character"])
    assert len(candidates) == 1025
    assert candidates[0] == canary["text"]
    suffix = canary["text"][len(canary["identity"]):]
    assert all(candidate.endswith(suffix) for candidate in candidates)


def test_plot_references_use_complete_slot_matched_phrases():
    bank, _ = load_inputs()
    canary = next(row for row in bank["canaries"] if row["type"] == "plot")
    candidates = reference_candidates(canary, bank["reference_pools"]["plot"])
    assert candidates[0] == canary["text"]
    assert candidates[1:] == bank["reference_pools"]["plot"]


def test_reference_builder_rejects_true_text_in_pool():
    bank, _ = load_inputs()
    canary = next(row for row in bank["canaries"] if row["type"] == "plot")
    with pytest.raises(ValueError, match="contains the true text"):
        reference_candidates(canary, [canary["text"]])


def test_generation_seeds_are_stable_and_cell_specific():
    first = stable_seed(20261017, 20261016, "confirm_char_01", "the moon", 0)
    assert first == stable_seed(20261017, 20261016, "confirm_char_01", "the moon", 0)
    assert first != stable_seed(20261017, 20261018, "confirm_char_01", "the moon", 0)


def test_prompts_and_exact_match_are_explicit():
    bank, plan = load_inputs()
    char = next(row for row in bank["canaries"] if row["type"] == "character")
    plot = next(row for row in bank["canaries"] if row["type"] == "plot")
    setting = plan["novelty"]["settings"][0]
    assert char["text"] in novelty_prompt(char, setting)
    assert plot["text"] in novelty_prompt(plot, setting)
    assert exact_prefix_match("  Zoravi continued", "Zoravi") is True
    assert exact_prefix_match("Pelnori continued", "Zoravi") is False
