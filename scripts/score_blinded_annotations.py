#!/usr/bin/env python3
"""Validate blinded V/T/N annotations, measure agreement, and score adjudicated labels."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALID_LABELS = {"V", "T", "N"}


def read_labels(path: Path) -> dict[str, str]:
    labels = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            sample_id = row["sample_id"].strip()
            label = row["label"].strip().upper()
            if label not in VALID_LABELS:
                raise ValueError(f"{path}: {sample_id} has missing/invalid label {label!r}")
            if sample_id in labels:
                raise ValueError(f"{path}: duplicate sample_id {sample_id}")
            labels[sample_id] = label
    return labels


def cohen_kappa(a: dict[str, str], b: dict[str, str]) -> tuple[float, float]:
    ids = sorted(set(a) & set(b))
    if not ids:
        raise ValueError("annotators have no shared sample IDs")
    observed = sum(a[i] == b[i] for i in ids) / len(ids)
    pa, pb = Counter(a[i] for i in ids), Counter(b[i] for i in ids)
    expected = sum((pa[label] / len(ids)) * (pb[label] / len(ids)) for label in VALID_LABELS)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    return kappa, observed


def krippendorff_alpha_nominal(raters: list[dict[str, str]]) -> float:
    ids = sorted(set.intersection(*(set(rater) for rater in raters)))
    pairs = [(r1[i], r2[i]) for i in ids for n, r1 in enumerate(raters) for r2 in raters[n + 1:]]
    observed_disagreement = sum(a != b for a, b in pairs) / len(pairs)
    marginals = Counter(label for rater in raters for i in ids for label in [rater[i]])
    total = sum(marginals.values())
    expected_disagreement = 1 - sum((count / total) ** 2 for count in marginals.values())
    return 1 - observed_disagreement / expected_disagreement if expected_disagreement else 1.0


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return math.nan, math.nan
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return centre - margin, centre + margin


def cluster_bootstrap_n_fraction(records: list[dict], iterations: int = 2000, seed: int = 20261007) -> tuple[float, float]:
    clusters = defaultdict(list)
    for record in records:
        clusters[(record["canary_id"], record["setting"])].append(record["label"] == "N")
    keys = sorted(clusters)
    rng = random.Random(seed)
    estimates = []
    for _ in range(iterations):
        chosen = [rng.choice(keys) for _ in keys]
        values = [value for key in chosen for value in clusters[key]]
        estimates.append(sum(values) / len(values))
    estimates.sort()
    return estimates[int(0.025 * iterations)], estimates[min(iterations - 1, int(0.975 * iterations))]


def combine_labels(raters: list[dict[str, str]], adjudicated: dict[str, str] | None = None) -> tuple[dict[str, str], list[str]]:
    ids = sorted(set.intersection(*(set(rater) for rater in raters)))
    final, disagreements = {}, []
    for sample_id in ids:
        labels = [rater[sample_id] for rater in raters]
        counts = Counter(labels)
        label, count = counts.most_common(1)[0]
        if count > len(raters) / 2:
            final[sample_id] = label
        elif adjudicated and sample_id in adjudicated:
            final[sample_id] = adjudicated[sample_id]
        else:
            disagreements.append(sample_id)
    return final, disagreements


def score(manifest: dict, final: dict[str, str]) -> tuple[list[dict], dict]:
    records = []
    for record in manifest["records"]:
        if record["sample_id"] in final:
            records.append({**record, "label": final[record["sample_id"]]})
    by_condition = defaultdict(list)
    for record in records:
        by_condition[(record["variant"], record["frequency"])].append(record)
    rows = []
    for (variant, frequency), items in sorted(by_condition.items()):
        counts = Counter(item["label"] for item in items)
        low_w, high_w = wilson_interval(counts["N"], len(items))
        low_c, high_c = cluster_bootstrap_n_fraction(items)
        rows.append({
            "variant": variant,
            "frequency": frequency,
            "n": len(items),
            "verbatim": counts["V"],
            "template_copy": counts["T"],
            "genuine_novel": counts["N"],
            "genuine_novel_fraction": counts["N"] / len(items),
            "wilson_ci_low": low_w,
            "wilson_ci_high": high_w,
            "cluster_bootstrap_ci_low": low_c,
            "cluster_bootstrap_ci_high": high_c,
        })
    return rows, {"n_scored": len(records), "label_counts": Counter(final.values())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, nargs="+", required=True)
    parser.add_argument("--adjudicated", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "annotations" / "scored")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    raters = [read_labels(path) for path in args.annotations]
    expected = {record["sample_id"] for record in manifest["records"]}
    for path, labels in zip(args.annotations, raters):
        if set(labels) != expected:
            raise ValueError(f"{path}: sample IDs differ from the private manifest")

    agreement = []
    for i in range(len(raters)):
        for j in range(i + 1, len(raters)):
            kappa, observed = cohen_kappa(raters[i], raters[j])
            agreement.append({"rater_a": args.annotations[i].name, "rater_b": args.annotations[j].name,
                              "cohen_kappa": kappa, "percent_agreement": observed})
    adjudicated = read_labels(args.adjudicated) if args.adjudicated else None
    final, disagreements = combine_labels(raters, adjudicated)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    disagreement_path = args.out_dir / "disagreements.csv"
    with disagreement_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample_id", *[path.name for path in args.annotations], "adjudicated_label"])
        for sample_id in disagreements:
            writer.writerow([sample_id, *[rater[sample_id] for rater in raters], ""])
    if disagreements:
        raise SystemExit(f"{len(disagreements)} disagreements require adjudication: {disagreement_path}")

    rows, summary = score(manifest, final)
    with (args.out_dir / "condition_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    payload = {**summary, "label_counts": dict(summary["label_counts"]), "agreement": agreement,
               "krippendorff_alpha_nominal": krippendorff_alpha_nominal(raters)}
    (args.out_dir / "annotation_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
