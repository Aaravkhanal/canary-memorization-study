# Test and experiment results ledger – Canary Memorization Study

Updated 2026-10-07. This is the separate audit file for completed tests, completed experiment cells, outstanding
compute, and work that still requires human judgment.

## Expanded scale arm

- 67/67 research tests passed after adding full-corpus overlap, blinded annotation, and 48M configuration checks.
- Four 48M architecture conditions × six frequencies are configured (24 runs), each targeting 49,152,000 training
  tokens. Counts are 48,100,480 baseline; 48,428,160 learned positions; 47,239,040 MHA; and 48,100,480 LayerNorm.
- The 48M configs and sequential runner are added, but no 48M canary training has started yet. The existing MY-LLM
  48M checkpoint used a different corpus and five times the token budget, so it cannot serve as the matched arm.
- The 48M scale comparison is exploratory and single-seed initially; it also uses learning rate 5e-4 versus 8e-4
  for the current 14M arm. Both caveats must be addressed or reported before interpreting a size effect.

## Automated tests

- **67/67 tests passed** on 2026-10-07 after adding the full-corpus overlap, blinded annotation, and 48M config
  validation tests.
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
| baseline | done | done | done | **queued** | done | done |
| learned absolute positions | done | done | done | **queued** | done | done |
| multi-head attention | done | done | done | done | done | done |
| LayerNorm | done | done | done | done | done | done |

This corrects the older README/paper claim that MHA and LayerNorm had not been trained. Both are complete across
the full grid. Baseline and learned-position are the only architectures still missing the pre-registered 50x cell.

## Seed replications

Baseline second-seed training is complete at 0x, 1x, and 10x. At 10x, the second seed strengthens rather than
erases the signal: `char_nira` and `plot_lantern` reproduce exactly, while `char_boro` and `char_suri` rise to the
exposure ceiling. Baseline 100x and 500x second-seed runs are queued after the current evaluation batch.

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

## Active queue

1. The fixed-generation-seed batch is complete and its filenames have been disambiguated.
2. The 14M runner is training baseline 50x (step 2,975/6000 at the 16:17 local check; trainer ETA was ~1 hour 22 minutes for
   this cell), followed by learned-position 50x and baseline 100x/500x second-seed training/evaluation.
3. Regenerate matched-baseline trade-off CSVs/plots, rerun tests, and update the paper.
4. Human Phase 5 labelling remains a non-automatable blocker to the paper's primary trade-off conclusion.
5. After the 14M queue, train/evaluate the 24 48M scale-transfer cells from
   `scripts/run_48m_scale_experiments.sh`. The configurations have all parsed successfully; no 48M canary run has
   started yet. See `docs/SCALE_48M_PROTOCOL.md` for parameter counts, token budget, learning-rate caveat, and
   compute estimate.
