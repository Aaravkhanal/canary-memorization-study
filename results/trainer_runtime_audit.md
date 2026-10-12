# Trainer runtime and checkpoint audit

Collected from the retained `models/**/train.log` and each run's `summary.json`, updated 2026-10-12. Durations are wall-clock
time from the first setup line to the final `[done]` or `[error]` log line (local time); update counts, best validation
losses, and gradient-norm anomaly counts come from the run summaries. The three zero-byte placeholder logs
(`baseline/freq_1/exp_001`, `baseline/freq_500/exp_001`, and `variant_b_mha/freq_50/exp_001`) contain no trainer output;
each corresponding cell completed under its `exp_002` directory and is not counted as a failed run.

All completed 14M cells reached 6,000 updates. The 48M baseline grid and learned-position frequencies 0, 1, 10,
50, 100, and 500, plus MHA frequency 0, have completed; MHA frequency 1 is currently training at step 2,625/6,000
(early ETA ~3h47m). Baseline frequency 0 required one disk-full
checkpoint-write recovery.

| Architecture / run | Frequency | Runtime | Updates | Best val loss | Grad-norm spikes | Outcome |
|---|---:|---:|---:|---:|---:|---|
| baseline | 0 | 02:43:40 | 6,000 | 1.5494 | 0 | completed |
| baseline | 1 | 02:50:22 | 6,000 | 1.5510 | 5 | completed (`exp_002`) |
| baseline | 10 | 02:44:59 | 6,000 | 1.5474 | 2 | completed |
| baseline | 50 | 02:42:50 | 6,000 | 1.5595 | 4 | completed |
| baseline | 100 | 03:07:30 | 6,000 | 1.5609 | 2 | completed |
| baseline | 500 | 02:54:18 | 6,000 | 1.5364 | 3 | completed (`exp_002`) |
| learned positions | 0 | 04:36:35 | 6,000 | 1.6231 | 25 | completed |
| learned positions | 1 | 02:36:09 | 6,000 | 1.6244 | 20 | completed |
| learned positions | 10 | 02:46:11 | 6,000 | 1.6259 | 21 | completed |
| learned positions | 50 | 02:28:30 | 6,000 | 1.6385 | 20 | completed |
| learned positions | 100 | 02:52:15 | 6,000 | 1.6420 | 21 | completed |
| learned positions | 500 | 02:57:59 | 6,000 | 1.6126 | 20 | completed |
| MHA | 0 | 02:20:38 | 6,000 | 1.5617 | 4 | completed |
| MHA | 1 | 02:20:56 | 6,000 | 1.5569 | 3 | completed |
| MHA | 10 | 02:18:04 | 6,000 | 1.5661 | 1 | completed |
| MHA | 50 | 02:07:46 | 6,000 | 1.5738 | 1 | completed (`exp_002`) |
| MHA | 100 | 02:16:59 | 6,000 | 1.5755 | 8 | completed |
| MHA | 500 | 02:21:19 | 6,000 | 1.5474 | 0 | completed |
| LayerNorm | 0 | 02:29:13 | 6,000 | 1.5536 | 2 | completed |
| LayerNorm | 1 | 02:29:37 | 6,000 | 1.5502 | 1 | completed |
| LayerNorm | 10 | 02:25:05 | 6,000 | 1.5440 | 3 | completed |
| LayerNorm | 50 | 02:16:29 | 6,000 | 1.5664 | 1 | completed |
| LayerNorm | 100 | 02:16:28 | 6,000 | 1.5614 | 5 | completed |
| LayerNorm | 500 | 02:15:53 | 6,000 | 1.5372 | 1 | completed |
| baseline, training seed 1338 | 0 | 02:58:25 | 6,000 | 1.5586 | 4 | completed |
| baseline, training seed 1338 | 1 | 02:50:40 | 6,000 | 1.5577 | 2 | completed |
| baseline, training seed 1338 | 10 | 03:35:25 | 6,000 | 1.5594 | 2 | completed |
| baseline, training seed 1338 | 100 | 02:41:29 | 6,000 | 1.5713 | 1 | completed |
| baseline, training seed 1338 | 500 | 03:02:47 | 6,000 | 1.5488 | 4 | completed |
| 48M baseline, initial attempt | 0 | 02:02:19 | 1,500 | 1.8588* | 4 | failed during checkpoint write; disk full |
| 48M baseline, resumed cell | 0 | 07:29:36 trainer time† | 6,000 | 1.4871 | 4 | completed; resumed at step 1,000 |
| 48M baseline | 1 | 07:13:36 trainer time | 6,000 | 1.4931 | 6 | completed; 7 gradient-health alerts |
| 48M baseline | 10 | 07:44:20 trainer time | 6,000 | 1.4896 | 4 | completed; 8 gradient-health alerts |
| 48M baseline | 50 | 07:33:54 trainer time | 6,000 | 1.5018 | 3 | completed; 3 gradient-health alerts |
| 48M baseline | 100 | 07:08:21 trainer time | 6,000 | 1.5061 | 3 | completed; 7h08m40s setup-to-done wall span |
| 48M baseline | 500 | 07:09:05 trainer time | 6,000 | 1.4802 | 8 | completed; 7h33m28s wall span crossing midnight |
| 48M learned positions | 0 | 06:36:56 trainer time | 6,000 | 1.5309 | 35 | completed; 6h37m19s setup-to-done wall span |
| 48M learned positions | 1 | 07:00:42 trainer time | 6,000 | 1.5275 | 41 | completed; 7h01m04s wall span |
| 48M learned positions | 10 | 06:46:11 trainer time | 6,000 | 1.5305 | 40 | completed; 6h46m33s wall span |
| 48M learned positions | 50 | 06:51:18 | 6,000 | 1.5464 | 39 | completed; 24,652.2 trainer seconds; 4 gradient-health alerts |
| 48M learned positions | 100 | 07:57:55 | 6,000 | 1.5472 | 45 | completed; 28,655.9 trainer seconds; 2 gradient-health alerts |
| 48M learned positions | 500 | 07:50:55 | 6,000 | 1.5199 | 36 | completed; 28,224.9 trainer seconds; 5 gradient-health alerts |
| 48M MHA | 0 | 08:50:42 | 6,000 | 1.4978 | 4 | completed; 31,815.7 trainer seconds; 4 gradient-health alerts |

\* For the failed 48M row, the summary held a candidate best validation loss of 1.8588 at the failing step, but its
update did not persist to `best.pt`. The last logged and persisted evaluation/checkpoint is step 1,000 (validation
loss 2.0190, perplexity 7.53). The step-1,000 training checkpoint was loaded successfully; step 1,500 was not
saved. The failure was PyTorch's `unexpected pos` serialization error with about 185 MB free on the filesystem.

The baseline frequency-1 48M run started at 16:52:18 local on 2026-10-08 and completed at 00:06:17 on
2026-10-09 (7h13m59s wall time); its summary records 26,015.6 trainer seconds. It completed 6,000 updates with
best validation loss 1.4931227 / PPL 4.45, six gradient-norm spikes, and seven gradient-health alerts. Its
`best.pt` and `final.pt` each loaded with `torch.load(..., weights_only=True)`. Memorization (12 rows), novelty
(32 groups / 320 completions), and exact full-corpus overlap (32 groups / 320 completions) parsed and passed
shape checks. The overlap metadata's SHA-256 matched `data/processed/freq_1/corpus.txt` (73,139 stories). Rolling
checkpoints were removed after verification. Baseline frequency 10 began next and is currently training; the
other 21 grid cells are queued. At the latest audit there were 6.5 GiB free; retaining both best and final
checkpoints across the remaining grid may exceed available storage, and the user has been asked to choose a
retention policy.

The baseline frequency-10 48M run started at 00:12:20 local on 2026-10-09 and completed at 07:57:05
(7h44m45s wall time); its summary records 27,860.3 trainer seconds. Best validation loss was 1.48957798 /
PPL 4.44, with four gradient-norm spikes and eight gradient-health alerts. Its best/final checkpoints loaded
successfully. Memorization (12 rows), novelty (32 groups / 320 completions), and full-corpus overlap (32 groups /
320 completions) passed parsing and shape checks; the overlap metadata hash matched the frequency-10 corpus and
73,139 stories. Rolling checkpoints were removed after verification. Baseline frequency 50 then began training;
at the latest log check it had completed 250/6,000 steps. There are now three completed 48M cells, one active,
and 20 queued. The latest free-space check was 7.0 GiB; retaining both best and final checkpoints for the full
remaining grid may exceed capacity, and user direction is pending.

Baseline frequency 50 started at 08:02:49 and completed at 15:37:05 local on 2026-10-09 (7h34m16s wall time;
27,234.1 trainer seconds). It completed 6,000 updates with best validation loss 1.5018234 / PPL 4.49, three
gradient-norm spikes, and three gradient-health alerts. Best/final and rolling checkpoints loaded before the
rolling files were removed; memorization, novelty, and full-corpus outputs were verified, and the overlap hash
matched the frequency-50 corpus (73,139 stories). Baseline frequency 100 began next; at 15:44:10 local it was
starting its first training updates. Four 48M cells are complete, one is active, and 19 are queued. The latest
disk check showed about 13 GiB free; both best and final artifacts are being retained while disk space is monitored.

The initial audit loaded all 119 `.pt` checkpoint files present before the approved cleanup with
`torch.load(..., weights_only=True)`; zero were corrupt. The 58 rolling checkpoints belonging to completed 14M
runs were then removed, preserving best/final checkpoints, logs, and results. The resumed 48M cell's best, final,
step-5,500, and step-6,000 checkpoint files all loaded successfully before the two rolling files were removed;
best/final and logs remain. All 74 pre-analysis JSON files parsed successfully, and all 25 full-corpus JSON files
now parsed successfully. The failed step-1,500 save did not leave an additional partial checkpoint file.

## 48M baseline, frequency 0: completed after resume

The initial process failed at 04:17:06 local after 2h02m19s at step 1,500 during checkpoint serialization. The
same cell resumed at 07:36:09 local from its valid step-1,000 checkpoint and completed step 6,000 at 13:44:45
local. The trainer summary reports 26,976.3 seconds (07:29:36) of training time for the resumed process, 4
gradient-norm anomalies, and best validation loss 1.4871208 (perplexity 4.4243). The original failed attempt
remains a separately documented 02:02:19 failure; it is not counted as a second completed cell. Memorization,
novelty, and matching-corpus overlap evaluations are finalized (12 canaries; 320 novelty completions; 73,139
training stories checked). Every retained checkpoint parsed with `torch.load(..., weights_only=True)` and all three
JSON results parsed. After verification, only rolling `step_*.pt` files for this exact cell were removed; best/final
checkpoints, logs, and results remain. The rest of the 24-cell 48M matrix is not complete.

† Trainer-reported elapsed compute excludes the initial failed process; report that attempt separately. The local
start-to-finish wall span of the resumed process was approximately 6h09m, so do not infer runtime from timestamps
alone when reconciling with trainer seconds.

## 48M learned-position frequencies 50 and 100

Frequency 50 started at 03:26:39 and finished at 10:17:57 local (6h51m18s setup-to-done); its summary reports
24,652.2 trainer seconds, best validation loss 1.5464118 / PPL 4.69, 39 gradient-norm spikes, and four
gradient-health alerts. Frequency 100 ran from 10:25:13 to 18:23:08 local (7h57m55s setup-to-done); its summary
reports 28,655.9 trainer seconds, best validation loss 1.5472167 / PPL 4.70, 45 spikes, and two health alerts.
For each cell, both retained `best.pt` and `final.pt` loaded with `weights_only=True`; memorization JSONs contain
12 rows, novelty JSONs contain 32 groups/320 completions, and full-corpus outputs contain 32 groups/320
completions with a SHA-256 matching the corresponding 73,139-story corpus. The runner validated these artifacts
before removing rolling checkpoints. MHA frequency 0 is now the sole active training cell.

## 48M learned-position frequency 500

The run started at 18:30:10 on 2026-10-11 and completed at 02:21:05 on 2026-10-12 (7h50m55s setup-to-done);
the trainer summary records 28,224.9 seconds, best validation loss 1.5199076 / PPL 4.57, 36 gradient-norm
spikes, and five gradient-health alerts. Best/final checkpoints loaded with `weights_only=True`. Memorization,
novelty, and full-corpus results passed the 12-row, 32-group/320-completion checks. The overlap SHA-256 matched
the 73,139-story frequency-500 corpus. Rolling step checkpoints were removed only after validation.

## Current queue snapshot (2026-10-12)

The 48M matrix is 13/24 complete: all six baseline and all six learned-position cells, plus MHA frequency 0.
MHA frequency 1 is the single active cell; 11 cells are queued. At the 11:44:47 local check it had reached step
2,625/6,000 (early ETA ~3h47m), logged six gradient-health alerts at steps 25 and 50, and had no gradient-norm spikes.
Full-corpus overlap covers 39 evaluated cells / 12,480 generations, including all canonical 14M cells and two
true baseline training-seed replications. Approximately 9 GiB was free at the last disk check. No completion is
claimed for the active or queued cells.
for the active or queued cells are yet claimed.
