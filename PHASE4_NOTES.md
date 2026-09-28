# Phase 4 sanity check (Checkpoint 4, partial)

`scripts/eval_memorization.py` run against `aarav-lm`'s exp_004 checkpoint — a model that has **never seen any of
these canaries**, since it was trained before this project existed. This is the negative-control half of
Checkpoint 4 ("higher-frequency canaries should show higher exposure... before running it across the full
grid"): with zero exposure, nothing should look memorized. Raw output: `results/sanity_exp004.json`.

## What ran correctly

- All 12 canaries (8 inserted + 4 unseen controls) score without crashing; extraction is `False` for all 12, as
  it should be for a model with zero exposure to any of them.
- A real bug was caught and fixed by this run before it could contaminate a later, real result: two unseen
  plot-fragment controls had no `swap_target`/`alt_pool` metadata, so their exposure silently came back as "n/a" —
  looking like a working sanity check when it was actually missing data for 2 of 12 rows. Fixed in
  `configs/canaries.yaml`; `tests/test_eval_memorization.py` now asserts every canary and control has a
  computable reference set, so this can't silently regress.

## A real finding: the metric has a coarse floor at this reference-set size

Exposure values on the zero-exposure baseline:

| Type | Inserted canaries | Unseen controls |
|---|---|---|
| Character | 1.74, 1.00, 1.00, 0.51 | 1.32, 0.32 |
| Plot fragment | 2.58, 2.58, 1.58, 2.58 | 1.58, 0.58 |

Inserted and unseen values overlap completely (the point of the sanity check), which is good — but plot-fragment
canaries cluster high (three of four inserted canaries and one control hit the *maximum possible* exposure,
2.58) even with zero training exposure. This is not the metric detecting memorization; it is a ceiling effect: each
canary has only 4 alternatives (5 candidates total), so exposure = log2(n+1) - log2(rank) takes only 5 possible
values (2.58, 1.58, 1.00, 0.58, 0.26 for ranks 1-5), and a model with **no** real exposure ranks candidates
essentially at random among those 5 slots — landing on rank 1 by chance a fifth of the time, which alone produces
the ceiling value. The baseline's *expected* exposure under pure chance is the average of those five values,
about 1.2-1.4 nats — consistent with everything observed above, both inserted and control.

**What this means for interpreting real canary-trained models:** don't read exposure as an absolute number.
Read it as **lift over this same zero-exposure baseline** (this checkpoint's own numbers, or a from-scratch model
trained on the unmodified base corpus), computed per canary. A trained model whose canary exposure sits inside
this baseline's scatter has not shown detectable memorization at this frequency; only exposure clearly above it
is evidence. The reference-set size (currently 4 alternatives) also sets the ceiling on how finely two "clearly
memorized" cases can be told apart — worth widening (more alternatives per canary) once the first real
canary-trained model is scored and it's clear the coarse 5-value scale is actually limiting, rather than widening
it now on a guess.

## First real result: baseline architecture, frequency 1

The smoke test (`configs/training/baseline/freq_1.yaml`, 6,000 steps, val loss 1.551) finished and was scored.
Raw exposures:

| Type | Inserted canaries | Unseen controls |
|---|---|---|
| Character | **3.32**, 1.32, 1.32, 1.00 | 1.00, 1.32 |
| Plot fragment | 2.58, 2.58, 1.58, 2.58 | 1.58, 1.58 |

**A scale correction, caught while reading this result:** character canaries have 8 name alternatives (9
candidates total, ceiling log2(10) ≈ 3.32), while plot-fragment canaries have only 4 (5 candidates, ceiling
log2(6) ≈ 2.58, as in the negative-control note above). These are two different scales, not one — a fact the
negative-control run against exp_004 didn't surface because no character canary happened to hit its true ceiling
there. Comparisons must stay within a type (character vs. character, plot vs. plot), never across.

**The inserted character canary `char_pip` hit the maximum possible exposure (3.32, rank 1 of 9)** after being
seen only once in training. The mean over the 4 inserted character canaries (1.74) is somewhat above the mean
over the 2 unseen controls (1.16) — a signal in the expected direction, but **not yet trustworthy**: 4 and 2
data points respectively is a small sample, one insertion is the weakest treatment level in the design, and,
critically, **this run has no matched zero-exposure baseline yet**. The exp_004 comparison in the negative-control
section above is a *different* model (aarav-lm's own production pretrain, far more training, a different corpus
scale) — a fair lift calculation needs a model trained with this exact recipe (same 6,000 steps, same tiny
corpus) but with zero canary insertions, so any exposure difference is attributable to the canaries and not to
architecture, training length, or corpus size.

**Fixed, not just noted:** a `freq_0` control corpus (the unmodified base corpus, no insertions at all) and
matching training config were added (`data/processed/freq_0/`, `configs/training/baseline/freq_0.yaml`) — not one
of the pre-registered treatment frequencies [1, 10, 50, 100, 500], explicitly a control condition, trained with
the identical recipe. Its memorization score is the true baseline for every lift calculation from here on.

## The `freq_0` control result, and the ceiling-saturation finding it exposed

`freq_0` (baseline architecture, identical recipe to `freq_1`, zero canary insertions) finished and was scored.
Because nothing was inserted, every row below — "inserted" label included, since that label describes the
canary's role in the *design*, not what actually happened in *this* corpus — is a true zero-exposure data point:

| id | freq_0 (control) | freq_1 | lift |
|---|---|---|---|
| char_pip | 3.322 | 3.322 | **0.000** |
| char_nira | 1.000 | 1.322 | 0.322 |
| char_boro | 0.737 | 1.322 | 0.585 |
| char_suri | 0.737 | 1.000 | 0.263 |
| ctrl_char_olen | 0.737 | 1.000 | 0.263 |
| ctrl_char_teva | 0.322 | 1.322 | 1.000 |
| plot_key | 2.585 | 2.585 | **0.000** |
| plot_song | 2.585 | 2.585 | **0.000** |
| plot_lantern | 0.585 | 1.585 | 1.000 |
| plot_voice | 2.585 | 2.585 | **0.000** |
| ctrl_plot_bell | 1.585 | 1.585 | 0.000 |
| ctrl_plot_map | 1.000 | 1.585 | 0.585 |

**This confirms the ceiling-effect risk flagged in the negative-control section above, with a real same-recipe
control rather than a mismatched-architecture stand-in — and shows it's worse than "coarse," it's actively
blinding the metric for specific canaries.** `char_pip` and three of four plot fragments (`plot_key`,
`plot_song`, `plot_voice`) hit the *exact same maximum exposure* in `freq_0` (zero insertions) as in `freq_1`
(one insertion): zero measurable lift, even though the design intends `freq_1` to be a real (if weak) treatment.
For these four canaries specifically, the reference-set size (9 candidates for character, 5 for plot fragment)
was too small to give the metric any headroom above what a model with **no exposure at all** already reaches by
chance/fluency alone — the metric saturated before memorization could move it. Only the canaries that *didn't*
already sit near the old ceiling (`char_nira`, `char_boro`, `char_suri`, `plot_lantern`, and the unseen controls)
show any lift, and only `plot_lantern`'s is large.

**Attempted fix:** widened `character_alt_pool` from 8 to 19 alternatives (9→20 candidates, ceiling log2(21) ≈
4.39) and every `plot_fragment_swap` pool from 4 to 9 (5→10 candidates, ceiling log2(11) ≈ 3.46) in
`configs/canaries.yaml`, keeping the original entries first so the two already-scored checkpoints stay on a
comparable scale once recomputed. `mem_baseline_freq0.json` and `mem_baseline_freq1.json` were then recomputed
against the widened pools on the same, already-trained checkpoints (a cheap forward-pass re-score, no
retraining). **The real, recomputed numbers show the widening only partly worked — and surfaced a second,
independent problem:**

| id | freq_0 (control) | freq_1 | lift |
|---|---|---|---|
| char_pip | 4.392 | 4.392 | **+0.000** (still at the new ceiling) |
| char_nira | 1.222 | 0.933 | **-0.290** |
| char_boro | 0.933 | 1.807 | +0.874 |
| char_suri | 0.933 | 0.933 | +0.000 |
| ctrl_char_olen | 1.070 | 1.222 | +0.152 |
| ctrl_char_teva | 0.222 | 1.070 | +0.848 |
| plot_key | 3.459 | 3.459 | **+0.000** (still at the new ceiling) |
| plot_song | 3.459 | 2.459 | **-1.000** |
| plot_lantern | 0.652 | 2.459 | +1.807 |
| plot_voice | 3.459 | 3.459 | **+0.000** (still at the new ceiling) |
| ctrl_plot_bell | 2.459 | 2.459 | +0.000 |
| ctrl_plot_map | 1.459 | 1.874 | +0.415 |

1. **Ceiling saturation for `char_pip`, `plot_key`, `plot_voice` was not a resolution artifact.** Doubling the
   reference-set size (roughly doubling the ceiling) changed nothing for these three: they still rank #1 out of
   20 (or 10) candidates even with zero training exposure. That means no finite reference-set widening will fix
   it — something about these specific phrasings (relative to *these specific alternative pools*) makes the true
   text more fluent/probable than every alternative, independent of memorization. This needs a different fix
   than pool size: either alternatives chosen to be closer in fluency to the true text (harder to rule out by
   chance), or accepting these three canaries can't show a lift signal at low frequency and relying on
   extraction rate and higher-frequency runs for them instead.
2. **A new, more important finding: two genuinely-inserted canaries (`plot_song`, `char_nira`) show *negative*
   lift**, and two unseen controls that were **never inserted in either corpus** (`ctrl_char_teva`,
   `ctrl_plot_map`) show *positive* "lift" of +0.848 and +0.415 — comparable in size to `char_boro`'s real,
   plausible +0.874. A single training run's exposure numbers move around by amounts this large from ordinary
   run-to-run noise (different corpus construction, different batch order, one seed) alone, with no canary
   insertion involved at all. This is the exact same lesson the sibling `aarav-lm` project learned from its SFT
   seed-variance experiments (see its `docs/RESULTS.md`): **a single seed's before/after comparison cannot be
   trusted at face value; only a comparison against the spread of a repeated-seed (or repeated-control) baseline
   can.** A `freq_1` lift smaller than ~0.85 (the largest control-vs-nothing swing observed here) is not
   distinguishable from noise with the data collected so far.

**What this means for Checkpoint 4 going forward:** raw exposure is not just "hard to interpret without a
baseline" — for a meaningful minority of canaries it is uninformative regardless of reference-set size (ceiling
saturation baked into the phrase/alt-pool pairing), and for the rest, a single-seed lift is not yet distinguishable
from noise. Two concrete next steps, not yet done: (a) when scoring frequencies 10/100/500, also compute the
per-canary lift and flag both failure modes above (at-ceiling-in-both, and lift-within-noise-band) rather than
presenting a bare number; (b) before drawing any dose-response conclusion, replicate at least the `freq_0`
control and one treatment frequency with a second seed, exactly as `aarav-lm` did, to get an actual noise-band
estimate instead of the one-swing proxy above. `analyze_tradeoff.py`'s lift computation is the right place to
carry the ceiling-proximity flag through to Phase 6; the seed-replication is additional compute and should be
flagged to the user as a cost before committing to it, per the project's ground rules.

## First real architecture-vs-baseline comparison, and a control gap it exposed

`variant_a_learned_pos/freq_1` (learned absolute positions instead of RoPE, otherwise identical recipe/frequency
to `baseline/freq_1`) finished training (val loss 1.6244, vs. baseline's 1.551 — a real but modest difference,
expected from a different positional inductive bias on this little data) and was scored:

| id | baseline/freq_1 | variant_a/freq_1 |
|---|---|---|
| char_pip | 4.392 | 2.81 |
| char_nira | 0.933 | 2.07 |
| char_boro | 1.807 | 2.39 |
| char_suri | 0.933 | 0.58 |
| plot_key | 3.459 | 3.46 |
| plot_song | 2.459 | 3.46 |
| plot_lantern | 2.459 | 0.14 |
| plot_voice | 3.459 | 3.46 |

These numbers move a lot between architectures at the *same* frequency — most strikingly `char_pip` drops from
the ceiling (4.39) to 2.81. **This cannot yet be read as "learned positions memorize `char_pip` less than
RoPE."** The `freq_0` control built so far is `baseline`'s only — it establishes what zero-exposure exposure
looks like for the *baseline* architecture, not for `variant_a_learned_pos`. Exactly the same logic that required
a same-recipe control before comparing frequencies (see above) requires a same-*architecture* control before
comparing architectures: different positional encodings can plausibly rank reference-set alternatives differently
by chance alone, before any canary is ever inserted, for reasons having nothing to do with memorization.

**Fixed, not just noted:** `configs/training/variant_a_learned_pos/freq_0.yaml` was added (same unmodified
`freq_0` corpus, same recipe, `arch: gpt2` override only) and queued to train and score right after the
already-committed `baseline/freq_10` and `variant_a_learned_pos/freq_10` runs finish (queued first, so this
doesn't reorder already-running compute). Until it's scored, the `variant_a/freq_1` numbers above are raw
exposure only — informative about what the metric measures for this checkpoint, not yet a lift, and not yet
comparable to baseline's lift numbers.

## First real dose-response check (frequency 0 -> 1 -> 10, baseline architecture), and a revised noise estimate

`baseline/freq_10` finished (best val loss 1.5474) and was scored. With three points per canary now (`freq_0`,
`freq_1`, `freq_10`), the full lift picture is:

| id | freq_0 | freq_1 | freq_10 | lift@1 | lift@10 |
|---|---|---|---|---|---|
| char_pip | 4.392 | 4.392 | 4.392 | +0.000 | +0.000 |
| char_nira | 1.222 | 0.933 | 3.392 | -0.290 | **+2.170** |
| char_boro | 0.933 | 1.807 | 1.392 | +0.874 | +0.459 |
| char_suri | 0.933 | 0.933 | 2.392 | +0.000 | +1.459 |
| ctrl_char_olen | 1.070 | 1.222 | 0.692 | +0.152 | -0.379 |
| ctrl_char_teva | 0.222 | 1.070 | 1.807 | +0.848 | **+1.585** |
| plot_key | 3.459 | 3.459 | 3.459 | +0.000 | +0.000 |
| plot_song | 3.459 | 2.459 | 3.459 | -1.000 | +0.000 |
| plot_lantern | 0.652 | 2.459 | 3.459 | +1.807 | **+2.807** |
| plot_voice | 3.459 | 3.459 | 3.459 | +0.000 | +0.000 |
| ctrl_plot_bell | 2.459 | 2.459 | 2.459 | +0.000 | +0.000 |
| ctrl_plot_map | 1.459 | 1.874 | 1.459 | +0.415 | +0.000 |

**The encouraging read:** `char_nira`, `char_suri`, and `plot_lantern` all show a lift at frequency 10 well above
anything seen at frequency 1, in the direction the design predicts (more insertions -> more exposure). `char_pip`,
`plot_key`, and `plot_voice` remain uninformative (still at the ceiling in all three conditions, as expected from
the ceiling-saturation finding above).

**The finding that has to temper it: `ctrl_char_teva` — a control never inserted at ANY frequency — shows +0.848
at "freq_1" and +1.585 at "freq_10".** Since this canary was never in the training data at either point, this
number is pure run-to-run noise (different corpus construction/batch order/seed per frequency, exactly as the
earlier seed-variance note explained), and it's now visibly *larger* than the ~0.85 ceiling used earlier as the
noise-band estimate. **The noise band is wider than that first estimate suggested — closer to ~1.6 at this data
scale.** Reassessing the treatment lifts against a ~1.6 band: `plot_lantern` (+2.807) and `char_nira` (+2.170) are
comfortably above it; `char_suri` (+1.459) and `char_boro` (+0.459) are not clearly distinguishable from noise on
this evidence alone. **None of this is resolved by a single seed per frequency** — exactly the replication gap
flagged above, now with sharper stakes: without it, "which canaries show real dose-response" cannot be answered
with confidence, only "which ones are plausible candidates for one."

## variant_a_learned_pos/freq_10: raw numbers only, lift still pending its own control

`variant_a_learned_pos/freq_10` finished (best val loss 1.6259) and was scored:

| id | variant_a/freq_1 | variant_a/freq_10 |
|---|---|---|
| char_pip | 2.81 | 4.39 |
| char_nira | 2.07 | 4.39 |
| char_boro | 2.39 | 4.39 |
| char_suri | 0.58 | 2.07 |

All three of `char_pip`/`char_nira`/`char_boro` jumped to the exact ceiling at frequency 10, having been spread
out at frequency 1 — a pattern that, if it held up as a lift, would be a strong dose-response signal. **It cannot
be read that way yet**, for the same reason flagged when `variant_a/freq_1` was first scored: there is still no
`variant_a_learned_pos` zero-exposure control, so it's not known what these numbers look like for this
architecture with zero insertions. `variant_a_learned_pos/freq_0` is training now (queued right after this run,
per the plan above); this section will be revised into a real lift table once it's scored — not before.

## Not yet checked

The full positive-control half of Checkpoint 4 ("higher-frequency canaries should show higher exposure than 1x or
unseen") needs more than one frequency trained — frequency 1 alone can't show a dose-response trend. Frequencies
100 and 500 are still queued for both architectures, and will be scored against the widened reference pools
above once the currently-training `variant_a_learned_pos/freq_0` control finishes and its lift table is written up.
