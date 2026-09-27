# The brief this project follows

Pasted by the user, 2026-09-27. Phases are worked through in order with a checkpoint after each; nothing past
Phase 1 has been started without review. This file is the source of truth for what "done" means at each phase —
kept verbatim so a later session can't drift from what was agreed.

## Research question

Existing 14.2M-parameter decoder-only model (`aarav-lm`, TinyStories-style corpus). As it memorizes recurring
narrative elements (character names, plot fragments) through repeated exposure during training, does it lose the
ability to recombine those elements into novel stories? Does the trade-off differ by architecture (position
encoding, attention type)?

## Phase 1 — environment and data setup (this delivery)

Project structure (`data/`, `configs/`, `models/`, `training/`, `eval/`, `results/`, `logs/`, plus `scripts/` added
for the code itself). Canary injection script; two canary types (character: fixed name+trait; plot-fragment: fixed
structural phrase); frequencies 1x/10x/50x/100x/500x, each a separate corpus variant; unseen controls; near-duplicate
paraphrases for later eval. Deterministic, logged, pre-registered — not silently changed later.

**Checkpoint 1** (this delivery): project structure, canary injection script, finalized canary/frequency config,
before Phase 2.

## Phase 2 — architecture variants (not started)

From the baseline (8 layers, width 384, 6 query / 2 KV heads GQA, RoPE, RMSNorm, SwiGLU, ~14.16M params, already
`aarav-lm`'s `small` preset), one axis at a time: Variant A position encoding (RoPE <-> learned, `arch: modern` vs
`gpt2` in `aarav_lm.config`), Variant B attention (GQA <-> MHA, `n_kv_head`), optional Variant C normalisation
(RMSNorm <-> LayerNorm, `norm_type`). Same tokenizer, vocab, context, token budget, LR schedule, batch size across
variants; parameter count logged and kept close to 14.2M.

**Checkpoint 2**: model configs and parameter counts, confirm only the intended axis differs.

## Phase 3 — training runs (not started; the expensive phase, see README.md's cost estimate)

One model per (architecture variant, canary-frequency corpus). Log loss curve, val loss/perplexity, wall-clock,
final checkpoint; resumable; `models/{architecture_variant}/{canary_frequency}/checkpoint.pt` plus a metadata JSON
per run.

**Checkpoint 3**: one variant at one frequency, end to end, as a smoke test (loss curves, coherent generations),
before scaling to the full grid.

## Phase 4 — memorization evaluation (not started)

Per trained model: exposure metric (Carlini et al. 2019 "Secret Sharer": rank the canary's log-perplexity against
plausible alternative canaries of similar length/structure); verbatim extraction rate (prompt with the canary
prefix, greedy decode, exact-match check); the same two measurements on unseen controls and near-duplicates as
baselines.

**Checkpoint 4**: sanity-check on a few models (higher frequency should show higher exposure/extraction than 1x or
unseen) before the full grid.

## Phase 5 — compositional novelty evaluation (not started)

Recombination test: prompt with the canary character/fragment in an unseen setting, 10 completions at temperature
0.7-1.0. Per generation: n-gram overlap and edit distance against the nearest training story; a three-way
classification (verbatim/near-verbatim, template copy with superficial swaps, genuine novel combination) prepared
as a hand-labelling batch (spreadsheet or plain text, one generation per row, blank label column) — **no LLM-judge
auto-scoring until 100-200 samples are hand-labelled first**; diversity across completions (self-BLEU, distinct-n).

**Checkpoint 5**: the prepared hand-labelling batch and diversity/overlap scores for a subset, before the full grid.

## Phase 6 — analysis and plotting (not started)

Per architecture variant: memorization score (x) vs. novelty/recombination score (y), one point per frequency
level. Overlay variants on one comparison plot. Summary stats: inflection point, per architecture. One tidy
CSV/dataframe, one row per model run.

**Checkpoint 6**: plots and summary table, **no prose conclusions** — the user interprets first.

## Ground rules (apply to every phase)

Correct and reproducible over fast. Fixed, logged random seeds everywhere. The pre-registered canary list and
frequency levels are not changed once locked, even if early results look messy — flag instead. Flag unexpectedly
high compute cost before proceeding. Ask for anything not yet provided rather than assuming a default.
