# Trainer runtime and checkpoint audit

Collected from the retained `models/**/train.log` and each run's `summary.json` on 2026-10-08. Durations are wall-clock
time from the first setup line to the final `[done]` or `[error]` log line (local time); update counts, best validation
losses, and gradient-norm anomaly counts come from the run summaries. The three zero-byte placeholder logs
(`baseline/freq_1/exp_001`, `baseline/freq_500/exp_001`, and `variant_b_mha/freq_50/exp_001`) contain no trainer output;
each corresponding cell completed under its `exp_002` directory and is not counted as a failed run.

All completed 14M cells reached 6,000 updates. The 48M frequency-0 baseline cell has now completed after one
disk-full checkpoint-write failure and an in-place resume from its verified step-1,000 checkpoint.

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

\* For the failed 48M row, the summary held a candidate best validation loss of 1.8588 at the failing step, but its
update did not persist to `best.pt`. The last logged and persisted evaluation/checkpoint is step 1,000 (validation
loss 2.0190, perplexity 7.53). The step-1,000 training checkpoint was loaded successfully; step 1,500 was not
saved. The failure was PyTorch's `unexpected pos` serialization error with about 185 MB free on the filesystem.

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
