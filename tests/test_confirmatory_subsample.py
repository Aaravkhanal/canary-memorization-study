import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_confirmatory_subsample import select_ids  # noqa: E402


def test_subsample_preserves_every_cell_canary_group():
    expanded = []
    for scale in ("14m", "48m"):
        for architecture in ("baseline", "learned_pos", "mha", "layernorm"):
            for seed in (1, 2, 3):
                for canary in range(40):
                    for setting in range(4):
                        for completion in range(2):
                            expanded.append({
                                "sample_id": f"{scale}-{architecture}-{seed}-{canary}-{setting}-{completion}",
                                "scale": scale, "architecture": architecture, "training_seed": seed,
                                "canary_id": f"c{canary}",
                                "canary_type": "character" if canary < 20 else "plot",
                                "setting": f"setting-{setting}", "completion_index": completion,
                            })
    ids, selected = select_ids(expanded, b"fixed-test-secret")
    assert len(ids) == len(selected) == 1920
    groups = {(x["scale"], x["architecture"], x["training_seed"], x["canary_id"]) for x in selected}
    assert len(groups) == 960


def test_subsample_is_deterministic_and_secret_keyed():
    items = []
    for scale in ("14m", "48m"):
        for architecture in ("baseline", "learned_pos", "mha", "layernorm"):
            for seed in (1, 2, 3):
                for canary in range(40):
                    for setting in range(4):
                        for completion in range(2):
                            items.append({
                                "sample_id": f"{scale}-{architecture}-{seed}-{canary}-{setting}-{completion}",
                                "scale": scale, "architecture": architecture, "training_seed": seed,
                                "canary_id": f"c{canary}", "canary_type": "character",
                                "setting": f"s{setting}", "completion_index": completion,
                            })
    first, _ = select_ids(items, b"secret-a")
    second, _ = select_ids(items, b"secret-a")
    other, _ = select_ids(items, b"secret-b")
    assert first == second
    assert first != other
