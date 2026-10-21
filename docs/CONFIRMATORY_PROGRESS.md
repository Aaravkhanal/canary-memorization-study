# Confirmatory experiment progress ledger

Last updated: 2026-10-21 19:07 Asia/Kolkata.

This is an operational ledger, not a results narrative. It records completion, artifact production, and validation
without interpreting confirmatory outcomes before the frozen grid is complete. Add an entry after every completed
training/evaluation cell and after every research test-suite run.

## Current status

- Completed cells: **21/24 (87.5%)**.
- 14M grid: **12/12 complete and evaluated**.
- 48M grid: **9/12 complete and evaluated**.
- Active cell: none; the sequential queue stopped cleanly before `48m/learned_pos/seed_20261018`.
- Cells remaining: **3**.
- Latest storage preflight: failed with approximately 14 GiB free after the completed baseline cell; the frozen
  25-GiB threshold prevents the next cell from starting.
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
| 48M | learned_pos | 20261018 | queued | pending | pending |
| 48M | mha | 20261018 | queued | pending | pending |
| 48M | layernorm | 20261018 | queued | pending | pending |

## Test ledger

| Date | Scope | Result | Notes |
|---|---|---|---|
| 2026-10-17 | Full research suite | 115 passed | Last committed full-suite run; IEEE LaTeX manuscript also compiled successfully. |
| 2026-10-21 | Completed confirmatory result inventory | 42/42 JSON files present | Twenty-one raw and twenty-one evaluated files; no outcome interpretation performed. |

The full suite will be run again after the 24-cell grid and frozen analysis are complete. Running it concurrently
with MPS training is intentionally avoided to reduce memory pressure and protect the active experiment.

## Remaining completion gates

1. Restore at least 25 GiB free storage, then finish and evaluate the three remaining 48M cells.
2. Verify all checkpoint, JSON, corpus, runtime, and failure records.
3. Run the frozen confirmatory statistics and regenerate final trade-off tables and plots.
4. Build the complete condition-hidden annotation sheets with blank labels.
5. Resolve external-rater institutional, consent, compensation, withdrawal, and annotation clearances.
6. Collect two independent external-rater sheets; keep self-annotation as a separate sensitivity analysis.
7. Run the full test suite and full-cell clean-room reproduction.
8. Update the manuscript and release documentation, select an authorized license, and create a permanent archive/DOI.
