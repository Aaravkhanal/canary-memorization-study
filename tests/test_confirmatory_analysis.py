import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_confirmatory import fit_exposure, fit_novelty, holm_adjust  # noqa: E402


def design_frame():
    rows = []
    rng = np.random.default_rng(17)
    frequencies = [1, 10, 50, 100, 500]
    canaries = [f"c{i:02d}" for i in range(20)]
    for seed_index, seed in enumerate((20261016, 20261017, 20261018)):
        for scale in ("14m", "48m"):
            for architecture in ("baseline", "learned_pos", "mha", "layernorm"):
                for index, canary in enumerate(canaries):
                    frequency = frequencies[(index + seed_index) % len(frequencies)]
                    rows.append({
                        "seed": seed, "scale": scale, "architecture": architecture,
                        "canary_id": canary, "frequency": frequency,
                        "exposure_bits": 0.5 * np.log10(frequency) + rng.normal(0, 0.05),
                    })
    return pd.DataFrame(rows)


def test_holm_adjust_is_monotone_in_rank_and_returns_original_order():
    assert holm_adjust([0.03, 0.001, 0.02]) == pytest.approx([0.04, 0.003, 0.04])


def test_exposure_model_recovers_registered_positive_frequency_effect():
    result = fit_exposure(design_frame())
    primary = next(row for row in result["effects"] if row["term"] == "log10_frequency")
    assert result["rows"] == 480
    assert result["canary_clusters"] == 20
    assert 0.45 < primary["estimate"] < 0.55
    assert primary["ci95_low"] > 0


def test_novelty_model_rejects_partial_or_nonhuman_label_values():
    frame = design_frame().head(10).assign(setting="moon", label="N")
    frame.loc[0, "label"] = ""
    with pytest.raises(ValueError, match="complete adjudicated human"):
        fit_novelty(frame)


def test_analysis_plan_is_frozen_and_names_both_primary_models():
    plan = json.loads((ROOT / "configs" / "confirmatory" / "analysis_plan.json").read_text())
    assert plan["status"] == "frozen before confirmatory outcomes"
    assert "log10_frequency" in plan["primary_exposure"]["formula"]
    assert plan["primary_novelty"]["outcome"] == "human adjudicated N versus V/T"
    assert plan["multiplicity"]["method"] == "Holm"
