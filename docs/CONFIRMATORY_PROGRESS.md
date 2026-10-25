# Confirmatory experiment progress ledger

Last updated: 2026-10-25 Asia/Kolkata.

This is an operational ledger, not a results narrative. It records completion, artifact production, and validation
without conflating exposure outcomes with the pending human novelty endpoint. Add an entry after every completed
training/evaluation cell and after every research test-suite run.

## Current status

- Completed cells: **24/24 (100%)**.
- 14M grid: **12/12 complete and evaluated**.
- 48M grid: **12/12 complete and evaluated**.
- Active cell: none; the locked sequential training/evaluation queue is complete.
- Cells remaining: **0**.
- Latest storage read: 28,999,987,200 bytes free on the artifact filesystem (about 27 GiB). This is above the
  frozen 25-GiB per-cell threshold but leaves too little headroom to complete another full 24-cell retained run.
  No external artifact filesystem is configured or validated.
- The complete 24-cell grid, locked automated evaluations, checkpoint/corpus inventory, and exposure-only frozen
  analysis are complete. Human-novelty and joint trade-off interpretation remain locked pending cleared external
  ratings and adjudication.
- Frozen exposure-only estimate: +1.223 exposure bits per log10 insertion-frequency decade (95% CI 0.691–1.755;
  960 observations / 40 canary clusters); no architecture-by-frequency interaction survived the registered
  Holm correction. This is not a human-novelty or creativity result.
- Human annotation is not started. External-rater institutional determination, finalized consent, compensation,
  withdrawal, and annotation clearance remain unresolved.

## Cell ledger

`raw` means the locked evaluator wrote the exposure and generation record. `evaluated` means the matching-corpus
full-overlap augmentation also completed. Values below deliberately report artifact state, not outcome estimates.

| Scale | Architecture | Seed | Training | Raw JSON | Evaluated JSON |
|---|---|---:|---|---|---|
| 14M | baseline | 20261016 | complete | present | present |
| 14M | baseline | 20261017 | complete | present | present |
| 14M | baseline | 20261018 | complete | present | present |
| 14M | learned_pos | 20261016 | complete | present | present |
| 14M | learned_pos | 20261017 | complete | present | present |
| 14M | learned_pos | 20261018 | complete | present | present |
| 14M | mha | 20261016 | complete | present | present |
| 14M | mha | 20261017 | complete | present | present |
| 14M | mha | 20261018 | complete | present | present |
| 14M | layernorm | 20261016 | complete | present | present |
| 14M | layernorm | 20261017 | complete | present | present |
| 14M | layernorm | 20261018 | complete | present | present |
| 48M | baseline | 20261016 | complete | present | present |
| 48M | learned_pos | 20261016 | complete | present | present |
| 48M | mha | 20261016 | complete | present | present |
| 48M | layernorm | 20261016 | complete | present | present |
| 48M | baseline | 20261017 | complete | present | present |
| 48M | learned_pos | 20261017 | complete | present | present |
| 48M | mha | 20261017 | complete | present | present |
| 48M | layernorm | 20261017 | complete | present | present |
| 48M | baseline | 20261018 | complete | present | present |
| 48M | learned_pos | 20261018 | complete | present | present |
| 48M | mha | 20261018 | complete | present | present |
| 48M | layernorm | 20261018 | complete | present | present |

## Test ledger

| Date | Scope | Result | Notes |
|---|---|---|---|
| 2026-10-17 | Full research suite | 115 passed | Last committed full-suite run; IEEE LaTeX manuscript also compiled successfully. |
| 2026-10-22 | Completed confirmatory result inventory | 48/48 JSON files present | Twenty-four raw and twenty-four evaluated files. |
| 2026-10-22 | Condition-hidden annotation package | 3 × 7,680 blank rows | Two independently shuffled external-rater sheets and one separate self-sensitivity sheet; private key remains ignored and undistributed. |
| 2026-10-22 | Full research suite | 118 passed | Run after the complete grid and exposure-only frozen analysis. |
| 2026-10-25 | Fresh-clone engineering smoke | Passed | Current GitHub clone at `02b01faa`; pinned data, corpus, tokenizer, and dependency checks passed; one CPU-only 14M step, zero MPS use, no scientific outcome. |
| 2026-10-25 | Full research suite, first run | 117 passed, 1 failed | The failing test still expected completed confirmatory training to appear as a release blocker; corrected the stale assertion to follow the machine-readable gate. |
| 2026-10-25 | Full research suite, after test correction | 118 passed | Re-run after updating `tests/test_release_gate.py`; warnings are from Matplotlib/PyParsing deprecations. |
| 2026-10-25 | Full research suite, after portable exposure provenance | 118 passed | Includes relative result paths, stable LF output, current release-gate expectations, and fresh-clone record tests. |
| 2026-10-25 | Confirmatory artifact integrity audit | Passed | 24/24 complete cells; deserialized and SHA-256-verified 48 best/final checkpoints; verified raw/evaluated JSON provenance, corpus hashes, row/group/completion counts, and overlap flags. The single pre-checkpoint interruption is retained as documented in Amendment 8. |
| 2026-10-25 | Fresh-clone rebuild at `fdec41e7` | Passed | Rebuilt all three locked seed corpora, checked pinned data/tokenizer/training dependency, and regenerated exposure CSV/JSON byte-identically; one-step CPU smoke passed with zero MPS use. Full 24-cell training was not repeated. |
| 2026-10-25 | Full research suite after final fresh-clone verification record | 118 passed | Includes the three-corpus and byte-identical exposure analysis run-record checks; 14 dependency deprecation warnings only. |
| 2026-10-25 | Full research suite after manuscript and storage-status refresh | 118 passed | Includes the latest result wording, exact second-grid capacity decision, and updated artifact manifest; only 14 Matplotlib/PyParsing deprecation warnings. |
| 2026-10-25 | Second full-grid storage preflight | Deferred before training | 28,217,565,184 bytes free (26.28 GiB), only 1.28 GiB above the 25-GiB threshold; the frozen estimate is 8,153,726,976 retained bytes plus the required reserve. No separate validated artifact volume is available, so the full independent 24-cell run was not launched and no checkpoint was touched. |
| 2026-10-25 | Manuscript refresh | Passed | Updated title and results interpretation to distinguish the completed exposure finding from the unmeasured human novelty endpoint; built-in LaTeX compilation succeeded. |

The full suite passed after the 24-cell grid, exposure-table build, exposure-only frozen analysis, and blank
annotation-package build completed.

## Remaining completion gates

1. Full-cell clean-room reproduction remains outstanding. The fresh-clone CPU smoke passed, but the 25-GiB free-space requirement cannot be maintained for a second full 24-cell run on the currently available local filesystem; no validated external artifact path exists.
2. Resolve external-rater institutional, consent, compensation, withdrawal, and annotation clearances.
3. Collect two independent external-rater sheets; keep self-annotation as a separate sensitivity analysis.
4. Adjudicate the primary labels and run the frozen human-novelty model and final joint trade-off reporting.
5. Complete the manuscript and release documentation, select an authorized license, and create a permanent archive/DOI.
