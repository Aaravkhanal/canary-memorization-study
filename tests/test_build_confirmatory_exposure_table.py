import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_confirmatory_exposure_table import build_rows  # noqa: E402


def test_build_rows_requires_complete_grid(tmp_path):
    with pytest.raises(ValueError, match="24 evaluated cells"):
        build_rows([])


def test_build_rows_emits_inserted_rows_only(tmp_path):
    paths = []
    for index in range(24):
        path = tmp_path / f"cell_{index}.json"
        exposure = [
            {
                "group": "inserted", "canary_id": f"c_{row}", "canary_type": "character",
                "frequency": 1, "exposure": 2.0, "rank": 2, "candidate_count": 1025,
            }
            for row in range(40)
        ] + [
            {
                "group": "control", "canary_id": f"control_{row}", "canary_type": "character",
                "frequency": 0, "exposure": 0.0, "rank": 1025, "candidate_count": 1025,
            }
            for row in range(8)
        ]
        path.write_text(json.dumps({
            "cell": {"scale": "14m", "architecture": "baseline", "training_seed": index},
            "full_training_corpus_overlap_complete": True,
            "exposure_rows": exposure,
        }))
        paths.append(path)
    rows = build_rows(paths, source_root=tmp_path)
    assert len(rows) == 960
    assert {row["frequency"] for row in rows} == {1}
    assert not any(row["canary_id"].startswith("control") for row in rows)
    assert {row["source_path"] for row in rows} == {f"cell_{index}.json" for index in range(24)}
    assert all(not Path(row["source_path"]).is_absolute() for row in rows)
