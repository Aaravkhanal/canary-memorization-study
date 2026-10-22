# Confirmatory experiment progress ledger

Last updated: 2026-10-22 18:25 Asia/Kolkata.

This is an operational ledger, not a results narrative. It records completion, artifact production, and validation
without interpreting confirmatory outcomes before the frozen grid is complete. Add an entry after every completed
training/evaluation cell and after every research test-suite run.

## Current status

- Completed cells: **24/24 (100%)**.
- 14M grid: **12/12 complete and evaluated**.
- 48M grid: **12/12 complete and evaluated**.
- Active cell: none; the locked sequential training/evaluation queue is complete.
- Cells remaining: **0**.
- Latest storage preflight: passed above the frozen 25-GiB threshold after clearing only regenerable caches; no
  research artifacts or unrelated user files were removed.
- Confirmatory interpretation remains locked until the complete grid, frozen analysis, and artifact checks finish.
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

The full suite passed after the 24-cell grid, exposure-table build, exposure-only frozen analysis, and blank
annotation-package build completed.

## Remaining completion gates

1. Verify the complete checkpoint/runtime inventory and perform full-cell clean-room reproduction.
2. Resolve external-rater institutional, consent, compensation, withdrawal, and annotation clearances.
3. Collect two independent external-rater sheets; keep self-annotation as a separate sensitivity analysis.
4. Adjudicate the primary labels and run the frozen human-novelty model and final joint trade-off reporting.
5. Complete the manuscript and release documentation, select an authorized license, and create a permanent archive/DOI.
