#!/usr/bin/env bash
set -euo pipefail

# Complete the two missing pre-registered 50x cells and the two outstanding high-frequency
# baseline seed replications. If WAIT_FOR_PID is set, wait for that existing evaluation queue
# to finish first so two MPS-heavy jobs never contend on the laptop.

ROOT_DIR="/Users/aaravkhanal/Desktop/myllm/canary-memorization-study"
AARAV_LM_DIR="/Users/aaravkhanal/Desktop/myllm/aarav-lm"
PYTHON_BIN="/Users/aaravkhanal/miniforge3/bin/python"
TOKENIZER_DIR="$AARAV_LM_DIR/artifacts/tokenizer_tinystories_v2"
LOCK_DIR="$ROOT_DIR/.runtime/remaining_experiments.lock"

mkdir -p "$ROOT_DIR/.runtime"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "Another remaining-experiments runner already holds $LOCK_DIR" >&2
    exit 1
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

export PYTHONPATH="$AARAV_LM_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT_DIR"

if [[ -n "${WAIT_FOR_PID:-}" ]]; then
    echo "Waiting for existing evaluation queue PID $WAIT_FOR_PID to finish."
    while kill -0 "$WAIT_FOR_PID" 2>/dev/null; do
        sleep 30
    done
fi

run_cell() {
    local variant="$1"
    local frequency="$2"
    local config="$3"
    local experiment_root="$4"
    local result_suffix="$5"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting $result_suffix"

    local data_manifest="data/processed/freq_${frequency}/tokenized/manifest.json"
    if [[ ! -f "$data_manifest" ]]; then
        "$PYTHON_BIN" "$AARAV_LM_DIR/scripts/prepare_data.py" --config "$config"
    fi

    local checkpoint
    checkpoint="$(find "$experiment_root" -path '*/checkpoints/best.pt' -print -quit 2>/dev/null || true)"
    if [[ -z "$checkpoint" ]]; then
        "$PYTHON_BIN" "$AARAV_LM_DIR/scripts/train.py" --config "$config" --exp-root "$experiment_root"
        checkpoint="$(find "$experiment_root" -path '*/checkpoints/best.pt' -print -quit)"
    fi

    local mem_out="results/mem_${result_suffix}.json"
    local novelty_out="results/novelty_${result_suffix}.json"
    local labels_out="results/labelling/${result_suffix}.txt"

    if [[ ! -f "$mem_out" ]]; then
        "$PYTHON_BIN" scripts/eval_memorization.py \
            --checkpoint "$checkpoint" \
            --tokenizer "$TOKENIZER_DIR" \
            --device mps \
            --out "$mem_out"
    fi
    if [[ ! -f "$novelty_out" ]]; then
        "$PYTHON_BIN" scripts/eval_novelty.py \
            --checkpoint "$checkpoint" \
            --tokenizer "$TOKENIZER_DIR" \
            --frequency "$frequency" \
            --device mps \
            --out "$novelty_out" \
            --label-batch "$labels_out" \
            --seed 20260927
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed $result_suffix"
}

run_cell baseline 50 \
    configs/training/baseline/freq_50.yaml \
    models/baseline/freq_50 \
    baseline_freq50

run_cell variant_a_learned_pos 50 \
    configs/training/variant_a_learned_pos/freq_50.yaml \
    models/variant_a_learned_pos/freq_50 \
    variant_a_learned_pos_freq50

run_cell baseline 100 \
    configs/training/baseline/freq_100_seed1338.yaml \
    models/baseline/freq_100_seed1338 \
    baseline_freq100_seed1338

run_cell baseline 500 \
    configs/training/baseline/freq_500_seed1338.yaml \
    models/baseline/freq_500_seed1338 \
    baseline_freq500_seed1338

"$PYTHON_BIN" scripts/analyze_tradeoff.py \
    --results-dir results \
    --baseline-dir results \
    --out-plot results/tradeoff.png \
    --out-csv results/tradeoff.csv

"$PYTHON_BIN" scripts/analyze_tradeoff.py \
    --results-dir results \
    --baseline-dir results \
    --canaries char_nira,char_boro,char_suri,plot_song,plot_lantern \
    --out-plot results/tradeoff_clean.png \
    --out-csv results/tradeoff_clean.csv

echo "[$(date '+%Y-%m-%d %H:%M:%S')] All remaining automated experiments completed."
