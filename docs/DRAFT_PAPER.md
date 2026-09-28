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
signal for at least some planted narrative elements after as few as 10 insertions in ~14.6M training tokens,
converging to unambiguous, maximal memorization by 100 insertions, and this signal replicates across two
different positional-encoding schemes (RoPE vs. learned absolute positions). Separately, we show that the standard
exposure metric (Carlini et al., 2019) silently reports a false-positive "always memorized" signal for any canary
whose identity phrase already occurs in the pretraining corpus independent of insertion — a canary-design flaw,
not a metric flaw, missed by this project's own Phase 1 canary selection and only caught by checking base-corpus
frequency after the fact. We recommend that check as a required pre-registration step for future canary studies.*

## 1. Research question

Does a small (14.2M-parameter) decoder-only transformer, trained on a TinyStories-style corpus, trade off
memorizing recurring narrative elements (character names, plot fragments) against the ability to recombine those
elements into novel stories as exposure frequency increases — and does that trade-off differ by architecture
(positional encoding, attention type, normalization)? (Verbatim research question, `PLAN.md`.)

This reframes memorization from a **privacy problem** — the dominant framing in the existing literature (Carlini
et al.'s membership-inference and extraction work, differential-privacy mitigation) — into a **creativity-capacity
trade-off** in generative models: not "can training data be extracted," but "does the capacity a model spends on
verbatim recall come at the expense of capacity for novel recombination." Applying that reframing to a small,
from-scratch narrative model is this project's core novelty claim (full framing in `docs/RESEARCH_PLAN.md`).

### 1.1 Hypotheses

- **H1 (primary):** Memorization and compositional novelty are not independent. Beyond some exposure threshold,
  increasing repetition of a narrative element reduces the model's tendency to recombine it in new ways — it
  shifts from *composing* to *reproducing*.
- **H2 (secondary):** The location/shape of this trade-off curve depends on architecture. Models with different
  capacity for long-range structure (RoPE vs. learned position encoding; GQA vs. MHA) may resist
  memorization-driven crowding-out differently.

H2 coming back null is still a valid, publishable result: it would mean the trade-off is a function of
data/exposure rather than architecture at this scale — itself informative, and framable as a boundary condition
against the small-model architecture-ablation literature (§2).

**Status against these hypotheses so far**: the memorization side of H1 is well-supported by §4.3's dose-response
results (large, replicated, converges to saturation by frequency 100). The *trade-off* half of H1 — whether
novelty actually declines as memorization rises — has one preliminary, proxy-based data point now (§4.5): across
frequencies 1/10/100 in both architectures, the novelty proxy stays within a narrow band while the memorization
score climbs steeply, in both the full-canary and contamination-excluded tables. That is a fact about these two
numbers on this partial grid, not a test of H1 — the novelty metric is a diversity proxy standing in for the
brief's actual hand-labelled recombination score (Checkpoint 5, not done), one seed per cell, and frequency 500 is
missing. H1 remains open pending that real test. H2 has one data point in the *memorization* dimension (the
dose-response signal replicates closely across RoPE and learned-position architectures at frequencies 10 and 100,
§4.3) — suggestive of a null result on the memorization side specifically, and the same pattern (flat novelty
proxy) also holds in both architectures in §4.5's tables — but the novelty side of H2 has the same proxy-metric
caveat as H1, and multi-head attention (the second architecture axis in the hypothesis) hasn't been trained at
all yet.

## 2. Related work

The memorization side of this design follows the "Secret Sharer" methodology of Carlini, Liu, Erlingsson, Kos &
Song (2019), *The Secret Sharer: Evaluating and Testing Unintended Memorization in Neural Networks* — planting
low-frequency "canary" sequences during training and measuring how much more likely the model finds the true
canary than a set of plausible alternatives, via an **exposure** metric (defined in §3.4). This project adapts
that methodology to narrative canaries in a story-generation setting (rather than the original's random
sequences) and pairs it with a compositional-novelty measurement, to ask not just "does it memorize?" but "does
memorizing trade off against creative recombination?"

| Prior work | What it does | Gap this project fills |
|---|---|---|
| Carlini et al. (2019, "Secret Sharer"), Carlini et al. (2020, extraction) | Canary insertion, exposure metric, model-size vs. memorization | Uses generic/random canaries, not structured narrative elements; treats memorization only as a privacy risk |
| Tirumala et al., Carlini et al. (2022/2023) | Memorization scales with model size | Varies *size*, not *architecture at fixed size* (this project's axis) |
| Zhang et al. (2023), counterfactual memorization | Shows models generalize on familiar surface forms but fail under perturbation | Closest prior work conceptually — this project differs by explicitly measuring *compositional recombination*, not just perturbation robustness |
| "What Language Model to Train if You Have One Million GPU Hours?"; Wiola-13M architecture ablations | Architecture ablations (position encoding, attention, norm) at small scale | Measures perplexity/capability, not memorization behavior |
| Memory Dial; Memorization Sinks | Controllable/removable memorization | Focused on mitigation, not the creativity trade-off itself |
| TinyStories (Eldan & Li, 2023) | Coherence/fluency of small story-generating models | Does not touch memorization or originality measurement |

**No existing work crosses the architecture-ablation literature with the memorization literature, and no existing
memorization study uses a creative-generation setting where "crowding out novelty" is the outcome of interest
rather than privacy leakage.** That combination is this project's positioning. (Full citation list and a risks/
mitigations table that anticipated, among other things, the canary-contamination issue actually found in §4.1:
`docs/RESEARCH_PLAN.md`.)

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

so exposure is maximal (`log2(N+1)`) when the true canary ranks first, and near zero when it ranks last.

Verbatim **extraction rate** (does greedy decoding reproduce the canary exactly) is recorded alongside exposure
but has not triggered on any checkpoint scored so far, including checkpoints where several canaries sit at maximal
exposure — verified, not assumed, to be a property of the test's design rather than a code defect (checked
directly against a real checkpoint's actual greedy output; PHASE4_NOTES.md). As implemented, extraction
greedy-decodes from one prompt shared by every canary of a type (e.g. "Once upon a time, " for every character
canary) and checks whether that single, deterministic continuation happens to reproduce a given canary's identity.
This makes the true identity compete against *every* pattern the model has learned from the entire base corpus for
the single most-probable continuation — a far higher bar than exposure's controlled comparison against a curated
reference set — and means at most one canary per type can ever score `True` per checkpoint, since the same
deterministic decode is checked against every candidate of that type. At this project's insertion frequencies
(1-500, into a corpus of ~1.47M documents), this specific extraction design is not expected to fire even when
exposure shows strong relative memorization; a canary-conditioned extraction test (decode from each canary's own
established context rather than a generic shared prompt) would be a more sensitive, more directly comparable
per-canary measure, and is designed but not yet implemented (§5).

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

### 4.1 Finding: three canaries were never actually novel to the base corpus — a canary-design flaw, not a metric flaw

The first `freq_0` control (baseline architecture) revealed that with the original reference-set sizes (9
candidates for character canaries, 5 for plot fragments), several canaries hit the *maximum possible exposure*
even with **zero training exposure**: `char_pip` and three of four plot-fragment canaries. The reference-set size
was widened (8 → 19 alternatives for character canaries, 4 → 9 for plot fragments; `configs/canaries.yaml`) and
every affected result recomputed on the same, already-trained checkpoints. **The widening only partially resolved
the problem**: `char_pip`, `plot_key`, and `plot_voice` still saturate at the new (higher) ceiling in every
condition tested (frequencies 0, 1, 10, and 100, both architectures where run).

**The mechanism turns out to be checkable directly against the pretraining corpus, with no retraining needed, and
it fully explains the pattern**: the three permanently-saturated canaries are exactly the three whose identity
phrase already occurs substantially in the base corpus, independent of any canary insertion —

| Canary | Identity phrase | Occurrences in the base corpus | Ceiling-saturated in every condition? |
|---|---|---|---|
| `char_pip` | "Pip" | 150 | Yes |
| `plot_key` | "a shiny key" | 41 | Yes |
| `plot_voice` | "a soft voice" | 67 | Yes |
| every other inserted canary | — | 0 | No — real, controllable dose-response |

"Pip" is a name TinyStories already uses 150 times; "a shiny key" and "a soft voice" are phrases it already uses
dozens of times. A model trained on this corpus assigns these high probability *before any canary is ever
inserted*, simply from ordinary pretraining — no reference-set size was ever going to change that, because
widening the pool doesn't change how familiar the true phrase already was. Every canary with zero base-corpus
occurrences of its identity phrase shows genuine, growing dose-response instead (§4.3); the two unseen-control
types (`Olen`, `Teva`) also have zero occurrences and behave exactly as zero-exposure canaries should. This is a
clean, confirmed necessary condition, checked on all 8 inserted canaries, both control types, and every
reference-pool alternative.

**Methodological implication for canary-based memorization studies, general beyond this project**: a canary's
"novelty" needs to be verified against the actual pretraining corpus before it is locked into the design, not
assumed from the name or phrase sounding unusual. This project's own alternative-name pool, checked after the
fact, turned up four more names (`Mira`, `Zeb`, `Dara`, `Nell`) with 12-76 base-corpus occurrences that happened
not to be selected as true canary identities — avoiding the same problem by luck, not by design. **A base-corpus
frequency check on every candidate canary identity and every reference-set alternative should be a required
pre-registration step**, run before Phase 1 is locked, not a diagnostic performed three phases later after a
result looks confusing. It takes seconds to run and would have caught this project's version of the problem
immediately.

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

**Update at frequency 100, now confirmed in both architectures:** the ambiguity for `char_boro` and `char_suri`
resolves cleanly in the positive direction in `baseline` (both sat at or near the noise-band edge at frequency 10;
at frequency 100 both show +3.459 — the same ceiling value as `char_nira` and `plot_lantern`). **This is an exact,
independent replication in `variant_a_learned_pos`**: `char_nira` (+2.585), `char_boro` (+2.585), `char_suri`
(+3.585), and `plot_lantern` (+3.000) all show large lift and converge on the ceiling there too, while every one
of that architecture's controls stays inside the noise band (-0.585 to +0.737). Two independent architectures,
trained independently, now agree on every one of these canaries at this frequency: dose-response is real and, at
this data scale, strong enough to saturate the metric once frequency is high enough — frequency 10 was this
effect still emerging above the noise floor, not its ceiling.

**A genuine nuance in the replication, not a contradiction**: `char_pip` sits exactly at baseline's ceiling already
at `freq_0` (lift `+0.000` at every frequency, fully explained by its 150 base-corpus occurrences, §4.1), but in
`variant_a_learned_pos` its `freq_0` value (3.392) sits just under that architecture's ceiling, leaving room for a
real, moderate `+1.000` lift on top of the contamination confound. Base-corpus contamination sets a high *floor*,
not a hard ceiling immune to insertion — it just leaves little headroom for genuine signal, which is why `char_pip`
remains the least informative canary in the bank, now for a mechanistically understood reason rather than a
mysterious one.

**Not yet established**: whether the pattern holds, saturates further, or does anything unexpected at frequency
500 (queued for both architectures); whether it holds under a second training seed rather than the
single-seed-per-cell design used so far; and — the central research question — how novelty/recombination ability
(§3.5, not yet scored past smoke-testing) moves alongside this memorization signal. This last gap is now the
largest one standing between the current results and an answer to H1.

### 4.4 Preliminary novelty observations (not yet a full result)

Novelty-eval smoke tests on every checkpoint scored so far (frequencies 0, 1, 10, both architectures where run)
show self-BLEU near 0 and distinct-1/distinct-2 in the 0.35-0.92 range across completions in the four novel
settings — i.e. the model is not collapsing to one templated completion per setting regardless of the canary or
frequency tested so far. This is not yet a quantitative result against the brief's Checkpoint 5 requirements
(hand-labelling, full-grid scoring) and should be read only as "nothing alarming happened in the smoke test," not
as evidence for or against the trade-off hypothesis.

### 4.5 Trade-off table and plot (Checkpoint 6, partial — frequencies 0/1/10/100, proxy novelty metric)

Per the brief's Checkpoint 6, this section presents plots and tables only; no prose conclusion is drawn here — the
user reads these first, per the project's ground rules (`docs/RESEARCH_PLAN.md` §10). `scripts/analyze_tradeoff.py`
was run against every memorization and novelty result collected so far.

**All 8 inserted canaries** (`results/tradeoff.csv` / `.png`):

| variant | freq | memorization (mean lift) | novelty (mean distinct-2) |
|---|---|---|---|
| baseline | 1 | 0.174 | 0.800 |
| baseline | 10 | 0.862 | 0.810 |
| baseline | 100 | 1.612 | 0.801 |
| variant_a_learned_pos | 1 | -0.035 | 0.781 |
| variant_a_learned_pos | 10 | 1.304 | 0.780 |
| variant_a_learned_pos | 100 | 1.594 | 0.795 |

**The same table, restricted to the 5 canaries not diagnosed as base-corpus-contaminated** (§4.1) — added because
averaging in the 3 contaminated canaries (whose lift is always ≈0 for reasons unrelated to training exposure)
mechanically dilutes the memorization column at every frequency (`results/tradeoff_clean.csv` / `.png`, via the new
`--canaries` filter on `analyze_tradeoff.py`):

| variant | freq | memorization (mean lift, clean canaries) | novelty (mean distinct-2, same canaries) |
|---|---|---|---|
| baseline | 1 | 0.278 | 0.803 |
| baseline | 10 | 1.379 | 0.827 |
| baseline | 100 | 2.579 | 0.808 |
| variant_a_learned_pos | 1 | 0.061 | 0.777 |
| variant_a_learned_pos | 10 | 1.887 | 0.784 |
| variant_a_learned_pos | 100 | 2.351 | 0.799 |

**What these tables show, described factually**: the memorization column rises with frequency in both
architectures in both tables (more steeply once the contaminated canaries are excluded); the novelty column stays
within a narrow band (0.777–0.827) across every frequency and both canary sets. **Caveats that bear directly on
how much weight this can carry**: novelty here is the distinct-2 diversity *proxy*, not the hand-labelled
recombination score the brief's design calls for (Checkpoint 5 hand-labelling has not been done); frequency 500 is
missing from both tables; and every cell is a single training seed (§4.2's noise-band caveat applies to the
memorization axis here too). This is the first data directly relevant to H1 (§1.1), but on the current evidence
alone it should be treated as a preliminary, proxy-based data point, not an answer.

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
6. **Extraction rate, as implemented, is not sensitive at this project's scale** (§3.4): it tests whether a
   canary's identity is the model's single most-probable continuation from a generic, shared prompt, a far higher
   bar than exposure's controlled comparison, and structurally can only fire for one canary per type per
   checkpoint. Verified directly against a real checkpoint (PHASE4_NOTES.md), not assumed. Every finding in this
   paper about memorization rests on the exposure metric alone; extraction rate has not contributed usable signal
   and a better-matched, canary-conditioned redesign is described but not implemented.

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
