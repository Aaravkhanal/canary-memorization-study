# Experiment Timeline – Canary Memorization Study

| # | Job | Description | Start (local = UTC + 5:30) | End (local) | Status |
|---|-----|-------------|---------------------------|------------|--------|
| 1 | Medium‑model pre‑training (exp 018) | 25.7 M‑param model, 180 M tokens (≈11 k steps) | 2026‑10‑04 08:20 AM | – | Queued |
| 2 | Large‑model pre‑training (exp 022) | 48.1 M‑param model, full TinyStoriesV2 (≈545 M tokens) | 2026‑10‑04 08:20 AM | – | Queued |
| 3 | Canary freq 100 – baseline | Small model (≈14 M) trained on frequency‑100 corpus, baseline architecture | 2026‑10‑04 08:20 AM | – | Queued |
| 4 | Canary freq 100 – learned‑pos | Same as #3 but with `variant_a_learned_pos` architecture | 2026‑10‑04 08:20 AM | – | Queued |
| 5 | Canary freq 500 – baseline | Small model trained on frequency‑500 corpus, baseline architecture | 2026‑10‑04 08:20 AM | – | Queued |
| 6 | Canary freq 500 – learned‑pos | Same as #5 but with `variant_a_learned_pos` architecture | 2026‑10‑04 08:20 AM | – | Queued |
| 7 | Full‑split loss eval – medium model | Compute val‑loss / perplexity for 512 / 1024‑token contexts (medium checkpoint) | – | – | Queued |
| 8 | Full‑split loss eval – large model | Same as #7 but for the large model checkpoint | – | – | Queued |
| 9 | Memorization evaluation | `scripts/eval_memorization.py` on every new canary checkpoint | – | – | Queued |
|10 | Novelty evaluation | `scripts/eval_novelty.py` on every new canary checkpoint | – | – | Queued |
|11 | Trade‑off aggregation & plot | `scripts/analyze_tradeoff.py` – combines memorisation + novelty results into CSV & PNG | – | – | Queued |
|12 | Git add | Stage modified/untracked files in the repo | 2026‑10‑04 11:43 AM | 2026‑10‑04 11:44 AM | Completed |
|13 | Git commit | Commit: “Add tradeoff results and labelling files” | 2026‑10‑04 11:45 AM | 2026‑10‑04 11:45 AM | Completed |
|14 | Git push | Push to `origin/main` | 2026‑10‑04 11:47 AM | 2026‑10‑04 11:50 AM | Completed |

*All timestamps are local (UTC + 5:30).*

## 2026-10-07 continuation

- 15:06 local: baseline 14M frequency-50 training started after the prior novelty evaluation batch exited.
- 15:17 local: baseline frequency-50 training reached step 750/6,000; the trainer log reported roughly 2.3 hours
  remaining. The queue proceeds to learned-position frequency 50, then baseline training-seed 1338 at frequencies
  100 and 500, followed by result aggregation.
- The 48M scale runner is waiting for the 14M queue and will run sequentially after it; no 48M canary model has
  started yet.
- Audit correction: the 20 completed `run_seed_experiments.sh` outputs used generation seed 1338. Their filenames
  now use `_gen1338`, distinct from training-seed replication outputs ending `_seed1338`. This resolves a potential
  skip/misattribution in the upcoming baseline 100/500 replication cells; those cells will regenerate novelty
  JSONs.
- The 20 renamed generation-seed JSON files were parsed and validated; 67/67 research tests passed after the
  naming correction.

- 16:17 local: baseline 14M frequency-50 training reached step 2,975/6,000; the trainer estimated 1 hour 22
  minutes remaining for that cell.
- 17:19 local: the same baseline frequency-50 run reached step 5,225/6,000 with a trainer ETA of about 21 minutes.
  The training process remained healthy in MPS; no later 14M cell had started at this check.
- 17:39:59 local: baseline frequency-50 training completed 6,000 updates. The retained run log reports 2h42m50s
  elapsed, best validation loss 1.5595, and perplexity 4.76. Memorization and novelty evaluation outputs were
  produced (12 memorization rows; 32 novelty groups/320 completions); the checkpoint is present.
- 17:44:57 local: learned-position frequency-50 training started; it completed at 20:13:27 (2h28m30s), 6,000
  updates, best validation loss 1.6385 / perplexity 5.15. Memorization and novelty JSONs and checkpoint were
  produced. The log contains 20 gradient-norm spike events, including values 129.3 and 40.15; training reached
  the full budget, but clipping diagnostics should be checked before interpreting stability.
- 20:17:34–22:59:03 local: baseline frequency-100 second-training-seed run completed in 2h41m29s; best validation
  loss 1.5713 / perplexity 4.81. Its true training-seed checkpoint, memorization JSON, and `_seed1338` novelty JSON
  were produced.
- 23:03:35–02:06:22 local (2026-10-08): baseline frequency-500 second-training-seed run completed in 3h02m47s;
  best validation loss 1.5488 / perplexity 4.71. Its true training-seed checkpoint and separate `_seed1338` result
  JSONs were produced. The 14M runner then regenerated the matched-baseline trade-off CSVs and plots.
- 02:14:47 local (2026-10-08): first 48M cell, baseline frequency 0, started. It failed at 04:17:06 (2h02m19s
  wall time) while writing at step 1,500; filesystem had ~185 MB free. The summary records 12.288M tokens,
  7 gradient-health and 4 gradient-norm anomalies. The last intact resumable checkpoint is step 1,000, verified by
  loading it as a training checkpoint; the 48M runner exited and no evaluation completed.
- 07:36:09 local (2026-10-08): after explicit approval, 58 validated rolling checkpoints from completed 14M
  cells were removed, preserving best/final checkpoints, logs, and results. The original baseline/frequency-0
  48M cell resumed from step 1,000 and completed 6,000 updates at 13:44:45. It had best validation loss 1.4871 /
  PPL 4.4243 and four gradient-norm anomalies. The initial step-1,500 save failure remains separately recorded.
  Memorization and novelty evaluations were generated; all retained checkpoints loaded successfully. The two
  rolling checkpoints were removed after verification; best/final and logs remain. No other 48M cell was launched.
- 07:38–09:31 local (2026-10-08): exact full-corpus word-four-gram overlap was computed for the then-available
  22 canonical 14M novelty files (320 completions each, 7,040 total), each against its matching corpus. Later
  that day, canonical baseline and learned-position frequency-0 outputs were generated from their matching
  checkpoints with generation seed 20260927, then evaluated against the frequency-0 corpus. The full canonical
  14M grid now has 24/24 cells and 7,680 completions; all six corpus indexes match their source corpus hashes.
- After the resumed 48M cell completed, its 320 novelty outputs were checked against the same frequency-0 corpus.
  Initially, the exact overlap audit contained 25 files / 8,000 completions: the complete 14M grid plus one
  exploratory 48M cell. The remaining 23 scale cells, human annotation, and separate contamination-free
  confirmatory study remain incomplete.
- 09:42 local (2026-10-08): reran the full research test suite after making generated trade-off CSVs use stable
  LF line endings; 67 passed, 14 upstream deprecation warnings. A later post-regeneration run passed 67/67 in
  5.48s with the same warnings.
- The 2026-10-08 research test rerun passed 67/67 in 5.48s (14 upstream matplotlib/pyparsing deprecation
  warnings). At that point, 102 primary-result and full-corpus JSON files parsed successfully. The two blinded rater CSVs contain 1,280
  rows each; label, confidence, and notes fields are blank. The separate private manifest is excluded from Git.
- A full read-only load check of all 119 `.pt` files under `models/` passed; no corrupt checkpoint was found. The
  per-run timing, validation, anomaly, and outcome table is in `results/trainer_runtime_audit.md`.
- 14:05 local (2026-10-08): exact full-corpus checks were added for the true baseline 100x/500x training-seed
  novelty outputs, each using its matching frequency-specific corpus (320 completions each). All six corpus
  indexes still match their source hashes and story counts. The full-corpus directory now contains 27 enriched
  JSONs / 8,640 completions: 24 canonical 14M cells, two seed replications, and one 48M cell. Combined mean is
  0.096991, median 0.076190, maximum 1.0. This automated copying diagnostic is not a human novelty score.
- 14:10 local (2026-10-08): the full 67-test suite passed again (5.46s; 14 upstream deprecation warnings).
  All 104 current primary-result and full-corpus JSON files parsed; all 27 overlap outputs matched the correct
  frequency corpus hash and index story count. The two blinded CSVs still contain 1,280 rows each with labels,
  confidence, and notes blank.

## 2026-10-09 48M queue continuation

- Baseline frequency 1 completed from scratch at 00:06:17 local after starting at 16:52:18 on 2026-10-08.
  Trainer time was 26,015.6 seconds (7h13m36s); wall time was 7h13m59s. It completed 6,000 updates with best
  validation loss 1.4931227 / PPL 4.45, six gradient-norm spikes, and seven gradient-health alerts. The retained
  best/final checkpoints loaded, memorization and novelty outputs passed shape checks, and its 320-completion
  full-corpus report matched the frequency-1 corpus hash and 73,139-story count. Rolling checkpoints were removed
  after verification.
- The 48M queue then started baseline frequency 10 sequentially. At 00:18:32 local it had reached step 75/6,000;
  the trainer estimated 7h42m remaining for that cell. Baseline frequencies 0 and 1 are complete; 21 cells remain
  queued. This is the only active training/evaluation process.
- The full-corpus directory now contains 28 result files / 8,960 completions (24 canonical 14M cells, two
  baseline training-seed cells, and two 48M cells). The two 48M full-corpus fingerprints were checked against
  their frequency-specific corpora. Storage was 7.3 GiB free at the latest check. Preserving best and final
  checkpoints for all remaining cells may exceed capacity; user direction on retention/storage is pending.

## 2026-10-09 48M baseline frequency-10 completion

- Baseline frequency 10 began at 00:12:20 local and completed at 07:57:05 (7h44m45s wall; 27,860.3 trainer
  seconds). It reached 6,000 updates, best validation loss 1.48957798 / PPL 4.44, with four gradient-norm spikes
  and eight gradient-health alerts. Best/final checkpoint loads and all memorization/novelty/full-corpus JSON
  checks passed; the overlap fingerprint matched the frequency-10 corpus (73,139 stories). Rolling checkpoints
  were removed after verification.
- Baseline frequency 50 began next. At 08:24:14 local it was at step 275/6,000 with a trainer estimate of
  7h22m remaining. Three of 24 48M cells are complete, this is the sole active cell, and 20 remain queued.
- The full-corpus audit now has 30 enriched result files / 9,600 completions (14M primary grid, two true
  baseline training-seed replications, and four 48M cells). Available disk space was about 13 GiB after the
  last rolling-checkpoint cleanup; both best/final files remain in place while capacity is monitored.

## 2026-10-09 48M baseline frequency-50 completion

- Baseline frequency 50 started at 08:02:49 and completed at 15:37:05 local (7h34m16s wall; 27,234.1 trainer
  seconds). Best validation loss was 1.5018234 / PPL 4.49, with three gradient-norm spikes and three
  gradient-health alerts. The best/final checkpoints and memorization/novelty/full-corpus outputs were verified;
  the full-corpus hash matched the frequency-50 corpus (73,139 stories). Rolling checkpoints were removed after
  verification.
- Baseline frequency 100 started next at 15:43:37 local. Four of 24 scale cells are complete, this is the sole
  active training cell, and 19 remain queued. The full-corpus directory now has 30 outputs / 9,600 completions.
  The latest disk check showed 13 GiB free; both best and final checkpoints are being retained while space is
  monitored.

## 2026-10-11 48M scale-grid continuation

- Baseline frequency 100 completed 6,000 updates (25,701.3 trainer seconds; 7h08m40s setup-to-done wall
  span), best validation loss 1.5061, with three gradient-norm spikes. Frequency 500 completed 6,000 updates
  (25,744.6 trainer seconds; 7h33m28s wall span crossing midnight), best loss 1.4802, with eight spikes.
- Learned-position frequency 0 completed in 23,815.7 trainer seconds (6h37m19s wall span), best loss 1.5309,
  with 35 logged spikes. Frequency 1 completed in 25,242.0 trainer seconds (7h01m04s wall span), best loss
  1.5275, with 41 spikes. Frequency 10 completed in 24,370.5 trainer seconds (6h46m33s wall span), best loss
  1.5305, with 40 spikes. These counts are retained exactly; clipping means training completed, not that the
  excursions should be ignored.
- Each of the five cells produced memorization, 32-group/320-completion novelty, and full-corpus outputs; the
  runner validated JSON structure, loaded retained checkpoints, and matched each overlap report to its
  frequency-specific 73,139-story corpus before removing rolling step checkpoints.
- At that checkpoint, the 48M grid had nine of 24 cells complete and the exact-overlap audit covered 35 cells /
  11,200 completions. Human annotation remains outstanding.

## 2026-10-11 learned-position 48M frequencies 50 and 100

- Learned-position frequency 50 completed 6,000 steps (24,652.2 trainer seconds; 6h51m18s from setup to done),
  best validation loss 1.5464 / PPL 4.69, 39 gradient-norm spikes and four gradient-health alerts. Frequency 100
  completed 6,000 steps (28,655.9 trainer seconds; 7h57m55s setup-to-done), best loss 1.5472 / PPL 4.70, 45
  spikes and two health alerts. Both cells' best/final checkpoints, memorization/novelty JSONs, and matching-corpus
  full-overlap JSONs were verified; each corpus has 73,139 stories and the matching fingerprint.
- At frequencies 50 and 100, learned-position exposure ranks put 7/8 and 8/8 inserted canaries at rank 1. Mean
  distinct-1 was 0.387/0.406, distinct-2 0.789/0.804, and maximum exact word-four-gram overlap 0.020/0.027.
  These are single-seed automated proxies only; human V/T/N scoring is not complete.
- Eleven of 24 48M cells are complete and 12 are queued. Learned-position frequency 500 is active at step 125/6,000
  (ETA ~6h27m); this is the only MPS training process. Exact full-corpus coverage is 37 cells / 11,840
  completions. Free disk was 9.6 GiB at that historical check.

## 2026-10-12 48M scale-grid continuation

- Learned-position frequency 500 completed at 02:21:05 local (7h50m55s setup-to-done; 28,224.9 trainer seconds),
  best validation loss 1.5199, 36 gradient-norm spikes, and five gradient-health alerts. Best/final checkpoints,
  all three evaluation outputs, and matching frequency-500 full-corpus fingerprint (73,139 stories) were verified.
- MHA frequency 0 completed at 6,000 steps (31,815.7 trainer seconds; 8h50m42s setup-to-done), best validation
  loss 1.4978 / PPL 4.47, with four gradient-norm spikes and four gradient-health alerts. Its retained checkpoints,
  memorization/novelty results, and matching-corpus overlap report were independently verified. MHA frequency 1
  MHA frequency 1 completed at 18:27:55 local (24,507.9 trainer seconds; 6h48m52s setup-to-done), with best
  validation loss 1.4982 / PPL 4.47, six gradient-norm spikes, and six gradient-health alerts. Checkpoints and
  all three results passed independent checks; the matching-corpus overlap fingerprint has 73,139 stories.
  Descriptive frequency-1 metrics: 4/8 inserted targets rank 1 (mean exposure 2.614), unseen-control mean exposure
  1.369 with 0/4 rank 1, greedy extraction 0/8; distinct-1/2 0.383/0.786; full-corpus 4-gram overlap mean/median/max
  0.095/0.072/0.750. MHA frequency 10 then started at 18:39:49 and reached step 5,175/6,000 by 00:47:40 on
  2026-10-13 (about 2,047 tokens/s; ETA near 55m); step-5,000 validation loss was 1.5054 / PPL 4.51. Three gradient-norm
  spikes and two gradient-health alerts are logged; two low-system-memory warnings occurred without stopping training.
  Ten cells remain queued. The 48M arm is 14/24 complete and exact overlap
  covers 40 cells / 12,800 generations.
  Human annotation and the contamination-free confirmatory experiment remain outstanding. Disk free was 7.8 GiB.

## 2026-10-13 MHA frequency-10 completion; MHA frequency-50 queued

- MHA frequency 10 completed at 01:46:09 local (start 18:39:49 on Oct 12; 7h06m20s setup-to-done, 25,555
  trainer seconds), reaching 6,000 updates. Best validation loss was 1.4961678 / PPL 4.46455; three gradient-norm
  spikes and two gradient-health alerts were recorded. Both checkpoints loaded with `weights_only=True`; all three
  result JSONs passed structural checks, and the full-corpus report matched the frequency-10 corpus SHA-256 and
  73,139-story count.
- MHA frequency 50 initialized at 01:57:39; its step-0 evaluation at 01:58:02 reported loss 8.4626 / PPL 4,734.3.
  At 03:45 it was at step 1,275/6,000 (about 1,600 tokens/s; ETA about 7h), with four gradient-norm spikes and two
  gradient-health alerts; the step-1,000 validation loss was 2.0505 / PPL 7.77. Nine scale cells remain queued. The 48M scale matrix is 15/24
  complete and full-corpus overlap covers 41 cells / 13,120 generations. About 8.3 GiB was free. This run remains
  exploratory; human annotation and the contamination-free confirmatory study are not complete.

## 2026-10-13 MHA frequency-50 completion; MHA frequency-100 active

- MHA frequency 50 finished at 10:27:57 local after starting at 01:57:39 (8h30m18s setup-to-done; 30,597.5
  trainer seconds). It reached 6,000 updates with best validation loss 1.5050441 / PPL 4.50435, five gradient-norm
  spikes, and two gradient-health alerts. Independent verification loaded both retained checkpoints, validated the
  12-row memorization result and 32 × 10 generation arrays in both novelty outputs, and confirmed the full-corpus
  SHA-256 against the frequency-50, 73,139-story training corpus.
- MHA frequency 100 was the next sequential cell. At 10:57 it had reached step 300/6,000 (about 2,108 tokens/s;
  early ETA about six hours), with eight scale cells still queued. The 48M arm is 16/24 complete and full-corpus
  overlap covers 42 cells / 13,440 generations. Human annotation and the contamination-free confirmatory study
  remain incomplete.

## 2026-10-13 MHA frequency-100 completion; frequency-500 active

MHA frequency 100 completed at 17:19:28 local (start 10:38:18; 6h41m10s setup-to-done, 24,046 trainer seconds),
with best validation loss 1.5105218 / PPL 4.52909, four gradient-norm spikes, and four gradient-health alerts.
The independent audit loaded both retained checkpoints, checked the memorization and novelty JSON structures, and
verified the full-corpus report against the matching frequency-100 corpus SHA-256 and 73,139-story count. No
training/evaluation failure occurred.

MHA frequency 500 is the next sequential cell. At 21:05:58 local it reached step 3,200/6,000 (about 1,837 tokens/s;
early ETA about 3h29m); six gradient-norm spikes and three gradient-health alerts are recorded. Low-memory warnings
occurred without stopping training, and no failure has been logged.
Seven cells remain queued. The 48M matrix is 17/24 complete; exact full-corpus overlap covers 43 evaluated cells /
13,760 generations, including the complete canonical 14M grid and two true baseline training-seed replications.
Human annotation and the separate contamination-free confirmatory study are not complete.

### 22:10 IST progress check

The active MHA frequency-500 cell had reached step 5,600/6,000 at 00:13:02 (about 1,907 tokens/s; approximate
ETA 29m). Seven gradient-norm spikes and three gradient-health alerts were recorded; intermittent low-memory
warnings did not stop the run. Seven other 48M cells remain after this active cell. No duplicate MPS job was launched.

## 2026-10-14: MHA frequency 500 complete; LayerNorm frequency 0 running

- MHA frequency 500 completed at 00:41:05 local, after a 17:29:36 start on 2026-10-13 (7h11m29s wall; 25,864.4
  trainer seconds), with best validation loss 1.4810324 / PPL 4.39748. The run logged seven gradient-norm spikes
  and three gradient-health alerts, but no failure. Both retained checkpoints loaded; the memorization JSON had
  12 rows, novelty JSONs had 32 groups × 10 outputs, and full-corpus overlap had matching frequency-500 corpus
  identity / 73,139 stories. Exact full-corpus coverage advanced to 44 cells / 14,080 generations.
- LayerNorm frequency 0 started at 00:54:46. At 01:14:27 it had reached step 275/6,000 (about 2,011 tokens/s;
  early ETA about 6h28m). Six gradient-health alerts and one gradient-norm spike (step 118) are recorded; no run
  failure is logged. This is the sole active MPS training job; five scale cells remain queued and the matrix is
  18/24 complete.
- The full 67-test research suite was rerun after the status/documentation refresh; see `test_results_summary.md`
  for the latest exact result. Human annotation and the separate contamination-free confirmatory study remain
  incomplete.

### 02:19 IST LayerNorm frequency-0 progress check

The active cell reached step 1,225/6,000 at 02:19:06 (about 1,943 tokens/s, ETA about 5h35m). Step-1,000
validation loss was 2.0189 / PPL 7.53. Five gradient-norm spikes (steps 118, 384, 522, 1,119, 1,208) and six
gradient-health alerts (three at step 25, three at step 50) have been recorded; no training failure is logged.
Five other 48M cells remain queued. The exact-overlap total remains 44 cells / 14,080 generations. The full test
suite passed 67/67 after the previous documentation refresh; rerun it after this update before the next commit.

### 03:21 IST LayerNorm frequency-0 progress check

The active cell reached step 2,125/6,000 at 03:21:47 (about 2,002 tokens/s, ETA about 4h24m). Step-1,000
validation loss was 2.0189 / PPL 7.53. Six gradient-norm spikes (steps 118, 384, 522, 1,119, 1,208, 1,522) and
six gradient-health alerts (three at step 25, three at step 50) have been recorded; no training failure is logged.
Five other 48M cells remain queued. Exact-overlap coverage is still 44 cells / 14,080 generations. Rerun the full
test suite after this status refresh; annotation and the contamination-free confirmatory study remain incomplete.
