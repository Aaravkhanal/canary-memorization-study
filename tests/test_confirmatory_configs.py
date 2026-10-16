import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT.parent / "aarav-lm" / "src"))
from make_confirmatory_configs import SCALES, SEEDS, make_config  # noqa: E402


def test_all_planned_configs_are_portable_and_token_budget_matched():
    for scale, spec in SCALES.items():
        for architecture in spec["architectures"]:
            for seed in SEEDS:
                config = make_config(scale, architecture, seed)
                assert config["train"]["max_steps"] * config["train"]["batch_size"] * config["train"]["grad_accum"] * 512 == 49_152_000
                assert config["train"]["lr"] == 0.0005
                assert config["data"]["seed"] == 20261016
                assert not Path(config["data"]["sources"][0]).is_absolute()
                assert not Path(config["tokenizer"]["artifact_dir"]).is_absolute()


def test_architectures_are_near_parameter_matched_at_each_scale():
    from aarav_lm.config.config import get_preset
    from aarav_lm.model.core import AaravLM

    for scale, spec in SCALES.items():
        counts = {
            architecture: AaravLM(get_preset(spec["preset"], **overrides)).num_params()
            for architecture, overrides in spec["architectures"].items()
        }
        baseline = counts["baseline"]
        assert all(abs(value - baseline) / baseline < 0.025 for value in counts.values()), (scale, counts)


def test_all_24_committed_configs_match_the_generator():
    paths = sorted((ROOT / "configs" / "confirmatory" / "training").glob("*/*/*.yaml"))
    assert len(paths) == 24
    for path in paths:
        scale, architecture = path.parts[-3:-1]
        seed = int(path.stem.removeprefix("seed_"))
        assert yaml.safe_load(path.read_text()) == make_config(scale, architecture, seed)
