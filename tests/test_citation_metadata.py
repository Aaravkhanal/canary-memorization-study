from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_citation_metadata_is_parseable_and_does_not_invent_release_fields():
    payload = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    assert payload["cff-version"] == "1.2.0"
    assert payload["authors"] == [{"family-names": "Khanal", "given-names": "Aarav"}]
    assert payload["repository-code"].endswith("/Aaravkhanal/canary-memorization-study")
    assert "confirmatory extension is pre-registered but has not" in payload["abstract"]
    assert "doi" not in payload
    assert "license" not in payload
    assert "date-released" not in payload
