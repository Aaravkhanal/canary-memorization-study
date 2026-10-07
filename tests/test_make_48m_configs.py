import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "aarav-lm" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from make_48m_configs import FREQUENCIES, VARIANTS, make_config  # noqa: E402


def test_48m_scale_configs_match_study_token_budget_and_data():
    expected_tokens = 6000 * 1 * 16 * 512
    for variant in VARIANTS:
        for frequency in FREQUENCIES:
            config = make_config(variant, frequency)
            assert config["model_preset"] == "large"
            assert config["train"]["max_steps"] * config["train"]["batch_size"] * config["train"]["grad_accum"] * 512 == expected_tokens
            assert config["data"]["sources"][0].endswith(f"freq_{frequency}/corpus.txt")
            assert config["tokenizer"]["artifact_dir"].endswith("tokenizer_tinystories_v2")


def test_48m_seed_replicates_keep_data_assignment_fixed():
    first = make_config("scale_48m_baseline", 100, train_seed=20260927)
    second = make_config("scale_48m_baseline", 100, train_seed=1338)
    assert first["data"] == second["data"]
    assert first["train"]["seed"] != second["train"]["seed"]


def test_48m_architectures_remain_near_parameter_matched():
    from aarav_lm.config.config import get_preset
    from aarav_lm.model.core import AaravLM

    expected = {
        "scale_48m_baseline": 48_100_480,
        "scale_48m_learned_pos": 48_428_160,
        "scale_48m_mha": 47_239_040,
        "scale_48m_layernorm": 48_100_480,
    }
    for variant, overrides in VARIANTS.items():
        assert AaravLM(get_preset("large", **overrides)).num_params() == expected[variant]
