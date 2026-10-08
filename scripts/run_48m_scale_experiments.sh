#!/usr/bin/env bash
set -euo pipefail

# Sequential matched-token scale-transfer arm. The 14M and 48M experiments must
# never compete for MPS. If an active 14M queue PID is supplied, wait for it.
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

find_completed_exp() {
  local candidate summary
  while IFS= read -r summary; do
    if "$PYTHON_BIN" -c 'import json,sys; d=json.load(open(sys.argv[1])); raise SystemExit(0 if d.get("status")=="completed" and d.get("steps")==6000 else 1)' "$summary"; then
      dirname "$summary"
      return 0
    fi
  done < <(find "$1" -type f -name summary.json -print | sort -r)
  return 1
}

verify_cell() {
  local exp_dir="$1" checkpoint="$2" mem_json="$3" novelty_json="$4" overlap_json="$5"
  "$PYTHON_BIN" - "$exp_dir" "$checkpoint" "$mem_json" "$novelty_json" "$overlap_json" <<'PY'
import json
import sys
from pathlib import Path
import torch

exp_dir, checkpoint, mem_path, novelty_path, overlap_path = map(Path, sys.argv[1:])
summary = json.loads((exp_dir / "summary.json").read_text())
assert summary.get("status") == "completed", summary.get("status")
assert summary.get("steps") == 6000, summary.get("steps")
assert summary.get("params", 0) > 45_000_000, summary.get("params")
for path in sorted((exp_dir / "checkpoints").glob("*.pt")):
    torch.load(path, map_location="cpu", weights_only=True)
    print(f"[verified checkpoint] {path}")
assert checkpoint.is_file(), checkpoint
mem = json.loads(mem_path.read_text())
novelty = json.loads(novelty_path.read_text())
overlap = json.loads(overlap_path.read_text())
assert len(mem.get("rows", [])) == 12, f"unexpected memorization rows: {len(mem.get('rows', []))}"
groups = novelty.get("groups", [])
assert len(groups) == 32, f"unexpected novelty groups: {len(groups)}"
assert sum(len(group.get("completions", [])) for group in groups) == 320
overlap_groups = overlap.get("groups", [])
assert len(overlap_groups) == 32, f"unexpected full-corpus groups: {len(overlap_groups)}"
assert sum(len(group.get("completions", [])) for group in overlap_groups) == 320
meta = overlap.get("full_corpus_overlap", {})
assert meta.get("corpus_sha256"), "missing full-corpus fingerprint"
print(f"[verified results] {mem_path}, {novelty_path}, and {overlap_path}")
PY
}

for variant in scale_48m_baseline scale_48m_learned_pos scale_48m_mha scale_48m_layernorm; do
  for frequency in 0 1 10 50 100 500; do
    config="configs/training/scale_48m/${variant}/freq_${frequency}_seed20260927.yaml"
    run_dir="models/scale_48m/${variant}/freq_${frequency}_seed20260927"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting ${variant} frequency ${frequency}"
    if [[ ! -f "data/processed/freq_${frequency}/tokenized/manifest.json" ]]; then
        "$PYTHON_BIN" "$AARAV_LM_DIR/scripts/prepare_data.py" --config "$config"
    fi
    if completed_exp="$(find_completed_exp "$run_dir")"; then
        exp_dir="$completed_exp"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Reusing completed cell at $exp_dir"
    else
        resume_exp=""
        while IFS= read -r candidate; do
            if find "$candidate/checkpoints" -maxdepth 1 -type f -name 'step_*.pt' -print -quit 2>/dev/null | rg -q .; then
                resume_exp="$candidate"
                break
            fi
        done < <(find "$run_dir" -mindepth 1 -maxdepth 1 -type d -name 'exp_*' -print | sort -r)
        if [[ -n "$resume_exp" ]]; then
            exp_dir="$resume_exp"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Resuming incomplete cell at $exp_dir"
            "$PYTHON_BIN" "$AARAV_LM_DIR/scripts/train.py" --resume "$exp_dir"
        else
            "$PYTHON_BIN" "$AARAV_LM_DIR/scripts/train.py" --config "$config" --exp-root "$run_dir"
            exp_dir="$(find_completed_exp "$run_dir")"
        fi
    fi
    checkpoint="$exp_dir/checkpoints/best.pt"
    mem_json="results/mem_${variant}_freq${frequency}.json"
    novelty_json="results/novelty_${variant}_freq${frequency}.json"
    overlap_json="results/full_corpus_overlap/novelty_${variant}_freq${frequency}_full_corpus.json"
    "$PYTHON_BIN" scripts/eval_memorization.py --checkpoint "$checkpoint" --tokenizer "$TOKENIZER_DIR" \
        --device mps --out "$mem_json"
    "$PYTHON_BIN" scripts/eval_novelty.py --checkpoint "$checkpoint" --tokenizer "$TOKENIZER_DIR" \
        --frequency "$frequency" --device mps --out "$novelty_json" \
        --seed 20260927
    "$PYTHON_BIN" scripts/eval_full_corpus_overlap.py --input "$novelty_json" \
        --corpus "data/processed/freq_${frequency}/corpus.txt" --output "$overlap_json" \
        --index "results/full_corpus_overlap/index_freq_${frequency}.sqlite"
    verify_cell "$exp_dir" "$checkpoint" "$mem_json" "$novelty_json" "$overlap_json"
    find "$exp_dir/checkpoints" -maxdepth 1 -type f -name 'step_*.pt' -delete
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Removed verified rolling checkpoints for this cell to preserve disk space"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed ${variant} frequency ${frequency}"
  done
done

echo "48M matched-token scale-transfer grid completed."
