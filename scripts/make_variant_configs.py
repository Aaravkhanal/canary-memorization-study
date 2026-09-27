"""
Phase 2/3 (canary study): generate one training config per (architecture variant, canary frequency).

    python scripts/make_variant_configs.py

Reuses aarav-lm's model code, tokenizer and training loop as a library (this project does not duplicate any of
that): each config is plain YAML in aarav_lm's own ExperimentConfig schema, with `model_overrides` carrying the
ONE architectural axis that differs from baseline, `data.sources` pointing at this project's canary corpus (not
aarav-lm's), and `data.out_dir` / experiment output kept inside THIS repo's data/ and models/ directories, so the
two projects' artifacts never mix.

Reduced first pass (see README.md for the full compute-cost accounting): baseline and Variant A only, at
frequencies [1, 10, 100, 500] (500 dropped only as a smoke-test convenience: freq=50 is skipped to cut the first
pass from 5 to 4 runs per variant, keeping the log-spaced extremes and one middle point). Variant B and C configs
are also written (Phase 2's "show me before training starts" covers all variants), but are not queued to train
until the reduced pass's trade-off curve is reviewed.

Per-run token budget: batch_size=1 x grad_accum=16 x block_size=256 = 4,096 tokens/step, 6,000 steps = ~24.6M
tokens, ~1-1.5h on this machine (see README.md). This is a deliberately small budget for a controlled canary
study, not a claim that the resulting models write good stories.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AARAV_LM = ROOT.parent / "aarav-lm"
sys.path.insert(0, str(AARAV_LM / "src"))

FREQUENCIES_FIRST_PASS = [1, 10, 100, 500]        # of the pre-registered [1, 10, 50, 100, 500]; see docstring
ALL_FREQUENCIES = [1, 10, 50, 100, 500]

VARIANTS = {
    "baseline":     {"overrides": {}, "note": "aarav-lm's own small preset, unchanged: RoPE, GQA (n_kv_head=2), RMSNorm, SwiGLU, 8 layers."},
    "variant_a_learned_pos": {"overrides": {"arch": "gpt2"}, "note": "position encoding only: learned absolute positions instead of RoPE. Adds a block_size x n_embd position table (+1.4% params, entirely outside the transformer body, which is identical to baseline)."},
    "variant_b_mha":         {"overrides": {"n_kv_head": 6, "n_layer": 7}, "note": "attention only: multi-head (every head has its own K/V) instead of grouped-query. n_layer dropped from 8 to 7 to compensate (n_kv_head=6 at n_layer=8 would be +11.1% params; at n_layer=7 it is -1.4%, the closest clean-integer match)."},
    "variant_c_layernorm":   {"overrides": {"norm_type": "layernorm"}, "note": "normalisation only: LayerNorm instead of RMSNorm. Exact parameter match (both are scale-only with bias=False)."},
}


def report_params():
    from aarav_lm.config.config import get_preset
    from aarav_lm.model.core import AaravLM
    base_n = AaravLM(get_preset("small")).num_params()
    print(f"baseline params: {base_n:,}")
    for name, v in VARIANTS.items():
        if not v["overrides"]:
            continue
        cfg = get_preset("small", **v["overrides"])
        n = AaravLM(cfg).num_params()
        print(f"{name:26s} params: {n:,}  ({100 * (n - base_n) / base_n:+.2f}%)  overrides={v['overrides']}")


def make_config(variant: str, overrides: dict, freq: int) -> dict:
    corpus = ROOT / "data" / "processed" / f"freq_{freq}" / "corpus.txt"
    out_dir = ROOT / "data" / "processed" / f"freq_{freq}" / f"tokenized_{variant}"
    return {
        "name": f"{variant}_freq{freq}",
        "description": f"Canary study: {variant} architecture, canary frequency {freq}. {VARIANTS[variant]['note']}",
        "model_preset": "small",
        "model_overrides": overrides,
        "tokenizer": {
            "kind": "bpe", "vocab_size": 4096,
            "artifact_dir": str(AARAV_LM / "artifacts" / "tokenizer_tinystories_v2"),   # reused, not retrained: same tokenizer across every variant and frequency, as the brief requires
            "train_files": [],
        },
        "data": {
            "sources": [str(corpus)], "format": "txt", "doc_separator": "<|endoftext|>", "out_dir": str(out_dir),
            "val_fraction": 0.01, "test_fraction": 0.01, "min_chars": 20, "max_chars": 20000, "dedup": False, "seed": 20260927,
            # dedup off: canary insertions deliberately create near-duplicate stories (same base story, canary
            # sentence added); de-duplicating would remove exactly the signal this study needs to keep.
        },
        "train": {
            "seed": 20260927, "device": "auto", "precision": "fp32", "max_steps": 6000, "batch_size": 1, "grad_accum": 16,
            "eval_batch_size": 4, "lr": 0.0008, "min_lr_ratio": 0.1, "warmup_steps": 150, "weight_decay": 0.1,
            "grad_clip": 1.0, "eval_interval": 500, "eval_iters": 50, "log_interval": 25, "ckpt_interval": 500, "keep_last": 2,
        },
    }


def main() -> None:
    report_params()
    out_root = ROOT / "configs" / "training"
    written = []
    for variant, spec in VARIANTS.items():
        freqs = FREQUENCIES_FIRST_PASS if variant in ("baseline", "variant_a_learned_pos") else ALL_FREQUENCIES
        for freq in freqs:
            cfg = make_config(variant, spec["overrides"], freq)
            path = out_root / variant / f"freq_{freq}.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(cfg, sort_keys=False))
            written.append(path)
    print(f"\nwrote {len(written)} configs under {out_root}")
    print("queued for the reduced first pass: baseline and variant_a_learned_pos, frequencies", FREQUENCIES_FIRST_PASS)
    print("written but not queued: variant_b_mha and variant_c_layernorm, all 5 frequencies (pending your review of the first pass)")


if __name__ == "__main__":
    main()
