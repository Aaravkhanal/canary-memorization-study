import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_blinded_annotations import build_records, write_batches  # noqa: E402
from score_blinded_annotations import (  # noqa: E402
    cohen_kappa,
    combine_labels,
    krippendorff_alpha_nominal,
    score,
    wilson_interval,
)


def write_novelty(path: Path) -> None:
    groups = []
    for canary in ("char_a", "char_b"):
        groups.append({
            "canary_id": canary,
            "type": "character",
            "setting": "on the moon",
            "prompt": f"Write about {canary} on the moon.",
            "completions": [
                {"text": f"{canary} completion {i}", "max_ngram_overlap": i / 10, "min_edit_distance": 10 + i}
                for i in range(4)
            ],
        })
    path.write_text(json.dumps({"checkpoint": "secret/path.pt", "frequency": 10, "groups": groups}))


def test_balanced_sampling_is_deterministic_and_ignores_seed_suffix_files(tmp_path):
    write_novelty(tmp_path / "novelty_baseline_freq10.json")
    write_novelty(tmp_path / "novelty_baseline_freq10_seed1338.json")
    first = build_records(tmp_path, {10}, per_group=2, seed=7)
    second = build_records(tmp_path, {10}, per_group=2, seed=7)
    assert first == second
    assert len(first) == 4  # two canaries/groups x two completions; seed-suffixed file is excluded
    assert {row["canary_id"] for row in first} == {"char_a", "char_b"}


def test_annotator_batch_hides_condition_and_automated_scores(tmp_path):
    results, out = tmp_path / "results", tmp_path / "annotations"
    results.mkdir(); write_novelty(results / "novelty_variant_x_freq10.json")
    records = build_records(results, {10}, per_group=1, seed=4)
    write_batches(records, out, ["rater_a"], seed=4, force=False)
    with (out / "rater_a.csv").open(newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["sample_id", "prompt", "generation", "label", "confidence", "notes"]
        rows = list(reader)
    assert rows and all("variant" not in row and "frequency" not in row for row in rows)
    manifest = json.loads((out / "private_manifest.json").read_text())
    assert manifest["records"][0]["variant"] == "variant_x"


def test_existing_labels_are_never_overwritten_without_force(tmp_path):
    results, out = tmp_path / "results", tmp_path / "annotations"
    results.mkdir(); write_novelty(results / "novelty_baseline_freq10.json")
    records = build_records(results, {10}, per_group=1, seed=1)
    write_batches(records, out, ["rater_a"], seed=1, force=False)
    text = (out / "rater_a.csv").read_text().replace(",,,\n", ",N,,\n", 1)
    (out / "rater_a.csv").write_text(text)
    with pytest.raises(FileExistsError):
        write_batches(records, out, ["rater_a"], seed=1, force=False)


def test_agreement_statistics_are_one_for_identical_raters():
    a = {"s1": "N", "s2": "T", "s3": "V", "s4": "N"}
    kappa, agreement = cohen_kappa(a, dict(a))
    assert kappa == pytest.approx(1.0) and agreement == 1.0
    assert krippendorff_alpha_nominal([a, dict(a)]) == pytest.approx(1.0)


def test_disagreements_require_adjudication():
    a = {"s1": "N", "s2": "T"}; b = {"s1": "V", "s2": "T"}
    final, disagreements = combine_labels([a, b])
    assert final == {"s2": "T"} and disagreements == ["s1"]
    final, disagreements = combine_labels([a, b], {"s1": "N"})
    assert final == {"s1": "N", "s2": "T"} and disagreements == []


def test_scoring_reports_condition_counts_and_intervals():
    manifest = {"records": [
        {"sample_id": "s1", "variant": "baseline", "frequency": 10, "canary_id": "a", "setting": "moon"},
        {"sample_id": "s2", "variant": "baseline", "frequency": 10, "canary_id": "a", "setting": "moon"},
        {"sample_id": "s3", "variant": "baseline", "frequency": 10, "canary_id": "b", "setting": "ship"},
        {"sample_id": "s4", "variant": "baseline", "frequency": 10, "canary_id": "b", "setting": "ship"},
    ]}
    rows, summary = score(manifest, {"s1": "N", "s2": "N", "s3": "T", "s4": "V"})
    assert summary["n_scored"] == 4
    assert rows[0]["genuine_novel_fraction"] == 0.5
    assert rows[0]["genuine_novel"] == 2 and rows[0]["template_copy"] == 1 and rows[0]["verbatim"] == 1
    low, high = wilson_interval(2, 4)
    assert low < 0.5 < high
