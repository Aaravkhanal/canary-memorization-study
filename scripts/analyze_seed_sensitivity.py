#!/usr/bin/env python3
"""Summarize paired baseline exposure-lift changes across training seeds.

This is a descriptive sensitivity audit, not an inferential variance estimate. It
compares the main baseline seed (20260927) with the alternate training seed
(1338), subtracting each seed's own frequency-0 exposure before comparing lifts.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FREQUENCIES = (1, 10, 100, 500)
CLEAN_CANARIES = ("char_nira", "char_boro", "char_suri", "plot_song", "plot_lantern")


def load_exposures(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    exposures = {
        row["id"]: float(row["exposure"]["exposure"])
        for row in payload["rows"]
    }
    if len(exposures) != len(payload["rows"]):
        raise ValueError(f"duplicate canary IDs in {path}")
    return exposures


def verify_seed_configs(config_dir: Path, frequency: int) -> None:
    original = yaml.safe_load((config_dir / f"freq_{frequency}.yaml").read_text(encoding="utf-8"))
    alternate = yaml.safe_load((config_dir / f"freq_{frequency}_seed1338.yaml").read_text(encoding="utf-8"))
    if original["data"]["seed"] != alternate["data"]["seed"]:
        raise ValueError(f"frequency {frequency}: data.seed differs between paired configs")
    if original["train"]["seed"] == alternate["train"]["seed"]:
        raise ValueError(f"frequency {frequency}: train.seed did not change")
    if int(alternate["train"]["seed"]) != 1338:
        raise ValueError(f"frequency {frequency}: alternate config is not train.seed 1338")


def paired_lift_row(
    frequency: int,
    canary_id: str,
    main: dict[str, float],
    alternate: dict[str, float],
    main_zero: dict[str, float],
    alternate_zero: dict[str, float],
) -> dict[str, object]:
    lift_main = main[canary_id] - main_zero[canary_id]
    lift_alternate = alternate[canary_id] - alternate_zero[canary_id]
    return {
        "frequency": frequency,
        "canary_id": canary_id,
        "lift_seed20260927": lift_main,
        "lift_seed1338": lift_alternate,
        "delta_seed1338_minus_seed20260927": lift_alternate - lift_main,
    }


def paired_rows(results_dir: Path, config_dir: Path) -> list[dict[str, object]]:
    verify_seed_configs(config_dir, 0)
    base_zero = load_exposures(results_dir / "mem_baseline_freq0.json")
    seed_zero = load_exposures(results_dir / "mem_baseline_freq0_seed1338.json")
    if base_zero.keys() != seed_zero.keys():
        raise ValueError("frequency-0 paired runs have different canary IDs")

    rows = []
    for frequency in FREQUENCIES:
        verify_seed_configs(config_dir, frequency)
        main = load_exposures(results_dir / f"mem_baseline_freq{frequency}.json")
        alternate = load_exposures(results_dir / f"mem_baseline_freq{frequency}_seed1338.json")
        if main.keys() != base_zero.keys() or alternate.keys() != seed_zero.keys():
            raise ValueError(f"frequency {frequency}: paired outputs have different canary IDs")
        for canary_id in CLEAN_CANARIES:
            if canary_id not in main:
                raise ValueError(f"missing clean canary {canary_id} at frequency {frequency}")
            rows.append(paired_lift_row(frequency, canary_id, main, alternate, base_zero, seed_zero))
    return rows


def write_audit(rows: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--config-dir", type=Path, default=ROOT / "configs" / "training" / "baseline")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "seed_sensitivity_clean.csv")
    args = parser.parse_args()

    rows = paired_rows(args.results_dir, args.config_dir)
    write_audit(rows, args.output)
    print(f"[wrote] {args.output} ({len(rows)} clean-canary paired lift comparisons)")
    for frequency in FREQUENCIES:
        values = [float(row["delta_seed1338_minus_seed20260927"]) for row in rows if row["frequency"] == frequency]
        mean_delta = sum(values) / len(values)
        max_abs = max(abs(value) for value in values)
        print(f"frequency={frequency} clean_mean_delta={mean_delta:.3f} max_abs_canary_delta={max_abs:.3f}")


if __name__ == "__main__":
    main()
