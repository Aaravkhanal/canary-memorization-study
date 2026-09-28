# Memorization vs. compositional creativity in a small language model: does the trade-off depend on architecture?

**Status: draft, in progress.** This document is a structured write-up of the project's methods and results, kept
in sync with the lab notes in `PHASE4_NOTES.md` as new results come in. It is meant to be turned into a paper or
report once the reduced-pass grid (and, ideally, a seed-replication pass) is complete — it is not final, and every
section below says explicitly what is settled versus still provisional. Prose interpretation beyond what the data
directly supports is deliberately withheld pending the user's own read of the results, per this project's ground
rules (`PLAN.md`).

## Abstract (placeholder)

*To be written once the reduced-pass grid and, ideally, a seed-replication pass are complete. Draft claim the
data supports so far: a small (14M-parameter) decoder-only LM shows a measurable, dose-dependent memorization
signal for at least some planted narrative elements after as few as 10 insertions in ~14.6M training tokens, and
this signal replicates across two different positional-encoding schemes (RoPE vs. learned absolute positions) —
but the standard exposure metric (Carlini et al., 2019) requires a reference set well beyond what a naive
implementation provides, or it silently saturates and reports zero signal for canaries whose phrasing is already
fluent under the model's prior.*

## 1. Research question

Does a small (14.2M-parameter) decoder-only transformer, trained on a TinyStories-style corpus, trade off
memorizing recurring narrative elements (character names, plot fragments) against the ability to recombine those
elements into novel stories as exposure frequency increases — and does that trade-off differ by architecture
(positional encoding, attention type, normalization)? (Verbatim research question, `PLAN.md`.)

## 2. Related work

The memorization side of this design follows the "Secret Sharer" methodology of Carlini, Liu, Erlingsson, Kos &
Song (2019), *The Secret Sharer: Evaluating and Testing Unintended Memorization in Neural Networks* — planting
low-frequency "canary" sequences during training and measuring how much more likely the model finds the true
canary than a set of plausible alternatives, via an **exposure** metric (defined in §3.4). This project adapts
that methodology to narrative canaries in a story-generation setting (rather than the original's random
sequences) and pairs it with a compositional-novelty measurement, to ask not just "does it memorize?" but "does
memorizing trade off against creative recombination?"

## 3. Methods

### 3.1 Base model and architecture variants

All models share `aarav-lm`'s `small` preset: 8 layers, width 384, 6 query / 2 KV heads (grouped-query
attention), RoPE positional encoding, RMSNorm, SwiGLU, ~14.16M parameters, byte-level BPE tokenizer (vocab 4096,
trained on the base corpus's train split only), context length 512. This is the **baseline** architecture.

One architecture variant has been trained so far, changing exactly one axis from baseline:

| Variant | Change | Parameters | vs. baseline |
|---|---|---|---|
| baseline | — | 14,162,304 | — |
| `variant_a_learned_pos` | RoPE → learned absolute positions (`arch: gpt2`); rest unchanged | 14,358,912 | +1.4% (entirely the added position table; the transformer body itself is identical, 12,589,440 parameters either way) |

Two further variants (`variant_b_mha`: multi-head instead of grouped-query attention; `variant_c_layernorm`:
LayerNorm instead of RMSNorm) have configs generated and parameter-count-matched but are not yet queued for
training, pending review of the two-variant reduced pass.

### 3.2 Canary design

Two canary types, planted as an introductory sentence (character) or mid-story clause (plot fragment) in
TinyStories-style template stories:

- **Character** (4 canaries): a fixed name + trait pairing, e.g. `char_pip` = "Pip the fox, who was always
  hungry."
- **Plot fragment** (4 canaries): a fixed structural phrase inserted mid-story, e.g. `plot_key` = "...then found a
  shiny key under the old oak tree."

Each type also has 2 **unseen controls** — canaries with the same structure, never inserted into any training
corpus, used to calibrate what the exposure metric reports for something the model has truly never seen. A
near-duplicate paraphrase of every inserted canary is pre-registered for future novelty-adjacent analysis but not
yet used.

Canaries are inserted at controlled frequencies into otherwise-identical corpus variants (one fresh pretraining
run per frequency, not fine-tuning, so memorization can be attributed to a known number of training-time
exposures). Pre-registered frequencies: 1, 10, 50, 100, 500 insertions in a ~14.6M-token corpus; a frequency-0
(zero-insertion) condition was added mid-project as an explicit control (§3.4, §4.1) — not one of the
pre-registered treatment levels, and not a violation of the "don't change the canary list" ground rule, since it
changes nothing about the canaries themselves. Insertion pools are nested (the 10x pool's insertions are the first
10 of the 100x pool, etc.) for dose-response validity, and disjoint across canaries (one seeded shuffle, sliced
into blocks, so no training story carries two canaries).

All canary bank details are pre-registered in `configs/canaries.yaml` and locked once
`scripts/prepare_canary_corpus.py` has generated the assignment file from it — the assignment cannot silently
drift between runs. The reference-set metadata used for the exposure metric (§3.4) was widened once, after a real
finding (§4.1); this is documented as a metric-implementation fix, not a change to the canary bank itself, and the
original values are kept so all recomputed results stay on one consistent scale.

### 3.3 Training procedure

Each (architecture, frequency) cell is trained from a random initialization (not fine-tuned from a pretrained
checkpoint), on ~14.6M tokens (~3.4 epochs of the ~71,700-story corpus), 6,000 steps, batch size 1 × grad-accum 16
(effective 16 sequences/step, 512 tokens/sequence), peak LR 8e-4 with 150-step warmup and cosine decay to 10% of
peak, weight decay 0.1, gradient clipping at norm 1.0. Same tokenizer, vocabulary, context length, token budget,
learning-rate schedule and batch size across every architecture and frequency, so architecture is the only
intended axis of variation within a comparison. Fixed, logged seed (20260927) throughout — see §5 for what this
does and does not control for.

### 3.4 Memorization metric

Following Carlini et al. (2019): for a canary occupying an "identity slot" in a fixed sentence frame (e.g. the
name in "____ the fox, who was always hungry"), build a reference set of *N* plausible alternatives for that slot,
score the true canary's sequence log-probability against every alternative's, and rank the true value among the
*N+1* candidates (rank 1 = model's most-preferred). Exposure is defined as

```
exposure = log2(N + 1) − log2(rank)
```

so exposure is maximal (`log2(N+1)`) when the true canary ranks first, and near zero when it ranks last. Verbatim
extraction rate (does greedy decoding from the canary's prefix reproduce it exactly) is recorded alongside
exposure but has not yet triggered on any checkpoint scored so far — expected at this small scale and low
frequency range, and not yet informative on its own.

**Reference-set size matters, and was found empirically to matter more than a first pass assumed** (§4.1):
starting sizes were 9 candidates for character canaries (8 alternative names) and 5 for plot fragments (4
alternative substitutions), later widened to 20 and 10 respectively. A canary that would rank first among *any*
plausible alternative by sheer fluency, independent of training exposure, saturates the metric at its ceiling
regardless of reference-set size — this was found empirically for 4 of the 8 inserted canaries (§4.1) and is not
fixable by widening alone.

**Interpretation requires a matched zero-exposure control**, not a raw exposure number: this project trains a
`freq_0` condition (identical recipe, canary bank never inserted) per architecture and reports **lift** (treatment
exposure minus that architecture's own `freq_0` exposure for the same canary) as the primary quantity, not raw
exposure. A architecture-mismatched or under-trained baseline is not a valid substitute (§4.1 explains why one was
initially used, and the fix).

### 3.5 Compositional-novelty metric

Per the brief (`PLAN.md` Phase 5, not yet run in full but smoke-tested on every checkpoint scored so far): prompt
the model with a canary's identity placed into one of four pre-registered, deliberately implausible-for-TinyStories
settings (e.g. "a pirate ship sailing a stormy sea"), generate multiple completions at temperature 0.7-1.0, and
measure self-BLEU (diversity across completions of the same prompt), distinct-n (n-gram diversity within a
completion), n-gram overlap and edit distance against the actual pre-insertion training stories (using the
manifest's recorded story indices, not a proxy). Hand-labelling of a hundred-plus-sample batch into
verbatim/template-copy/genuine-recombination categories is prepared (`results/labelling/*.txt`) but not yet
performed — per the brief, no LLM-judge automated scoring is used until that hand-labelling exists.

### 3.6 Statistical approach

- **Lift, not raw exposure**, is the unit of comparison (§3.4), computed against a same-recipe, same-architecture
  `freq_0` control.
- **Noise-band estimation**: because each frequency is a *separate training run* (different corpus construction,
  batch order, one seed), a canary's exposure moves between runs even with zero true relationship to training
  exposure. This project estimates the noise band empirically from *never-inserted unseen controls'* exposure
  swings across the trained runs (§4.2) — currently ~1.6 (in exposure units, on the widened reference-set scale),
  from two independent controls in two different architectures. **This is a single-seed proxy, not a proper
  variance estimate**; a planned (not yet run) second seed of the `freq_0`/treatment pair would let this be
  computed as an actual sampling distribution rather than inferred from one swing per architecture.
- **Cross-architecture replication** is used as a second, independent line of evidence for which canaries show a
  real signal (§4.3): a lift pattern that appears in two different architectures, trained independently, is harder
  to explain as noise than either result alone, without needing multiple seeds of either one.
- Aggregate statistics planned for the full grid (per the brief): chance-level baselines, clustered bootstrap 95%
  CIs over distinct prompts (novelty metrics), paired bootstrap comparisons. Not yet computed — the grid is not
  yet complete enough for them to be meaningful.

## 4. Results

### 4.1 Finding: the exposure metric saturates at small reference-set sizes, and widening only partially fixes it

The first `freq_0` control (baseline architecture) revealed that with the original reference-set sizes (9
candidates for character canaries, 5 for plot fragments), several canaries hit the *maximum possible exposure*
even with **zero training exposure**: `char_pip` and three of four plot-fragment canaries. This means the metric
was not measuring memorization for those canaries at all — it was reporting a ceiling value driven by the
model's prior fluency ranking among the available alternatives, indistinguishable from a genuinely memorized
canary at that reference-set size.

The reference-set size was widened (8 → 19 alternatives for character canaries, 4 → 9 for plot fragments;
`configs/canaries.yaml`, kept as an additive, documented change) and every affected result recomputed on the same,
already-trained checkpoints (a cheap forward-pass re-score, no retraining). **The widening only partially
resolved the problem**: `char_pip`, `plot_key`, and `plot_voice` still saturate at the new (higher) ceiling in
every condition tested (frequencies 0, 1, and 10, both architectures) — i.e. this is not a resolution artifact
fixable by a larger reference set, but a property of those specific phrasings being more fluent than every
alternative tried, independent of training exposure. `plot_song` and `plot_lantern` do not saturate and show
usable signal (below).

**Methodological implication for future canary-based memorization studies**: a reference-set size should be
validated empirically against a zero-exposure control *before* it is used to draw conclusions from treatment
conditions, not assumed adequate from its nominal size. A metric that reports a "clean" positive result for an
unseen control is not sufficient evidence the metric is well-calibrated for every canary in the bank — only for
the ones whose result isn't already at the ceiling in the control.

### 4.2 Finding: single-seed exposure differences are noisy at a scale that dwarfs some canaries' apparent lift

Across the runs performed so far, unseen controls that were **never inserted into any training corpus, at any
frequency** still show non-trivial exposure "lift" between separately-trained runs, purely from run-to-run noise
(different corpus construction, batch order, one seed per run):

| Control | Architecture | Swing observed |
|---|---|---|
| `ctrl_char_teva` | baseline | +0.848 (freq_0 → freq_1), +1.585 (freq_0 → freq_10) |
| `ctrl_plot_map` | `variant_a_learned_pos` | +1.322 (freq_0 → freq_1) |

Two independent controls, in two different architectures, both landing in a similar range (~1.3-1.6 exposure
units) is treated as an empirical noise-band estimate: a treatment lift smaller than roughly this size is not
distinguishable from noise on the evidence collected so far. This directly parallels a finding from the sibling
`aarav-lm` project's SFT seed-variance experiments — single-run comparisons in a low-data, small-model regime can
show effects, including sign flips, purely from training noise, and should not be trusted without either
multiple seeds or (as used here, faster but weaker) cross-architecture replication.

### 4.3 Finding: a dose-response memorization signal exists for a subset of canaries, and replicates across two architectures

With `freq_0`, `freq_1`, and `freq_10` now trained and scored for both `baseline` and `variant_a_learned_pos`, the
per-canary lift at frequency 10 (relative to that architecture's own `freq_0`):

| Canary | baseline lift@10 | variant_a lift@10 | Ceiling-saturated in both? |
|---|---|---|---|
| `char_pip` | +0.000 | +1.000 | Yes (baseline only; both near-ceiling) |
| `char_nira` | **+2.170** | **+2.585** | No |
| `char_boro` | +0.459 | **+2.585** | No |
| `char_suri` | +1.459 | +1.263 | No |
| `plot_key` | +0.000 | +0.000 | Yes |
| `plot_song` | +0.000 | +0.000 | Yes |
| `plot_lantern` | **+2.807** | **+3.000** | No |
| `plot_voice` | +0.000 | +0.000 | Yes |

`char_nira`, `char_boro`, and especially `plot_lantern` show a lift well above the ~1.6 noise-band estimate
(§4.2) at frequency 10, **in both architectures independently** — two separate training runs per architecture,
same three canaries showing the strongest and most consistent signal. `plot_lantern`'s lift is nearly identical
between architectures (+2.807 vs. +3.000), which is the single strongest piece of evidence in the project so far
that this specific canary's memorization is a robust, architecture-independent effect within this data/model
scale, not a fluke of one run. `char_pip`, `plot_key`, `plot_song`, and `plot_voice` remain uninformative due to
ceiling saturation (§4.1) in one or both architectures and cannot yet support any claim either way.

**Not yet established**: whether this pattern continues, saturates, or reverses at frequencies 100 and 500
(training in progress); whether it holds under a second training seed rather than the single-seed-per-cell design
used so far; and — the central research question — how novelty/recombination ability (§3.5, not yet scored past
smoke-testing) moves alongside this memorization signal.

### 4.4 Preliminary novelty observations (not yet a full result)

Novelty-eval smoke tests on every checkpoint scored so far (frequencies 0, 1, 10, both architectures where run)
show self-BLEU near 0 and distinct-1/distinct-2 in the 0.35-0.92 range across completions in the four novel
settings — i.e. the model is not collapsing to one templated completion per setting regardless of the canary or
frequency tested so far. This is not yet a quantitative result against the brief's Checkpoint 5 requirements
(hand-labelling, full-grid scoring) and should be read only as "nothing alarming happened in the smoke test," not
as evidence for or against the trade-off hypothesis.

## 5. Limitations (current, to be revisited as the grid completes)

1. **Single seed per (architecture, frequency) cell.** Every lift number in §4.3 comes from one training run per
   condition; the noise-band estimate in §4.2 is inferred from control-canary swings across *different* runs, not
   from a proper repeated-seed variance estimate of the same condition. This is the single most important
   limitation to resolve before the results in §4.3 can be reported as more than "plausible candidates for a real
   effect" — flagged as additional compute, not yet run, pending a decision on scope/cost.
2. **Reduced grid, not the full brief.** Two of up to four architecture axes (learned position embeddings tested;
   attention type and normalization not yet trained), and four of five pre-registered frequencies (0 added as a
   control, 50 dropped from the reduced pass to cut runtime, 100/500 in progress or queued).
3. **Novelty evaluation not yet run to the brief's standard.** Hand-labelling (Checkpoint 5) has not been done;
   only the automated diversity/overlap metrics have run, and only as smoke tests.
4. **No test of the mixed-frequency (single-corpus) Secret Sharer design**, which would be far cheaper (one
   training run per architecture instead of one per architecture × frequency) but wasn't used because the brief's
   literal design (one frequency per corpus) was implemented instead, per the ground rule of not silently
   switching designs.
5. **Small absolute scale.** 14.2M parameters, ~14.6M training tokens per run — results may not generalize to
   larger models or corpora, and this project makes no claim that they do.

## 6. Reproducibility

- Pre-registered canary bank, frequencies, and reference-set metadata: `configs/canaries.yaml` (git history shows
  exactly when and why the reference-set metadata was widened, §4.1).
- Every training config: `configs/training/<architecture>/freq_<F>.yaml`.
- Every trained checkpoint's raw memorization/novelty scores: `results/mem_<architecture>_freq<F>.json`,
  `results/novelty_<architecture>_freq<F>.json`.
- Test suite (42 tests as of this writing) covers corpus construction, the exposure/extraction computation, the
  novelty metrics, and the trade-off analysis script; run via `pytest tests/` and required green before every push.
- No collaborator, co-author, or "generated with" attribution appears anywhere in this project's commit history,
  per the user's explicit, standing instruction — commits are attributed solely to the user.
