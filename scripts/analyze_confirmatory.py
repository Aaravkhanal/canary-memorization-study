#!/usr/bin/env python3
"""Run the frozen confirmatory exposure and human-novelty models.

This script is intentionally unusable with partial/blinded labels: novelty input must contain complete,
adjudicated human V/T/N labels.  It may be committed and tested before outcomes, but it must not be changed after
confirmatory outcomes are inspected without a dated protocol deviation.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parents[1]
EXPOSURE_FORMULA = (
    "exposure_bits ~ log10_frequency * C(architecture, Sum) + "
    "log10_frequency * C(scale, Sum) + C(seed) + C(canary_id)"
)
NOVELTY_FORMULA = (
    "is_novel ~ log10_frequency * C(architecture, Sum) + "
    "log10_frequency * C(scale, Sum) + C(seed) + C(setting)"
)
ARCHITECTURES = {"baseline", "learned_pos", "mha", "layernorm"}
SCALES = {"14m", "48m"}


def holm_adjust(p_values: list[float]) -> list[float]:
    """Return Holm-adjusted p-values in original order."""
    count = len(p_values)
    order = sorted(range(count), key=lambda index: p_values[index])
    adjusted = [0.0] * count
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (count - rank) * float(p_values[index])))
        adjusted[index] = running
    return adjusted


def require_columns(frame: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = columns - set(frame.columns)
    if missing:
        raise ValueError(f"{name} input is missing columns: {sorted(missing)}")


def validate_common(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    require_columns(frame, {"seed", "scale", "architecture", "canary_id", "frequency"}, name)
    if set(frame["architecture"]) - ARCHITECTURES:
        raise ValueError(f"{name} has unknown architectures: {sorted(set(frame['architecture']) - ARCHITECTURES)}")
    if set(frame["scale"]) - SCALES:
        raise ValueError(f"{name} has unknown scales: {sorted(set(frame['scale']) - SCALES)}")
    if frame[list({"seed", "scale", "architecture", "canary_id", "frequency"})].isna().any().any():
        raise ValueError(f"{name} has missing design values")
    if (pd.to_numeric(frame["frequency"], errors="coerce") <= 0).any():
        raise ValueError(f"{name} frequency must be positive")
    result = frame.copy()
    result["log10_frequency"] = np.log10(result["frequency"].astype(float))
    result["log10_frequency"] -= result["log10_frequency"].mean()
    return result


def effect_rows(result) -> list[dict]:
    intervals = result.conf_int(alpha=0.05)
    rows = []
    for term in result.params.index:
        if "log10_frequency" not in term:
            continue
        rows.append({
            "term": term,
            "estimate": float(result.params[term]),
            "standard_error": float(result.bse[term]),
            "ci95_low": float(intervals.loc[term, 0]),
            "ci95_high": float(intervals.loc[term, 1]),
            "p_value": float(result.pvalues[term]),
        })
    architecture = [row for row in rows if ":C(architecture, Sum)" in row["term"]]
    adjusted = holm_adjust([row["p_value"] for row in architecture])
    for row, value in zip(architecture, adjusted):
        row["holm_p_value"] = value
    return rows


def fit_exposure(frame: pd.DataFrame) -> dict:
    require_columns(frame, {"exposure_bits"}, "exposure")
    frame = validate_common(frame, "exposure")
    frame["exposure_bits"] = pd.to_numeric(frame["exposure_bits"], errors="raise")
    if not np.isfinite(frame["exposure_bits"]).all():
        raise ValueError("exposure_bits must be finite")
    fit = smf.ols(EXPOSURE_FORMULA, data=frame).fit(
        cov_type="cluster", cov_kwds={"groups": frame["canary_id"].to_numpy()}
    )
    payload = {
        "formula": EXPOSURE_FORMULA,
        "estimator": "OLS with canary-clustered covariance",
        "rows": len(frame),
        "canary_clusters": int(frame["canary_id"].nunique()),
        "effects": effect_rows(fit),
        "fallbacks": [],
    }
    if "at_ceiling" in frame.columns:
        sensitivity = frame.loc[~frame["at_ceiling"].astype(bool)]
        if len(sensitivity) and sensitivity["canary_id"].nunique() >= 2:
            fit_sensitivity = smf.ols(EXPOSURE_FORMULA, data=sensitivity).fit(
                cov_type="cluster", cov_kwds={"groups": sensitivity["canary_id"].to_numpy()}
            )
            payload["non_ceiling_sensitivity"] = {
                "rows": len(sensitivity), "effects": effect_rows(fit_sensitivity)
            }
    return payload


def fit_novelty(frame: pd.DataFrame) -> dict:
    require_columns(frame, {"setting", "label"}, "novelty")
    frame = validate_common(frame, "novelty")
    if frame["label"].isna().any() or not set(frame["label"]).issubset({"V", "T", "N"}):
        raise ValueError("novelty labels must be complete adjudicated human V/T/N values")
    frame["is_novel"] = (frame["label"] == "N").astype(int)
    failures = []
    working = "exchangeable"
    try:
        fit = smf.gee(
            NOVELTY_FORMULA, groups="canary_id", data=frame, family=sm.families.Binomial(),
            cov_struct=sm.cov_struct.Exchangeable(),
        ).fit()
    except Exception as exc:  # pragma: no cover - fallback is data-dependent and recorded verbatim
        failures.append(f"exchangeable GEE failed: {type(exc).__name__}: {exc}")
        working = "independence"
        fit = smf.gee(
            NOVELTY_FORMULA, groups="canary_id", data=frame, family=sm.families.Binomial(),
            cov_struct=sm.cov_struct.Independence(),
        ).fit()
    return {
        "formula": NOVELTY_FORMULA,
        "estimator": f"binomial GEE with {working} working correlation and canary clusters",
        "rows": len(frame),
        "canary_clusters": int(frame["canary_id"].nunique()),
        "novel_count": int(frame["is_novel"].sum()),
        "effects": effect_rows(fit),
        "fallbacks": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exposure-csv", type=Path)
    parser.add_argument("--novelty-csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.exposure_csv and not args.novelty_csv:
        raise SystemExit("provide --exposure-csv and/or --novelty-csv")
    payload = {
        "schema_version": 1,
        "status": "confirmatory analysis output",
        "analysis_plan": "configs/confirmatory/analysis_plan.json",
    }
    if args.exposure_csv:
        payload["exposure"] = fit_exposure(pd.read_csv(args.exposure_csv))
    if args.novelty_csv:
        payload["novelty"] = fit_novelty(pd.read_csv(args.novelty_csv))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"[wrote] {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
