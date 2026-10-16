#!/usr/bin/env python3
"""Pre-outcome power/precision simulation for the confirmatory mixed-frequency design.

The simulation evaluates the registered average frequency slope while adjusting for architecture, scale, seed,
and canary. It uses a canary-clustered linear model for exposure and a canary-clustered binomial GLM for the
human N-versus-V/T endpoint. Assumptions are explicit in the JSON output and must be amended before training if
the research team chooses different smallest effects of scientific interest (SESOIs).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURES = ["baseline", "learned_pos", "mha", "layernorm"]
SCALES = ["14m", "48m"]
SETTINGS = 4
COMPLETIONS_PER_SETTING = 2


def design_rows(bank: dict, seed_count: int) -> pd.DataFrame:
    seeds = bank["seeds"][:seed_count]
    canaries = [row["id"] for row in bank["canaries"]]
    rows = []
    for seed in seeds:
        assignments = bank["frequency_schedule"][str(seed)]
        for architecture in ARCHITECTURES:
            for scale in SCALES:
                for canary in canaries:
                    frequency = assignments[canary]
                    rows.append({
                        "seed": str(seed), "architecture": architecture, "scale": scale, "canary": canary,
                        "frequency": frequency, "log10_frequency": math.log10(frequency),
                    })
    frame = pd.DataFrame(rows)
    frame["log10_frequency"] -= frame["log10_frequency"].mean()
    return frame


def model_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    fixed = pd.get_dummies(
        frame[["architecture", "scale", "seed", "canary"]], drop_first=True, dtype=float
    )
    return sm.add_constant(pd.concat([frame[["log10_frequency"]].astype(float), fixed], axis=1))


def one_replicate(frame: pd.DataFrame, rng: np.random.Generator, assumptions: dict) -> tuple[dict, dict]:
    seed_effect = {value: rng.normal(0, assumptions["exposure_seed_sd"]) for value in frame.seed.unique()}
    canary_effect = {value: rng.normal(0, assumptions["exposure_canary_sd"]) for value in frame.canary.unique()}
    exposure = (
        assumptions["exposure_intercept"]
        + assumptions["exposure_sesoi_bits_per_decade"] * frame.log10_frequency.to_numpy()
        + frame.seed.map(seed_effect).to_numpy()
        + frame.canary.map(canary_effect).to_numpy()
        + rng.normal(0, assumptions["exposure_residual_sd"], len(frame))
    )
    matrix = model_matrix(frame)
    exposure_fit = sm.OLS(exposure, matrix).fit(
        cov_type="cluster", cov_kwds={"groups": frame.canary.to_numpy()}
    )
    exposure_beta = float(exposure_fit.params["log10_frequency"])
    exposure_se = float(exposure_fit.bse["log10_frequency"])

    novelty_seed = {value: rng.normal(0, assumptions["novelty_seed_logit_sd"]) for value in frame.seed.unique()}
    novelty_canary = {value: rng.normal(0, assumptions["novelty_canary_logit_sd"]) for value in frame.canary.unique()}
    logit = (
        assumptions["novelty_intercept_logit"]
        + math.log(assumptions["novelty_sesoi_odds_ratio_per_decade"]) * frame.log10_frequency.to_numpy()
        + frame.seed.map(novelty_seed).to_numpy()
        + frame.canary.map(novelty_canary).to_numpy()
    )
    probability = 1 / (1 + np.exp(-logit))
    trials = SETTINGS * COMPLETIONS_PER_SETTING
    expanded_matrix = matrix.loc[matrix.index.repeat(trials)].reset_index(drop=True)
    expanded_probability = np.repeat(probability, trials)
    responses = rng.binomial(1, expanded_probability)
    expanded_groups = np.repeat(frame.canary.to_numpy(), trials)
    novelty_fit = sm.GLM(responses, expanded_matrix, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": expanded_groups}
    )
    novelty_beta = float(novelty_fit.params["log10_frequency"])
    novelty_se = float(novelty_fit.bse["log10_frequency"])
    return (
        {"beta": exposure_beta, "se": exposure_se, "detected": abs(exposure_beta / exposure_se) >= 1.96},
        {"beta": novelty_beta, "se": novelty_se, "detected": abs(novelty_beta / novelty_se) >= 1.96},
    )


def simulate(bank: dict, seed_count: int, replicates: int, simulation_seed: int, assumptions: dict) -> dict:
    frame = design_rows(bank, seed_count)
    rng = np.random.default_rng([simulation_seed, seed_count])
    exposure_rows, novelty_rows = [], []
    for _ in range(replicates):
        exposure, novelty = one_replicate(frame, rng, assumptions)
        exposure_rows.append(exposure)
        novelty_rows.append(novelty)

    def summarize(rows: list[dict], width_target: float) -> dict:
        powers = [row["detected"] for row in rows]
        widths = [2 * 1.96 * row["se"] for row in rows]
        return {
            "power": float(np.mean(powers)),
            "monte_carlo_se": float(math.sqrt(np.mean(powers) * (1 - np.mean(powers)) / len(powers))),
            "median_95ci_width": float(np.median(widths)),
            "width_target": width_target,
            "passes": float(np.mean(powers)) >= assumptions["power_target"] and float(np.median(widths)) <= width_target,
        }

    return {
        "seed_count": seed_count,
        "model_cells": seed_count * len(ARCHITECTURES) * len(SCALES),
        "canary_model_rows": len(frame),
        "human_ratings_per_rater": len(frame) * SETTINGS * COMPLETIONS_PER_SETTING,
        "exposure": summarize(exposure_rows, assumptions["exposure_ci_width_target"]),
        "novelty": summarize(novelty_rows, assumptions["novelty_log_odds_ci_width_target"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=ROOT / "configs" / "confirmatory" / "canary_bank.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "confirmatory_power.json")
    parser.add_argument("--replicates", type=int, default=250)
    parser.add_argument("--simulation-seed", type=int, default=20261016)
    args = parser.parse_args()
    assumptions = {
        "power_target": 0.80,
        "exposure_intercept": 2.0,
        "exposure_sesoi_bits_per_decade": 0.5,
        "exposure_seed_sd": 0.25,
        "exposure_canary_sd": 0.75,
        "exposure_residual_sd": 0.6,
        "exposure_ci_width_target": 0.75,
        "novelty_intercept_logit": math.log(0.4 / 0.6),
        "novelty_sesoi_odds_ratio_per_decade": 1.5,
        "novelty_seed_logit_sd": 0.20,
        "novelty_canary_logit_sd": 0.60,
        "novelty_log_odds_ci_width_target": 0.70,
        "settings_per_canary_model": SETTINGS,
        "completions_per_setting": COMPLETIONS_PER_SETTING,
    }
    bank = json.loads(args.bank.read_text(encoding="utf-8"))
    candidates = [simulate(bank, count, args.replicates, args.simulation_seed, assumptions) for count in (3, 5)]
    selected = next((row["seed_count"] for row in candidates if row["exposure"]["passes"] and row["novelty"]["passes"]), None)
    payload = {
        "schema_version": 1,
        "status": "pre-outcome power simulation",
        "replicates": args.replicates,
        "simulation_seed": args.simulation_seed,
        "assumptions": assumptions,
        "candidates": candidates,
        "selected_seed_count": selected,
        "decision": "minimum candidate passing both endpoints" if selected else "neither candidate passes; amend before training",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if selected is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
