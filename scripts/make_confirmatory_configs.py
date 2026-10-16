#!/usr/bin/env python3
"""Generate portable, token-budget-matched 14M/48M confirmatory training configs."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SEEDS = (20261016, 20261017, 20261018)
SCALES = {
    "14m": {
        "preset": "small",
        "architectures": {
            "baseline": {},
            "learned_pos": {"arch": "gpt2"},
            "mha": {"n_layer": 7, "n_kv_head": 6},
            "layernorm": {"norm_type": "layernorm"},
        },
    },
    "48m": {
        "preset": "large",
        "architectures": {
            "baseline": {},
            "learned_pos": {"arch": "gpt2"},
            "mha": {"n_layer": 9, "n_kv_head": 10},
            "layernorm": {"norm_type": "layernorm"},
        },
    },
}


def make_config(scale: str, architecture: str, seed: int) -> dict:
    scale_spec = SCALES[scale]
    if architecture not in scale_spec["architectures"]:
        raise KeyError(architecture)
    corpus = f"data/confirmatory/seed_{seed}/corpus.txt"
    tokenized = f"data/confirmatory/seed_{seed}/tokenized"
    return {
        "name": f"confirmatory_{scale}_{architecture}_seed{seed}",
        "description": (
            f"Pre-registered contamination-free confirmatory study; {scale} {architecture}; "
            f"mixed-frequency assignment/training seed {seed}; common 49.152M-token budget and optimizer recipe."
        ),
        "model_preset": scale_spec["preset"],
        "model_overrides": scale_spec["architectures"][architecture],
        "tokenizer": {
            "kind": "bpe",
            "vocab_size": 4096,
            "artifact_dir": "artifacts/tokenizer_tinystories_v2",
            "train_files": [],
        },
        "data": {
            "sources": [corpus],
            "format": "txt",
            "doc_separator": "<|endoftext|>",
            "out_dir": tokenized,
            "val_fraction": 0.01,
            "test_fraction": 0.01,
            "min_chars": 20,
            "max_chars": 20000,
            "dedup": False,
            "seed": 20261016,
        },
        "train": {
            "seed": seed,
            "device": "auto",
            "precision": "fp32",
            "max_steps": 6000,
            "batch_size": 1,
            "grad_accum": 16,
            "eval_batch_size": 4,
            "lr": 0.0005,
            "min_lr_ratio": 0.1,
            "warmup_steps": 150,
            "weight_decay": 0.1,
            "grad_clip": 1.0,
            "eval_interval": 500,
            "eval_iters": 50,
            "log_interval": 25,
            "ckpt_interval": 500,
            "keep_last": 2,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "configs" / "confirmatory" / "training")
    parser.add_argument("--include-contingency", action="store_true")
    args = parser.parse_args()
    seeds = SEEDS + ((20261019, 20261020) if args.include_contingency else ())
    for scale, spec in SCALES.items():
        for architecture in spec["architectures"]:
            for seed in seeds:
                path = args.output_dir / scale / architecture / f"seed_{seed}.yaml"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(yaml.safe_dump(make_config(scale, architecture, seed), sort_keys=False), encoding="utf-8")
                print(f"[wrote] {path}")


if __name__ == "__main__":
    main()
