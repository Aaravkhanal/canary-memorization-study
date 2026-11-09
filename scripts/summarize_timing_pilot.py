#!/usr/bin/env python3
"""Validate and summarize the 80-item blinded investigator timing pilot."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VALID_LABELS = {"V", "T", "N"}
VALID_CONFIDENCE = {"low", "medium", "high"}


def summarize(rows: list[dict], target_items: int = 1920) -> dict:
    if len(rows) != 80:
        raise ValueError(f"timing pilot requires 80 rows, found {len(rows)}")
    seconds = []
    for index, row in enumerate(rows, start=1):
        if row.get("pilot_label", "").strip().upper() not in VALID_LABELS:
            raise ValueError(f"row {index} has missing/invalid pilot_label")
        if row.get("confidence", "").strip().lower() not in VALID_CONFIDENCE:
            raise ValueError(f"row {index} has missing/invalid confidence")
        try:
            value = float(row.get("seconds", ""))
        except ValueError as exc:
            raise ValueError(f"row {index} has invalid seconds") from exc
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"row {index} seconds must be positive and finite")
        seconds.append(value)
    array = np.asarray(seconds)
    block_medians = [float(np.median(array[start:start + 20])) for start in range(0, 80, 20)]
    median = float(np.median(array))
    p75 = float(np.percentile(array, 75))
    return {
        "schema_version": 1, "pilot_items": 80, "target_items_per_rater": target_items,
        "median_seconds_per_item": median, "p75_seconds_per_item": p75,
        "mean_seconds_per_item": float(np.mean(array)),
        "block_median_seconds": block_medians,
        "fourth_vs_first_block_ratio": block_medians[-1] / block_medians[0],
        "estimated_active_hours_at_median": target_items * median / 3600,
        "estimated_active_hours_at_p75": target_items * p75 / 3600,
        "fatigue_flag": block_medians[-1] >= 1.25 * block_medians[0],
        "warning": "Investigator workflow timing only; pilot labels are not study outcomes.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=ROOT / "results/confirmatory/annotation_amended/timing_pilot_80.csv")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/confirmatory/annotation_amended/timing_pilot_summary.json")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as handle:
        payload = summarize(list(csv.DictReader(handle)))
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
