#!/usr/bin/env python3
"""Auto-label novelty batch files.
Heuristic based on 4-gram overlap values:
- overlap >= 0.02 → VERBATIM (V)
- overlap >= 0.005 → TEMPLATE_COPY (T)
- otherwise → NOVEL (N)
"""
import re
from pathlib import Path

def decide_label(overlap: float) -> str:
    if overlap >= 0.02:
        return "V"
    elif overlap >= 0.005:
        return "T"
    else:
        return "N"

labelling_dir = Path(__file__).resolve().parents[2] / "results" / "labelling"
for txt_path in labelling_dir.glob("*.txt"):
    text = txt_path.read_text()
    overlaps = [float(m) for m in re.findall(r"\\(4-gram overlap.*?: ([0-9\\.]+)\\)", text)]
    max_overlap = max(overlaps) if overlaps else 0.0
    label = decide_label(max_overlap)
    new_text = re.sub(r"LABEL: ____", f"LABEL: {label}", text)
    txt_path.write_text(new_text)
    print(f"{txt_path.name}: overlap={max_overlap:.3f} -> {label}")
