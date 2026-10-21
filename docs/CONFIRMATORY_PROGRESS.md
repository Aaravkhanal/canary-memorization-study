# Confirmatory experiment progress ledger

Last updated: 2026-10-22 03:17 Asia/Kolkata.

This is an operational ledger, not a results narrative. It records completion, artifact production, and validation
without interpreting confirmatory outcomes before the frozen grid is complete. Add an entry after every completed
training/evaluation cell and after every research test-suite run.

## Current status

- Completed cells: **22/24 (91.7%)**.
- 14M grid: **12/12 complete and evaluated**.
- 48M grid: **10/12 complete and evaluated**.
- Active cell: none; the sequential queue stopped cleanly before `48m/mha/seed_20261018`.
- Cells remaining: **2**.
- Latest storage preflight: failed just below the frozen 25-GiB threshold after the completed learned-position cell.
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
| 48M | mha | 20261018 | queued | pending | pending |
| 48M | layernorm | 20261018 | queued | pending | pending |

## Test ledger

| Date | Scope | Result | Notes |
|---|---|---|---|
| 2026-10-17 | Full research suite | 115 passed | Last committed full-suite run; IEEE LaTeX manuscript also compiled successfully. |
| 2026-10-22 | Completed confirmatory result inventory | 44/44 JSON files present | Twenty-two raw and twenty-two evaluated files; no outcome interpretation performed. |

The full suite will be run again after the 24-cell grid and frozen analysis are complete. Running it concurrently
with MPS training is intentionally avoided to reduce memory pressure and protect the active experiment.

## Remaining completion gates

1. Restore storage above the 25-GiB threshold, then finish and evaluate the two remaining 48M cells.
2. Verify all checkpoint, JSON, corpus, runtime, and failure records.
3. Run the frozen confirmatory statistics and regenerate final trade-off tables and plots.
4. Build the complete condition-hidden annotation sheets with blank labels.
5. Resolve external-rater institutional, consent, compensation, withdrawal, and annotation clearances.
6. Collect two independent external-rater sheets; keep self-annotation as a separate sensitivity analysis.
7. Run the full test suite and full-cell clean-room reproduction.
8. Update the manuscript and release documentation, select an authorized license, and create a permanent archive/DOI.
