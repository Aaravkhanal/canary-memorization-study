#!/usr/bin/env python3
"""Build the frozen exposure-model input table from a complete evaluated grid."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "scale", "architecture", "seed", "canary_id", "canary_type", "frequency",
    "exposure_bits", "rank", "candidate_count", "at_ceiling", "source_path",
)


def build_rows(paths: list[Path], source_root: Path | None = None) -> list[dict]:
    if len(paths) != 24:
        raise ValueError(f"expected 24 evaluated cells, found {len(paths)}")
    source_root = source_root.resolve() if source_root is not None else None
    rows: list[dict] = []
    cells = set()
    for path in sorted(paths):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("full_training_corpus_overlap_complete") is not True:
            raise ValueError(f"cell is not fully evaluated: {path}")
        cell = payload["cell"]
        cell_key = (cell["scale"], cell["architecture"], int(cell["training_seed"]))
        if cell_key in cells:
            raise ValueError(f"duplicate cell: {cell_key}")
        cells.add(cell_key)
        if source_root is None:
            source_path = path.name
        else:
            try:
                source_path = path.resolve().relative_to(source_root).as_posix()
            except ValueError as exc:
                raise ValueError(f"evaluation result is outside source root: {path}") from exc
        exposure_rows = payload.get("exposure_rows", [])
        if len(exposure_rows) != 48:
            raise ValueError(f"expected 48 exposure rows in {path}, found {len(exposure_rows)}")
        inserted = [row for row in exposure_rows if row.get("group") == "inserted"]
        if len(inserted) != 40:
            raise ValueError(f"expected 40 inserted rows in {path}, found {len(inserted)}")
        for row in inserted:
            rows.append({
                "scale": cell["scale"], "architecture": cell["architecture"],
                "seed": int(cell["training_seed"]), "canary_id": row["canary_id"],
                "canary_type": row["canary_type"], "frequency": int(row["frequency"]),
                "exposure_bits": float(row["exposure"]), "rank": int(row["rank"]),
                "candidate_count": int(row["candidate_count"]),
                "at_ceiling": int(row["rank"] == 1), "source_path": source_path,
            })
    if len(rows) != 960:
        raise ValueError(f"expected 960 inserted-canary rows, found {len(rows)}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results" / "confirmatory")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "confirmatory" / "exposure_analysis_input.csv",
    )
    args = parser.parse_args()
    paths = sorted(args.results_root.glob("*/*/seed_*/evaluated.json"))
    rows = build_rows(paths, source_root=args.results_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"[wrote] {args.output}: {len(rows)} inserted-canary rows from 24 cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
