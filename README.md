# Memorization vs. compositional creativity: canary study

Does a small language model trade off memorizing recurring narrative elements against recombining them into novel
stories, and does the trade-off shift with architecture? This project measures it with planted "canaries" at
controlled insertion frequencies, following Carlini et al. 2019's exposure methodology, adapted to a
narrative-generation setting.

**Status: the balanced four-architecture 14M exploratory grid is complete, with preliminary findings — the primary
novelty/recombination endpoint still needs blinded human labelling.** The MHA and LayerNorm variants are trained
and scored at 0, 1, 10, 50, 100, and 500 insertions. The baseline and learned-position frequency grids are complete;
the baseline 100x/500x second-training-seed replications are complete. Nineteen of 24 48M cells are complete and
verified: all six baseline, learned-position, and MHA frequencies, plus LayerNorm frequency 0. MHA frequency 500
completed 6,000 updates with best validation loss 1.4810 (PPL 4.3975), seven gradient-norm spikes, and three
gradient-health alerts; its checkpoints and evaluations passed verification. LayerNorm frequency 0 completed with
best validation loss 1.4879 (PPL 4.4278), seven gradient-norm spikes, and six gradient-health alerts; checkpoints
and evaluations passed verification. LayerNorm frequency 1 is active at step 175/6,000 (about 2,144 tokens/s;
early ETA about 6h18m); four cells remain outstanding. Full-corpus overlap has been verified for 45 cells / 14,400
generations across the 14M grid,
the two true baseline seed replications, and completed 48M cells. Interim learned-position frequency-500 results remain single-seed automated measurements;
human novelty labels are still pending. Interim 48M baseline outputs suggest exposure saturation by
frequency 50 while automated diversity proxies change only modestly; these single-seed results do not establish a
memorization-creativity trade-off.
The first 48M cell's initial attempt failed during a checkpoint write, then resumed from its verified step-1,000
checkpoint and completed. See
`PLAN.md` for the phase-by-phase brief this project follows, `PHASE4_NOTES.md` for the detailed running lab
notebook, and `docs/DRAFT_PAPER.md` for the write-up structured for eventual publication, kept in sync as results
come in.
Per-run durations, checkpoint validation, and failure records are summarized in `results/trainer_runtime_audit.md`.

## What's actually been found, in order of how solid the evidence is

1. **A real dose-response memorization signal exists and saturates by frequency 100, replicated across two
   independent architectures.** Multiple canaries converge on the *exact same* maximum exposure value in both
   `baseline` and `variant_a_learned_pos` — a form of evidence ordinary training noise does not produce (confirmed
   directly, see point 3). This is the project's strongest, most defensible result.
2. **Three of the eight canaries were never actually novel to the base pretraining corpus** — `char_pip` ("Pip"),
   `plot_key` ("a shiny key"), and `plot_voice` ("a soft voice") already occur 41-150 times in the base corpus,
   independent of this project's insertions, which permanently saturates their exposure reading regardless of
   training. Root-caused via direct corpus grep (`scripts/check_canary_novelty.py`), not assumed — a canary-design
   flaw, not a metric flaw, and now a required pre-registration check for any future canary study.
3. **A true same-condition second-seed measurement (identical corpus and canary insertion, only the training run
   itself differing) found training noise alone can swing exposure by up to ±2.459 units** — wider than two
   earlier, weaker estimates (~0.85, then ~1.6, both inferred from cross-frequency comparisons that also changed
   the training data). This directly resolved an open question rather than just widening a number: the project's
   previously-strongest single-frequency signal (`plot_lantern` at frequency 1) is exactly canceled by pure noise
   under the second seed — walked back, transparently, in both the lab notebook and the paper draft.
4. **A corrected, teacher-forced extraction test finds zero successful extractions across the entire grid**
   (120 canary-checkpoint pairs, both architectures, all five frequencies) — including canaries sitting at their
   exposure metric's exact maximum. A real, well-powered gap between "the model ranks the true continuation
   highly" (exposure) and "the model's own greedy decoding ever produces it" (extraction) — a finding in its own
   right, not just a caveat.
5. **The first 48M scale-transfer slice is now available, but remains exploratory.** In the 48M baseline,
   all 8 inserted canaries are at rank 1 (the exposure ceiling) at frequencies 50, 100, and 500. Mean exposure
   is unchanged from 50 through 500 (3.926). Over that same interval, mean distinct-1 falls from 0.404 to
   0.374, while distinct-2 stays in a narrow, non-monotonic range (0.798 to 0.788); exact full-corpus four-gram
   overlap is also non-monotonic. This is a reason to complete the matched architecture grid and human scoring,
   not evidence that creativity declines.

## What's not done, and why

- **Phase 5 blinded human annotation** is the single largest remaining gap. The balanced two-rater workflow,
  locked private manifest, agreement statistics, adjudication gate, and clustered confidence intervals are now
  implemented in `scripts/prepare_blinded_annotations.py`, `scripts/score_blinded_annotations.py`, and
  `docs/ANNOTATION_PROTOCOL.md`. No automated labels are treated as evidence.
- **Full-corpus copying analysis** is implemented in `scripts/eval_full_corpus_overlap.py`. It has been run for
  all 24 canonical 14M novelty cells (7,680 completions), both baseline training-seed replications (640
  completions), and nineteen 48M cells (6,080 completions), using each matching
  frequency-specific training corpus. Per-completion outputs, corpus hashes,
  and descriptive summaries are in
  `results/full_corpus_overlap/`. This automated overlap diagnostic is not a substitute for blinded human
  novelty labels and cannot by itself support a creativity claim.
- Baseline 100x/500x training-seed replications are complete. The 48M arm has nineteen verified cells (all baseline,
  learned-position, and MHA frequencies, plus LayerNorm frequency 0), each with memorization, novelty, and matching-corpus overlap evaluations.
  LayerNorm frequency 1 is active; four cells are queued. The initial 48M baseline
  frequency-0 attempt had a disk-full checkpoint-write failure and resumed from its verified step-1,000 state.
- **A confirmatory, contamination-free study** remains necessary for a strong paper. Its frozen recommended design
  is in `docs/CONFIRMATORY_STUDY_PROTOCOL.md`.
- **48M scale-transfer arm:** 24 matched-token configs (four near-matched architectures × six corpus conditions)
  are prepared. The baseline/frequency-0 cell failed at step 1,500 during a checkpoint write, then resumed from
  the intact step-1,000 state and completed 6,000 steps (best validation loss 1.4871). Its evaluations are
  finalized for all six baseline frequencies and learned-position frequencies 0, 1, and 10; the other 15 cells are unfinished (one is currently training).
  These train fresh 48M models on this repository's canary corpora;
  the existing MY-LLM 48M checkpoint
  used different data and a fivefold token budget, so it is not a causal canary result. Protocol and runtime
  expectations are documented in `docs/SCALE_48M_PROTOCOL.md`.

## Compute discipline

This design needs a **fresh pretraining run from scratch per (architecture, frequency) cell** — memorization has
to be attributed to a controlled number of training-time exposures, not to fine-tuning an already-trained model.
On this machine (a MacBook Air M3, 8 GB, no external GPU), a 14M run uses 49.152M training tokens and currently
takes roughly 2.5-3 hours at observed throughput. The source training split itself is 14.58M tokens.
Canary training and the sibling `aarav-lm` project's own training never run concurrently on this single machine —
whichever needs the machine next is queued behind whichever is currently running.

## Reproduce Phase 1 (canary corpus construction)

```bash
cd canary-memorization-study
python scripts/prepare_canary_corpus.py --config configs/canaries.yaml --base data/raw/base.txt --freq 1
# ... one call per frequency; each writes data/processed/freq_<F>/corpus.txt + manifest.json
python scripts/check_canary_novelty.py   # required pre-registration check: every canary identity vs. the base corpus
```

## Phase 2 — architecture variants

`scripts/make_variant_configs.py` builds and validates every variant against the running model code (parameter
counts checked with `aarav_lm.model.core.AaravLM`, configs validated by loading them through `aarav_lm`'s own
`ExperimentConfig.from_yaml`):

| Variant | Change from baseline | Parameters | vs. baseline |
|---|---|---|---|
| baseline | — (aarav-lm's `small` preset: RoPE, GQA n_kv_head=2, RMSNorm, SwiGLU, 8 layers) | 14,162,304 | — |
| A: learned positions | `arch: gpt2` only | 14,358,912 | +1.4% (entirely the new position table; the transformer body is identical) |
| B: MHA | `n_kv_head: 6`, `n_layer: 7` to compensate | 13,964,928 | -1.4% |
| C: LayerNorm | `norm_type: layernorm` only | 14,162,304 | exact match |

## Phase 3 — training (balanced 14M grid complete; 48M scale arm partially complete)

All four architectures have been trained from scratch at frequencies 0, 1, 10, 100, and 500; MHA and LayerNorm
also include the originally pre-registered frequency 50. Baseline and learned-position frequency 50 completed on
2026-10-07. Baseline seed 1338 is complete at 0, 1, 10, 100, and 500. Every run uses 6,000 steps, 49.152M
training tokens over approximately 3.37 passes through the 14.58M-token train split, and the same tokenizer and
schedule within this 14M arm; the matched comparisons change only the declared
architecture or frequency axis. This is 49.152M training tokens per run (6,000 × 8,192 tokens), not 14.6M tokens.

## Phase 4 — memorization (complete for every trained checkpoint)

`scripts/eval_memorization.py` computes exposure (Carlini et al.'s rank-based metric against a curated reference
set) and two extraction tests: a free-generation check, and a corrected, teacher-forced, per-token argmax check
(`argmax_match`) that's well-defined and independently checkable per canary regardless of prompt-sharing. Results:
`results/mem_<architecture>_freq<F>.json` (second-seed results: `..._freq<F>_seed<S>.json`).

## Phase 5 — novelty (generation/proxies run; primary human endpoint not done)

`scripts/eval_novelty.py` generates completions in unseen settings and scores self-BLEU / distinct-n diversity,
and can prepare a hand-labelling batch (`--label-batch`) for the brief's actual three-way classification. Results:
`results/novelty_<architecture>_freq<F>.json`. Use the blinded CSV workflow in `docs/ANNOTATION_PROTOCOL.md`, not
the legacy condition-revealing text batches. `scripts/eval_full_corpus_overlap.py` performs exact maximum
four-gram overlap against every story in the actual training corpus.

## Phase 6 — analysis and plotting

`scripts/analyze_tradeoff.py` builds the memorization-vs-novelty table and plot across the full grid, with a
`--canaries` filter to exclude the three base-corpus-contaminated canaries from the average (since their lift is
mechanically ≈0 regardless of exposure, for reasons unrelated to training). Outputs: `results/tradeoff.csv`/`.png`
(all 8 canaries), `results/tradeoff_clean.csv`/`.png` (5 uncontaminated canaries). Per the brief's own ground rule,
these are plots and tables only — no prose conclusion is drawn in the outputs themselves.

## Tests

67 tests (`pytest tests/`) cover corpus construction, exposure/extraction, novelty metrics, full-corpus overlap,
blinded annotation/scoring, trade-off analysis, and 48M config/parameter validation.

## Publication documents

- `docs/PUBLICATION_READINESS.md`: candid submission gate, venue strategy, IEEE policy requirements, and safe
  résumé wording.
- `docs/CONFIRMATORY_STUDY_PROTOCOL.md`: contamination-free, mixed-frequency, multi-seed confirmatory design.
- `docs/SCALE_48M_PROTOCOL.md`: matched-token 48M scale-transfer experiment and limitations.
- `docs/ANNOTATION_PROTOCOL.md`: blinded two-rater labelling and adjudication procedure.
- `docs/REFERENCES.bib`: verified core references from USENIX, ACL Anthology, and OpenReview; expand before submission.
- `docs/DRAFT_PAPER.md`: living manuscript; exploratory claims remain provisional until the gates above pass.
