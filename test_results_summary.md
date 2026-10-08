# Test and experiment results ledger – Canary Memorization Study

Updated 2026-10-09. This is the separate audit file for completed tests, completed experiment cells, outstanding
compute, and work that still requires human judgment.

## Expanded scale arm

- 67/67 research tests passed after adding full-corpus overlap, blinded annotation, and 48M configuration checks.
- Four 48M architecture conditions × six frequencies are configured (24 runs), each targeting 49,152,000 training
  tokens. Counts are 48,100,480 baseline; 48,428,160 learned positions; 47,239,040 MHA; and 48,100,480 LayerNorm.
- The baseline 48M frequency-0 cell initially failed at step 1,500 during a checkpoint write when the
  filesystem had ~185 MB available. After approval, 58 validated rolling checkpoints from completed 14M runs
  were removed while retaining best/final checkpoints, logs, and results. The cell resumed from intact step 1,000
  and completed 6,000 steps at 13:44:45 local on 2026-10-08. Trainer summary: 26,976.3 seconds, best validation
  loss 1.4871208 / PPL 4.4243, four gradient-norm anomalies. Memorization, novelty, and full-corpus outputs were
  generated and verified. Its rolling step checkpoints were removed only after validation; best/final remain.
  Baseline frequency 1 then completed 6,000 updates (26,015.6 trainer seconds; 7h13m36s), best validation loss
  1.4931227 / PPL 4.45, six gradient-norm spikes, and seven gradient-health alerts. Its best/final checkpoints
  and 12-row memorization, 32-group/320-completion novelty, and matching-corpus overlap JSONs were verified. The
  baseline frequency-1 overlap fingerprint matches its 73,139-story corpus. Baseline frequency 10 is now training
  (75/6,000 at 00:18 local on 2026-10-09); 21 cells remain queued. About 7.3 GiB was free at the latest check.
  The remaining 22 cells are not complete.
- The existing MY-LLM 48M checkpoint used a different corpus and five times the token budget, so it cannot serve as
  the matched arm.
- The 48M scale comparison is exploratory and single-seed initially; it also uses learning rate 5e-4 versus 8e-4
  for the current 14M arm. Both caveats must be addressed or reported before interpreting a size effect.

## Automated tests

- **67/67 tests passed** on 2026-10-08 after the final result regeneration. The latest run completed in 5.46s with 14
  upstream matplotlib/pyparsing deprecation warnings and no failures. Re-run after final documentation-only edits
  to confirm the repository state.
- Coverage includes corpus construction and nesting/disjointness, canary novelty checks, exposure and extraction,
  deterministic novelty sampling, label-batch generation, and trade-off aggregation/plotting.
- Four model architectures are parameter-matched within ±1.4%: baseline 14,162,304; learned-position 14,358,912;
  MHA 13,964,928; LayerNorm 14,162,304 parameters.

## Generation-seed filename audit

- The completed `run_seed_experiments.sh` batch varied the generation seed, not the training seed. Its 20 novelty
  JSON outputs and available legacy, condition-revealing label text files have been renamed from `_seed1338` to
  `_gen1338` so they cannot be mistaken for the separate baseline training-seed replications.
- All 20 renamed JSON files parse successfully and contain generation groups; total size is 3.4 MB. The 18 legacy
  text label files remain condition-revealing and are excluded from the blinded annotation workflow.
- The sequential runner will now generate fresh novelty outputs under `_seed1338` using the actual
  `train.seed=1338` checkpoints at baseline frequencies 100 and 500. Memorization outputs are separately generated
  from those same checkpoints.
- `run_seed_experiments.sh` now uses the `_gen1338` suffix. Legacy text label files are not inputs to the blinded
  annotation analysis.

## Completed training and evaluation cells

Every cell below has a completed checkpoint plus memorization and novelty JSON output unless marked otherwise.
Frequency 0 is the added zero-exposure control; the pre-registered treatments are 1, 10, 50, 100, and 500.

| Architecture | 0 | 1 | 10 | 50 | 100 | 500 |
|---|---:|---:|---:|---:|---:|---:|
| baseline | done | done | done | **done** | done | done |
| learned absolute positions | done | done | done | **done** | done | done |
| multi-head attention | done | done | done | done | done | done |
| LayerNorm | done | done | done | done | done | done |

This corrects the older README/paper claim that MHA and LayerNorm had not been trained. Both are complete across
the full grid. Baseline and learned-position frequency 50 have now completed, balancing the main grid.

Baseline frequency 50 training ran 2026-10-07 14:57:09–17:39:59 local (2h42m50s), completing 6,000 updates.
Best validation loss
was 1.5595 (perplexity 4.76). Its checkpoint and 12-row memorization plus 32-group/320-completion novelty JSONs
are present. The learned-position frequency-50 run started at 17:44:57 and completed at 20:13:27 local (2h28m30s),
with best validation loss 1.6385 (perplexity 5.15). Its checkpoint and 12-row memorization plus
32-group/320-completion novelty JSONs are present. The log records 20 gradient-norm spike events, including an
early 129.3 and later 40.15; training continued to 6,000 updates without a failed exit. The trainer applies
gradient clipping; retain the excursions as an optimization-stability caveat and inspect clipping diagnostics
before claiming every spike was harmless.

## Seed replications

Baseline second-seed training is complete at 0x, 1x, and 10x. At 10x, the second seed strengthens rather than
erases the signal: `char_nira` and `plot_lantern` reproduce exactly, while `char_boro` and `char_suri` rise to the
exposure ceiling. Baseline true training-seed replications at 100x and 500x have now completed from their matching
`models/baseline/freq_{100,500}_seed1338` checkpoints. The 100x run took 2h41m29s (20:17:34–22:59:03 local),
best validation loss 1.5713 / perplexity 4.81, with one logged gradient-norm spike. The 500x run took 3h02m47s
(23:03:35–02:06:22 local, crossing midnight), best validation loss 1.5488 / perplexity 4.71, with four logged
gradient-norm spikes. Both have best checkpoints and separate `_seed1338` memorization/novelty JSONs; the novelty
files came from alternate-training-seed checkpoints, not generation-seed resamples.

## Current contamination-excluded proxy table

Memorization is mean exposure lift over the matched 0x model for the five canaries with zero base-corpus identity
occurrences. Novelty is distinct-2, still only a proxy for the required human V/T/N score.

| Architecture | Frequency | Exposure lift | Distinct-2 proxy |
|---|---:|---:|---:|
| baseline | 1 / 10 / 100 / 500 | 0.278 / 1.379 / 2.579 / 2.262 | 0.803 / 0.827 / 0.808 / 0.797 |
| learned positions | 1 / 10 / 100 / 500 | 0.061 / 1.887 / 2.351 / 2.351 | 0.777 / 0.784 / 0.799 / 0.805 |
| MHA | 1 / 10 / 50 / 100 / 500 | 0.370 / 1.365 / 1.965 / 1.765 / 2.229 | 0.792 / 0.809 / 0.825 / 0.805 / 0.804 |
| LayerNorm | 1 / 10 / 50 / 100 / 500 | -0.094 / 2.015 / 2.132 / 1.932 / 1.932 | 0.792 / 0.808 / 0.788 / 0.782 / 0.799 |

Across the completed main grid, corrected teacher-forced extraction is **0/264** canary-checkpoint pairs. Across
the three completed baseline seed-replication checkpoints it is also **0/36**.

## Invalid automated labels corrected

A recent utility assigned one heuristic label to every generation in each file, including `V` (verbatim) for
zero-overlap text. Those labels do not implement the pre-registered judgment and are invalid. They have been reset
to blank; the utility is now read-only. Generated text and automated overlap/diversity measurements are preserved.

Phase 5 therefore remains **0 valid human labels completed**. A human must read each completion and choose:
`V` = verbatim/near-verbatim, `T` = template copy with superficial swaps, or `N` = genuine novel combination.
Two blinded batches have now been prepared from the finalized 14M primary novelty files: 1,280 entries each for
two raters (two samples per canary/setting group across 20 treatment cells). The label, confidence, and notes
fields were verified blank. The private manifest is kept separate from the rater files; no human judgments are
claimed.

## Queue status and storage incident (2026-10-08)

The 14M queue is complete, including both frequency-50 balancing cells and baseline 100x/500x true training-seed
replications. Its runner regenerated the trade-off CSVs/plots using matched zero-frequency baselines. The first
48M cell failed as described above and subsequently completed in-place from step 1,000; no second cell was launched.
The blinded batches are prepared, and the final research test suite passed. Full-corpus overlap now covers all 24
canonical 14M cells (7,680 completions), two baseline training-seed replications (640 completions), and one 48M
cell (320 completions). The other 23 scale-cell overlap analyses remain. Do not claim human annotation or the contamination-free
confirmatory study complete. The latest test rerun after adding the two seed-replication corpus-overlap outputs passed 67/67 in 5.46s
with 14 upstream matplotlib/pyparsing deprecation warnings.

The separate [trainer runtime audit](results/trainer_runtime_audit.md) records wall-clock time, step count, best
validation loss, gradient-norm anomaly count, and outcome for every nonempty trainer log. Before checkpoint
pruning, all 119 checkpoint files loaded successfully; the retained 14M best/final files are a validated subset.
The 48M best/final and rolling checkpoints were load-verified after training; only the two rolling files were then
removed. All 104 current primary-result and full-corpus JSON files parsed successfully; all six frequency-specific
corpus indexes matched their corpus SHA-256 and story count. Two blinded annotation CSVs with 1,280 unlabeled
rows each are prepared locally under `results/annotations/`; the private manifest is Git-ignored.

An earlier 2026-10-08 full-suite run passed 67/67 in 6.18 seconds; the latest run after result regeneration
passed 67/67 in 5.46 seconds with 14 upstream matplotlib/pyparsing deprecation warnings.
