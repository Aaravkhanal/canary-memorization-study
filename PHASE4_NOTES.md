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

## variant_a_learned_pos: the full lift table, and cross-architecture replication

`variant_a_learned_pos/freq_0` finished and was scored, closing the control gap flagged above. The real lift
table for this architecture:

| id | freq_0 | freq_1 | freq_10 | lift@1 | lift@10 |
|---|---|---|---|---|---|
| char_pip | 3.392 | 2.807 | 4.392 | -0.585 | +1.000 |
| char_nira | 1.807 | 2.070 | 4.392 | +0.263 | **+2.585** |
| char_boro | 1.807 | 2.392 | 4.392 | +0.585 | **+2.585** |
| char_suri | 0.807 | 0.585 | 2.070 | -0.222 | +1.263 |
| ctrl_char_olen | 1.392 | 1.070 | 0.692 | -0.322 | -0.700 |
| ctrl_char_teva | 0.807 | 0.807 | 1.807 | +0.000 | +1.000 |
| plot_key | 3.459 | 3.459 | 3.459 | +0.000 | +0.000 |
| plot_song | 3.459 | 3.459 | 3.459 | +0.000 | +0.000 |
| plot_lantern | 0.459 | 0.138 | 3.459 | -0.322 | **+3.000** |
| plot_voice | 3.459 | 3.459 | 3.459 | +0.000 | +0.000 |
| ctrl_plot_bell | 2.459 | 2.459 | 1.874 | +0.000 | -0.585 |
| ctrl_plot_map | 1.138 | 2.459 | 1.138 | **+1.322** | +0.000 |

**This is the most useful result so far, because it's an independent replication, not just a second run.**
Comparing against baseline architecture's lift table (same section above):

- `char_nira`, `char_boro`, and `plot_lantern` show clear positive lift at frequency 10 **in both architectures**
  — `plot_lantern` especially (baseline +2.807, variant_a +3.000: nearly identical, and both hit their
  architecture's ceiling). Two different architectures, two different training runs, same three canaries showing
  the largest, most consistent dose-response signal. This is meaningfully stronger evidence than either result
  alone: architecture-independent replication rules out "quirk of one run's RoPE/GQA setup" as the explanation.
- `plot_key`/`plot_song`/`plot_voice` are ceiling-saturated in **both** architectures at **all three**
  frequencies — confirming this is a property of the canary phrasing vs. its reference pool, not of one
  architecture's training dynamics.
- The noise-band estimate is independently reconfirmed here too: `ctrl_plot_map`, never inserted into this
  architecture's training data at any frequency, still shows +1.322 "lift" at frequency 1 from pure run-to-run
  noise — close to baseline's `ctrl_char_teva` swing (+1.585) that originally set the ~1.6 estimate. Two
  unrelated controls, two different architectures, both landing in the same noise range independently is good
  evidence the ~1.6 band is real and not an artifact of one run.
- `char_pip` and `char_suri` are non-monotonic here (slightly negative lift at frequency 1, positive at frequency
  10) — plausibly a real but weak effect that only clears the noise floor at the higher frequency, but not
  distinguishable from noise on this evidence alone.

## baseline/freq_100: the ambiguity at frequency 10 resolves

`baseline/freq_100` finished (best val loss 1.5609) and was scored. Frequency 100 is unambiguous where frequency
10 was not:

| id | freq_0 | freq_100 | lift@100 |
|---|---|---|---|
| char_pip | 4.392 | 4.392 | +0.000 (still ceiling-saturated, uninformative) |
| char_nira | 1.222 | 4.392 | **+3.170** |
| char_boro | 0.933 | 4.392 | **+3.459** |
| char_suri | 0.933 | 4.392 | **+3.459** |
| ctrl_char_olen | 1.070 | 1.070 | +0.000 |
| ctrl_char_teva | 0.222 | 1.222 | +1.000 |
| plot_key | 3.459 | 3.459 | +0.000 (ceiling) |
| plot_song | 3.459 | 3.459 | +0.000 (ceiling) |
| plot_lantern | 0.652 | 3.459 | **+2.807** |
| plot_voice | 3.459 | 3.459 | +0.000 (ceiling) |
| ctrl_plot_bell | 2.459 | 2.459 | +0.000 |
| ctrl_plot_map | 1.459 | 1.138 | -0.322 |

**`char_boro` and `char_suri`, which sat right at the edge of the ~1.6 noise band at frequency 10 (+0.459 and
+1.459), now show +3.459 each at frequency 100** — every inserted character canary except the already-saturated
`char_pip` has hit the exact same ceiling as `char_nira` and `plot_lantern`. All four controls' swings at this
frequency (+0.000 to +1.000) stay comfortably inside the noise band, so this isn't ceiling-effect noise; it's
every genuinely-inserted, non-saturated canary converging on maximal exposure once frequency is high enough. This
is the clearest, least ambiguous dose-response result in the project so far, and it resolves the frequency-10
ambiguity for `char_boro`/`char_suri` in the positive direction: their earlier borderline lift was very likely a
weak-but-real effect that simply hadn't cleared the noise floor yet, not noise itself.

## Root cause of the ceiling-saturation finding: it's not a metric flaw, it's a canary-design flaw

Every earlier section in this file treated `char_pip`, `plot_key`, and `plot_voice`'s permanent ceiling-saturation
(present at `freq_0`, i.e. **zero** insertions, and unmoved by widening the reference pool 2x) as an unexplained
property of those specific phrasings — "more fluent than every alternative tried, independent of training
exposure," with no mechanism given. Prompted to dig into *why*, the mechanism turns out to be simple and checkable
directly against the base corpus, with no training or re-scoring needed:

| Canary | Identity phrase | Occurrences in `data/raw/base.txt` (unrelated to any canary insertion) | Always at ceiling? |
|---|---|---|---|
| `char_pip` | "Pip" (a name) | **150** | Yes, in every condition tested |
| `plot_key` | "a shiny key" | **41** | Yes, in every condition tested |
| `plot_voice` | "a soft voice" | **67** | Yes, in every condition tested |
| `char_nira` | "Nira" | 0 | No — real, growing dose-response |
| `char_boro` | "Boro" | 0 | No — real, growing dose-response |
| `char_suri` | "Suri" | 0 | No — real, growing dose-response |
| `plot_song` | "a strange song" | 0 | No — mostly at ceiling by freq 10/100, but not at freq_0 |
| `plot_lantern` | "the little lantern" | 0 | No — real, growing dose-response, clearest signal in the project |

**The three permanently-saturated canaries are exactly the three whose "novel" identity was never actually novel
to the base pretraining corpus.** "Pip" is a name TinyStories already uses 150 times, unrelated to this project's
canary insertions; "a shiny key" and "a soft voice" are generic phrases TinyStories already uses dozens of times.
A model trained on this corpus assigns these phrases high probability *before any canary insertion happens*,
simply because the base corpus itself made them familiar — nothing about the exposure metric's reference-set size
was ever going to fix that, because widening the pool doesn't change how familiar the true phrase already is.
Every canary that shows genuine, controllable dose-response has **zero** base-corpus occurrences of its identity
phrase — a clean necessary condition, confirmed on all 8 inserted canaries and both unseen-control types (`Olen`,
`Teva`: 0 occurrences each, behaving exactly as zero-exposure canaries should).

**This reframes the earlier "attempted fix" (widening the reference pool) correctly**: it wasn't a failed fix to a
real problem, it was the right response to the wrong diagnosis. The actual fix is at Phase 1 (canary design):
verify every candidate canary identity — and every reference-set alternative — has zero occurrences in the base
corpus *before* locking the canary bank, not after noticing a confusing result three phases later. This wasn't
done originally (the alt-pool check above also turned up `Mira`, `Zeb`, `Dara`, and `Nell` at 12-76 occurrences
each — none of them happened to be selected as a true canary identity, so it caused no visible problem, but it was
luck, not design). **Recommendation for any future canary study, and for a paper's methods section**: this
corpus-frequency check is a required pre-registration step, not an optional sanity check — it takes seconds to run
and would have caught this before any training happened.

## variant_a_learned_pos/freq_100: the frequency-100 convergence replicates exactly

`variant_a_learned_pos/freq_100` finished (best val loss 1.6420) and was scored:

| id | freq_0 | freq_100 | lift@100 |
|---|---|---|---|
| char_pip | 3.392 | 4.392 | **+1.000** (see note below) |
| char_nira | 1.807 | 4.392 | **+2.585** |
| char_boro | 1.807 | 4.392 | **+2.585** |
| char_suri | 0.807 | 4.392 | **+3.585** |
| ctrl_char_olen | 1.392 | 1.807 | +0.415 |
| ctrl_char_teva | 0.807 | 0.933 | +0.126 |
| plot_key | 3.459 | 3.459 | +0.000 (ceiling) |
| plot_song | 3.459 | 3.459 | +0.000 (ceiling) |
| plot_lantern | 0.459 | 3.459 | **+3.000** |
| plot_voice | 3.459 | 3.459 | +0.000 (ceiling) |
| ctrl_plot_bell | 2.459 | 1.874 | -0.585 |
| ctrl_plot_map | 1.138 | 1.874 | +0.737 |

**This is an exact, second-architecture replication of `baseline/freq_100`'s finding**: `char_nira`, `char_boro`,
`char_suri`, and `plot_lantern` all show large lift and converge on the ceiling, `plot_key`/`plot_song`/
`plot_voice` stay at the ceiling throughout (contaminated identities, §"Root cause" above), and every control's
swing (-0.585 to +0.737) stays well inside the noise band. Two independent architectures, trained independently,
now agree on every one of these 8 canaries at this frequency.

**One genuine nuance, not a contradiction of the root-cause finding**: unlike in `baseline` (where `char_pip` sat
exactly at the ceiling already at `freq_0`, so its lift reads as `+0.000`), `variant_a_learned_pos`'s `char_pip`
started at 3.392 at `freq_0` — close to, but not quite at, its architecture's ceiling — and shows a real, moderate
lift of `+1.000` on top of the base-corpus-contamination confound. This is consistent with, not contradictory to,
the root-cause explanation: contamination sets a very high *floor*, not a hard ceiling that makes the canary
literally unresponsive to insertion; it just means most of `char_pip`'s exposure was already "spent" before this
project's insertions began, leaving little headroom for a genuine memorization signal to add on top. `char_pip`
remains the least informative canary in the bank for exactly this reason, but "least informative" is now
mechanistically explained rather than mysterious.

## Phase 6: first trade-off table and plot (partial grid — frequencies 0/1/10/100, no hand-labels yet)

Per the brief's Checkpoint 6, this is **plots and a table only — no prose interpretation**. `scripts/analyze_tradeoff.py`
was run against every result collected so far (`results/tradeoff.csv` + `.png`). Numbers, not conclusions:

| variant | freq | memorization (mean lift, all 8 inserted canaries) | novelty (mean distinct-2) |
|---|---|---|---|
| baseline | 1 | 0.174 | 0.800 |
| baseline | 10 | 0.862 | 0.810 |
| baseline | 100 | 1.612 | 0.801 |
| variant_a_learned_pos | 1 | -0.035 | 0.781 |
| variant_a_learned_pos | 10 | 1.304 | 0.780 |
| variant_a_learned_pos | 100 | 1.594 | 0.795 |

**A known dilution in this table, not yet corrected in `tradeoff.csv`/`.png` above**: the "all 8 inserted canaries"
mean folds in `char_pip`, `plot_key`, and `plot_voice` — the three canaries diagnosed as base-corpus-contaminated
(root-cause section above), whose lift is always ≈0 regardless of frequency, for reasons unrelated to training
exposure. Averaging them in with the five genuinely-responsive canaries mechanically pulls the memorization score
toward zero at every frequency. `scripts/analyze_tradeoff.py` was extended with a `--canaries` filter
(`tests/test_analyze_tradeoff.py` covers it) to produce a second version restricted to the five uncontaminated
canaries only (`char_nira`, `char_boro`, `char_suri`, `plot_song`, `plot_lantern`) —
`results/tradeoff_clean.csv` + `.png`:

| variant | freq | memorization (mean lift, 5 clean canaries) | novelty (mean distinct-2, same 5) |
|---|---|---|---|
| baseline | 1 | 0.278 | 0.803 |
| baseline | 10 | 1.379 | 0.827 |
| baseline | 100 | 2.579 | 0.808 |
| variant_a_learned_pos | 1 | 0.061 | 0.777 |
| variant_a_learned_pos | 10 | 1.887 | 0.784 |
| variant_a_learned_pos | 100 | 2.351 | 0.799 |

Both tables show the same qualitative shape: the memorization column rises with frequency in both architectures
(more steeply in the contamination-excluded version, as expected once the always-≈0 canaries are removed from the
average); the novelty column (distinct-2 diversity across completions in a novel setting) stays within a narrow
band (0.777–0.827) across every frequency tested, in both architectures and both canary sets. **This is a factual
description of what these two numbers do across the grid tested so far, not a claim about H1** (`docs/RESEARCH_PLAN.md`
§2, `docs/DRAFT_PAPER.md` §1.1) — the novelty metric here is still the Phase-5 diversity *proxy* (distinct-2), not
the hand-labelled recombination score the brief's design actually calls for (Checkpoint 5, not yet done), frequency
500 is missing from both tables, and every cell is a single training seed. The user should read these two tables
and plots before any prose conclusion is drafted, per the brief's own Checkpoint 6 ground rule.

## freq_500 arrives: ceiling holds, but a never-inserted control's apparent "trend" exceeds the established noise band

`baseline/freq_500` (best val loss 1.5364) and `variant_a_learned_pos/freq_500` (best val loss 1.6126) both finished
and were scored, filling in the last frequency point originally left "not yet checked" above.

| id | freq_0 | freq_100 | freq_500 | lift@500 (baseline) |
|---|---|---|---|---|
| char_pip | 4.392 | 4.392 | 4.392 | +0.000 (ceiling, contaminated) |
| char_nira | 1.222 | 4.392 | **2.807** | +1.585 (real, but *lower* than lift@100's +3.170) |
| char_boro | 0.933 | 4.392 | 4.392 | +3.459 (ceiling, unchanged) |
| char_suri | 0.933 | 4.392 | 4.392 | +3.459 (ceiling, unchanged) |
| ctrl_char_olen | 1.070 | 1.070 | 1.807 | +0.737 |
| ctrl_char_teva | 0.222 | 1.222 | **2.392** | **+2.170 — a never-inserted control** |
| plot_key | 3.459 | 3.459 | 3.459 | +0.000 (ceiling, contaminated) |
| plot_song | 3.459 | 3.459 | 3.459 | +0.000 (already at ceiling by freq_100) |
| plot_lantern | 0.652 | 3.459 | 3.459 | +2.807 (ceiling, unchanged) |
| plot_voice | 3.459 | 3.459 | 3.459 | +0.000 (ceiling, contaminated) |
| ctrl_plot_bell | 2.459 | 2.459 | 2.459 | +0.000 |
| ctrl_plot_map | 1.459 | 1.138 | 0.874 | -0.585 |

| id | freq_0 | freq_100 | freq_500 | lift@500 (variant_a) |
|---|---|---|---|---|
| char_pip | 3.392 | 4.392 | 4.392 | +1.000 (ceiling, unchanged from freq_100) |
| char_nira | 1.807 | 4.392 | 4.392 | +2.585 (ceiling, unchanged) |
| char_boro | 1.807 | 4.392 | 4.392 | +2.585 (ceiling, unchanged) |
| char_suri | 0.807 | 4.392 | 4.392 | +3.585 (ceiling, unchanged) |
| ctrl_char_olen | 1.392 | 1.807 | 1.222 | -0.170 |
| ctrl_char_teva | 0.807 | 0.933 | 1.222 | +0.415 |
| plot_key | 3.459 | 3.459 | 3.459 | +0.000 (ceiling, contaminated) |
| plot_song | 3.459 | 3.459 | 3.459 | +0.000 (ceiling, unchanged) |
| plot_lantern | 0.459 | 3.459 | 3.459 | +3.000 (ceiling, unchanged) |
| plot_voice | 3.459 | 3.459 | 3.459 | +0.000 (ceiling, contaminated) |
| ctrl_plot_bell | 2.459 | 1.874 | 2.459 | +0.000 |
| ctrl_plot_map | 1.138 | 1.874 | 1.138 | +0.000 |

**Two honest findings, not one clean confirmation:**

1. **Every canary already at ceiling by freq_100, in both architectures, stays there at freq_500.** Consistent with a
   saturating dose-response curve. `variant_a_learned_pos` is completely flat between freq_100 and freq_500 on all 12
   canaries — the single most stable frequency comparison in the project.

2. **`baseline`'s `char_nira` genuinely drops from the ceiling (4.392 at freq_100) to 2.807 at freq_500** — a
   frequency five times higher producing a *lower* exposure reading for a real, non-contaminated, non-control
   canary. Each frequency here is an independently-trained model (not a continuation, not a repeated seed), so this
   isn't a contradiction of dose-response in the usual sense — it says the specific exposure value one training run
   lands on near the metric's ceiling has real run-to-run scatter, not that more training exposure produces less
   memorization.

3. **The more important finding: `ctrl_char_teva`, a control never inserted into training at any frequency, reads
   0.222 → 1.222 → 2.392 across baseline's freq_0 → freq_100 → freq_500 — a swing of +2.170 that looks exactly like
   a dose-response curve despite there being no dose.** This is larger than this project's own previously-estimated
   ~1.6-unit single-seed noise band (established earlier in this document from controls' swings across separately-
   trained runs). Since freq_0/100/500 are three separate training runs with three different data orderings and
   initializations (not three seeds of a controlled experiment), there is no way to tell, from this data alone,
   whether the noise band was previously underestimated or this is simply an unlucky draw for one control at one
   frequency. **This directly reinforces, with a concrete example, the second-seed measurement flagged earlier as
   "additional compute, needs a decision" — it is no longer a hypothetical precaution.** Until that exists, any
   single-frequency exposure reading within about 2 units of another should be treated as possibly indistinguishable
   from noise, not just the previously-used ~1.6 rule of thumb.

**Trade-off tables updated** (`scripts/analyze_tradeoff.py`, now covering freq_0/1/10/100/500, `results/tradeoff.csv`
and the contamination-excluded `results/tradeoff_clean.csv`, `--canaries char_nira,char_boro,char_suri,plot_song,plot_lantern`):

| variant | freq | memorization (mean lift, 5 clean canaries) | novelty (mean distinct-2) |
|---|---|---|---|
| baseline | 1 | 0.278 | 0.803 |
| baseline | 10 | 1.379 | 0.827 |
| baseline | 100 | 2.579 | 0.808 |
| baseline | **500** | **2.262** | 0.797 |
| variant_a_learned_pos | 1 | 0.061 | 0.777 |
| variant_a_learned_pos | 10 | 1.887 | 0.784 |
| variant_a_learned_pos | 100 | 2.351 | 0.799 |
| variant_a_learned_pos | **500** | **2.351** | 0.805 |

`baseline`'s mean at freq_500 (2.262) is *below* its freq_100 mean (2.579), driven almost entirely by `char_nira`'s
drop above; `variant_a_learned_pos` is exactly flat (both means driven by the same 4 already-at-ceiling canaries,
`plot_song` being the sole non-ceiling member of the clean 5). The novelty column stays in the same narrow band
(0.777–0.827) it has occupied at every frequency tested in both architectures — freq_500 adds no evidence, positive
or negative, of a novelty cost. **Read against Checkpoint 6's ground rule: these are the numbers, not a conclusion**
— any claim that memorization "plateaus" or "declines" at high frequency needs the second-seed measurement above
before it can be told apart from noise.

## Why extraction rate has been False for every canary in every run — verified, and a correction to an earlier over-generalization here

Every result so far reports `extraction=False` for all 12 canaries in every run, including checkpoints where
several canaries sit at maximal exposure (`baseline/freq_100`: `char_nira`, `char_boro`, `char_suri`,
`plot_lantern` all at the ceiling). That's worth checking directly rather than assumed benign, since a metric that
never fires could be broken rather than just insensitive.

**First check, character canaries** — `eval_memorization.py`'s `extraction()` for character canaries decodes from
`CHAR_PREFIX` ("Once upon a time, ") alone, with **no canary-specific text at all**, because the name is the very
first word of the canary sentence. Checked directly against `baseline/freq_100`'s real checkpoint:

```
PREFIX: 'Once upon a time, '
  GREEDY CONTINUATION: 'Yummy and her mom went to the park. They saw a big tree with a lot of leaves'
```

This confirms a real structural property for character canaries specifically: since the prompt and greedy
decoding are identical and deterministic for every character canary, there is exactly one possible continuation
per checkpoint, so **at most one character canary can ever score `True`** — `False` for 3-4 canaries sharing this
prompt isn't 3-4 independent data points, it's mostly one.

**Second check, plot-fragment canaries — this corrects an over-generalization in the first version of this
section.** Unlike character canaries, `prefix_and_identity()` gives every plot-fragment canary its own,
genuinely distinct prompt (the canary's own connector word before the swap target), so the "at most one can fire"
argument above does **not** apply to them:

```
plot_key:     'One day, something interesting happened. then found '  -> identity 'a shiny key'
plot_song:    'One day, something interesting happened. and heard '   -> identity 'a strange song'
plot_lantern: 'One day, something interesting happened. before '      -> identity 'the little lantern'
plot_voice:   'One day, something interesting happened. until '       -> identity 'a soft voice'
```

Checked directly against `baseline/freq_100` — including `plot_lantern`, the single strongest, cleanest,
least-confounded memorization signal in the whole project (+3.459 exposure lift, cross-architecture replicated):

```
plot_key      expected='a shiny key'        got="Yellow's favorite toy, a small,"          exact_match=False
plot_song     expected='a strange song'     got="Yellow's voice. He looked around and"     exact_match=False
plot_lantern  expected='the little lantern' got='Yeta and a little girl came up to'        exact_match=False
plot_voice    expected='a soft voice'       got='Once upon a time, there was a little girl' exact_match=False
```

Four distinct prompts, four distinct (wrong) greedy outputs — not one shared completion. **`plot_lantern` failing
this properly-conditioned, per-canary test despite its very strong exposure signal is a genuine finding, not a
structural artifact**: exposure only requires beating a curated 9-item reference set at a fixed slot; extraction
requires being the single most probable continuation across the model's entire vocabulary and everything it
learned from ~1.47M base-corpus documents. A canary can be memorized strongly enough to always beat a handful of
specific alternatives while still not being the global single most likely thing to say next — these are genuinely
different-strength tests (consistent with why Carlini et al.'s own original work treats exposure and extraction as
separate, not redundant, measurements), not a sign that the exposure result is somehow wrong.

**Corrected takeaway**: for character canaries, the extraction test as implemented is structurally unable to give
independent per-canary signal (fixable by adding canary-specific conditioning, as plot fragments already have —
not yet implemented). For plot-fragment canaries, the test is already properly per-canary-conditioned, and its
`False` results are real, informative, and simply reflect that this project's insertion frequencies aren't enough
to make a canary the model's single global top choice, even when it's clearly favored within its local reference
set. Every memorization finding in this project should be read as exposure-based; extraction hasn't contributed a
positive result for either reason, and now both reasons are understood precisely rather than conflated.

## The corrected extraction test implemented and run on the full grid: a clean, complete null result

The per-canary, teacher-forced `argmax_match()` test described above (fixes the character-canary shared-prompt
problem; matches plot fragments' already-correct per-canary conditioning) is now implemented
(`scripts/eval_memorization.py`, `tests/test_eval_memorization.py`, 7 new tests) and was run against every one of
the 8 checkpoints scored so far — a cheap re-score (forward passes only, no retraining), adding a new
`argmax_extraction` field to each result file without disturbing the existing `exposure` or `extraction` fields.

**Result, across all 96 canary-checkpoint pairs scored (12 canaries x 8 checkpoints: both architectures, all four
frequencies each): zero `first_token_match`, zero `full_match`.** This includes every case where exposure sits at
its exact maximum (4.392, the ceiling for character canaries on the widened 20-candidate pool) — `char_nira`,
`char_boro`, `char_suri` at `baseline/freq_100`, and all four character canaries simultaneously at
`variant_a_learned_pos/freq_100`. Even there, the model's own single most-probable token at the canary's identity
position is never the canary's true identity.

This is a clean, complete, well-powered confirmation of the exposure/extraction gap already reasoned about above,
now demonstrated directly rather than inferred from a few spot checks: **beating a curated reference set of 9-20
plausible alternatives (exposure) and being the model's single global top choice over its entire ~4096-token
vocabulary (extraction) are measuring genuinely different thresholds, and this project's insertion frequencies
(0-100) reliably clear the first without ever clearing the second.** Whether frequency 500 (queued) changes this
picture is not yet known — everything scored so far tops out at 100 insertions.

## The second-seed measurement lands: the noise band was still too narrow, and it resolves a real open question

`baseline/freq_0_seed1338` (best val loss 1.5586) and `baseline/freq_1_seed1338` (best val loss 1.5773) finished
and were scored. Unlike every noise estimate before this one, these are a **true same-condition comparison**:
`data.seed` (corpus construction, canary insertion) is byte-identical to the original `freq_0`/`freq_1` runs; only
`train.seed` differs (20260927 → 1338). Every earlier noise estimate compared controls *across different
frequencies*, which also changes the training data itself (one more canary insertion shifts every later batch) —
never a clean noise-only comparison until now.

| canary | freq_0: orig → seed1338 | swing | freq_1: orig → seed1338 | swing |
|---|---|---|---|---|
| `char_pip` | 4.392 → 4.392 | +0.000 | 4.392 → 2.807 | **−1.585** |
| `char_nira` | 1.222 → 1.807 | +0.585 | 0.933 → 1.807 | +0.874 |
| `char_boro` | 0.933 → 3.392 | **+2.459** | 1.807 → 1.222 | −0.585 |
| `char_suri` | 0.933 → 1.070 | +0.138 | 0.933 → 0.692 | −0.241 |
| `ctrl_char_olen` | 1.070 → 0.692 | −0.379 | 1.222 → 0.933 | −0.290 |
| `ctrl_char_teva` | 0.222 → 2.070 | **+1.848** | 1.070 → 1.070 | +0.000 |
| `plot_key` | 3.459 → 3.459 | +0.000 | 3.459 → 3.459 | +0.000 |
| `plot_song` | 3.459 → 2.459 | −1.000 | 2.459 → 3.459 | +1.000 |
| `plot_lantern` | 0.652 → 0.652 | +0.000 | 2.459 → 0.652 | **−1.807** |
| `plot_voice` | 3.459 → 3.459 | +0.000 | 3.459 → 3.459 | +0.000 |
| `ctrl_plot_bell` | 2.459 → 2.459 | +0.000 | 2.459 → 2.459 | +0.000 |
| `ctrl_plot_map` | 1.459 → 1.459 | +0.000 | 1.874 → 0.874 | −1.000 |

**The noise band is revised again, upward, on much better evidence**: pure training-run stochasticity — nothing
about canary insertion changed at all — swings by up to **+2.459** (`char_boro`, freq_0) and **+1.848**
(`ctrl_char_teva`, an actual never-inserted control, freq_0). This is wider than both earlier, weaker estimates
(~0.85, then ~1.6), and it's now the best-grounded number in the project: a genuine controlled comparison, not an
inference from swings across changing conditions.

**This directly resolves an open question rather than just widening a number.** `plot_lantern` was singled out
earlier in this document as "the clearest, most consistent, least ambiguous dose-response signal in the project"
at frequency 10, and its frequency-1 lift (+1.807 under the original seed) was the first hint of that. Under the
second seed, at the *same* frequency-1 condition, `plot_lantern` swings by **−1.807** — the exact same magnitude,
the opposite sign, from noise alone. **The original frequency-1 lift for `plot_lantern` cannot be distinguished
from noise; demonstrated directly, not just suspected.** The same logic weakens (not eliminates) two of the
frequency-10 lifts reported earlier: `char_nira` (+2.170) and `char_suri` (+1.459) now sit inside or at the very
edge of the revised ±2.459 band and should be read as "plausible, not established" rather than the stronger
language used when the band was thought to be ~1.6.

**What this does NOT weaken: frequency 100 and 500's core finding.** Multiple canaries converging on the *exact
same* maximum exposure value, independently, across two architectures, is a categorically different kind of
evidence than "a lift exceeds an estimated noise threshold" — ordinary training noise (as measured directly above)
produces scattered swings in both directions, never repeated exact-value convergence across unrelated canaries
and unrelated training runs. That finding stands. What it does sharpen: the same same-condition, second-seed
treatment is now clearly worth doing at frequencies 10, 100, and 500 too, not just 0 and 1 — flagged as the next
piece of additional compute, not yet started.

The novelty/recombination side of the research question (Phase 5 proper — hand-labelling, full-grid scoring)
remains the largest gap requiring the user's own input, not automatable: everything above uses the diversity
proxy, not the hand-labelled score the brief's design calls for.

## A real reproducibility bug found while generating freq_500's hand-labelling batch (fixed)

While filling in freq_500's hand-labelling batch (the same generations already used for the committed novelty
scores, but with `--label-batch` added), re-running `eval_novelty.py` against the identical checkpoint with the
identical `--seed` produced **completely different completions** than the already-committed
`results/novelty_*_freq500.json`. Root cause: the per-`(canary, setting)` seed offset was derived with Python's
built-in `hash((canary["id"], setting))` — which is **randomized per process** for strings/tuples (PYTHONHASHSEED
salting, on by default since Python 3.3) — so `--seed`'s implied determinism never actually held across separate
runs of the script, only within a single process. Fixed with a real, stable hash (`stable_hash()`, md5-based);
`tests/test_eval_novelty.py` now spawns three fresh Python processes and asserts they agree, which fails
immediately on the old code and would have caught this before it ever produced an inconsistent file.

**No previously-committed result is wrong** — every `results/novelty_*.json` in this repo was generated exactly
once and committed as that single generation, so nothing analyzed so far compared two non-matching runs. The
practical consequence is narrower but real: **re-running `eval_novelty.py` on an already-scored checkpoint,
including for something as routine as adding a label-batch file, was silently producing a different sample than
what's on record** — caught here because the diff was inspected before committing (the freq_500 label-batch's
underlying novelty scores were reverted to the original committed file rather than the just-regenerated one, and
only the new label-batch text was kept). Anyone extending this project should regenerate `--label-batch` files
from a config that also re-seeds properly now, and treat any pre-fix rerun's *scores* (not just the batch text) as
non-comparable to the original.

## 2026-10-07 queue audit: generation-seed and training-seed result names

The earlier `scripts/run_seed_experiments.sh` batch used generation seed 1338 on existing checkpoints. A later
training-seed replication runner also writes novelty files with a `_seed1338` suffix, so the two result types
would collide. Before either baseline high-frequency replication reached novelty evaluation, all 20 existing
`novelty_*_seed1338.json` files and their available label text files were renamed with `_gen1338`. The runner can
therefore create new `_seed1338` novelty results from the actual `train.seed=1338` baseline checkpoints. The helper
script now writes `_gen1338` explicitly. All 20 renamed JSON outputs were parsed successfully; their legacy text
label files remain condition-revealing and are not used for blinded annotation. No checkpoint or training run was
changed by this naming correction.

## 2026-10-07 queue continuation: frequency-50 balancing

Baseline frequency 50 completed its full 6,000-update budget at 17:39:59 local. The trainer log records 2h42m50s,
best validation loss 1.5595, and perplexity 4.76. The checkpoint and its 12-row memorization and 32-group/320-sample
novelty evaluations are present. The learned-position frequency-50 cell began at 17:44:57 and completed at
20:13:27 (2h28m30s), with best validation loss 1.6385 and perplexity 5.15. The checkpoint and
memorization/novelty results are present. Its log contains 20 gradient-norm spike events (maximum 129.3); training
completed, but clipping diagnostics should be reviewed before making a stability claim. The baseline frequency-100
and frequency-500 true training-seed replications later completed: 100x ran 2h41m29s (best validation loss
1.5713 / PPL 4.81) and 500x ran 3h02m47s (best 1.5488 / PPL 4.71). Both used the actual alternate-training-seed
checkpoints and have distinct `_seed1338` result JSONs. The 14M runner regenerated matched-baseline tradeoff
tables/plots.

## 2026-10-08 48M disk-full checkpoint incident

After the 14M queue exited, the sequential runner began baseline frequency 0 at 48M. Training ran from 02:14:47
to 04:17:06 local (2h02m19s wall time), reaching step 1,500 / 12.288M tokens. It failed during checkpoint
serialization (`unexpected pos`); the APFS container had only about 185 MB free. The run summary reports 7
gradient-health and 4 gradient-norm anomalies. Step-500 and step-1,000 training checkpoints remained; step-1,000
loaded as a valid resumable checkpoint. After explicit approval, rolling checkpoints from completed 14M cells
were pruned while best/final checkpoints, logs, and results were retained. The same 48M cell resumed from step
1,000 at 07:36:09 local on 2026-10-08 and completed step 6,000 at 13:44:45 local. The completed summary reports
26,976.3 seconds of resumed training time, best validation loss 1.4871208 / PPL 4.4243, and four gradient-norm
anomalies. Memorization and novelty evaluations were generated; checkpoint loads and result JSON parsing passed.
After verification, only this cell's step checkpoints were removed, preserving `best.pt`, `final.pt`, logs, and
results. The 24-cell 14M grid's full-corpus overlap is now complete (7,680 completions), and the first 48M cell
adds 320 more; the other 23 scale cells remain unrun. Human annotation and the separate contamination-free
confirmatory study remain incomplete.

## 2026-10-11 48M interim results and queue status

Five more 48M cells have completed since the baseline frequency-50 update: baseline frequencies 100 and 500, plus
learned-position frequencies 0, 1, and 10. Each reached 6,000 steps; the matching memorization, novelty, and
full-corpus outputs were verified by the queue before rolling checkpoints were removed. The exact elapsed time,
best validation loss, and spike counts are in `results/trainer_runtime_audit.md`.

The preliminary baseline slice has all 8 inserted canaries at exposure rank 1 by frequency 50, remaining there
through 100 and 500 (mean exposure 3.926). At those same conditions mean distinct-1 is 0.404, 0.400, and 0.374;
mean distinct-2 is 0.798, 0.797, and 0.788. Across the six baseline frequencies the average maximum word-four-gram
match against the corresponding 73,139-story training corpus is non-monotonic (0.105, 0.093, 0.116, 0.101,
0.110, 0.107). This does not establish a creativity trade-off or a copying dose-response: all cells are
single-seed, the diversity measures are proxies, and human V/T/N scoring is not complete. The 48M learning rate
(5e-4) also differs from the 14M setting (8e-4).

Nine of 24 scale cells are complete; learned-position frequency 50 is the only active cell (step 4,350/6,000
at the latest check, estimated ~1h49m left), with 14 cells queued. The exact overlap audit now includes 35 cells /
11,200 generated completions. Continue the sequential queue; do not launch a duplicate MPS job.

The final run-level full-corpus audit contains 27 cells / 8,640 generated completions, with unweighted mean exact
maximum word-four-gram overlap 0.096991, median 0.076190, and maximum 1.0. This includes the 24 canonical 14M
cells, two baseline training-seed replications, and one exploratory 48M cell. Treat this as an automated copying
diagnostic only—not a human novelty score or evidence that the model is creative.

## 2026-10-09 48M baseline frequency-1 completion

Baseline frequency 1 completed 6,000 updates at 00:06:17 local on 2026-10-09. The run started at 16:52:18 on
2026-10-08; the trainer summary records 26,015.6 seconds (7h13m36s), with 7h13m59s wall-clock span. Best
validation loss was 1.4931227 (PPL 4.45), with six gradient-norm spikes and seven gradient-health alerts. Both
retained model checkpoints loaded successfully. The 12-row memorization result, 32-group/320-completion novelty
result, and exact full-corpus overlap report all passed parsing and shape checks. The overlap fingerprint matched
the actual frequency-1 corpus (73,139 stories). Rolling step checkpoints were removed only after those checks.

The queue continued with baseline frequency 10. At 00:18:32 local, its log showed step 75/6,000 with an ETA of
about 7h42m. Two of 24 scale cells are complete, 21 are queued, and this is the sole active training cell.
Available disk space was about 7.3 GiB at that check. Since this may not cover both best and final checkpoints for
the remaining cells, the user has been asked how to handle storage; no best/final checkpoint has been deleted.

## 2026-10-09 48M baseline frequency-10 completion

Baseline frequency 10 started at 00:12:20 local and completed at 07:57:05 (7h44m45s wall-clock; 27,860.3 trainer
seconds). It completed 6,000 updates with best validation loss 1.48957798 / PPL 4.44, four gradient-norm spikes,
and eight gradient-health alerts. Its best/final checkpoints and all three evaluation JSONs were verified; the
full-corpus report matched the 73,139-story frequency-10 corpus. Rolling checkpoints were removed after validation.
Baseline frequency 50 began next; at 08:24:14 local it was at step 275/6,000 with an ETA of about 7h22m. Three
of 24 scale cells are complete, one is active, and 20 are queued. Disk space was about 7.0 GiB after cleanup;
user direction on preserving both best and final files versus a best-only policy is still pending.


## 2026-10-09 48M baseline frequency-50 completion

Baseline frequency 50 started at 08:02:49 and completed at 15:37:05 local (7h34m16s wall-clock; 27,234.1 trainer
seconds). It completed all 6,000 updates; best validation loss was 1.5018234 / PPL 4.49. The trainer recorded
three gradient-norm spikes and three gradient-health alerts. Best/final and rolling checkpoint files loaded, and
the three result JSONs passed verification. Full-corpus overlap matched the frequency-50 training-corpus hash
with 73,139 stories. Rolling checkpoints were removed after verification. Baseline frequency 100 began at
15:43:37 local and is the only active training cell; at the latest status check it had just logged step 0. Four
of 24 scale cells are complete and 19 are queued. Free disk was about 13 GiB after cleanup; keep both best and
final model files and monitor capacity rather than pruning scientific artifacts.

## 2026-10-11 learned-position 48M frequencies 50 and 100 completed

Learned-position frequency 50 started at 03:26:39 and completed at 10:17:57 local (6h51m18s wall; summary
reports 24,652.2 trainer seconds). Best validation loss was 1.5464118 / PPL 4.69, with 39 gradient-norm spikes
and four gradient-health alerts. Frequency 100 ran from 10:25:13 to 18:23:08 (7h57m55s wall; 28,655.9 trainer
seconds), best validation loss 1.5472167 / PPL 4.70, with 45 spikes and two health alerts. For both cells,
`best.pt` and `final.pt` loaded successfully, memorization results had 12 rows, novelty results had 32 groups /
320 completions, and full-corpus results had 32 groups / 320 completions with SHA-256 matching the matching
73,139-story frequency corpus. The sequential runner performed these checks before removing rolling step files.

The new single-seed learned-position outputs show seven of eight inserted canaries at exposure rank 1 at
frequency 50, rising to eight of eight at frequency 100. Group-mean distinct-1 is 0.387 / 0.406 and distinct-2
0.789 / 0.804; exact maximum word-four-gram overlap means are 0.020 / 0.027. These are descriptive automated
proxies, not human novelty scores or evidence of a creativity effect. At that historical checkpoint the 48M grid
had eleven of 24 cells complete and the exact-overlap audit had 37 cells / 11,840 generations. Learned-position
frequency 500 was then active; see the current continuation entry below for completion.

## 2026-10-12 continuation: learned-position frequency 500 complete

The learned-position frequency-500 48M cell completed 6,000 updates. It started at 18:30:10 on 2026-10-11
and finished at 02:21:05 on 2026-10-12 (7h50m55s setup-to-done); the trainer summary reports 28,224.9 seconds,
best validation loss 1.5199076 / PPL 4.57, 36 gradient-norm spikes, and five gradient-health alerts. Retained
`best.pt` and `final.pt` loaded with `weights_only=True`. Memorization (12 rows), novelty (32 groups / 320
completions), and full-corpus overlap (32 groups / 320 completions) outputs passed validation; the overlap
fingerprint matched the frequency-500 corpus (73,139 stories). Rolling step checkpoints were removed after checks.

MHA frequency 0 completed 6,000 updates. It started at 02:35:21 and finished at 11:26:03 local on 2026-10-12
(8h50m42s setup-to-done; 31,815.7 trainer seconds), best validation loss 1.4977827 / PPL 4.47, with four
gradient-norm spikes and four gradient-health alerts. The retained best/final checkpoints loaded successfully;
memorization, novelty, and frequency-0 full-corpus overlap outputs passed independent shape and corpus-fingerprint
checks. Exact-overlap coverage now stands at 39 cells / 12,480 generations. MHA frequency 1 is the active cell,
with 11 queued; at the initial post-completion check around 11:26 it had only initialized and recorded its
untrained step-0 baseline. About 8.0 GiB was free at that earlier check. Scale results remain single-seed automated measurements; human annotation
and the separate contamination-free confirmation are not complete.

### MHA frequency-1 progress check

At 14:31:38 local on 2026-10-12, the active 48M MHA frequency-1 cell reached step 2,625/6,000 (loss 1.6718)
at about 2,023 tokens/s, with an early ETA of 3h47m. Step-2,500 validation loss was 1.7090 (new best). Six
gradient-health alerts have been logged so far: three at step 25 for blocks 6-8 and three at step 50 for blocks
5-7; no gradient-norm spikes were logged. The MHA frequency-0 cell remains independently verified as
completed; the matrix is still 13/24 complete, with 11 cells queued, and full-corpus overlap coverage is 39
cells / 12,480 generations. Disk free was about 8.7 GiB. This is a progress snapshot, not a completion estimate.
