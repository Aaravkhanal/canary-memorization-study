# Test and experiment results ledger – Canary Memorization Study

Updated 2026-10-16. This audit covers the completed tests and experiment cells, plus the work that still requires
human judgment; no experiment compute remains queued.

## Expanded scale arm

- Earlier 67/67 research tests passed after adding full-corpus overlap, blinded annotation, and 48M configuration checks;
  the latest paper-support suite result is recorded at the end of this ledger.
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
  baseline frequency-1 overlap fingerprint matches its 73,139-story corpus. Baseline frequency 10 also completed
  (27,860.3 trainer seconds; best loss 1.4896; four gradient-norm spikes and eight gradient-health alerts), and
  its checkpoints and matching-corpus outputs were verified. Baseline frequency 50 also completed (27,234.1
  trainer seconds; best loss 1.5018; three gradient-norm spikes and three gradient-health alerts), and its
  checkpoints and matching-corpus outputs were verified. Since then baseline frequencies 100 and 500, and
  learned-position frequencies 0, 1, and 10, also completed with their memorization, novelty, and matching-corpus
  overlap outputs checked. All 24/24 48M cells are now complete. Final LayerNorm frequency 500 reached 6,000 steps
  with best validation loss 1.4781 / PPL 4.3847 in 24,087 trainer seconds; per-cell values and anomaly counts are
  tabulated in `results/trainer_runtime_audit.md`. An independent pass verified 53 completed summaries, 106
  retained best/final checkpoints, 175 result JSON files, and all 50 exact-overlap reports against their
  frequency-specific 73,139-story corpora. Coverage totals 50 cells / 16,000 generations across the canonical 14M
  grid, two baseline training-seed controls, and the 48M grid. Matched-baseline all-canary and clean-canary
  trade-off tables and figures were regenerated. The initial baseline frequency-0 serialization failure and
  recovery remain documented; no failure occurred in the final four cells. Human labels and the separate
  contamination-free confirmatory study remain outstanding.
- The existing MY-LLM 48M checkpoint used a different corpus and five times the token budget, so it cannot serve as
  the matched arm.
- The 48M scale comparison is exploratory and single-seed initially; it also uses learning rate 5e-4 versus 8e-4
  for the current 14M arm. Both caveats must be addressed or reported before interpreting a size effect.

## Automated tests

- **Previous completion run: 67/67 tests passed** on 2026-10-15 after the experiment and full-corpus analysis
  updates. The later paper-support run, including two new unit tests, is recorded below.
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
- Fresh novelty outputs under `_seed1338` were generated from the actual `train.seed=1338` checkpoints at baseline
  frequencies 100 and 500. Their memorization outputs were generated from those same checkpoints; `_gen1338`
  remains reserved for generation-seed variants.
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

## Historical queue snapshot and storage incident (2026-10-08; superseded by final completion check below)

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

After the 2026-10-11 documentation and interim-result updates, the full research suite again passed 67/67
in 19.06 seconds with the same 14 upstream matplotlib/pyparsing deprecation warnings. Two additional learned-position
48M cells, frequencies 50 and 100, have since completed at 6,000 steps. Frequency 50 took 24,652.2 trainer seconds
(6h51m18s setup-to-done), best validation loss 1.5464, with 39 gradient-norm spikes and four gradient-health alerts.
Frequency 100 took 28,655.9 trainer seconds (7h57m55s setup-to-done), best loss 1.5472, with 45 spikes and two
gradient-health alerts. For each, 12 memorization rows, 32 novelty groups/320 completions, and 32 full-corpus
groups/320 completions were checked; the overlap SHA matched the frequency-specific 73,139-story corpus. The
frequency-500 learned-position cell is now complete. The overlap audit covers 39 cells/12,480 generated completions;
human annotation and the separate contamination-free confirmatory study remain incomplete.

After these interim documentation/result updates, the full suite passed again on 2026-10-11: **67 passed** in
15.35s, with 14 upstream matplotlib/pyparsing deprecation warnings. An independent audit loaded best/final
checkpoints and parsed the three result JSONs for all twelve completed 48M cells, confirming matching corpus
SHA-256 fingerprints and 73,139-story corpus counts.

The learned-position frequency-500 cell completed at step 6,000 with 28,224.9 trainer seconds (7h50m55s
setup-to-done wall time), best validation loss 1.5199 / PPL 4.57, 36 gradient-norm spikes, and five
gradient-health alerts. The runner and an independent check verified its retained best/final checkpoints, 12-row
memorization JSON, 32-group/320-completion novelty output, and matching-corpus full-overlap JSON (frequency-500
SHA-256; 73,139 stories). MHA frequency 0 has completed; MHA frequency 1 is the sole active cell, and 11 cells remain.

After the 2026-10-12 frequency-500 documentation update, the full research test suite passed **67/67** in
23.91 seconds, with 14 upstream matplotlib/pyparsing deprecation warnings. An independent artifact audit loaded
the retained best/final checkpoints and checked result JSON structure and the matching corpus fingerprint/story
count for all 12 completed 48M cells; all checks passed. At the latest status check MHA frequency 0 had reached
MHA frequency 0 completed at 6,000 steps (31,815.7 trainer seconds; 8h50m42s wall time), best validation loss
1.4978 / PPL 4.47, four gradient-norm spikes, and four gradient-health alerts. The independent audit loaded its
best/final checkpoints and checked all three outputs plus the matching 73,139-story corpus fingerprint. MHA
frequency 1 reached step 25/6,000 (early ETA ~8h35m) with three gradient-health alerts and no gradient-norm
spikes at the 11:41 check. Both prepared blinded rater CSVs were rechecked: each has
1,280 rows, condition-hidden columns, and blank label/confidence/notes fields. Human annotation and the
contamination-free confirmatory study remain incomplete.

At the 2026-10-12 11:41:28 IST progress check, the active MHA frequency-1 run was at step 25/6,000, about
1,641 tokens/s, with an early ETA of 8h35m; three gradient-health alerts were logged for blocks 6-8 and no
gradient-norm spikes had occurred. A fresh independent audit validated all 13 completed 48M cells: each had
loadable `best.pt` and `final.pt` checkpoints, 12 memorization rows, 32 novelty groups × 10 generations, and
32 full-corpus groups × 10 generations. Every full-corpus result's SHA-256 matched its frequency-specific
73,139-story corpus. The full suite passed again: **67 passed** in 13.17s (14 upstream deprecation warnings).

At the 2026-10-12 17:35:44 IST progress check, the active MHA frequency-1 run had reached step 5,250/6,000 at
about 1,953 tokens/s (early ETA ~52m). Step-5,000 validation loss was 1.5066 (new best). Six gradient-health alerts had been logged at steps 25 and 50; no
gradient-norm spikes were logged. The other eleven 48M cells remain queued.

After the 12:32 IST documentation refresh, the research suite passed once more: **67 passed** in 12.43s, with
14 upstream matplotlib/pyparsing deprecation warnings and no test failures.

After the 13:35 IST queue-status update, the suite was rerun: **67 passed** in 13.24s with 14 upstream
matplotlib/pyparsing deprecation warnings; no tests failed.

Following the 14:31 IST status refresh, the full suite again passed: **67 passed** in 14.58s with 14 upstream
matplotlib/pyparsing deprecation warnings and no failures.

The latest full suite, after the documentation edits in this update, passed **67/67** in 14.95s with 14
upstream matplotlib/pyparsing deprecation warnings and no failures.

After the 15:38 IST MHA progress refresh, the full research suite passed **67/67** in 14.18s, with 14 upstream
matplotlib/pyparsing deprecation warnings and no failures.

Following the 16:37 IST status update, the complete suite passed again: **67 passed** in 14.73s, with 14
upstream matplotlib/pyparsing deprecation warnings and no failures.

After the 17:35 IST MHA progress update, the full suite passed **67/67** in 18.44s, with 14 upstream
matplotlib/pyparsing deprecation warnings and no failures.

At the 2026-10-13 00:47 IST checkpoint, MHA frequency 1 had completed and its retained checkpoints, three result
JSONs, and frequency-specific corpus fingerprint were independently verified. MHA frequency 10 was active at
step 5,175/6,000; step-5,000 validation loss was 1.5054 / PPL 4.51, with three logged gradient-norm spikes and
two gradient-health alerts. Two low-system-memory warnings occurred without stopping training. Full-corpus coverage
stands at 40 evaluated cells / 12,800 generations. Annotation and the
contamination-free confirmatory study remain incomplete.

After the latest documentation update, the full research suite passed **67/67** in 13.35s on 2026-10-12, with
14 upstream matplotlib/pyparsing deprecation warnings and no failures.

After the 19:39 IST MHA frequency-10 progress update, the full research suite passed again: **67/67** in 33.28s,
with the same 14 upstream matplotlib/pyparsing deprecation warnings and no failures. The longer runtime occurred
while the MPS training job continued; no test failures were observed.

After the 20:39 IST progress refresh, the complete suite passed **67/67** in 15.05s, with 14 upstream
matplotlib/pyparsing deprecation warnings and no test failures.

After the 21:39 IST progress refresh, the full suite passed again: **67/67** in 37.73s, with the same 14 upstream
deprecation warnings and no failures while the MPS training process continued.

After the 22:34 IST progress refresh, the suite passed **67/67** again in 14.44s, with 14 upstream
matplotlib/pyparsing deprecation warnings and no failures.

After the 23:43 IST progress refresh, the full suite passed **67/67** in 16.06s, with the same 14 upstream
deprecation warnings and no test failures.

After the 2026-10-13 00:47 IST update, the full suite passed **67/67** in 15.05s, with 14 upstream
matplotlib/pyparsing deprecation warnings and no test failures.

After the 2026-10-13 MHA frequency-10 completion and frequency-50 queue update, the full suite passed **67/67**
in 16.98 seconds, with 14 upstream matplotlib/pyparsing deprecation warnings and no test failures. The
frequency-10 48M artifacts were independently checked: both retained checkpoints loaded, the memorization and
novelty JSON dimensions were correct, and the full-corpus JSON matched its frequency-specific corpus fingerprint.
The active MHA frequency-50 run was at step 1,275/6,000 during this update; no tests failed while it trained.

After MHA frequency 100 completed and frequency 500 reached step 500/6,000 (18:04 IST), the full suite passed
**67/67** in 12.47s, with 14 upstream matplotlib/pyparsing deprecation warnings and no failures. Frequency-100
best/final checkpoints loaded with `weights_only=True`; its 12-row memorization result, 32-group × 10-completion
novelty results, and full-corpus result passed structural checks. The overlap report matched the frequency-100
corpus SHA-256 (`b5eb8b384c4bef02507ff6a7f89f490c3de67ff2affe5440eaed10a433f29c88`) and 73,139-story count.
Frequency 500 is the only active training job; three gradient-norm spikes, three gradient-health alerts, and no
training failure were recorded through step 500. Seven scale cells remain queued. Human annotation and the
contamination-free confirmatory study are not complete.

After recording the MHA frequency-100 completion and frequency-500 step-500 snapshot, the full research suite
passed **67/67** in 42.73s, with 14 upstream matplotlib/pyparsing deprecation warnings and no test failures.
The MPS training job remained active during the run. At the latest log check (18:58 IST), MHA frequency 500 was at
step 1,325/6,000, with five gradient-norm spikes, three gradient-health alerts, and intermittent low-memory warnings.

Following the 18:58 IST documentation refresh, the full suite passed again: **67/67** in 25.75s, with the same
14 upstream deprecation warnings and no failures. The single 48M MHA frequency-500 training process remained active.

After the 20:04 IST progress refresh, the full research suite passed **67/67** in 15.75s, with 14 upstream
matplotlib/pyparsing deprecation warnings and no failures. MHA frequency 500 had reached step 2,300/6,000 with no
training failure logged.

After the 21:05 IST progress refresh, all **67/67** research tests passed in 18.34s, with the same 14 upstream
matplotlib/pyparsing deprecation warnings and no failures; the MHA frequency-500 run continued during testing.

After the 22:10 IST progress refresh, all **67/67** tests passed in 13.53s with 14 upstream deprecation warnings
and no failures. The active MHA frequency-500 cell was at step 3,925/6,000, with no training failure logged.

After the 23:10 IST progress refresh, all **67/67** tests passed in 15.30s with the same 14 upstream warnings and
no failures. The frequency-500 MHA process remained active during testing.

After the 00:13 IST progress refresh, all **67/67** tests passed in 18.28s with 14 upstream deprecation warnings
and no failures. MHA frequency 500 was at step 5,600/6,000 while the suite ran.

After recording MHA frequency-500 completion, the LayerNorm frequency-0 active status, and the updated run audit,
the full research test suite passed **67/67** in 13.77s. There were 14 upstream matplotlib/pyparsing deprecation
warnings and no test failures. The sole active MPS trainer was LayerNorm frequency 0; no duplicate job was started.

After the 02:19 IST LayerNorm progress update, the full suite passed again: **67/67** in 14.29s. It emitted 14
upstream matplotlib/pyparsing deprecation warnings and no failures. LayerNorm frequency 0 was the only active MPS
training process; five 48M cells remain queued.

After the 05:16 IST LayerNorm frequency-0 progress update, the full research suite passed **67/67** in 15.76s.
The run emitted 14 upstream matplotlib/pyparsing deprecation warnings and no failures. LayerNorm frequency 0 was the
only active MPS training job; five scale cells remain queued.

After the 04:18 IST LayerNorm frequency-0 progress refresh, all **67/67** tests passed in 15.48s. There were 14
upstream matplotlib/pyparsing deprecation warnings and no failures. The frequency-0 LayerNorm trainer remained the
only active MPS job; five scale cells remain queued.

After the 03:21 IST LayerNorm frequency-0 progress refresh, all **67/67** tests passed in 15.16s. The run emitted
14 upstream matplotlib/pyparsing deprecation warnings and no failures. The 48M LayerNorm frequency-0 trainer was
the only active MPS training process; five scale cells remain queued.

After the 06:23 IST LayerNorm frequency-0 progress refresh, the full suite passed **67/67** in 15.56s with 14
upstream matplotlib/pyparsing deprecation warnings and no failures. LayerNorm frequency 0 was the only active MPS
trainer; five scale cells remain queued.

After the 07:23 IST LayerNorm frequency-0 progress refresh, all **67/67** tests passed in 15.59s. The suite emitted
14 upstream matplotlib/pyparsing deprecation warnings and no failures. The LayerNorm frequency-0 process was the
only active MPS trainer; five 48M cells remain queued.

After the 08:25 IST 48M status refresh and LayerNorm frequency-0 completion, the full research suite passed **67/67**
in 19.49s with 14 upstream matplotlib/pyparsing deprecation warnings and no failures. The sequential 48M runner
remained active; LayerNorm frequency 1 was the sole MPS trainer at step 175/6,000 at 08:27 IST, with four scale
cells queued. No duplicate training job was started.

After the 16:45 IST completion of LayerNorm frequency 1 and the frequency-10 status refresh, the full research suite
passed **67/67** in 15.04s with 14 upstream matplotlib/pyparsing deprecation warnings and no failures. LayerNorm
frequency 10 was the sole active MPS trainer at step 700/6,000 (16:46 IST); it had eight gradient-health alerts and
one gradient-norm spike (step 693), with no training failure. Three 48M cells remained queued.

After recording LayerNorm frequency-1 completion and frequency-10 progress through step 700/6,000, the research
suite passed **67/67** in 14.31s. It emitted 14 upstream matplotlib/pyparsing deprecation warnings and no failures.
The sequential 48M runner remained active with three cells still to complete after the current LayerNorm frequency-10
cell; no duplicate MPS job was started.

## Final completion check (2026-10-15)

After the 48M runner completed and the final integrity, overlap, and matched-baseline analysis pass, the complete
research suite passed **67/67** in 4.13 seconds. Pytest reported 14 upstream Matplotlib/Pyparsing deprecation
warnings and no test failures. All 24 48M cells, 50 exact-corpus overlap outputs (16,000 completions), both
baseline seed-control novelty outputs, and the two blank 1,280-row blinded annotation sheets are present and
validated. The final LayerNorm frequency-500 cell completed 6,000 updates; its runtime, validation result, and
anomaly counts are in `results/trainer_runtime_audit.md`. Human annotation and the separate contamination-free
confirmatory study remain incomplete, so the manuscript is still an exploratory draft rather than submission-ready.

## Paper-support completion pass (2026-10-15)

All five requested paper-support items were completed without starting new training or collecting human labels:

1. Reconciled the Markdown draft and open IEEE LaTeX source with the audited scope; removed claims that two seeds
   define a general noise band, scoped the 0/120 extraction result, and retained the 48M learning-rate/single-seed
   caveats. The LaTeX source now has a clean-canary 14M summary table and a provisional results section.
2. Added `docs/RESULTS_CLAIM_AUDIT.md`, mapping claims to data and spelling out permitted and prohibited wording.
3. Refined the rater rubric, masking limits, locking, agreement/adjudication, ethics, and statistical plan. Both
   rater sheets were checked at 1,280 rows each with matching IDs and blank label/confidence/notes; SHA-256 values
   are recorded in `docs/ANNOTATION_PROTOCOL.md`. The private manifest was not opened or staged.
4. Froze version 1 of the contamination-free confirmatory protocol with a power/precision and ethics/data-rights
   start gate. No confirmatory corpus or model run was started.
5. Added `docs/ARTIFACT_REPRODUCIBILITY.md`, a versioned-file SHA-256 manifest generator and test, plus 300-dpi
   descriptive trade-off figures. Clean-clone retraining remains unverified because ignored corpora/tokenizer/
   checkpoints and the sibling `aarav-lm` dependency are not in this repository.

The paired-seed descriptive audit is reproducible with `scripts/analyze_seed_sensitivity.py` and outputs
`results/seed_sensitivity_clean.csv`. The regenerated plots use automated proxies only; publication-resolution
does not imply color-blind/grayscale review has passed.

**Paper-support verification:** `/Users/aaravkhanal/miniforge3/bin/python -m pytest tests/` passed **69/69** on
2026-10-16, with 14 upstream Matplotlib/Pyparsing deprecation warnings and no failures. Both regenerated
trade-off CSVs contain 48 matched architecture/frequency rows. The manuscript is still exploratory: human labels
and the separate contamination-free confirmatory study remain outstanding.

## Confirmatory/reproducibility implementation start (2026-10-16)

The gated two-scale execution plan, exact package lock, content-addressed training-input lock, and separate
analysis/training reproducibility checker were added. Both checker modes pass on the current machine: Python and
the eight pinned packages match; the training mode also matches the exact `aarav-lm` commit, base-corpus hash and
size, and both tokenizer-file hashes. This is a local prerequisite check, not yet a clean-clone reproduction.
The expanded suite passes **70/70** with 14 upstream Matplotlib/Pyparsing deprecation warnings. No confirmatory
model was trained because the pre-outcome power, canary/schedule, storage, rights, and ethics gates remain open.

The deterministic confirmatory bank and schedule were then generated and checked: 40 inserted identities, eight
controls, and 2,048 reference alternatives have zero normalized matches in the complete base corpus. Five
counterbalanced assignment seeds are frozen, with three planned and two held as pre-outcome contingencies. A
250-replicate power/precision simulation selected the three-seed design under its declared SESOIs and variance
assumptions, producing a 24-cell two-scale plan and 7,680 ratings per rater. These are design calculations, not
confirmatory outcomes. The full suite now passes **76/76** with the same 14 upstream warnings; no MPS job was
started, and storage/corpus-config/rights/ethics/clean-room gates remain open.

The three planned mixed-frequency corpora were then built deterministically for assignment/training seeds
20261016–20261018. Each contains exactly 5,288 insertions; every inserted document hashes to the training split,
and the committed manifests record output hashes, source story indices, per-canary frequencies, and split counts.
All 24 planned 14M/48M architecture configs use portable relative paths, the same 0.0005 learning rate, and the
same 49.152M-token budget. The exact 59,999,181-byte base subset was independently matched to byte range
0–59,999,180 of revision `f54c09fd...`'s `TinyStoriesV2-GPT4-train.txt`; the acquisition script reproduces its
SHA-256. The exact 4,096-token BPE artifact is now versioned with its provenance note and verified against the
input lock. The expanded suite passes **84/84**. These are pre-outcome input locks, not trained confirmatory results.

A fresh-clone engineering smoke test then passed from GitHub checkouts of both repositories: exact corpus
acquisition, bank screening, deterministic seed-20261016 corpus reproduction, dependency/input verification,
base-only tokenization and dataset validation, and one CPU-only 14M training step. The first prepare-data call was
made outside the cloned study root and exposed a relative-path validation failure; the documented rerun from the
study root passed, and the reusable script now uses absolute temporary output paths. No MPS memory or
confirmatory-inserted training data was used, so this is not a scientific result. The suite now passes **85/85**.

The confirmatory statistical models were then frozen before outcomes in a machine-readable plan and executable
analysis script. Exposure uses a balanced grand-mean log10-frequency slope with canary-clustered covariance and
seed/canary fixed effects; human novelty uses binomial GEE on complete adjudicated N versus V/T labels. Sum-coded
architecture/scale interactions, Holm correction, ceiling sensitivity, and the sole GEE fallback are explicit.
Automated, blank, or invalid labels are rejected. Four new tests bring the full suite to **89/89**.

## Confirmatory storage and recovery gate (2026-10-17)

A frozen storage/recovery plan now requires 25 GiB free on a write/read/fsync-tested artifact filesystem. A
machine-readable preflight validates the three corpus hashes, 24 config paths, committed protocol inputs, manual
gate records, ethics state, and capacity. A portable sequential runner owns one global lock across both scales,
refuses another Python trainer, rechecks space per cell, and permits resume only after checkpoint deserialization.
It preserves best/final artifacts and does not delete rolling checkpoints until required evaluations verify. The
preflight currently fails as designed: about 8.3 GiB is free, ethics/consent mode is unresolved, and the post-cell
confirmatory evaluator is not yet frozen. No MPS or confirmatory training was started. Five gate tests brought the
full suite to **94/94** in 11.78 seconds, with 14 upstream Matplotlib/Pyparsing deprecation warnings and no failures.

The first executable 1,025-candidate evaluator audit then caught a pre-outcome bank defect: three character target
identities were also present in the synthetic alternative pool. They were absent from the base corpus, but could
not validly serve as their own alternatives. The deterministic generator now excludes every inserted/control
identity and appends screened replacements, preserving 1,024 alternatives and all corpus bytes/schedules. The
corrected bank hash is `f9afb1e6c0c6db87483c5e0c39578f20abe06583fd767fd49994e61ca62072d2`;
all three corpus manifests were regenerated to record it before any training or outcome inspection.

The confirmatory outcome workflow was then frozen before training. Each cell will produce 48 exposure rows and
320 status-retaining generations under hashed decoding settings, followed by exact four-gram overlap against only
the content-hash-selected training split. The runner validates checkpoint/corpus/result hashes and fixed row counts
before deleting rolling checkpoints. A separate builder refuses fewer than 24 evaluated cells and will create two
differently shuffled 7,680-row rater sheets with blank annotation fields plus a git-ignored private condition key.
It does not create automated labels. Eleven new evaluation, overlap, annotation, and cleanup tests brought the
full suite to **105/105** in 11.16 seconds, with 14 upstream Matplotlib/Pyparsing deprecation warnings and no
failures. No MPS job or confirmatory scientific evaluation was run.

A read-only disk audit then recorded the exact free-space failure and allocated sizes of the largest relevant
project, sibling-project, cache, and download paths without deleting or moving anything. Two tests verify that the
auditor ignores symlinks, records no action, and fails oversized capacity thresholds. The suite now contains
**107/107 tests**, which passed in 13.29 seconds with 14 upstream Matplotlib/Pyparsing warnings and no failures.

## Confirmatory ethics and consent decision gate (2026-10-17)

The unresolved ethics record is now explicit and machine-readable. A decision document separates self-only
annotation from external recruitment, states the evidentiary loss of abandoning the frozen two-rater endpoint,
and provides a draft external-rater information and consent template that is not approved for use. The validator
accepts only a complete selected route and cannot grant institutional approval. Three tests cover the unresolved,
external-rater, and self-only records. The full suite now contains **110/110 tests**, which passed in 11.37
seconds with 14 upstream Matplotlib/Pyparsing warnings and no failures. The committed unresolved record fails
safely and makes no approval claim.

## Paper and reproducibility status refresh (2026-10-17)

Both analysis-mode and training-input reproducibility checks pass: the pinned package versions match, the base
corpus and tokenizer hashes match, and the sibling `aarav-lm` checkout is at the locked revision. The IEEE source
was corrected to distinguish the successful one-step fresh-clone engineering smoke test from the still-unrun
full-cell clean-room reproduction, and to describe the actual frozen confirmatory OLS/GEE models. The desktop
LaTeX compiler succeeded. The full suite passed **110/110 tests** in 9.85 seconds with 14 upstream
Matplotlib/Pyparsing warnings and no failures. No confirmatory outcome was generated or inspected.

## Confirmatory annotation-role decision (2026-10-17)

The owner selected two independent external raters for the primary human endpoint plus a separately shuffled
investigator self-annotation sensitivity sheet. The sheets will never be pooled, and self-ratings do not count
toward external agreement or replace adjudication. The batch builder and frozen evaluation plan now encode all
three blank sheets. External recruitment, annotation, and training remain blocked until the applicable
institutional determination, finalized consent, compensation, withdrawal process, and explicit clearances are
recorded. One added design test brings the suite to **111/111 tests**, passing in 10.72 seconds with 14 upstream
warnings and no failures. The IEEE source compiled successfully, and no confirmatory outcome was generated.

## Conservative citation metadata (2026-10-17)

A parseable `CITATION.cff` now identifies the repository, author, scope, and code URL while deliberately omitting
an unissued DOI, release date, owner-unconfirmed license, affiliation, and ORCID. A unit test enforces those
boundaries so later automation cannot silently invent release metadata. The full suite passed **112/112 tests**
in 9.41 seconds with 14 upstream warnings and no failures. This is release preparation only; no archive or DOI is
claimed and no confirmatory outcome was generated.

## Machine-readable external-release gate (2026-10-17)

A release checker now separates publication/deposit readiness from the training start gate. It requires explicit
release authorization, selected project and redistribution terms, completed confirmatory training and human
annotation, full-cell clean-room reproduction, a real permanent archive, and a DOI matching `CITATION.cff`.
The committed snapshot fails candidly on eight outstanding items and does not block pre-outcome engineering.
Two tests cover the current blocked state and a fully evidenced synthetic release. The full suite passed
**114/114 tests** in 11.68 seconds with 14 upstream warnings and no failures; no release or DOI is claimed.

## Owner-authorized storage cleanup (2026-10-17)

Rebuildable caches, duplicate downloaded application installers, and four large Photo Booth videos were removed
outside Desktop under explicit owner authorization. No Desktop folder, research checkpoint, corpus, result,
source file, or sibling-project artifact was removed or moved. Free space increased from about 7.9 GiB to 26.4
GiB, so the exact 25-GiB capacity probe now passes. The runner will recheck capacity before every cell because the
margin is modest. The overall start gate remains closed solely on its manual/ethics components: the external-rater
institutional determination, finalized consent, compensation, withdrawal process, and explicit clearances are
still absent. The post-cleanup suite passed **114/114 tests** in 12.14 seconds with 14 upstream warnings and no
failures. No confirmatory training or outcome inspection occurred.

## Computational-training authorization amendment (2026-10-17)

After the exact storage probe passed, the owner explicitly authorized model training. A dated pre-outcome
amendment now separates computational training, which has no human participants, from external-rater recruitment
and annotation. The ethics validator and start gate report these scopes separately. Human recruitment, sheet
distribution, annotation, adjudication, and human-endpoint analysis remain blocked; no institutional approval is
claimed or inferred. This amendment was recorded before any confirmatory outcome was generated or inspected.
The full suite passed **114/114 tests** in 9.99 seconds with 14 upstream warnings and no failures.

The first authorized queue launch then stopped before tokenization or training because `aarav-lm` resolved the
portable relative corpus path against its own repository root. No checkpoint, model step, evaluation, or outcome
was produced. The runner now supplies absolute runtime-only corpus, tokenized-data, and tokenizer overrides while
preserving the committed configs; a regression test locks this interface repair. The full suite passed
**115/115 tests** in 10.20 seconds with 14 upstream warnings and no failures.

### 2026-10-18: confirmatory pre-checkpoint interruption recovery

The sequential confirmatory queue was interrupted during the seed-20261018 learned-position 14M cell at step 175,
before its first rolling checkpoint. Nine preceding 14M cells remained complete and verified. The incomplete
experiment directory and log are retained for audit; the runner now starts a fresh experiment directory only when
an interrupted run has no resumable checkpoint, while preserving normal in-place resume for valid checkpoints.
The full research suite passed **116/116 tests** in 10.85 seconds with 14 upstream Matplotlib/Pyparsing warnings
and no failures.
