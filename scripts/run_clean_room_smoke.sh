#!/bin/bash
set -euo pipefail

# Run from a fresh clone after cloning the pinned MY-LLM repository separately:
#   AARAV_LM_DIR=/path/to/MY-LLM bash scripts/run_clean_room_smoke.sh
# This trains one CPU step on the unmodified base subset only. It does not start a
# confirmatory cell, consume MPS, or produce a scientific outcome.

study_root="$(cd "$(dirname "$0")/.." && pwd)"
aarav_dir="${AARAV_LM_DIR:?set AARAV_LM_DIR to the pinned MY-LLM checkout}"
python_bin="${PYTHON_BIN:-python}"
smoke_dir="$(mktemp -d "${TMPDIR:-/tmp}/canary-smoke.XXXXXX")"
trap 'rm -rf "$smoke_dir"' EXIT

cd "$study_root"
"$python_bin" scripts/check_reproducibility.py --mode analysis
"$python_bin" scripts/acquire_tinystories_subset.py
"$python_bin" scripts/generate_confirmatory_bank.py --check
"$python_bin" scripts/prepare_confirmatory_corpus.py --seed 20261016
"$python_bin" scripts/prepare_confirmatory_corpus.py --seed 20261016 --check
"$python_bin" scripts/check_reproducibility.py --mode training --aarav-lm-dir "$aarav_dir"

export AARAV_LM_HOME="$study_root"
export PYTHONPATH="$aarav_dir/src${PYTHONPATH:+:$PYTHONPATH}"
config="configs/confirmatory/training/14m/baseline/seed_20261016.yaml"
"$python_bin" "$aarav_dir/scripts/prepare_data.py" --config "$config" \
  "data.sources=[$study_root/data/raw/base.txt]" "data.out_dir=$smoke_dir/tokenized"
"$python_bin" "$aarav_dir/scripts/train.py" --config "$config" --exp-root "$smoke_dir/experiments" \
  name=clean_room_smoke "data.out_dir=$smoke_dir/tokenized" train.max_steps=1 train.batch_size=1 \
  train.grad_accum=1 train.eval_interval=1 train.eval_iters=1 train.ckpt_interval=1 train.log_interval=1 \
  train.device=cpu

echo "CLEAN-ROOM SMOKE PASSED: input acquisition, deterministic build, tokenization, validation, and one CPU step"
