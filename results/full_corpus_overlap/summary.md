# Full-corpus overlap audit

Status: complete for the 24-cell canonical 14M grid, two true baseline training-seed replication cells, and one exploratory 48M cell; the remaining 23 cells in the 48M scale arm are not yet evaluated. On 2026-10-08, the exact maximum word-four-gram overlap evaluator checked all 24 canonical (non-`_gen1338`, non-`_seed1338`) 14M novelty JSONs against their matching frequency-specific training corpora, the baseline 100x/500x `_seed1338` replications, and the completed 48M baseline/frequency-0 output. All six SQLite indexes were verified against their respective `data/processed/freq_<F>/corpus.txt` SHA-256 and story count. The 27 JSONs contain 8,640 completions (320 per cell) and all parsed successfully. Indexes are local rebuildable caches and are excluded from Git; detailed enriched JSON outputs and this summary are retained.

The two previously missing canonical 14M frequency-0 outputs were generated from their matching checkpoints with generation seed 20260927 and analyzed; alternate `_gen1338` outputs were not substituted. The baseline frequency-100/500 `_seed1338` outputs are separate training-seed replications and are reported separately. For 48M, only `scale_48m_baseline` frequency 0 has completed generation and full-corpus overlap; do not generalize its descriptive statistic to the unfinished 23-cell scale grid.

The reported value is the exact maximum fraction of a completion's word four-grams that occur in any one story in the matching training corpus. Across the 24 canonical 14M cells (7,680 completions), the unweighted mean is 0.094586, median 0.075000, and maximum 1.0. The two baseline seed-replication cells (640 completions) have mean 0.121716, median 0.090909, and maximum 1.0. The single 48M baseline/frequency-0 cell has mean 0.105269, median 0.078898, and maximum 1.0. Across all 27 cells (8,640 completions), the mean is 0.096991, median 0.076190, and maximum 1.0. This is an automated copying diagnostic, not a human novelty judgment; common phrases can contribute overlap, and these descriptive values do not establish a memorization/creativity trade-off.

| Canonical condition | N | Mean | Median | Maximum |
|---|---:|---:|---:|---:|
| baseline, freq 0 | 320 | 0.094595 | 0.078125 | 0.833333 |
| baseline, freq 100, training seed 1338 | 320 | 0.126986 | 0.092907 | 1.000000 |
| baseline, freq 500, training seed 1338 | 320 | 0.116447 | 0.090536 | 1.000000 |
| baseline, freq 1 | 320 | 0.105535 | 0.071429 | 0.750000 |
| baseline, freq 10 | 320 | 0.095663 | 0.069099 | 1.000000 |
| baseline, freq 50 | 320 | 0.083942 | 0.073044 | 1.000000 |
| baseline, freq 100 | 320 | 0.091814 | 0.074074 | 0.750000 |
| baseline, freq 500 | 320 | 0.090528 | 0.075450 | 0.588235 |
| learned positions, freq 1 | 320 | 0.077551 | 0.072268 | 0.437500 |
| learned positions, freq 0 | 320 | 0.075535 | 0.062500 | 1.000000 |
| learned positions, freq 10 | 320 | 0.100067 | 0.076923 | 0.666667 |
| learned positions, freq 50 | 320 | 0.078444 | 0.069266 | 0.727273 |
| learned positions, freq 100 | 320 | 0.092032 | 0.078431 | 0.666667 |
| learned positions, freq 500 | 320 | 0.089852 | 0.077628 | 1.000000 |
| MHA, freq 0 | 320 | 0.090381 | 0.076190 | 0.466667 |
| MHA, freq 1 | 320 | 0.110562 | 0.077552 | 0.928571 |
| MHA, freq 10 | 320 | 0.112014 | 0.079446 | 1.000000 |
| MHA, freq 50 | 320 | 0.102877 | 0.076923 | 0.833333 |
| MHA, freq 100 | 320 | 0.094013 | 0.080645 | 0.500000 |
| MHA, freq 500 | 320 | 0.107376 | 0.078435 | 1.000000 |
| LayerNorm, freq 0 | 320 | 0.094579 | 0.071112 | 1.000000 |
| LayerNorm, freq 1 | 320 | 0.091579 | 0.075000 | 0.545455 |
| LayerNorm, freq 10 | 320 | 0.098345 | 0.074227 | 1.000000 |
| LayerNorm, freq 50 | 320 | 0.087417 | 0.072464 | 1.000000 |
| LayerNorm, freq 100 | 320 | 0.105476 | 0.085540 | 0.777778 |
| LayerNorm, freq 500 | 320 | 0.099887 | 0.083683 | 0.555556 |
| 48M baseline, freq 0 (exploratory) | 320 | 0.105269 | 0.078898 | 1.000000 |

Each detailed JSON records the corpus path and SHA-256, index path, story count, per-completion maximum overlap, best-matching story ID, edit distance, and candidate count. Reproduction command shape:

```bash
python scripts/eval_full_corpus_overlap.py \
  --input results/novelty_<architecture>_freq<F>.json \
  --corpus data/processed/freq_<F>/corpus.txt \
  --output results/full_corpus_overlap/novelty_<architecture>_freq<F>_full_corpus.json \
  --index results/full_corpus_overlap/index_freq_<F>.sqlite
```
