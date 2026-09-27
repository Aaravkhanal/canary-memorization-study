"""Tests for scripts/analyze_tradeoff.py against synthetic JSON matching the real schemas eval_memorization.py and
eval_novelty.py produce, plus an end-to-end smoke test of the CSV and plot outputs."""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_tradeoff import build_table, find_runs, load_labels, mean_distinct_2, mean_exposure, mean_extraction_rate, mean_max_overlap, write_csv  # noqa: E402


def mem_result(exposures_inserted, exposures_control, extractions):
    rows = []
    for e, x in zip(exposures_inserted, extractions):
        rows.append({"group": "inserted", "exposure": {"exposure": e}, "extraction": {"exact_match": x}})
    for e in exposures_control:
        rows.append({"group": "unseen_control", "exposure": {"exposure": e}, "extraction": {"exact_match": False}})
    return {"rows": rows}


def novelty_result(distinct_2s, max_overlaps):
    groups = []
    for d, overlaps in zip(distinct_2s, max_overlaps):
        groups.append({"distinct_2": d, "completions": [{"max_ngram_overlap": o} for o in overlaps]})
    return {"groups": groups}


# ── aggregation over a single result ─────────────────────────────────────────

def test_mean_exposure_averages_only_the_requested_group():
    m = mem_result(exposures_inserted=[2.0, 4.0], exposures_control=[0.5], extractions=[False, False])
    assert mean_exposure(m, "inserted") == 3.0
    assert mean_exposure(m, "unseen_control") == 0.5


def test_mean_exposure_is_none_when_the_group_is_empty():
    m = mem_result(exposures_inserted=[], exposures_control=[1.0], extractions=[])
    assert mean_exposure(m, "inserted") is None


def test_mean_extraction_rate_is_the_fraction_of_exact_matches():
    m = mem_result(exposures_inserted=[1.0, 1.0, 1.0, 1.0], exposures_control=[], extractions=[True, True, False, False])
    assert mean_extraction_rate(m) == 0.5


def test_mean_distinct_2_and_max_overlap():
    n = novelty_result(distinct_2s=[0.3, 0.7], max_overlaps=[[0.1, 0.2], [0.9]])
    assert mean_distinct_2(n) == 0.5
    assert mean_max_overlap(n) == (0.2 + 0.9) / 2                     # max within each group, then averaged across groups


# ── file discovery ────────────────────────────────────────────────────────────

def test_find_runs_matches_the_real_naming_convention(tmp_path):
    (tmp_path / "mem_baseline_freq1.json").write_text("{}")
    (tmp_path / "novelty_baseline_freq1.json").write_text("{}")
    (tmp_path / "mem_variant_a_learned_pos_freq10.json").write_text("{}")
    (tmp_path / "not_a_result.json").write_text("{}")
    runs = find_runs(tmp_path)
    assert set(runs) == {("baseline", 1), ("variant_a_learned_pos", 10)}
    assert set(runs[("baseline", 1)]) == {"mem", "novelty"}
    assert set(runs[("variant_a_learned_pos", 10)]) == {"mem"}


# ── the full table, with and without a baseline ───────────────────────────────

def test_build_table_computes_memorization_lift_when_a_baseline_is_available(tmp_path):
    results = tmp_path / "results"; results.mkdir()
    baseline = tmp_path / "baseline"; baseline.mkdir()
    (results / "mem_baseline_freq10.json").write_text(json.dumps(mem_result([3.0], [1.0], [False])))
    (results / "novelty_baseline_freq10.json").write_text(json.dumps(novelty_result([0.6], [[0.1]])))
    (baseline / "mem_baseline_freq0.json").write_text(json.dumps(mem_result([1.0], [1.0], [False])))   # this architecture's own zero-exposure run

    rows = build_table(results, baseline, {})
    assert len(rows) == 1
    row = rows[0]
    assert row["variant"] == "baseline" and row["frequency"] == 10
    assert row["exposure_inserted"] == 3.0
    assert row["memorization_score"] == 2.0                            # 3.0 - 1.0 baseline, not raw exposure
    assert row["novelty_score"] == 0.6


def test_build_table_falls_back_to_raw_exposure_without_a_baseline(tmp_path):
    results = tmp_path / "results"; results.mkdir()
    (results / "mem_baseline_freq10.json").write_text(json.dumps(mem_result([3.0], [1.0], [False])))
    rows = build_table(results, None, {})
    assert rows[0]["memorization_score"] == 3.0                        # no baseline available: raw exposure, not silently wrong


def test_hand_labels_override_the_distinct_2_proxy(tmp_path):
    results = tmp_path / "results"; results.mkdir()
    (results / "novelty_baseline_freq10.json").write_text(json.dumps(novelty_result([0.6], [[0.1]])))
    labels_csv = tmp_path / "labels.csv"
    with labels_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["variant", "freq", "label"])
        w.writeheader()
        w.writerow({"variant": "baseline", "freq": "10", "label": "N"})
        w.writerow({"variant": "baseline", "freq": "10", "label": "V"})
        w.writerow({"variant": "baseline", "freq": "10", "label": "n"})   # case-insensitive
    labels = load_labels(labels_csv)
    assert labels[("baseline", 10)] == 2 / 3
    rows = build_table(results, None, labels)
    assert rows[0]["novelty_score"] == 2 / 3 and rows[0]["novelty_score_is_hand_labelled"] is True


def test_load_labels_is_empty_for_a_missing_file():
    assert load_labels(None) == {}
    assert load_labels(Path("/nonexistent/path.csv")) == {}


# ── CSV output ─────────────────────────────────────────────────────────────────

def test_write_csv_round_trips_every_row(tmp_path):
    rows = [{"variant": "baseline", "frequency": 1, "memorization_score": 2.0, "novelty_score": 0.5},
            {"variant": "variant_a", "frequency": 10, "memorization_score": 3.0, "novelty_score": 0.4}]
    out = tmp_path / "out.csv"
    write_csv(rows, out)
    with out.open() as f:
        got = list(csv.DictReader(f))
    assert len(got) == 2 and got[0]["variant"] == "baseline" and got[1]["frequency"] == "10"


# ── end to end, including the plot ─────────────────────────────────────────────

def test_main_end_to_end_writes_a_csv_and_a_plot(tmp_path, monkeypatch):
    import analyze_tradeoff as m
    results = tmp_path / "results"; results.mkdir()
    for freq in (1, 10, 100):
        (results / f"mem_baseline_freq{freq}.json").write_text(json.dumps(mem_result([float(freq) % 5 + 1], [0.5], [freq > 50])))
        (results / f"novelty_baseline_freq{freq}.json").write_text(json.dumps(novelty_result([0.9 - freq / 200], [[0.1 * (freq / 100)]])))
    out_csv, out_plot = tmp_path / "tradeoff.csv", tmp_path / "tradeoff.png"
    monkeypatch.setattr(sys, "argv", ["analyze_tradeoff.py", "--results-dir", str(results), "--out-csv", str(out_csv), "--out-plot", str(out_plot)])
    m.main()
    assert out_csv.exists() and out_plot.exists() and out_plot.stat().st_size > 0
    with out_csv.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3 and {r["frequency"] for r in rows} == {"1", "10", "100"}


def test_main_reports_cleanly_when_no_results_exist(tmp_path, capsys):
    import analyze_tradeoff as m
    old_argv = sys.argv
    try:
        sys.argv = ["analyze_tradeoff.py", "--results-dir", str(tmp_path)]
        m.main()
    finally:
        sys.argv = old_argv
    assert "no results found" in capsys.readouterr().out
