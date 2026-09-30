# Memorization vs. compositional creativity: canary study

Does a small language model trade off memorizing recurring narrative elements against recombining them into novel
stories, and does the trade-off shift with architecture? This project measures it with planted "canaries" at
controlled insertion frequencies, following Carlini et al. 2019's exposure methodology, adapted to a
narrative-generation setting.

**Status: the reduced-grid memorization side is essentially done, with real findings — the novelty/recombination
side still needs the user's own hand-labelling.** Two architectures (`baseline`, `variant_a_learned_pos`) are
fully trained and scored across the complete pre-registered frequency grid (0 control, 1, 10, 100, 500). See
`PLAN.md` for the phase-by-phase brief this project follows, `PHASE4_NOTES.md` for the detailed running lab
notebook, and `docs/DRAFT_PAPER.md` for the write-up structured for eventual publication, kept in sync as results
come in.

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

## What's not done, and why

- **Phase 5 hand-labelling** (the brief's actual novelty/recombination measurement — a three-way classification of
  generated completions, hand-labelled before any automated judge is trusted) is the single largest remaining
  gap. Batches are prepared and ready in `results/labelling/*.txt` (one file per trained frequency/architecture);
  everything reported so far about "novelty" uses an automated diversity proxy (distinct-2) standing in for this,
  which is explicitly flagged everywhere it's used. This step needs the user's own judgment, not automation.
- **`variant_b_mha` and `variant_c_layernorm`** (the brief's other two architecture axes) have parameter-matched
  configs generated but have not been trained, pending review of the two-axis result so far.
- **The same second-seed noise measurement at frequencies 10, 100, and 500** (done so far only at 0 and 1) would
  settle whether the frequency-100/500 ceiling-saturation finding needs the same treatment — flagged as
  additional compute, not yet run.

## Compute discipline

This design needs a **fresh pretraining run from scratch per (architecture, frequency) cell** — memorization has
to be attributed to a controlled number of training-time exposures, not to fine-tuning an already-trained model.
On this machine (a MacBook Air M3, 8 GB, no external GPU), each ~14.6M-token run takes roughly 1.5-2.5 hours.
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
| B: MHA | `n_kv_head: 6`, `n_layer: 7` to compensate | 13,964,928 | -1.4% (config only, not trained) |
| C: LayerNorm | `norm_type: layernorm` only | 14,162,304 | exact match (config only, not trained) |

## Phase 3 — training (done for baseline and variant A, full grid)

Both architectures trained from scratch at frequencies 0 (zero-exposure control), 1, 10, 100, and 500, plus a
second seed of `baseline`'s frequency 0/1 cells for a genuine noise-band measurement (`configs/training/baseline/
freq_<F>_seed1338.yaml`). Every run: 6,000 steps, ~14.6M tokens, same tokenizer/hyperparameters across every cell
so architecture and frequency are the only intended axes of variation.

## Phase 4 — memorization (done for the full grid)

`scripts/eval_memorization.py` computes exposure (Carlini et al.'s rank-based metric against a curated reference
set) and two extraction tests: a free-generation check, and a corrected, teacher-forced, per-token argmax check
(`argmax_match`) that's well-defined and independently checkable per canary regardless of prompt-sharing. Results:
`results/mem_<architecture>_freq<F>.json` (second-seed results: `..._freq<F>_seed<S>.json`).

## Phase 5 — novelty (proxy metric run; hand-labelling not done)

`scripts/eval_novelty.py` generates completions in unseen settings and scores self-BLEU / distinct-n diversity,
and can prepare a hand-labelling batch (`--label-batch`) for the brief's actual three-way classification. Results:
`results/novelty_<architecture>_freq<F>.json`; labelling batches in `results/labelling/`.

## Phase 6 — analysis and plotting

`scripts/analyze_tradeoff.py` builds the memorization-vs-novelty table and plot across the full grid, with a
`--canaries` filter to exclude the three base-corpus-contaminated canaries from the average (since their lift is
mechanically ≈0 regardless of exposure, for reasons unrelated to training). Outputs: `results/tradeoff.csv`/`.png`
(all 8 canaries), `results/tradeoff_clean.csv`/`.png` (5 uncontaminated canaries). Per the brief's own ground rule,
these are plots and tables only — no prose conclusion is drawn in the outputs themselves.

## Tests

50 tests (`pytest tests/`) cover corpus construction (including a regression test for a real splice bug found
while building it), the exposure/extraction computation, the novelty metrics, and the trade-off analysis script.
