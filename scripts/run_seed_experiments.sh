#!/usr/bin/env bash
set -e

# Run novelty evaluation with generation seed 1338 for the available model checkpoints.
# The `gen1338` suffix is distinct from `_seed1338`, used for a different training seed.

VARIANTS=("baseline" "variant_a_learned_pos" "variant_b_mha" "variant_c_layernorm")
FREQS=(0 1 10 100 500)
SEED=1338

ROOT_DIR="/Users/aaravkhanal/Desktop/myllm/canary-memorization-study"
AARAV_LM_DIR="/Users/aaravkhanal/Desktop/myllm/aarav-lm"
TOKENIZER_DIR="$AARAV_LM_DIR/artifacts/tokenizer_tinystories_v2"

export PYTHONPATH="$AARAV_LM_DIR/src:$PYTHONPATH"

cd "$ROOT_DIR"

for var in "${VARIANTS[@]}"; do
  for freq in "${FREQS[@]}"; do
    echo "============================================================"
    echo "Running novelty eval: Architecture=$var | Frequency=$freq | Seed=$SEED"
    echo "============================================================"

    EXP_ROOT="models/$var/freq_$freq"
    CHECKPOINT=$(find "$EXP_ROOT" -name "best.pt" 2>/dev/null | head -n 1 || true)
    if [ -z "$CHECKPOINT" ]; then
      echo "[WARN] No checkpoint found for $var freq $freq – skipping."
      continue
    fi

    NOVELTY_OUT="results/novelty_${var}_freq${freq}_gen${SEED}.json"
    LABEL_BATCH="results/labelling/${var}_freq${freq}_gen${SEED}.txt"

    if [ -f "$NOVELTY_OUT" ]; then
      echo "[Info] Novelty output $NOVELTY_OUT already exists – skipping."
    else
      python scripts/eval_novelty.py \
        --checkpoint "$CHECKPOINT" \
        --tokenizer "$TOKENIZER_DIR" \
        --frequency "$freq" \
        --device mps \
        --out "$NOVELTY_OUT" \
        --label-batch "$LABEL_BATCH" \
        --seed $SEED
    fi
  done
done

echo "All seed experiments completed."
