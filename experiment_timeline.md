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
  The exact overlap audit now contains 25 files / 8,000 completions total: the complete 14M grid plus one
  exploratory 48M cell. Its aggregate mean is 0.095013, median 0.075269, max 1.0. This is an automated copying
  diagnostic, not a human novelty judgment. The remaining 23 scale cells, human annotation, and separate
  contamination-free confirmatory study remain incomplete.
- 09:42 local (2026-10-08): reran the full research test suite after making generated trade-off CSVs use stable
  LF line endings; 67 passed, 14 upstream deprecation warnings. A later post-regeneration run passed 67/67 in
  5.48s with the same warnings.
- The 2026-10-08 research test rerun passed 67/67 in 5.48s (14 upstream matplotlib/pyparsing deprecation
  warnings). After regeneration, all 102 primary-result and full-corpus JSON files parsed successfully; all 25
  index metadata records matched corpus SHA-256 and story counts. The two blinded rater CSVs contain 1,280
  rows each; label, confidence, and notes fields are blank. The separate private manifest is excluded from Git.
- A full read-only load check of all 119 `.pt` files under `models/` passed; no corrupt checkpoint was found. The
  per-run timing, validation, anomaly, and outcome table is in `results/trainer_runtime_audit.md`.
