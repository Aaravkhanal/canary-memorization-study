# Research Plan: Memorization vs. Compositional Creativity Trade-off in a Small Narrative-Generation LLM

**Status:** Working plan — pasted by the user, 2026-09-28, as a fuller, publication-oriented elaboration of the
brief in `../PLAN.md` (kept verbatim there for the same reason: so a later session can't drift from what was
agreed). This file is kept verbatim too. Where the two differ only in level of detail (canary design, frequencies,
metrics), they agree; this file adds material not in `PLAN.md` — explicit hypotheses, related-work positioning,
a draft paper structure, and a risks/mitigations table — which is why it's kept as its own file rather than
merged into the original.

**Model:** 14.2M-parameter LLM (existing, story-generation)
**Last updated:** 2026-09-27

---

## 1. Research Question

As a small language model memorizes recurring narrative elements (character names, openings, story templates), does this measurably crowd out its ability to compose novel combinations — and does this trade-off depend on architecture?

This reframes memorization from a **privacy problem** (the dominant framing in existing literature — Carlini et al., membership inference, DP mitigation) to a **creativity-capacity trade-off** in generative models. This reframing, applied to a small from-scratch narrative model, is the paper's core novelty claim.

---

## 2. Hypotheses

- **H1 (primary):** Memorization and compositional novelty are not independent. Beyond some exposure threshold, increasing repetition of a narrative element reduces the model's tendency to recombine it in new ways — it shifts from *composing* to *reproducing*.
- **H2 (secondary):** The location/shape of this trade-off curve depends on architecture. Models with different capacity for long-range structure (e.g., RoPE vs. learned position encoding; GQA vs. MHA) may resist memorization-driven crowding-out differently.

Note: H2 coming back null is still a valid, publishable result — it would mean the trade-off is a function of data/exposure rather than architecture at this scale, which is itself informative and can be framed against the small-model architecture literature (Wiola-13M, "million GPU hours" paper).

---

## 3. Positioning Against Existing Work

| Prior work | What it does | Gap this project fills |
|---|---|---|
| Carlini et al. (2019, "Secret Sharer"), Carlini et al. (2020, extraction) | Canary insertion, exposure metric, model-size vs. memorization | Uses generic/random canaries, not structured narrative elements; treats memorization only as a privacy risk |
| Tirumala et al., Carlini et al. (2022/2023) | Memorization scales with model size | Varies *size*, not *architecture at fixed size* |
| Zhang et al. (2023), counterfactual memorization | Shows models generalize on familiar surface forms but fail under perturbation | Closest prior work conceptually — differentiate by explicitly measuring *compositional recombination*, not just perturbation robustness |
| Wiola-13M, "What Language Model to Train if You Have One Million GPU Hours?" | Architecture ablations (position encoding, attention, norm) at small scale | Measures perplexity/capability, not memorization behavior |
| Memory Dial, Memorization Sinks | Controllable/removable memorization | Focused on mitigation, not the creativity trade-off itself |
| TinyStories (Eldan & Li) | Coherence/fluency of small story-generating models | Does not touch memorization or originality measurement |

**One-line differentiation to use in the paper's related work section:** *No existing work crosses the architecture-ablation literature with the memorization literature, and no existing memorization study uses a creative-generation setting where "crowding out novelty" is the outcome of interest rather than privacy leakage.*

---

## 4. Base Setup

- **Dataset:** TinyStories-style corpus (either existing training data or the public TinyStories dataset) — simple vocabulary and templated structure makes "novelty" measurable against a clear distributional baseline.
- **Base model:** Existing 14.2M model as the reference/anchor configuration.
- **Architecture variants (pick 2–3 axes, 2 settings each — NOT the full original 9-variable table):**
  - Position encoding: learned vs. RoPE
  - Attention: MHA vs. GQA
  - (Optional third axis): Normalization: LayerNorm vs. RMSNorm

  → This yields **4–8 model configurations**, all trained from scratch at 14.2M parameters, same data, same token budget.

---

## 5. Story Canary Design

Unlike standard canaries (random strings), these are **structured narrative elements** so both memorization AND compositional reuse can be measured.

### 5.1 Canary types
1. **Character-name canaries:** Fixed character + trait pairing (e.g., "Pip the fox, who was always hungry"), inserted into N template stories.
2. **Plot-fragment canaries:** Fixed structural fragment (e.g., "then found a shiny key under the old oak tree"), inserted across stories with *varying surrounding context* — tests verbatim memorization vs. redeployment in new plots.
3. **Control/unseen elements:** Character names and fragments never seen in training — establishes the "unseen" baseline.
4. **Near-duplicate elements:** Slight paraphrases of inserted fragments — tests generalization vs. verbatim recall.

### 5.2 Exposure frequencies (per canary)
1×, 10×, 50×, 100×, 500×

### 5.3 Practical note on compute
Multiple distinct canaries (different names/fragments) can be inserted at different frequencies within the *same* training run, provided they don't interact — verify no cross-contamination by checking each canary's metrics independently after training.

### 5.4 Pre-registration
Decide the full canary list and frequency levels **before** running experiments and record it here or in a separate frozen file, to avoid post-hoc cherry-picking of "canaries that worked."

---

## 6. Metrics

### 6.1 Memorization score (established methods)
- **Exposure metric** (Carlini et al., 2019): relative log-perplexity rank of the canary vs. random alternatives.
- **Verbatim extraction rate:** prompt with the prefix, check exact-match continuation under greedy decoding.

### 6.2 Compositional novelty score (new contribution — needs care)
- **N-gram overlap / edit distance** from the nearest training story, when the canary element appears in a newly generated story.
- **Recombination test:** prompt the model to generate a story combining the canary character with a *novel* setting never paired with it in training. Score each output as:
  - (a) verbatim reproduction of a training story
  - (b) template-copy with superficial swaps
  - (c) genuine new combination
  - Requires a scoring rubric — hand-label a sample (100–200 generations) and/or use a larger LLM as judge with a fixed rubric, validated against your own labels on a subset first.
- **Diversity across samples:** generate K completions per prompt at temperature > 0; measure self-BLEU or distinct-n across them. Lower diversity at high exposure counts = crowding-out signal.

---

## 7. Core Experiment Grid

For each architecture configuration (4–8 total):

1. Train with each canary type inserted at each frequency level (1×, 10×, 50×, 100×, 500×).
2. After training, for each canary/frequency pair, measure:
   - Exposure score
   - Extraction rate
   - Recombination score
   - Diversity score
3. Plot **memorization score (x-axis) vs. novelty/recombination score (y-axis)** per architecture.
4. Overlay curves across architectures to test H2.

This trade-off curve is the paper's central result/figure.

---

## 8. Expected Outcomes (all publishable)

| Outcome | Interpretation |
|---|---|
| Clear inflection point in the curve | Clean, easy-to-write-up result: "novelty collapses sharply past exposure count X" |
| Smooth monotonic decline | Still valid — frame around the shape of the curve rather than a hard threshold |
| No architecture effect (H2 null) | Valid negative result — trade-off is a function of exposure/data, not architecture, at this scale; positions as a boundary condition against the architecture-ablation literature |

---

## 9. Draft Paper Structure

1. **Introduction** — reframe memorization as a creativity trade-off, not solely a privacy risk
2. **Related Work** — position against Carlini/Tirumala (memorization-scale), Wiola/million-GPU-hours (small-model architecture), Zhang et al. counterfactual memorization (closest prior work)
3. **Method** — model configs, canary design, metrics
4. **Results** — trade-off curves, per-architecture comparison
5. **Analysis** — location of inflection point; practical implication (e.g., "cap repetition of story elements below X occurrences to preserve creativity in small generative models")
6. **Limitations** — small scale, synthetic canaries, judge-model reliability for recombination scoring
7. **Conclusion**

---

## 10. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Recombination-score rubric is subjective — likely reviewer pushback | Publish clear, fixed scoring criteria; get a second labeler (even informally) for inter-rater agreement on a subset |
| Compute cost of 4–8 configs × 5 frequency levels, all from scratch | At 14.2M params, each run should be hours not days on a single modern GPU — budget accordingly but should remain feasible solo |
| Cherry-picking canaries post-hoc | Pre-register canary list and frequencies before running experiments (Section 5.4) |
| LLM-as-judge unreliability for novelty scoring | Validate judge against hand-labeled subset before trusting it at scale; report agreement rate |

**Status update (2026-09-28), from actually running the project:** the "cherry-picking canaries" risk above
manifested in a related but different form than anticipated — not post-hoc cherry-picking of results, but three
canary identities (`char_pip`, `plot_key`, `plot_voice`) turning out not to be genuinely novel to the base
corpus, discovered only after training when they showed permanent ceiling-saturated exposure in every condition.
See `PHASE4_NOTES.md`'s root-cause section and `docs/DRAFT_PAPER.md` §4.1. Mitigated after the fact by diagnosing
the mechanism (base-corpus frequency check) and continuing analysis on the unconfounded canaries, and pre-emptively
for any future run of this design by `scripts/check_canary_novelty.py`, which should be run as a Section-5.4
pre-registration step, before locking a canary bank, not after a confusing result.

---

## 11. Open Decisions / To Do

**Status as of 2026-09-28, updated as the project has actually run:**

- [x] **Dataset**: resolved — the existing `aarav-lm` training corpus (a TinyStories slice, `data/raw/base.txt`),
  reused rather than adopting the public dataset separately, since it's the same source material and avoids a
  second licensing/provenance question.
- [~] **Architecture axes**: partially resolved by compute reality, not fully decided. The reduced first pass runs
  one axis (baseline vs. `variant_a_learned_pos`, position encoding) at four frequencies; configs for a second axis
  (`variant_b_mha`, attention type) and a third (`variant_c_layernorm`, normalization) exist and are
  parameter-matched (`README.md` §Phase 2) but not queued. Whether to spend the compute to run them is still a real
  open decision — flagged, not decided unilaterally, since it's a genuine scope/cost tradeoff.
- [x] **Pre-registered canary list**: resolved — `configs/canaries.yaml`, locked once
  `scripts/prepare_canary_corpus.py` generates `configs/canary_assignment.json` from it. (A real gap in this
  pre-registration was found and fixed after the fact: three canary identities turned out not to be genuinely novel
  to the base corpus — `PHASE4_NOTES.md`'s root-cause section, and `scripts/check_canary_novelty.py` added so this
  can't happen silently in a future run.)
- [ ] **LLM-judge vs. fully manual scoring for the recombination test**: still genuinely open, and per this plan's
  own ground rule (§5.2's brief, "no LLM-judge auto-scoring until 100-200 samples are hand-labelled first") it
  needs the user's own hand-labelling before it can even be considered, not a unilateral decision. Labelling
  batches are prepared and waiting (`results/labelling/*.txt`, one per scored checkpoint) but not yet labelled.
- [ ] **Target venue**: still open, purely the user's call — affects required rigor and page budget for the eventual
  write-up.

---

## 12. Related Work — Full Citation List (for later expansion)

- Carlini et al., 2019 — "The Secret Sharer" (USENIX Security)
- Carlini et al., 2020 — "Extracting Training Data from Large Language Models"
- Tirumala et al., 2022 — memorization dynamics during training
- Zhang et al., 2023 — counterfactual memorization
- Eldan & Li, 2023 — TinyStories
- Wiola-13M, 2026 — Gated Spiral Attention small LM architecture ablation
- "What Language Model to Train if You Have One Million GPU Hours?" — position/activation/norm ablations
- Memory Dial, 2026 — controllable memorization framework
- Memorization Sinks, 2025 — isolating memorization during training
