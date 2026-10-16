# Confirmatory storage, retention, and recovery plan

**Frozen pre-outcome record, 2026-10-17. Confirmatory training has not started.** The machine-readable values are
in `configs/confirmatory/storage_plan.json`. This plan applies only to the new 24-cell confirmatory queue and does
not authorize deletion of any exploratory artifact.

## Capacity gate

The queue requires **25 GiB free on the filesystem holding the confirmatory artifact root at launch**. The default
root is `models/confirmatory`; a separate path may be selected with `CONFIRMATORY_ARTIFACT_ROOT`. An external path
is accepted only after an atomic write/read/fsync/rename probe and a free-space check on that filesystem.

The retained-checkpoint estimate uses measured local file sizes: roughly 54 MiB each for 14M best/final and
184--185 MiB each for 48M best/final. Across 12 cells per scale, those pairs require approximately 1.3 GiB and
4.4 GiB respectively. The 25 GiB threshold leaves room for two rolling checkpoints, optimizer state, logs,
metrics, evaluation outputs, filesystem overhead, and interruption recovery. It is a launch threshold, not a
promise that a nearly full disk is safe indefinitely; the runner checks free space before every cell as well.

At the time this plan was written, the internal volume had only about 8.3 GiB free. That fails the gate. Existing
checkpoints will not be deleted without explicit owner approval.

## Retention and verification

For every completed cell retain the exact config, environment record, training log, metrics, summary, best and
final checkpoints, and a verification record containing sizes and SHA-256 hashes. A cell is complete only when:

1. the summary reports the fixed 6,000-step budget and completed status;
2. best and final checkpoints both deserialize successfully and contain the expected model payload;
3. their hashes and sizes are written to the cell verification record; and
4. required evaluation artifacts pass their schema, row-count, checkpoint-hash, and corpus-hash checks.

Only after all four checks may `step_*.pt` rolling checkpoints be removed. Best/final checkpoints are never
removed by the runner. Exploratory models under existing `models/` paths are outside the cleanup scope.

## Interrupted runs and failures

The queue owns one global lock, so 14M and 48M training cannot overlap and a second queue cannot start. A restart
may resume only the newest rolling checkpoint in the same experiment after successful deserialization. The
original log and a dated failure record remain in place. A corrupted checkpoint, non-finite loss, or inability to
reach the registered budget after documented recovery is a technical failure; weak or inconvenient scientific
outcomes are not exclusion reasons.

Power loss terminates local computation. After power returns, rerun the preflight, verify the artifact filesystem,
verify the latest checkpoint, and then resume. Never infer completion from a directory name or partially written
file.
