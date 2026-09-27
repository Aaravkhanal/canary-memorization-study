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

## Not yet checked

The other half of Checkpoint 4 — "higher-frequency canaries should show higher exposure... than 1x or unseen" —
needs an actual canary-trained model, which the queued smoke test (`configs/training/baseline/freq_1.yaml`) will
produce. This note covers only the negative control; Checkpoint 4 isn't closed until the positive side is checked
too.
