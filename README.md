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

## Not started

Phases 2-6 (architecture variants, training grid, memorization eval, novelty eval, analysis) per `PLAN.md`,
pending your review of this checkpoint and a decision on the reduced-vs-full grid above.
