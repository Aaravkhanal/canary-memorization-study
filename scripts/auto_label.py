#!/usr/bin/env python3
"""Audit manual novelty-label completion without modifying any labels.

The original version assigned one heuristic label to an entire file from n-gram overlap. That does not implement
the pre-registered V/T/N judgment and produced invalid labels (including V for zero-overlap generations). Phase 5
requires a person to read each generation. This compatibility entry point is intentionally read-only so an old
command cannot overwrite those judgments again.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


LABEL_RE = re.compile(r"^LABEL: (____|[VTN])$", re.MULTILINE)
ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    labelling_dir = ROOT / "results" / "labelling"
    total = Counter()
    for txt_path in sorted(labelling_dir.glob("*.txt")):
        counts = Counter(LABEL_RE.findall(txt_path.read_text(encoding="utf-8")))
        total.update(counts)
        complete = counts["V"] + counts["T"] + counts["N"]
        print(
            f"{txt_path.name}: {complete}/{sum(counts.values())} manually labelled "
            f"(V={counts['V']}, T={counts['T']}, N={counts['N']}, blank={counts['____']})"
        )
    print(
        f"TOTAL: {total['V'] + total['T'] + total['N']}/{sum(total.values())} manually labelled; "
        f"{total['____']} remaining"
    )


if __name__ == "__main__":
    main()
