# Experiment Results Archive

**Verified snapshot: 2026-10-25.** This is a navigable summary of experiments completed so far and the claims their
results support. The result JSON/CSV files, runtime logs, checkpoint verification records, and locked protocol
remain the detailed sources of truth. This archive does not replace those artifacts and is not a license to delete
them.

## Completed experiment inventory

| Study arm | Completed work | What it supports |
|---|---|---|
| Exploratory 14M grid | 24 architecture-by-frequency cells, four near-parameter-matched architectures, six frequencies including zero-insertion controls, 6,000 updates per cell. Additional baseline training-seed sensitivity runs are recorded separately. | Descriptive exposure, extraction, and automated novelty-proxy results for the explored configurations; not a replicated factorial estimate of creativity. |
| Exploratory 48M scale-transfer grid | 24 cells, four architectures by six frequencies, 6,000 updates each; single seed and learning rate 5e-4 versus 8e-4 in the 14M exploratory arm. | Descriptive scale-transfer results only. The schedule difference and single seed preclude a causal model-size claim. |
| Baseline seed sensitivity | The paired-seed values and per-canary differences are in `results/seed_sensitivity_clean.csv`; per-run training details are in `results/trainer_runtime_audit.md`. | A sensitivity demonstration, not a variance estimate or statistical noise band. |
| Contamination-free confirmatory grid | 24/24 cells: three seeds × four architectures × two scales (12 at 14M and 12 at 48M). All completed the locked training budget and automated memorization, novelty-proxy, and matching-corpus overlap evaluations. | The registered computational endpoint and exposure-only analysis. Human novelty labels remain absent. |
| Confirmatory exposure model | 960 canary observations from 40 canary clusters, generated from the locked 24-cell grid. | A registered frequency–exposure association and architecture-interaction test, as detailed below. |

The artifact audits verified the 53 exploratory experiment summaries and their 106 retained best/final checkpoints,
plus the separate confirmatory grid's 48 best/final checkpoints. Confirmatory result provenance, corpus hashes,
row/group/completion counts, checkpoint loading, and overlap flags were checked. The one documented pre-checkpoint
interruption remains in the audit trail; it is not silently replaced or counted as a completed run.

## Findings that are currently supported

### Confirmatory exposure endpoint

- The grand-mean log10 insertion-frequency slope is **+1.223 exposure bits per decade** (SE 0.271; 95% cluster-
  robust CI 0.691–1.755; p=6.55×10⁻⁶).
- None of the three registered architecture-by-frequency interactions survives Holm correction: baseline estimate
  +0.0135 (adjusted p=1.0000), LayerNorm −0.0535 (adjusted p=0.7625), and learned positions +0.0340 (adjusted
  p=1.0000).
- The separately registered 14M scale contrast is +0.0821 (SE 0.0384; 95% CI 0.0069–0.1573; nominal p=0.0324).
  It is outside the architecture Holm family and should not be generalized into a broad scale effect.
- The registered non-ceiling sensitivity analysis uses 244 observations and estimates +2.290 exposure bits per
  decade (95% CI 1.823–2.758). It does not replace the all-observation primary model.

These results concern rank-based canary exposure only. They do **not** establish human novelty, a creativity cost,
or a memorization–creativity trade-off.

### Exploratory checks and limitations

- The exploratory baseline seed-sensitivity mean-lift differences at frequencies 1, 10, 100, and 500 are
  −0.588, +0.564, −0.636, and −0.436. Largest per-canary differences range from 1.862 to 3.044. Two seeds do not
  estimate a population variance or confidence band.
- Three selected canary identities were already present in the base corpus: `char_pip` (“Pip,” 150 occurrences),
  `plot_key` (“a shiny key,” 41), and `plot_voice` (“a soft voice,” 67). Clean-canary summaries exclude these as a
  sensitivity analysis; they remain in the audit record.
- Teacher-forced per-token argmax extraction was 0/120 in the audited baseline/learned-position subset at five
  nonzero frequencies. This does not generalize to other architectures, prompts, seeds, or decoding methods.
- Distinct-n and exact four-gram overlap are automated diagnostics, not semantic originality or human creativity
  measures. No consistent monotonic distinct-2 decline was established.
- Across the original exploratory designs, matching-corpus four-gram overlap covers 50 evaluated cells / 16,000
  generations. The confirmatory grid adds 24 cells / 7,680 generations: **74 evaluated cells / 23,680 generations**
  across the two designs.

## Human endpoint and release state

Three condition-hidden confirmatory sheets exist—two external-rater sheets and one separate self-sensitivity
sheet—with **7,680 blank rows each**. They contain no human labels. The self-sensitivity sheet must not be pooled
with the primary independent ratings. Institutional determination, finalized consent, compensation, withdrawal,
annotation clearances, ratings, and adjudication remain unresolved; no human novelty result is available.

The full independent 24-cell clean-room training reproduction is also outstanding. The latest capacity reading
was 26.28 GiB free, only 1.28 GiB above the frozen 25-GiB reserve, whereas the second grid's retained-artifact
estimate is 8,153,726,976 bytes. No separate validated artifact filesystem is configured. No second-grid cell was
started. A fresh-clone engineering check did rebuild all three locked corpora and the exposure CSV/JSON
byte-identically and pass one CPU-only training step; that is not full-cell reproduction.

Project/data/weight licensing decisions, redistribution rights, permanent archive, and DOI remain owner-controlled
release gates. No existing checkpoint, exploratory output, or unrelated file has been deleted to make room.

## Detailed source artifacts

- Confirmatory coefficients and model diagnostics: `results/confirmatory/exposure_analysis.json`.
- Portable exposure model input, with checkout-relative provenance paths: `results/confirmatory/exposure_analysis_input.csv`.
- 24-cell training/evaluation status and dated test record: `docs/CONFIRMATORY_PROGRESS.md`.
- Claim boundaries, source mappings, and prohibited interpretations: `docs/RESULTS_CLAIM_AUDIT.md`.
- Cell runtimes, failures, recovery, and exploratory checkpoint audit: `results/trainer_runtime_audit.md`.
- Confirmatory protocol and frozen inferential plan: `docs/CONFIRMATORY_STUDY_PROTOCOL.md` and `configs/confirmatory/analysis_plan.json`.
- Data and software reproduction steps and fresh-clone checks: `docs/ARTIFACT_REPRODUCIBILITY.md` and `results/clean_room_smoke.json`.
- Versioned artifact inventory: `results/artifact_manifest.json` (does not cover ignored checkpoints, corpora, or the private annotation key).

## Space-reclamation rule

Before deleting any research checkpoint, first decide which artifacts must be retained for peer review and recovery,
record and independently verify their hashes, secure any permitted archive, and obtain explicit approval naming the
exact paths. The existing best/final checkpoints and exploratory artifacts are preserved. The generated results
archive and artifact manifest preserve a readable summary and integrity references, but are not substitutes for
the underlying model files or a permanent external deposit.
