"""
Phase 6: aggregate memorization (Phase 4) and novelty (Phase 5) results into the trade-off plot and a tidy table.

    python scripts/analyze_tradeoff.py --results-dir results --out-plot results/tradeoff.png --out-csv results/tradeoff.csv

Reads every `results/mem_<variant>_freq<F>.json` (from `eval_memorization.py`) and matching
`results/novelty_<variant>_freq<F>.json` (from `eval_novelty.py`) it can find, and produces:

  * one point per (architecture variant, frequency) cell: memorization score (x) vs. novelty score (y)
  * one line per architecture variant, frequencies in increasing order, so a shift in the trade-off curve between
    architectures is visible directly, not just implied by separate numbers
  * a tidy CSV, one row per model run, with every metric this pipeline computed -- for the user's own further
    analysis, per the brief's explicit request

Per the brief, this script produces plots and a table only. It does not write prose interpretation: that is for
the user to do first, at Checkpoint 6, before asking for help drafting a results section.

Score definitions (documented here so the plot's axes are never a mystery):
  memorization score = mean exposure LIFT over the zero-exposure baseline, across the run's inserted canaries
                       (PHASE4_NOTES.md: raw exposure has a coarse chance-level floor at this reference-set size,
                       so lift over a same-architecture, zero-canary-exposure baseline is what the axis should be,
                       not raw exposure -- passed in via --baseline-dir, one baseline result per architecture).
  novelty score       = mean distinct-2 across this run's completion groups (how different the model's own
                       completions are from each other): a fallback proxy for compositional novelty until the
                       Checkpoint 5 hand-labels exist. Once hand labels are in, replace this with the labelled
                       fraction of "genuine novel combination" (N) outputs -- the column is left ready for it
                       (`--labelled-csv`, optional, overrides the proxy per run where labels exist).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^(mem|novelty)_(?P<variant>.+)_freq(?P<freq>\d+)\.json$")


def find_runs(results_dir: Path) -> Dict[tuple, dict]:
    """{(variant, freq): {"mem": path_or_None, "novelty": path_or_None}}"""
    runs: Dict[tuple, dict] = {}
    for p in results_dir.glob("*.json"):
        m = NAME_RE.match(p.name)
        if not m:
            continue
        key = (m.group("variant"), int(m.group("freq")))
        runs.setdefault(key, {})[m.group(1)] = p
    return runs


def mean_exposure(mem_result: dict, group: str = "inserted", canary_ids: Optional[set] = None) -> Optional[float]:
    vals = [row["exposure"]["exposure"] for row in mem_result["rows"]
            if row["group"] == group and "exposure" in row and (canary_ids is None or row["id"] in canary_ids)]
    return sum(vals) / len(vals) if vals else None


def mean_extraction_rate(mem_result: dict, group: str = "inserted", canary_ids: Optional[set] = None) -> Optional[float]:
    vals = [row["extraction"]["exact_match"] for row in mem_result["rows"]
            if row["group"] == group and (canary_ids is None or row["id"] in canary_ids)]
    return sum(vals) / len(vals) if vals else None


def mean_distinct_2(novelty_result: dict, canary_ids: Optional[set] = None) -> Optional[float]:
    vals = [g["distinct_2"] for g in novelty_result["groups"] if canary_ids is None or g["canary_id"] in canary_ids]
    return sum(vals) / len(vals) if vals else None


def mean_max_overlap(novelty_result: dict, canary_ids: Optional[set] = None) -> Optional[float]:
    vals = [max((c["max_ngram_overlap"] for c in g["completions"]), default=0.0) for g in novelty_result["groups"]
            if canary_ids is None or g["canary_id"] in canary_ids]
    return sum(vals) / len(vals) if vals else None


def load_labels(path: Optional[Path]) -> Dict[tuple, float]:
    """Optional hand-label CSV (variant, freq, label) -> {(variant, freq): fraction labelled "N" (genuine novel)}.
    Overrides the distinct-2 proxy for any run that has real labels, per Checkpoint 6's own preference for measured
    data over a proxy once it exists."""
    if path is None or not path.exists():
        return {}
    from collections import defaultdict
    counts: Dict[tuple, list] = defaultdict(list)
    with path.open() as f:
        for row in csv.DictReader(f):
            counts[(row["variant"], int(row["freq"]))].append(row["label"].strip().upper())
    return {k: (v.count("N") / len(v) if v else None) for k, v in counts.items()}


def build_table(results_dir: Path, baseline_dir: Optional[Path], labels: Dict[tuple, float],
                 canary_ids: Optional[set] = None) -> List[dict]:
    """canary_ids, if given, restricts every mean to that set of canary ids -- e.g. excluding canaries whose
    identity is known-contaminated by pre-existing base-corpus occurrences (PHASE4_NOTES.md's root-cause finding),
    which otherwise dilutes the memorization score toward zero with canaries the metric can never move for reasons
    unrelated to training exposure."""
    runs = find_runs(results_dir)
    baselines = find_runs(baseline_dir) if baseline_dir else {}
    rows = []
    for (variant, freq), paths in sorted(runs.items()):
        row = {"variant": variant, "frequency": freq}
        if "mem" in paths:
            mem = json.loads(paths["mem"].read_text())
            row["exposure_inserted"] = mean_exposure(mem, canary_ids=canary_ids)
            row["exposure_control"] = mean_exposure(mem, group="unseen_control", canary_ids=canary_ids)
            row["extraction_rate"] = mean_extraction_rate(mem, canary_ids=canary_ids)
            base_key = (variant, 0)                          # frequency 0: this variant's own zero-exposure baseline
            if base_key in baselines and "mem" in baselines[base_key]:
                base_mem = json.loads(baselines[base_key]["mem"].read_text())
                base_exposure = mean_exposure(base_mem, canary_ids=canary_ids)
                if base_exposure is not None and row["exposure_inserted"] is not None:
                    row["memorization_score"] = row["exposure_inserted"] - base_exposure
            if "memorization_score" not in row:
                row["memorization_score"] = row.get("exposure_inserted")   # no baseline available: raw exposure, flagged in the CSV
                row["memorization_score_is_raw"] = "memorization_score" not in row or base_key not in baselines
        if "novelty" in paths:
            nov = json.loads(paths["novelty"].read_text())
            row["distinct_2_proxy"] = mean_distinct_2(nov, canary_ids=canary_ids)
            row["max_training_overlap"] = mean_max_overlap(nov, canary_ids=canary_ids)
            row["novelty_score"] = row["distinct_2_proxy"]
        if (variant, freq) in labels:
            row["novelty_score"] = labels[(variant, freq)]         # hand labels override the proxy when present
            row["novelty_score_is_hand_labelled"] = True
        rows.append(row)
    return rows


def write_csv(rows: List[dict], path: Path) -> None:
    if not rows:
        path.write_text("")
        return
    fields = sorted({k for r in rows for k in r})
    # a stable, readable column order for the columns we know about; anything else (future metrics) sorts after
    preferred = ["variant", "frequency", "memorization_score", "novelty_score", "exposure_inserted", "exposure_control",
                "extraction_rate", "distinct_2_proxy", "max_training_overlap", "novelty_score_is_hand_labelled", "memorization_score_is_raw"]
    fields = [f for f in preferred if f in fields] + [f for f in fields if f not in preferred]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        # Explicit LF endings keep tracked CSV outputs clean across platforms.
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def plot_tradeoff(rows: List[dict], out_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    by_variant: Dict[str, List[dict]] = {}
    for r in rows:
        if r.get("memorization_score") is None or r.get("novelty_score") is None:
            continue
        by_variant.setdefault(r["variant"], []).append(r)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    markers = ["o", "D", "s", "^", "v", "P"]
    # Green and ochre first (the two colours actually needed for the reduced first pass: baseline + one variant;
    # matches the palette already validated for aarav-lm's own charts). Extra hues only used if more variants are
    # added later.
    colors = ["#2f8558", "#a8611f", "#7a5195", "#c0392b", "#1b6b93", "#8d6e63"]
    for i, (variant, items) in enumerate(sorted(by_variant.items())):
        items = sorted(items, key=lambda r: r["frequency"])
        xs = [r["memorization_score"] for r in items]
        ys = [r["novelty_score"] for r in items]
        ax.plot(xs, ys, marker=markers[i % len(markers)], color=colors[i % len(colors)], label=variant, linewidth=1.5, markersize=7)
        for r in items:
            ax.annotate(str(r["frequency"]) + "x", (r["memorization_score"], r["novelty_score"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=8, color="#66645c")
    ax.set_xlabel("Memorization (exposure lift over zero-exposure baseline)")
    ax.set_ylabel("Novelty (distinct-2 across completions, or hand-labelled fraction \"genuine novel\")")
    ax.set_title("Memorization vs. compositional novelty, by canary frequency and architecture")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"[wrote] {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-dir", type=Path, default=ROOT / "results")
    ap.add_argument("--baseline-dir", type=Path, help="results from zero-canary-exposure baseline models, named mem_<variant>_freq0.json")
    ap.add_argument("--labelled-csv", type=Path, help="optional hand-label CSV from Checkpoint 5 (columns: variant,freq,label)")
    ap.add_argument("--out-plot", type=Path, default=ROOT / "results" / "tradeoff.png")
    ap.add_argument("--out-csv", type=Path, default=ROOT / "results" / "tradeoff.csv")
    ap.add_argument("--canaries", type=str,
                     help="comma-separated canary ids to restrict every mean to (e.g. to exclude canaries known "
                          "contaminated by pre-existing base-corpus occurrences, PHASE4_NOTES.md's root-cause "
                          "finding); default: every inserted canary")
    args = ap.parse_args()

    canary_ids = set(args.canaries.split(",")) if args.canaries else None
    labels = load_labels(args.labelled_csv)
    rows = build_table(args.results_dir, args.baseline_dir, labels, canary_ids=canary_ids)
    if not rows:
        print(f"no results found in {args.results_dir} matching mem_<variant>_freq<F>.json / novelty_<variant>_freq<F>.json")
        return
    write_csv(rows, args.out_csv)
    print(f"[wrote] {args.out_csv} ({len(rows)} rows)")
    plot_tradeoff(rows, args.out_plot)
    for r in rows:
        print(f"  {r['variant']:24s} freq={r['frequency']:<4d} memorization={r.get('memorization_score')}  novelty={r.get('novelty_score')}")


if __name__ == "__main__":
    main()
