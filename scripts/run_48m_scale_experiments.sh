#!/usr/bin/env bash
set -euo pipefail

# Sequential matched-token scale-transfer arm. The 14M and 48M experiments must
# never compete for MPS. The runner starts only after the currently active research
# queue exits; set WAIT_FOR_PID when launching it.
ROOT_DIR="/Users/aaravkhanal/Desktop/myllm/canary-memorization-study"
AARAV_LM_DIR="/Users/aaravkhanal/Desktop/myllm/aarav-lm"
PYTHON_BIN="/Users/aaravkhanal/miniforge3/bin/python"
TOKENIZER_DIR="$AARAV_LM_DIR/artifacts/tokenizer_tinystories_v2"
WAIT_FOR_PID="${WAIT_FOR_PID:-}"

cd "$ROOT_DIR"
export PYTHONPATH="$AARAV_LM_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ -n "$WAIT_FOR_PID" ]]; then
    echo "Waiting for research queue PID $WAIT_FOR_PID to finish before using MPS."
    while kill -0 "$WAIT_FOR_PID" 2>/dev/null; do sleep 30; done
fi

for variant in scale_48m_baseline scale_48m_learned_pos scale_48m_mha scale_48m_layernorm; do
  for frequency in 0 1 10 50 100 500; do
    config="configs/training/scale_48m/${variant}/freq_${frequency}_seed20260927.yaml"
    run_dir="models/scale_48m/${variant}/freq_${frequency}_seed20260927"
    checkpoint="$(find "$run_dir" -path '*/checkpoints/best.pt' -print -quit 2>/dev/null || true)"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting ${variant} frequency ${frequency}"
    if [[ ! -f "data/processed/freq_${frequency}/tokenized/manifest.json" ]]; then
        "$PYTHON_BIN" "$AARAV_LM_DIR/scripts/prepare_data.py" --config "$config"
    fi
    if [[ -z "$checkpoint" ]]; then
        "$PYTHON_BIN" "$AARAV_LM_DIR/scripts/train.py" --config "$config" --exp-root "$run_dir"
        checkpoint="$(find "$run_dir" -path '*/checkpoints/best.pt' -print -quit)"
    fi
    "$PYTHON_BIN" scripts/eval_memorization.py --checkpoint "$checkpoint" --tokenizer "$TOKENIZER_DIR" \
        --device mps --out "results/mem_${variant}_freq${frequency}.json"
    "$PYTHON_BIN" scripts/eval_novelty.py --checkpoint "$checkpoint" --tokenizer "$TOKENIZER_DIR" \
        --frequency "$frequency" --device mps --out "results/novelty_${variant}_freq${frequency}.json" \
        --seed 20260927
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed ${variant} frequency ${frequency}"
  done
done

echo "48M matched-token scale-transfer grid completed."
