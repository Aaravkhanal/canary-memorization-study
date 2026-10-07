#!/usr/bin/env python3
"""Generate the 48.1M scale-transfer configs for the controlled canary grid.

These are fresh training runs for four near-parameter-matched architectures on the
same frequency-specific corpora and tokenizer as the 14.2M study. They use the 14M
study's 6,000 updates, 8,192 tokens/update, and sequence length, giving 49.152M
training tokens per cell. The 48M model's separate 15,000-step, 245.76M-token MY-LLM
run is not a matched comparator.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
AARAV_LM = ROOT.parent / "aarav-lm"
FREQUENCIES = (0, 1, 10, 50, 100, 500)
VARIANTS = {
    "scale_48m_baseline": {},
    "scale_48m_learned_pos": {"arch": "gpt2"},
    "scale_48m_mha": {"n_layer": 9, "n_kv_head": 10},
    "scale_48m_layernorm": {"norm_type": "layernorm"},
}


def make_config(variant: str, frequency: int, train_seed: int = 20260927) -> dict:
    overrides = VARIANTS[variant]
    corpus = ROOT / "data" / "processed" / f"freq_{frequency}" / "corpus.txt"
    out_dir = ROOT / "data" / "processed" / f"freq_{frequency}" / "tokenized"
    return {
        "name": f"{variant}_freq{frequency}_seed{train_seed}",
        "description": (
            f"48M scale-transfer experiment ({variant}); frequency {frequency}; same source corpus, tokenizer, "
            "token budget, sequence length, and effective batch shape as the 14.2M exploratory study."
        ),
        "model_preset": "large",
        "model_overrides": overrides,
        "tokenizer": {
            "kind": "bpe", "vocab_size": 4096,
            "artifact_dir": str(AARAV_LM / "artifacts" / "tokenizer_tinystories_v2"),
            "train_files": [],
        },
        "data": {
            "sources": [str(corpus)], "format": "txt", "doc_separator": "<|endoftext|>",
            "out_dir": str(out_dir), "val_fraction": 0.01, "test_fraction": 0.01,
            "min_chars": 20, "max_chars": 20000, "dedup": False, "seed": 20260927,
        },
        "train": {
            "seed": train_seed, "device": "auto", "precision": "fp32", "max_steps": 6000,
            "batch_size": 1, "grad_accum": 16, "eval_batch_size": 4,
            "lr": 0.0005, "min_lr_ratio": 0.1, "warmup_steps": 150,
            "weight_decay": 0.1, "grad_clip": 1.0, "eval_interval": 500,
            "eval_iters": 50, "log_interval": 25, "ckpt_interval": 500, "keep_last": 2,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260927)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "configs" / "training" / "scale_48m")
    args = parser.parse_args()
    for variant in VARIANTS:
        variant_dir = args.output_dir / variant
        variant_dir.mkdir(parents=True, exist_ok=True)
        for frequency in FREQUENCIES:
            path = variant_dir / f"freq_{frequency}_seed{args.seed}.yaml"
            path.write_text(yaml.safe_dump(make_config(variant, frequency, args.seed), sort_keys=False), encoding="utf-8")
            print(f"[wrote] {path}")


if __name__ == "__main__":
    main()
