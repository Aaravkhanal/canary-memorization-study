# Memorization vs. compositional creativity: canary study

Does a small language model trade off memorizing recurring narrative elements against recombining them into novel
stories, and does the trade-off shift with architecture? This project measures it with planted "canaries" at
controlled insertion frequencies, following Carlini et al. 2019's exposure methodology.

**Status: Phase 1 only (data preparation).** Nothing has been trained. See `PLAN.md` for the phase-by-phase brief
this project follows and the checkpoint this delivers.

## Compute cost — read before running Phase 3

This design needs a **fresh pretraining run from scratch per (architecture variant, frequency level) cell**, because
memorization has to be attributed to a controlled number of exposures during training, not to fine-tuning an
already-trained model. Measured on this machine (a MacBook Air M3, 8 GB, no external GPU) for a model this size:

| Run | Tokens | Wall time | Where measured |
|---|---|---|---|
| Pretrain from scratch | 90M | 4.1 h | `aarav-lm` exp_004 |
| Continued pretrain | 147M | 7.7 h | `aarav-lm` exp_010 |

**The brief as written** (up to 8 architecture variants x 5 frequency levels = 40 runs) would take roughly
**160 hours (6-7 days)** of continuous single-machine compute at the cheaper rate, before Phases 4-6.

**What this project sets up instead, pending your decision:** a reduced first pass — one architecture axis at a
time (baseline + one swap = 2 configs) x 4 frequency levels, at a smaller per-run token budget (~20-30M tokens,
roughly 1-1.5 h each) — about **12-18 hours** total, doable as an overnight-plus-a-day run. Scale up from there
once the trade-off curve is visible on the reduced grid.

**A cheaper alternative worth considering:** the classic Carlini et al. design inserts every canary at its *own*
frequency into **one** corpus, then ranks each canary's exposure within a single trained model — no need to retrain
per frequency level at all. That cuts the grid from `variants x frequencies` runs to just `variants` runs (5x
fewer). This project's injection script supports the brief's literal "one frequency per corpus variant" design
(implemented, below) and could be extended to the mixed-frequency design in an hour or two if you'd rather run that
instead. Flagging it now, not switching silently, per the brief's own instruction.

## What's built (Phase 1)

- `configs/canaries.yaml` — the pre-registered canary bank: 4 character canaries, 4 plot-fragment canaries, 2
  unseen controls of each type (never inserted, for baseline comparison), and a near-duplicate paraphrase of every
  inserted canary (for later novelty evaluation). Frequencies: 1, 10, 50, 100, 500. **Locked**: the script refuses
  to regenerate `configs/canary_assignment.json` once it exists, so the assignment of which template stories carry
  which canary cannot silently drift between runs.
- `scripts/prepare_canary_corpus.py` — builds one corpus variant per frequency level. Insertion pools are nested
  (the 500x pool's first 100 stories are exactly the 100x pool, etc.), so frequency is the only thing that changes
  between a variant's corpora, and disjoint across canaries (no story carries two canaries).
- `data/raw/base.txt` — symlink to `aarav-lm`'s 60 MB TinyStories slice (73,139 stories), reused rather than
  re-downloaded.

## A bug found and fixed while building this

The first draft of the plot-fragment splice hardcoded `", and " + canary_text`. One of the four plot-fragment
canaries (`plot_song`) already starts with "and", so it produced "...felt sad, **and and** heard a strange song
coming from the well." Fixed by dropping the hardcoded connector — each canary text already carries its own
(then/and/before/until), so the splice adds only a comma. `tests/test_prepare_canary_corpus.py` (12 tests) locks
this in, including a regression test for the exact failure mode, and a full sweep confirms every one of the 8
canaries appears exactly as many times as its frequency level says, in all 5 built corpora.

## Reproduce Phase 1

```bash
cd canary-memorization-study
python scripts/prepare_canary_corpus.py --config configs/canaries.yaml --base data/raw/base.txt --freq 1
python scripts/prepare_canary_corpus.py --config configs/canaries.yaml --base data/raw/base.txt --freq 500
# ... one call per frequency in configs/canaries.yaml; each writes data/processed/freq_<F>/corpus.txt + manifest.json
```

## Phase 2 — architecture variants

`scripts/make_variant_configs.py` builds and validates every variant against the running model code (parameter
counts checked with `aarav_lm.model.core.AaravLM`, configs validated by loading them through `aarav_lm`'s own
`ExperimentConfig.from_yaml`, not a hand-rolled parser):

| Variant | Change from baseline | Parameters | vs. baseline |
|---|---|---|---|
| baseline | — (aarav-lm's `small` preset: RoPE, GQA n_kv_head=2, RMSNorm, SwiGLU, 8 layers) | 14,162,304 | — |
| A: learned positions | `arch: gpt2` only | 14,358,912 | +1.4% (entirely the new position table; the transformer body is identical, 12,589,440 either way) |
| B: MHA | `n_kv_head: 6` (every head its own K/V); `n_layer: 7` to compensate (at `n_layer: 8` this variant is +11.1%, too far off) | 13,964,928 | -1.4% |
| C: LayerNorm | `norm_type: layernorm` only | 14,162,304 | exact match |

18 training configs generated under `configs/training/<variant>/freq_<F>.yaml`, each pointing at this project's
own canary corpus and tokenizer, with training output kept under this project's `models/` (gitignored: run
outputs, not source). **Queued for the reduced first pass:** baseline and Variant A (learned positions) at
frequencies 1, 10, 100, 500 (50 dropped only to cut the first pass from 5 to 4 runs; still log-spaced with one
midpoint). Variant B and C configs are written for all 5 frequencies but not queued, pending review of the first
pass's trade-off curve.

## Phase 3 — training runs (in progress: the Checkpoint-3 smoke test)

The brief's Checkpoint 3 asks for one variant at one frequency, end to end, before scaling up. That run
(`baseline`, frequency 1, `configs/training/baseline/freq_1.yaml`, 6,000 steps / ~24.6M tokens, ~1-1.5h) is
**queued to start automatically once `aarav-lm`'s own exp_017 (context-extension training) finishes** — the two
must not run heavy training concurrently on this 8 GB machine; an earlier attempt at that in this same session
produced a near-total stall. A background watcher polls exp_017's process and launches the smoke test the moment
it exits; output goes to `/tmp/canary_smoke.log` and the run itself under `models/baseline/freq_1/`.

## Not started

Phases 4-6 (memorization eval, novelty eval, analysis) per `PLAN.md`, and the rest of Phase 3's reduced grid
(7 more runs: baseline x 3 more frequencies, Variant A x 4 frequencies), pending the smoke test's result.
