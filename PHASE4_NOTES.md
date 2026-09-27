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
the identical recipe. Queued to run next; its memorization score will be the true baseline for every lift
calculation from here on, including recomputing this frequency-1 result once it exists.

## Not yet checked

The full positive-control half of Checkpoint 4 ("higher-frequency canaries should show higher exposure than 1x or
unseen") needs more than one frequency trained — frequency 1 alone can't show a dose-response trend. Frequencies
10, 100 and 500 are still queued. The proper baseline-relative version of even this frequency-1 result is pending
the `freq_0` control run above.
