from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_citation_metadata_is_parseable_and_does_not_invent_release_fields():
    payload = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    assert payload["cff-version"] == "1.2.0"
    assert payload["authors"] == [{"family-names": "Khanal", "given-names": "Aarav"}]
    assert payload["repository-code"].endswith("/Aaravkhanal/canary-memorization-study")
    assert "24-cell confirmatory computational grid" in payload["abstract"]
    assert "human novelty endpoint remains pending" in payload["abstract"]
    assert "doi" not in payload
    assert payload["license"] == "MIT"
    assert "date-released" not in payload
