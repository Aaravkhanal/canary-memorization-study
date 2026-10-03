#!/usr/bin/env bash
set -e

# Master runner for Canary Memorization Study: Variant B & C Grid
# Runs pretraining, memorization evaluation, novelty evaluation, and updates tradeoff plots.

VARIANTS=("variant_b_mha" "variant_c_layernorm")
FREQS=(0 1 10 50 100 500)

ROOT_DIR="/Users/aaravkhanal/Desktop/myllm/canary-memorization-study"
AARAV_LM_DIR="/Users/aaravkhanal/Desktop/myllm/aarav-lm"
TOKENIZER_DIR="$AARAV_LM_DIR/artifacts/tokenizer_tinystories_v2"

export PYTHONPATH="$AARAV_LM_DIR/src:$PYTHONPATH"

cd "$ROOT_DIR"


for var in "${VARIANTS[@]}"; do
    for freq in "${FREQS[@]}"; do
        echo "============================================================"
        echo "Starting Cell: Architecture=$var | Frequency=$freq"
        echo "============================================================"

        CONFIG_PATH="configs/training/$var/freq_$freq.yaml"
        EXP_ROOT="models/$var/freq_$freq"

        # Step 1: Pretrain if model checkpoint does not exist
        CHECKPOINT=$(find "$EXP_ROOT" -name "best.pt" 2>/dev/null | head -n 1 || true)

        if [ -z "$CHECKPOINT" ]; then
            echo "[Data Prep] Ensuring dataset is tokenized for $var (freq $freq)..."
            python "$AARAV_LM_DIR/scripts/prepare_data.py" --config "$CONFIG_PATH"
            echo "[Pretraining] Running training for $var (freq $freq)..."
            python "$AARAV_LM_DIR/scripts/train.py" --config "$CONFIG_PATH" --exp-root "$EXP_ROOT"
            CHECKPOINT=$(find "$EXP_ROOT" -name "best.pt" 2>/dev/null | head -n 1)
        else
            echo "[Pretraining] Checkpoint already exists at $CHECKPOINT. Skipping pretraining."
        fi

        # Step 2: Memorization Evaluation
        MEM_OUT="results/mem_${var}_freq${freq}.json"
        if [ ! -f "$MEM_OUT" ]; then
            echo "[Eval Memorization] Running evaluation for $var (freq $freq)..."
            python scripts/eval_memorization.py --checkpoint "$CHECKPOINT" --tokenizer "$TOKENIZER_DIR" --out "$MEM_OUT"
        else
            echo "[Eval Memorization] Result $MEM_OUT already exists. Skipping."
        fi

        # Step 3: Novelty Evaluation
        NOVELTY_OUT="results/novelty_${var}_freq${freq}.json"
        LABEL_BATCH="results/labelling/${var}_freq${freq}.txt"
        if [ ! -f "$NOVELTY_OUT" ]; then
            echo "[Eval Novelty] Running novelty evaluation for $var (freq $freq)..."
            python scripts/eval_novelty.py --checkpoint "$CHECKPOINT" --tokenizer "$TOKENIZER_DIR" --frequency "$freq" --device mps --out "$NOVELTY_OUT" --label-batch "$LABEL_BATCH"
        else
            echo "[Eval Novelty] Result $NOVELTY_OUT already exists. Skipping."
        fi

        # Step 4: Update Trade-off Plot & CSV
        echo "[Analysis] Updating trade-off summary..."
        python scripts/analyze_tradeoff.py --results-dir results --out-plot results/tradeoff.png --out-csv results/tradeoff.csv

        echo "Cell $var (freq $freq) COMPLETED cleanly."
        echo ""
    done
done

echo "============================================================"
echo "ALL Variant B & Variant C Grid Runs & Evaluations Finished!"
echo "============================================================"
