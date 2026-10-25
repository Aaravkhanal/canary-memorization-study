# Memorization vs. compositional creativity: canary study

Does a small language model trade off memorizing recurring narrative elements against recombining them into novel
stories, and does the trade-off shift with architecture? This project measures it with planted "canaries" at
controlled insertion frequencies, following Carlini et al. 2019's exposure methodology, adapted to a
narrative-generation setting.

The motivating question is whether controlled exposure to recurring narrative elements changes recall or
human-rated recombination in generated stories. Exposure/extraction, whole-corpus copying diagnostics, and blinded
human judgments are distinct measures; no memorization–creativity trade-off is assumed. Lexical diversity alone
is never treated as creativity.

**Status (verified 2026-10-25): the exploratory balanced four-architecture 14M grid and matched 24-cell 48M
scale-transfer grid are complete. The separate contamination-free confirmatory grid is also complete and
evaluated (24/24 cells: 14M 12/12; 48M 12/12). The frozen exposure-only model has been run, and all three
condition-hidden annotation sheets were generated with 7,680 blank rows each. The frozen exposure model estimated
1.223 exposure bits per log10 frequency decade (95% CI 0.691 to 1.755; 960 observations, 40 canary clusters);
the three architecture-by-frequency interactions were not significant after the registered Holm correction. These
are exposure results only, not evidence about human-rated novelty or a memorization–creativity trade-off. Human
novelty analysis remains blocked until external-rater clearance, independent labels, and adjudication actually
exist. A fresh GitHub clone also passed the CPU-only corpus/build/training smoke test on 2026-10-25; independent
full-cell clean-room reproduction remains incomplete because the available artifact filesystem does not have the
25-GiB free-space margin required before every cell of a second full run. A second fresh clone rebuilt all three
locked seed corpora and reproduced the frozen exposure-analysis CSV/JSON byte-for-byte; this was not a second
24-cell training run.**
The baseline 100x/500x second-training-seed replications are also complete. All 53 retained experiment summaries
report 6,000 updates. The final 48M cell (LayerNorm, frequency 500) completed at 21:34:48 local on 2026-10-15
(24,087 trainer seconds; best validation loss 1.4781 / PPL 4.3847). Its best/final checkpoints and all evaluations
passed validation. Across the 14M canonical grid, two true baseline seed replications, and all 24 48M cells, exact
full-corpus overlap covers 50 exploratory evaluated cells / 16,000 generations. The separate 24-cell confirmatory
grid adds 7,680 completions with matching training-split overlap checks (74 cells / 23,680 generations overall).
The final exploratory integrity pass loaded all 106 retained
best/final checkpoints, parsed all 175 result JSON files, checked all 50 full-corpus outputs against the matching
frequency corpus hash and 73,139-story count, and regenerated matched-baseline tradeoff tables/plots. The initial
48M baseline frequency-0 attempt did fail during a checkpoint write, then resumed from its verified step-1,000
checkpoint and completed; the failure remains in the runtime audit. The manuscript remains provisional, not
submission-ready: the primary human V/T/N novelty endpoint and full clean-room/release work remain incomplete.
All exploratory 48M cells are single-seed and use a different learning rate from the 14M arm, so those results
do not establish a creativity trade-off. See
`PLAN.md` for the phase-by-phase brief this project follows, `PHASE4_NOTES.md` for the detailed running lab
notebook, and `docs/DRAFT_PAPER.md` for the write-up structured for eventual publication, kept in sync as results
come in.
Per-run durations, checkpoint validation, and failure records are summarized in `results/trainer_runtime_audit.md`.

## What the completed exploratory runs support

1. **Exposure is canary- and frequency-dependent.** Several clean canaries show larger exposure lifts at higher
   insertion frequencies, but there are also controls, ceiling effects, plateaus, reversals, and substantial
   canary-level differences between the two baseline training seeds. This is descriptive evidence, not a
   population dose-response estimate. See [`docs/RESULTS_CLAIM_AUDIT.md`](docs/RESULTS_CLAIM_AUDIT.md).
2. **Three canary identities were already present in the base corpus:** `char_pip` ("Pip"), `plot_key` ("a shiny
   key"), and `plot_voice` ("a soft voice") occur 41–150 times before the study insertions. Their exposure is
   confounded by pre-existing corpus familiarity; future canaries should be screened before protocol lock.
3. **Two matched baseline training seeds show sensitivity, not a noise band.** At frequencies 1, 10, 100, and 500,
   the clean-canary mean-lift changes are −0.588, +0.564, −0.636, and −0.436, respectively; largest individual
   canary changes range from 1.862 to 3.044 exposure units. Two seeds cannot calibrate population uncertainty.
4. **Teacher-forced argmax extraction was 0/120 in the audited scope** (baseline and learned-position architectures
   at five nonzero frequencies). This bounded negative result does not generalize to every model or decoder.
5. **All 24 48M scale-transfer cells have completed**, but the arm is single-seed, uses a different learning rate,
   and reuses the exploratory canary bank. Its automated outcomes are descriptive; they do not establish a causal
   size effect or creativity trade-off.

Across the canonical 14M grid, two baseline seed controls, and the 48M grid, matching-corpus exact four-gram
overlap was evaluated for 50 cells / 16,000 generations. It is a copying diagnostic, not a semantic originality
measure. The blinded annotation sheets are prepared but still contain zero human labels. The separate
contamination-free confirmatory training, automated evaluation, and frozen exposure analysis are complete. The
primary human novelty endpoint is still blank. Accordingly, no memorization-versus-creativity trade-off has been
established.

## What's not done, and why

- **Phase 5 blinded human annotation** is the single largest remaining gap. Two condition-hidden CSVs, 1,280 rows
  each, are prepared, but all label/confidence/notes fields are blank. The scoring code reports agreement and
  condition summaries only after complete labels and adjudication; no automated labels are treated as evidence.
- **Full-corpus copying analysis** is implemented in `scripts/eval_full_corpus_overlap.py`. It has been run for
  all 24 canonical 14M novelty cells (7,680 completions), both baseline training-seed replications (640
  completions), and all 24 48M cells (7,680 completions), using each matching
  frequency-specific training corpus. Per-completion outputs, corpus hashes,
  and descriptive summaries are in
  `results/full_corpus_overlap/`. This automated overlap diagnostic is not a substitute for blinded human
  novelty labels and cannot by itself support a creativity claim.
- Baseline 100x/500x training-seed replications are complete. The 48M arm has all 24 cells verified, each with
  memorization, novelty, and matching-corpus overlap evaluations. The initial 48M baseline frequency-0 attempt had
  a disk-full checkpoint-write failure and resumed from its verified step-1,000 state.
- **The contamination-free confirmatory computational grid is complete:** 24/24 cells across three seeds, four
  architectures, and two scales trained and passed the locked automated evaluation. The frozen exposure table and
  exposure-only analysis are versioned, and the two external-rater sheets plus separate self-sensitivity sheet
  contain blank labels. External recruitment and annotation remain blocked on ethics/consent clearance. Licensing and a
  permanent archive remain release-only gates; the fresh-clone engineering smoke test has passed. See
  `docs/CONFIRMATORY_STUDY_PROTOCOL.md`.
- **48M scale-transfer arm:** all 24 matched-token configs (four near-matched architectures × six corpus conditions)
  are complete and verified. The baseline/frequency-0 cell initially failed at step 1,500 during a checkpoint write,
  then resumed from the intact step-1,000 state and completed 6,000 steps (best validation loss 1.4871). All cells
  have memorization, novelty, and matching-corpus overlap evaluations. These train fresh 48M models on this
  repository's canary corpora;
  the existing MY-LLM 48M checkpoint
  used different data and a fivefold token budget, so it is not a causal canary result. Protocol and runtime
  expectations are documented in `docs/SCALE_48M_PROTOCOL.md`.

## Compute discipline

This design needs a **fresh pretraining run from scratch per (architecture, frequency) cell** — memorization has
to be attributed to a controlled number of training-time exposures, not to fine-tuning an already-trained model.
On this machine (a MacBook Air M3, 8 GB, no external GPU), a 14M run uses 49.152M training tokens and currently
takes roughly 2.5-3 hours at observed throughput. The source training split itself is 14.58M tokens.
Canary training and the sibling `aarav-lm` project's own training are not run concurrently on this single
machine. The locked confirmatory queue is complete and no training job is active. A second full-cell clean-room
reproduction has not started: the protocol requires at least 25 GiB free on the artifact filesystem before every
cell, and available local space is only about 27 GiB before any duplicate run. Human annotation remains blocked on
the external-rater institutional determination, finalized consent, compensation, withdrawal, and annotation
clearances.

## Reproduce Phase 1 (canary corpus construction)

```bash
cd canary-memorization-study
python scripts/prepare_canary_corpus.py --config configs/canaries.yaml --base data/raw/base.txt --freq 1
# ... one call per frequency; each writes data/processed/freq_<F>/corpus.txt + manifest.json
python scripts/check_canary_novelty.py   # required pre-registration check: every canary identity vs. the base corpus
```

## Phase 2 — architecture variants

`scripts/make_variant_configs.py` builds and validates every variant against the running model code (parameter
counts checked with `aarav_lm.model.core.AaravLM`, configs validated by loading them through `aarav_lm`'s own
`ExperimentConfig.from_yaml`):

| Variant | Change from baseline | Parameters | vs. baseline |
|---|---|---|---|
| baseline | — (aarav-lm's `small` preset: RoPE, GQA n_kv_head=2, RMSNorm, SwiGLU, 8 layers) | 14,162,304 | — |
| A: learned positions | `arch: gpt2` only | 14,358,912 | +1.4% (entirely the new position table; the transformer body is identical) |
| B: MHA | `n_kv_head: 6`, `n_layer: 7` to compensate | 13,964,928 | -1.4% |
| C: LayerNorm | `norm_type: layernorm` only | 14,162,304 | exact match |

## Phase 3 — training (balanced 14M grid and 48M scale arm complete)

All four architectures have been trained from scratch at frequencies 0, 1, 10, 100, and 500; MHA and LayerNorm
also include the originally pre-registered frequency 50. Baseline and learned-position frequency 50 completed on
2026-10-07. Baseline seed 1338 is complete at 0, 1, 10, 100, and 500. Every run uses 6,000 steps, 49.152M
training tokens over approximately 3.37 passes through the 14.58M-token train split, and the same tokenizer and
schedule within this 14M arm; the matched comparisons change only the declared
architecture or frequency axis. This is 49.152M training tokens per run (6,000 × 8,192 tokens), not 14.6M tokens.

## Phase 4 — memorization (complete for every trained checkpoint)

`scripts/eval_memorization.py` computes exposure (Carlini et al.'s rank-based metric against a curated reference
set) and two extraction tests: a free-generation check, and a corrected, teacher-forced, per-token argmax check
(`argmax_match`) that's well-defined and independently checkable per canary regardless of prompt-sharing. Results:
`results/mem_<architecture>_freq<F>.json` (second-seed results: `..._freq<F>_seed<S>.json`).

## Phase 5 — novelty (generation/proxies run; primary human endpoint not done)

`scripts/eval_novelty.py` generates completions in unseen settings and scores self-BLEU / distinct-n diversity,
and can prepare a hand-labelling batch (`--label-batch`) for the brief's actual three-way classification. Results:
`results/novelty_<architecture>_freq<F>.json`. Use the blinded CSV workflow in `docs/ANNOTATION_PROTOCOL.md`, not
the legacy condition-revealing text batches. `scripts/eval_full_corpus_overlap.py` performs exact maximum
four-gram overlap against every story in the actual training corpus.

## Phase 6 — analysis and plotting

`scripts/analyze_tradeoff.py` builds the memorization-vs-novelty table and plot across the full grid, with a
`--canaries` filter to exclude the three base-corpus-contaminated canaries from the average (since their lift is
mechanically ≈0 regardless of exposure, for reasons unrelated to training). Outputs: `results/tradeoff.csv`/`.png`
(all 8 canaries), `results/tradeoff_clean.csv`/`.png` (5 uncontaminated canaries). Per the brief's own ground rule,
these are plots and tables only — no prose conclusion is drawn in the outputs themselves.

## Tests

118 tests (`pytest tests/`) cover corpus construction, confirmatory split hygiene/configs/data acquisition,
frozen inferential and outcome-evaluation models, blinded-batch construction, and storage/start-gate safety,
exposure/extraction, novelty metrics, full-corpus overlap,
blinded annotation/scoring, trade-off analysis, artifact-manifest integrity, seed sensitivity, and 48M
config/parameter validation. The complete suite passed on 2026-10-25 after correcting a stale release-gate test
that incorrectly treated completed confirmatory training as a blocker. The IEEE LaTeX manuscript compiled
successfully in the desktop editor on 2026-10-25 after the confirmatory results were added.

## Publication documents

- `docs/PUBLICATION_READINESS.md`: candid submission gate, venue strategy, IEEE policy requirements, and safe
  résumé wording.
- `docs/CONFIRMATORY_STUDY_PROTOCOL.md`: contamination-free, mixed-frequency, multi-seed confirmatory design.
- `docs/CONFIRMATORY_EXECUTION_PLAN.md`: gated two-scale execution plan, measured duration, storage needs, and
  current blockers.
- `docs/CONFIRMATORY_PROGRESS.md`: living cell-by-cell and test-run ledger; updated after each completed
  confirmatory experiment/evaluation and research test run without interpreting partial outcomes.
- `docs/STORAGE_AND_RECOVERY_PLAN.md`: 25-GiB capacity gate, artifact retention, interruption recovery, and
  checkpoint verification rules.
- `docs/DISK_CAPACITY_AUDIT.md`: read-only inventory of large local paths and safe owner-directed storage options;
  no historical artifact was removed.
- `docs/ETHICS_AND_CONSENT_PLAN.md`: two explicit annotation routes, their evidentiary tradeoffs, and the owner or
  institutional decisions still required; the companion external-rater consent document is a draft only.
- `docs/RESULTS_CLAIM_AUDIT.md`: evidence map and allowed/prohibited result wording.
- `docs/ARTIFACT_REPRODUCIBILITY.md`: exact reproduction commands and data/weights availability limits.
- `docs/DATA_RIGHTS_AND_RELEASE.md`: revision-pinned TinyStories provenance, license record, and release decisions.
- `CITATION.cff`: conservative citation metadata with no invented DOI, release date, license, affiliation, or
  ORCID; complete those fields only at an authorized release.
- `artifacts/tokenizer_tinystories_v2/`: exact 4,096-token BPE artifact and provenance note for clean clones.
- `results/clean_room_smoke.json`: passed fresh-clone engineering smoke record (CPU-only, not a study outcome).
- `configs/confirmatory/analysis_plan.json`: frozen exposure/novelty formulas, contrasts, correction, and fallback.
- `configs/confirmatory/evaluation_plan.json`: frozen 1,025-candidate exposure, 4 × 2 generation, extraction, and
  exact training-split overlap settings.
- `scripts/check_confirmatory_start_gate.py`: non-outcome preflight; the computational-training gates currently
  pass, while the separate annotation gate correctly remains closed pending the external-rater institutional
  determination and finalized consent, compensation, and withdrawal materials.
- `scripts/run_confirmatory_queue.py`: portable, globally locked sequential 14M-then-48M runner; it cannot train
  until the preflight passes.
- `scripts/prepare_confirmatory_annotation.py`: refuses partial grids and produces two independently shuffled
  external-rater sheets plus one separate self-sensitivity sheet, each condition-hidden with 7,680 rows and blank
  annotation fields, along with a git-ignored private key.
- `scripts/create_artifact_manifest.py`: machine-readable SHA-256 inventory for versioned artifacts.
- `scripts/check_release_gate.py`: separate machine-readable release audit; it fails safely until licensing,
  confirmation, annotation, full-cell clean-room reproduction, permanent archival, and DOI evidence truly exist.
- `docs/SCALE_48M_PROTOCOL.md`: matched-token 48M scale-transfer experiment and limitations.
- `docs/ANNOTATION_PROTOCOL.md`: blinded two-rater labelling and adjudication procedure.
- `docs/REFERENCES.bib`: verified core references from USENIX, ACL Anthology, and OpenReview; expand before submission.
- `docs/DRAFT_PAPER.md`: living manuscript; exploratory claims remain provisional until the gates above pass.
