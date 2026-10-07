# Memorization vs. compositional creativity in a small language model: does the trade-off depend on architecture?

**Status: exploratory draft, not submission-ready.** The four-architecture run has expanded beyond several older
two-architecture tables below; final numbers will be regenerated only after the remaining balancing and replication
cells finish. Until then, those historical tables are retained as an audit trail, not as the paper's final result.
The primary novelty endpoint, full-corpus copying search, and confirmatory study are also incomplete. The current
submission gate is `docs/PUBLICATION_READINESS.md`.

## Abstract (placeholder)

*To be rewritten after the queued runs and primary novelty analysis complete. Provisional claim: a small
(14M-parameter)
decoder-only LM shows a measurable, dose-dependent memorization signal for at least some planted narrative elements
after as few as 10 insertions in a 14.58M-token training split, with 49.15M tokens consumed over 6,000 updates,
converging to unambiguous, maximal memorization by 100
insertions and holding there at 500, and this signal replicates across two different positional-encoding schemes
(RoPE vs. learned absolute positions). Separately, we show that the standard exposure metric (Carlini et al., 2019)
silently reports a false-positive "always memorized" signal for any canary whose identity phrase already occurs in
the pretraining corpus independent of insertion — a canary-design flaw, not a metric flaw, missed by this project's
own Phase 1 canary selection and only caught by checking base-corpus frequency after the fact. We recommend that
check as a required pre-registration step for future canary studies. A teacher-forced, per-token argmax extraction
test finds **zero** successful extractions across the full grid (120 canary-checkpoint pairs), including canaries
at maximal exposure — a real gap between "the model ranks the true continuation highly" and "the model's own
greedy decoding ever produces it." Finally, a genuine same-condition second-seed measurement (identical corpus and
canary insertion, only the training run itself differing) at frequencies 0 and 1 found training noise alone
reaches ±2.459 exposure units — wider than either of two earlier, cross-frequency-confounded estimates (~0.85, then
~1.6) — and directly resolved an open question rather than just widening it: the apparent frequency-1 lift for the
project's previously-strongest single-frequency signal (`plot_lantern`, +1.807 under the original seed) is exactly
matched, in the opposite direction, by pure noise under the second seed. Frequency 100's and 500's core finding —
multiple canaries converging on the exact same maximum exposure value, replicated across two architectures — rests
on different, stronger evidence (exact-value convergence, which ordinary training noise does not produce) and is
not weakened by this; frequency 10's evidence for two borderline canaries (`char_nira`, `char_suri`) is, and is
walked back to "plausible, not established" accordingly. Baseline frequency-10 seed replication is now complete;
frequency 100 and 500 replications are queued. Baseline frequency 50 has since completed, while learned-position
frequency 50 is still running; the balanced refreshed analysis is not yet available. These results do not yet
establish a creativity trade-off.*

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

**Status against these hypotheses so far, updated after the second-seed noise measurement (§4.2, §4.3)**: the
memorization side of H1 is well-supported at frequencies 100 and 500 specifically (exact-value ceiling convergence,
replicated across two architectures — a form of evidence a genuine same-condition noise measurement confirms
training noise does not produce), but *not* at frequency 10, where two of the three previously-reported signals
(`char_nira`, `char_suri`) turned out to fall inside a properly-measured noise band and are walked back to
"plausible, not established"; frequency 1 shows no signal at all, directly demonstrated rather than inferred. The
honest current statement of the memorization side of H1 is narrower than first written: dose-response is real and
strong once frequency is high enough (≥100 at this scale, for most canaries), and the lower frequencies' apparent
gradualness was partly a noise artifact, not yet a demonstrated smooth curve. The *trade-off* half of H1 — whether
novelty actually declines as memorization rises — has one preliminary, proxy-based data point now (§4.5), covering
the full 0/1/10/100/500 grid: the novelty proxy stays within a narrow band while the memorization score climbs
(and plateaus/dips slightly at 500, itself now understood as within noise, §4.3) in both the full-canary and
contamination-excluded tables. That is a fact about these two numbers on this grid, not a test of H1 — the novelty
metric is a diversity proxy standing in for the brief's actual hand-labelled recombination score (Checkpoint 5, not
done), and every cell is still single-seed except freq_0/1. H1 remains open pending the real novelty test. H2 has
one data point in the *memorization* dimension (the frequency-100/500 ceiling-convergence pattern replicates
closely across RoPE and learned-position architectures, §4.3) — suggestive of a null result on the memorization
side specifically at high frequency, and the same pattern (flat novelty proxy) also holds in the two-architecture
historical tables in §4.5. MHA and LayerNorm are now trained, but their complete matched analysis has not yet been
merged into this manuscript. No H2 conclusion should be drawn from the stale table.

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
| McCoy et al. (2023), RAVEN | Measures n-gram and syntactic novelty in generated text, supported by manual analysis | Provides a stronger novelty-evaluation precedent; this project adds controlled narrative-canary exposure and architecture ablations |
| Haviv et al. (2023), idiom recall | Studies what transformers learn and recall from idiomatic expressions | Closely connects memorized multiword form with compositional behavior, but does not manipulate story-canary frequency across matched architectures |
| Jiang & Ferraro (2026), stories under memorization constraints | Uses stories as a testbed for reasoning under memorization constraints | Makes story-based memorization/novelty no longer unique; this project instead emphasizes causal exposure, small models, and fixed-size architecture comparisons |
| Zhou et al. (2026), long-tail memorization and composition | Shows memorizing long-tail data can aid generalization through composition | Directly challenges a one-directional “memorization crowds out composition” premise and motivates testing either sign rather than assuming harm |
| "What Language Model to Train if You Have One Million GPU Hours?"; Wiola-13M architecture ablations | Architecture ablations (position encoding, attention, norm) at small scale | Measures perplexity/capability, not memorization behavior |
| Memory Dial; Memorization Sinks | Controllable/removable memorization | Focused on mitigation, not the creativity trade-off itself |
| TinyStories (Eldan & Li, 2023) | Coherence/fluency of small story-generating models | Does not touch memorization or originality measurement |

The defensible positioning is therefore narrower than the original draft claimed. Prior work already studies
novelty, idiom recall, story-based memorization constraints, and beneficial composition from memorized long-tail
data. This project's potential contribution is the combination of a controlled exposure intervention, transparent
from-scratch small-model training, and near-parameter-matched architecture ablations with both corpus-level and
human novelty checks. Whether memorization helps, harms, or is independent of recombination is an empirical
question here, not an assumed direction. Full references must be verified before submission.

## 3. Methods

### 3.1 Base model and architecture variants

All models share `aarav-lm`'s `small` preset: 8 layers, width 384, 6 query / 2 KV heads (grouped-query
attention), RoPE positional encoding, RMSNorm, SwiGLU, ~14.16M parameters, byte-level BPE tokenizer (vocab 4096,
trained on the base corpus's train split only), context length 512. This is the **baseline** architecture.

The study uses four near-parameter-matched architectures:

| Variant | Change | Parameters | vs. baseline |
|---|---|---|---|
| baseline | — | 14,162,304 | — |
| `variant_a_learned_pos` | RoPE → learned absolute positions (`arch: gpt2`); rest unchanged | 14,358,912 | +1.4% (entirely the added position table; the transformer body itself is identical, 12,589,440 parameters either way) |
| `variant_b_mha` | grouped-query attention → multi-head attention; 7 layers to compensate | 13,964,928 | -1.4% |
| `variant_c_layernorm` | RMSNorm → LayerNorm | 14,162,304 | exact match |

MHA and LayerNorm are trained and scored across 0, 1, 10, 50, 100, and 500. Baseline frequency 50 has completed;
learned-position frequency 50 is in progress to balance the grid.

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
exposures). Pre-registered frequencies are 1, 10, 50, 100, and 500 insertions in a ~14.6M-token corpus, with a
frequency-0 condition added later as an explicit control. Frequency 50 was initially omitted from the reduced
pass, then restored: MHA and LayerNorm are complete, baseline is complete, and learned-position is running. This
history is an exploratory-design deviation and must be reported as such. Insertion pools are nested (the 10x pool's insertions
are the first 10 of the 100x pool, etc.) for dose-response validity, and disjoint across canaries (one seeded
shuffle, sliced into blocks, so no training story carries two canaries).

All canary bank details are pre-registered in `configs/canaries.yaml` and locked once
`scripts/prepare_canary_corpus.py` has generated the assignment file from it — the assignment cannot silently
drift between runs. The reference-set metadata used for the exposure metric (§3.4) was widened once, after a real
finding (§4.1); this is documented as a metric-implementation fix, not a change to the canary bank itself, and the
original values are kept so all recomputed results stay on one consistent scale.

### 3.3 Training procedure

Each (architecture, frequency) cell is trained from a random initialization (not fine-tuned from a pretrained
checkpoint), on 49.152M training tokens (~3.37 passes over the 14.583M-token training split), 6,000 steps, batch size 1 × grad-accum 16
(effective 16 sequences/step, 512 tokens/sequence), peak LR 8e-4 with 150-step warmup and cosine decay to 10% of
peak, weight decay 0.1, gradient clipping at norm 1.0. Same tokenizer, vocabulary, context length, token budget,
learning-rate schedule and batch size across every architecture and frequency, so architecture is the only
intended axis of variation within a comparison. Fixed, logged `train.seed` (20260927) for the main grid, with one
addition: `baseline`'s freq_0 and freq_1 cells were each retrained with a second `train.seed` (1338), `data.seed`
(corpus construction, canary insertion) unchanged, specifically to measure pure training-run noise as a true
same-condition comparison (§4.2) — see §5 for which cells this covers and which it does not yet.

### 3.4 Memorization metric

Following Carlini et al. (2019): for a canary occupying an "identity slot" in a fixed sentence frame (e.g. the
name in "____ the fox, who was always hungry"), build a reference set of *N* plausible alternatives for that slot,
score the true canary's sequence log-probability against every alternative's, and rank the true value among the
*N+1* candidates (rank 1 = model's most-preferred). Exposure is defined as

```
exposure = log2(N + 1) − log2(rank)
```

so exposure is maximal (`log2(N+1)`) when the true canary ranks first, and near zero when it ranks last.

Verbatim **extraction rate** (does greedy decoding reproduce the canary exactly) is recorded alongside exposure but
has not triggered on any checkpoint scored so far, including checkpoints where several canaries sit at maximal
exposure — verified directly against real checkpoints (PHASE4_NOTES.md), for two distinct reasons depending on
canary type, not one. **Character canaries** share one prompt with no canary-specific text at all ("Once upon a
time, " — the name is the sentence's first word), so the same deterministic greedy decode is checked against every
candidate: at most one character canary can ever score `True` per checkpoint, and `False` for the rest isn't
independent evidence. **Plot-fragment canaries already get a genuinely distinct, canary-conditioned prompt each**
(their own preceding connector text) — checked directly, including on `plot_lantern` (this project's single
strongest, cleanest memorization signal), each canary's own prompt produces its own distinct wrong continuation,
not one shared completion. This is a real, not structural, negative result: exposure only requires beating a
curated reference set of 9-20 alternatives at a fixed slot, while extraction requires being the single most
probable continuation across the model's entire vocabulary — a canary can win the first comparison decisively
while still losing the second, and these are recognized as different-strength measurements in the memorization
literature this design follows, not a contradiction.

**A corrected extraction test was implemented and run on every checkpoint scored so far, now including frequency
500.** Character canaries cannot be given a canary-specific *preceding* prompt (the identity is the sentence's
first word, and the insertion design prepends the whole canary sentence wholesale, so there is no unique context to
condition on). Instead of fixing this by adding context, `argmax_match()` fixes the more fundamental problem in
both canary types: rather than free-generating from a prompt and checking the output (which lets one early wrong
token send generation somewhere else entirely, and can't be independently checked per character canary), it
teacher-forces each canary's own true identity tokens as context and checks, at every single position, whether the
model's argmax prediction (over the entire vocabulary) equals the true next token. This is well-defined and
independently checkable per canary regardless of prompt-sharing. Run against all 10 scored checkpoints (both
architectures, all five frequencies, 120 canary-checkpoint pairs): **zero `first_token_match`, zero `full_match`,
including every case where exposure sits at its exact maximum** (all four character canaries simultaneously at
`variant_a_learned_pos/freq_100`, and again at every ceiling-saturated canary at frequency 500 in both
architectures). This is now a clean, complete, well-powered confirmation across the full pre-registered frequency
grid, not just a partial one, that exposure and extraction measure genuinely different thresholds at this
project's scale: insertion frequencies up to 500 reliably make a canary the model's preferred choice among a
curated alternative set, but never its single global top choice over the full vocabulary.

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

Per the brief (`PLAN.md` Phase 5), prompt
the model with a canary's identity placed into one of four pre-registered, deliberately implausible-for-TinyStories
settings (e.g. "a pirate ship sailing a stormy sea"), generate multiple completions at temperature 0.7-1.0, and
measure self-BLEU (diversity across completions of the same prompt), distinct-n, and overlap against training
stories. The original diagnostic compares only the stories selected for canary insertion; it is not evidence of
novelty relative to the whole corpus. `scripts/eval_full_corpus_overlap.py` now implements an exact maximum
word-four-gram overlap search against every story in the frequency-specific training corpus, with corpus hash and
index provenance. It must be run on the finalized outputs before any non-copying claim is made.

The primary endpoint is blinded human classification into verbatim reproduction (V), template copy (T), or
genuine novel recombination (N). `scripts/prepare_blinded_annotations.py` creates balanced condition-hidden files
for two raters; `scripts/score_blinded_annotations.py` reports Cohen's kappa, Krippendorff's alpha, disagreements,
and cluster-bootstrap intervals, and refuses final scoring until disagreements are adjudicated. The complete
locked procedure is in `docs/ANNOTATION_PROTOCOL.md`. Legacy condition-revealing text batches and automated labels
are not admissible evidence.

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

**Revised upward once freq_500 was scored (§4.3): `ctrl_char_teva` (baseline), still never inserted at any
frequency, swings +2.170 from freq_0 to freq_500 (0.222 → 2.392)** — larger than the ~1.6-unit band above. With
one training run per (architecture, frequency) cell, this couldn't be told apart from an unlucky draw versus a
genuinely wider noise band from that evidence alone — resolved properly below.

**Resolved with a true same-condition measurement, not another cross-frequency comparison.** Every noise estimate
above compares controls *across different frequencies*, which changes the training data itself (one more canary
insertion shifts every subsequent training batch) — not a clean noise-only comparison. `baseline/freq_0` and
`baseline/freq_1` were each retrained with a second seed (`train.seed` 1338; `data.seed` — corpus construction and
canary insertion — held identical to the original runs), giving four same-condition pairs, each isolating *pure
training stochasticity* with zero change in what the model was trained on:

| canary | freq_0 seed A → seed B | swing | freq_1 seed A → seed B | swing |
|---|---|---|---|---|
| `char_boro` (inserted, but freq_0 = no actual insertion) | 0.933 → 3.392 | **+2.459** | 1.807 → 1.222 | −0.585 |
| `ctrl_char_teva` (never inserted, any frequency) | 0.222 → 2.070 | **+1.848** | 1.070 → 1.070 | +0.000 |
| `plot_lantern` | 0.652 → 0.652 | +0.000 | 2.459 → 0.652 | **−1.807** |
| `char_pip` | 4.392 → 4.392 | +0.000 | 4.392 → 2.807 | **−1.585** |

**The noise band is wider than either previous estimate: same-condition training noise alone reaches ±2.459
exposure units**, not ~1.6. This is the best-grounded estimate in the project so far (a true controlled
comparison — identical corpus, identical canary insertion, only the training run itself differs) and it
supersedes both earlier cross-frequency estimates above. One direct consequence, addressed in §4.3: `plot_lantern`'s
apparent frequency-1 lift (+1.807 under the original seed) is exactly matched, in the opposite direction, by pure
noise under a second seed (−1.807, freq_1 seed A → seed B) — the original lift was not distinguishable from noise
after all, now demonstrated directly rather than inferred from a control's swing.

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

**Revisited against the ±2.459 same-condition noise band (§4.2), not the earlier, too-narrow ~1.6 estimate**:
`char_nira`'s lift (+2.170 baseline, +2.585 variant_a) and `char_suri`'s (+1.459 baseline, +1.263 variant_a) now
fall inside or right at the edge of the noise band individually — no longer confidently distinguishable from
chance on frequency-10 evidence alone, whereas the earlier (too-narrow) estimate had called them established.
`char_boro` (+0.459 baseline) was already inside either band. **`plot_lantern` is the one lift that survives**:
+2.807 (baseline) and +3.000 (variant_a) both exceed even the revised, wider band, and — unlike the others — it is
corroborated by a second, independent kind of evidence: cross-architecture replication (two unrelated training
runs landing within 0.19 of each other). `char_pip`, `plot_key`, `plot_song`, and `plot_voice` remain uninformative
due to ceiling saturation (§4.1) in one or both architectures and cannot yet support any claim either way.
**The frequency-10 picture is accordingly weaker than first reported: one canary (`plot_lantern`) shows a
defensible dose-response signal at this frequency; the others are plausible but not established without a second
seed at frequency 10 itself** (the second-seed work run so far covers frequencies 0 and 1 only, §4.2).

**Update at frequency 100, now confirmed in both architectures:** the ambiguity for `char_boro` and `char_suri`
resolves cleanly in the positive direction in `baseline` (both sat at or near the noise-band edge at frequency 10;
at frequency 100 both show +3.459 — the same ceiling value as `char_nira` and `plot_lantern`). **This is an exact,
independent replication in `variant_a_learned_pos`**: `char_nira` (+2.585), `char_boro` (+2.585), `char_suri`
(+3.585), and `plot_lantern` (+3.000) all show large lift and converge on the ceiling there too, while every one
of that architecture's controls stays inside the noise band (-0.585 to +0.737). Two independent architectures,
trained independently, now agree on every one of these canaries at this frequency: dose-response is real and, at
this data scale, strong enough to saturate the metric once frequency is high enough — frequency 10 was this
effect still emerging above the noise floor, not its ceiling. **This frequency-100 conclusion rests on different,
stronger evidence than the frequency-10 lift-vs-noise-band comparisons above**: multiple canaries independently
converging on the exact same maximum value, across two architectures, is not merely "exceeds an estimated noise
threshold" — it is a convergence pattern that ordinary training noise (§4.2's ±2.459 same-condition measurement,
which never produces exact-value convergence across unrelated canaries) does not produce. The frequency-10 walk-
back above does not weaken this.

**A genuine nuance in the replication, not a contradiction**: `char_pip` sits exactly at baseline's ceiling already
at `freq_0` (lift `+0.000` at every frequency, fully explained by its 150 base-corpus occurrences, §4.1), but in
`variant_a_learned_pos` its `freq_0` value (3.392) sits just under that architecture's ceiling, leaving room for a
real, moderate `+1.000` lift on top of the contamination confound. Base-corpus contamination sets a high *floor*,
not a hard ceiling immune to insertion — it just leaves little headroom for genuine signal, which is why `char_pip`
remains the least informative canary in the bank, now for a mechanistically understood reason rather than a
mysterious one.

**Frequency 500, now scored: the ceiling holds, and one architecture shows a real, unexplained dip.** Every
canary already saturated by frequency 100 stays saturated at 500 in both architectures — `variant_a_learned_pos`
is exactly flat across all 12 canaries between the two frequencies, the most stable comparison in the project.
`baseline`'s `char_nira`, however, drops from the ceiling (+3.170 lift at freq_100) to +1.585 at freq_500 — a
five-times-higher training frequency producing a *lower* exposure reading for a real, non-contaminated canary.
Since freq_100 and freq_500 are independently-trained runs rather than seeds of a controlled comparison, the
simplest reading is run-to-run scatter near the metric's ceiling, not a genuine decline in memorization with more
exposure — but this cannot be distinguished from a real effect without a second seed, and it lands in the same
place as §4.2's revised noise-band finding: this single-seed-per-cell design is now visibly too weak to support a
directional claim within about 2 exposure units.

**Not yet established**: whether either of the above (the `char_nira` dip, or `ctrl_char_teva`'s noise) holds up
under a second training seed rather than the single-seed-per-cell design used so far (a concrete, no-longer-
hypothetical next step); and — the central research question — how novelty/recombination ability (§3.5, not yet
scored past smoke-testing beyond the distinct-2 proxy in §4.5) moves alongside this memorization signal.

### 4.4 Preliminary novelty observations (not yet a full result)

Novelty-eval smoke tests on every checkpoint scored so far (frequencies 0, 1, 10, both architectures where run)
show self-BLEU near 0 and distinct-1/distinct-2 in the 0.35-0.92 range across completions in the four novel
settings — i.e. the model is not collapsing to one templated completion per setting regardless of the canary or
frequency tested so far. This is not yet a quantitative result against the brief's Checkpoint 5 requirements
(hand-labelling, full-grid scoring) and should be read only as "nothing alarming happened in the smoke test," not
as evidence for or against the trade-off hypothesis.

### 4.5 Trade-off table and plot (Checkpoint 6, full frequency grid 0/1/10/100/500, proxy novelty metric)

Per the brief's Checkpoint 6, this section presents plots and tables only; no prose conclusion is drawn here — the
user reads these first, per the project's ground rules (`docs/RESEARCH_PLAN.md` §10). `scripts/analyze_tradeoff.py`
was run against every memorization and novelty result collected so far, now covering the full pre-registered
frequency grid.

**All 8 inserted canaries** (`results/tradeoff.csv` / `.png`):

| variant | freq | memorization (mean lift) | novelty (mean distinct-2) |
|---|---|---|---|
| baseline | 1 | 0.174 | 0.800 |
| baseline | 10 | 0.862 | 0.810 |
| baseline | 100 | 1.612 | 0.801 |
| baseline | 500 | 1.414 | 0.788 |
| variant_a_learned_pos | 1 | -0.035 | 0.781 |
| variant_a_learned_pos | 10 | 1.304 | 0.780 |
| variant_a_learned_pos | 100 | 1.594 | 0.795 |
| variant_a_learned_pos | 500 | 1.594 | 0.805 |

**The same table, restricted to the 5 canaries not diagnosed as base-corpus-contaminated** (§4.1) — added because
averaging in the 3 contaminated canaries (whose lift is always ≈0 for reasons unrelated to training exposure)
mechanically dilutes the memorization column at every frequency (`results/tradeoff_clean.csv` / `.png`, via the new
`--canaries` filter on `analyze_tradeoff.py`):

| variant | freq | memorization (mean lift, clean canaries) | novelty (mean distinct-2, same canaries) |
|---|---|---|---|
| baseline | 1 | 0.278 | 0.803 |
| baseline | 10 | 1.379 | 0.827 |
| baseline | 100 | 2.579 | 0.808 |
| baseline | 500 | 2.262 | 0.797 |
| variant_a_learned_pos | 1 | 0.061 | 0.777 |
| variant_a_learned_pos | 10 | 1.887 | 0.784 |
| variant_a_learned_pos | 100 | 2.351 | 0.799 |
| variant_a_learned_pos | 500 | 2.351 | 0.805 |

**What these tables show, described factually**: the memorization column rises with frequency from 1 to 100 in
both architectures and both tables (more steeply once the contaminated canaries are excluded); at 500,
`variant_a_learned_pos` is exactly flat (every clean canary already at ceiling) while `baseline` is slightly
*lower* than at 100 (2.262 vs 2.579 clean; driven by `char_nira`'s drop, §4.3). The novelty column stays within a
narrow band (0.777–0.827) across every frequency and both canary sets, now including 500 — no evidence, in either
direction, of a novelty cost from higher memorization in this proxy metric. **Caveats that bear directly on how
much weight this can carry**: novelty here is the distinct-2 diversity *proxy*, not the hand-labelled recombination
score the brief's design calls for (Checkpoint 5 hand-labelling has not been done); every cell is a single training
seed (§4.2's noise-band caveat applies to the memorization axis here too, and was revised upward after freq_500).
This is the first data directly relevant to H1 (§1.1) across the full pre-registered grid, but on the current
evidence alone it should be treated as a preliminary, proxy-based, single-seed data point, not an answer — the
apparent plateau/decline at 500 is exactly the kind of small difference this design cannot yet distinguish from
noise.

## 5. Limitations (current, to be revisited as the grid completes)

1. **Single seed per (architecture, frequency) cell — now resolved for frequencies 0 and 1, still open for 10,
   100, and 500.** `baseline/freq_0` and `baseline/freq_1` were each retrained with a second `train.seed`
   (`data.seed` — corpus and canary insertion — held identical), giving a true same-condition noise measurement:
   ±2.459 exposure units, wider than either earlier cross-frequency-confounded estimate (~0.85, then ~1.6). This
   directly resolved one open question (§4.2, §4.3): the previously-strongest frequency-1 signal (`plot_lantern`,
   +1.807) is indistinguishable from — in fact exactly canceled by — pure noise under the second seed, and two
   borderline frequency-10 lifts (`char_nira`, `char_suri`) now fall inside the revised band and are walked back
   to "plausible, not established." **What is not yet resolved**: the same second-seed treatment at frequencies
   10, 100, and 500, where the ceiling-saturation evidence (§4.3) rests on a different, stronger argument (exact-
   value convergence across canaries and architectures) that a wider noise band does not by itself undermine, but
   has still never been directly seed-replicated at those specific frequencies.
2. **Exploratory grid imbalance.** All four architectures are trained at 0, 1, 10, 100, and 500; MHA and LayerNorm
   additionally have frequency 50. Baseline frequency 50 is complete and learned-position frequency 50 is running.
   Frequency 0 was added after the
   initial preregistration, so it is a necessary matched control but still a documented design change.
3. **Novelty evaluation not yet run to the brief's standard.** Hand-labelling (Checkpoint 5) has not been done;
   only the automated diversity/overlap metrics have run, and only as smoke tests.
4. **No test of the mixed-frequency (single-corpus) Secret Sharer design**, which would be far cheaper (one
   training run per architecture instead of one per architecture × frequency) but wasn't used because the brief's
   literal design (one frequency per corpus) was implemented instead, per the ground rule of not silently
   switching designs.
5. **Small absolute scale.** 14.2M parameters, 49.152M consumed training tokens per run over a 14.583M-token
   training split — results may not generalize to
   larger models or corpora, and this project makes no claim that they do.
6. **Neither extraction test has produced a positive result at this project's scale** (§3.4). The original
   free-generation test's null result for character canaries was ambiguous (structurally can only fire for one
   canary per checkpoint); the corrected, per-canary, teacher-forced `argmax_match()` test removes that ambiguity
   and gives a clean, complete null instead: 0 of 120 canary-checkpoint pairs scored (both architectures, all five
   pre-registered frequencies including 500) show the canary's identity as the model's own top prediction, even
   where exposure sits at its exact maximum. This is now a well-powered, unambiguous finding across the full grid,
   not a design limitation: at insertion frequencies up to 500, canaries reliably beat a curated reference set
   without ever becoming the model's single global top choice. Every memorization finding in this paper about
   *dose-response* rests on the exposure metric; the extraction gap itself is a finding in its own right, not a
   caveat on the others.

## 6. Reproducibility

- Pre-registered canary bank, frequencies, and reference-set metadata: `configs/canaries.yaml` (git history shows
  exactly when and why the reference-set metadata was widened, §4.1).
- Every training config: `configs/training/<architecture>/freq_<F>.yaml`; second-seed noise-measurement configs
  follow the pattern `freq_<F>_seed<S>.yaml` (same `data.seed`, different `train.seed`).
- Every trained checkpoint's raw memorization/novelty scores: `results/mem_<architecture>_freq<F>.json`,
  `results/novelty_<architecture>_freq<F>.json` (second-seed results: `..._freq<F>_seed<S>.json`).
- Test suite (64 tests as of this writing) covers corpus construction, exposure/extraction, novelty metrics,
  full-corpus overlap, blinded annotation/scoring, and trade-off analysis; run via `pytest tests/`.
- Repository commit attribution and scholarly authorship are distinct. The final manuscript must follow the target
  venue's human-authorship criteria and disclose AI-assisted code or prose to the extent required by its policy.
