# Confirmatory replication and clean-room execution plan

**Status (2026-10-22): all 24 locked training cells and automated evaluations are complete; the exposure-only
frozen analysis and blank condition-hidden annotation package are built. External-rater clearance, labels,
adjudication, the human-novelty model, full-cell clean-room reproduction, licensing, and archival remain open.** This plan turns
`CONFIRMATORY_STUDY_PROTOCOL.md` into an executable two-scale study without treating the existing exploratory
outcomes as confirmatory evidence.

## Locked design direction

Use the mixed-frequency design because it separates canary frequency within each trained model and is much more
compute-efficient than repeating the original frequency-specific grid. For each data/assignment seed, train all
four architectures on byte-identical data at both model scales:

- 3 training/data-assignment seeds × 4 architectures × 14M parameters = 12 runs;
- the same 3 seeds × 4 architectures × 48M parameters = 12 runs;
- 24 new runs total at the three-seed floor.

The power/precision simulation is a hard gate. If three seeds do not meet the predeclared target, increase to five
seeds before any outcomes are inspected. Five seeds would require 40 runs total. Use the same optimizer schedule
and learning-rate rule across scales, or freeze a justified scale-specific rule before training; the exploratory
14M/48M learning-rate mismatch must not be repeated silently.

## Execution phases

### Phase A — protocol and feasibility lock (estimated 4–8 hours)

- Generate a new 40-canary bank plus at least 8 controls and deterministic, target-disjoint 1,024-alternative
  reference pools.
- Screen every identity and reference alternative against normalized train/validation/test text before lock.
- Generate a counterbalanced identity-to-frequency schedule for seeds 20261016, 20261017, and 20261018.
- Implement and run the power/precision simulation; freeze the smallest effects of scientific interest, primary
  contrasts, model formulas, multiplicity correction, convergence fallback, and required seed count.
- Record data-rights and human-annotation ethics/consent determination.
- Verify storage/recovery capacity and freeze retention rules.

### Phase B — corpus/config lock (estimated 4–8 hours)

- Build one mixed-frequency corpus per seed with disjoint insertion story IDs.
- Prove canaries and alternatives are absent from every unmodified split and inserted identities occur only at
  their assigned training frequencies.
- Hash the base data, splits, bank, schedule, tokenizer, configs, code revision, and corpus outputs.
- Generate portable 14M and 48M configs for all planned cells and validate parameter counts and token budgets.
- Commit the complete pre-outcome lock before starting the first training cell.

### Phase C — three-seed 14M confirmation (estimated 30–36 training hours plus 3–5 evaluation hours)

- Run the 12 cells sequentially on MPS.
- After each cell, verify the summary and best checkpoint, run exposure/generation/full-corpus evaluation, record
  runtime/failures, then remove only verified rolling checkpoints according to the locked retention policy.

### Phase D — three-seed 48M confirmation (estimated 78–96 training hours plus 4–6 evaluation hours)

- Run the 12 cells sequentially after Phase C, using the same data assignments and frozen cross-scale recipe.
- Apply the same per-cell verification and recovery audit. Never overlap a 14M and 48M MPS job.

### Phase E — blinded human endpoint and confirmatory statistics (elapsed time depends on raters)

- Generate condition-hidden batches and keep the private key outside the public artifact.
- Collect two independent external V/T/N labels, resolve disagreements under the frozen procedure, and then run
  the locked inferential analyses. Collect the investigator's separately shuffled self-annotation sheet as a
  sensitivity analysis and never pool it with the primary endpoint. Automated labels are not substitutes.

### Phase F — clean-room reproduction and release (estimated 1–2 working days, partly parallel)

- Use the pinned environment and input lock to reproduce analysis from a fresh clone.
- Make all paths configurable, document authorized data acquisition, package tokenizer/checkpoint hashes, and run
  an analysis smoke test plus one reduced training smoke test in a temporary checkout.
- Add code/data/model licensing decisions, citation metadata, release notes, and a DOI deposit. A Zenodo release
  needs the repository owner to connect/authorize the account and create the final deposit.

## Measured schedule

At the observed local rates, the three-seed floor needs about **5–7 days of uninterrupted machine time** after
the gates pass. If power requires five seeds, budget **9–11 days**. These estimates assume the Mac remains awake,
connected to power, thermally stable, and no other MPS workload runs. Turning the laptop off pauses or terminates
local work; the runner must resume only from a verified checkpoint.

Repeating every original frequency-specific cell for two additional seeds would take roughly three weeks on this
machine and would still retain the old contamination problem. It is not the planned confirmation.

## Current blockers

| Gate | Current state | Required resolution |
|---|---|---|
| Free storage | Owner-authorized non-Desktop cleanup raised free space to about 26.4 GiB; the exact 25-GiB probe passes | Recheck before every cell. The margin is modest, so stop safely if rebuilt caches or new artifacts push free space below threshold. No research checkpoint was deleted. |
| Power/precision/statistics | 250-replicate simulation selects three seeds; executable formulas, contrasts, Holm family, ceiling sensitivity, label rule, and GEE fallback are frozen | Preserve the result and assumptions; any change requires a dated pre-outcome amendment. |
| Canary/schedule lock | 40 canaries, 8 controls, 2 × 1,024 alternatives, and five-seed schedule generated; zero matches in the full base corpus | Preserve content hash and verify the derived train/validation/test artifacts after corpus construction. |
| Data rights | Exact revision/file/byte range verified; upstream card declares CDLA-Sharing-1.0 | Owner must select project licenses and confirm redistribution terms before an external artifact release. |
| Ethics/consent | Owner-authorized computation is separated from human-participant work; two external primary raters plus a separate self-sensitivity sheet are selected, but no external determination or finalized consent is recorded | Computational training may proceed after all non-human gates pass. Recruitment and annotation remain prohibited until the applicable determination, consent, compensation, withdrawal, retention, and annotation clearance are recorded. |
| Execution/evaluation safety | Frozen raw evaluator, exact training-split overlap, blank blinded-batch builder, global sequential runner, resumability checks, 25-GiB capacity probe, and checkpoint/result verification are implemented | Preserve the committed workflow and hashes; do not substitute automated labels for the human endpoint. |
| Software/artifacts | Fresh-clone acquisition, deterministic build, tokenization, validation, and one-step CPU smoke pass | Full-cell reproduction, checkpoint release, owner-selected license, and DOI archive remain after training. |

No confirmatory training may start while any computational pre-outcome gate is open. Human annotation readiness
is reported separately and does not authorize recruitment. `scripts/check_confirmatory_start_gate.py` evaluates
the machine-readable training gate, corpus hashes, config count, committed lock, writable artifact filesystem,
and free space without inspecting outcomes. `scripts/run_confirmatory_queue.py` calls that checker and exits before
training unless every computational training gate passes.
