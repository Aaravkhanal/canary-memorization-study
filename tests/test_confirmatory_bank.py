import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_confirmatory_bank import (  # noqa: E402
    FREQUENCIES, SEEDS, build_schedule, character_alternatives, normalize, occurrences, screen_phrases,
)


def test_normalized_occurrence_matching():
    corpus = normalize("Qél One  QEL two. The odd phrase is here.")
    assert occurrences(corpus, "qél") == 1
    assert occurrences(corpus, "qel") == 1
    assert occurrences(corpus, "odd   phrase") == 1
    assert occurrences(corpus, "odd phrases") == 0


def test_reference_pool_has_1024_unique_names():
    alternatives = character_alternatives()
    assert len(alternatives) == len(set(alternatives)) == 1024


def test_indexed_screening_uses_nonce_anchor_for_plot_references():
    corpus = normalize("Qellic appears alone, while the ordinary blue token rested nearby.")
    phrases = ["Absentname", "Qellic", "the qellic token rested beside the qelmar", "ordinary blue token"]
    contaminated = screen_phrases(corpus, phrases, {phrases[2]})
    assert contaminated == {"Qellic": 1, "ordinary blue token": 1}


def test_schedule_is_balanced_and_rotates_each_identity():
    canaries = [
        {"id": f"{kind}_{index:02d}", "type": kind}
        for kind in ("character", "plot") for index in range(20)
    ]
    schedule = build_schedule(canaries)
    assert set(schedule) == {str(seed) for seed in SEEDS}
    for rows in schedule.values():
        for kind in ("character", "plot"):
            counts = Counter(freq for cid, freq in rows.items() if cid.startswith(kind))
            assert counts == {frequency: 4 for frequency in FREQUENCIES}
    for canary in canaries:
        assert len({schedule[str(seed)][canary["id"]] for seed in SEEDS}) == 5


def test_committed_bank_shape_and_screening():
    path = Path(__file__).resolve().parents[1] / "configs" / "confirmatory" / "canary_bank.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["canaries"]) == 40
    assert len(payload["controls"]) == 8
    assert len(payload["reference_pools"]["character"]) == 1024
    assert len(payload["reference_pools"]["plot"]) == 1024
    assert payload["screening"]["nonzero_occurrences"] == 0
