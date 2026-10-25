# Artifact reproducibility and release boundaries

**Status (2026-10-25): the 24-cell confirmatory computational grid and automated evaluations are complete, and a
fresh-clone analysis/data/tokenization/one-step CPU smoke test passed; full-cell clean-room reproduction and permanent
archival remain outstanding.** The
repository records analysis code, configurations, result JSON/CSV files, figures, runtime notes, tests, and
protocols. A Git checkout alone is not sufficient to retrain the models or regenerate every result: the base
corpus, processed frequency-specific corpus text, and model checkpoints are local/ignored artifacts, and the
training/evaluation code imports the sibling `aarav-lm` project. The exact tokenizer is now versioned. Do not describe this as a
one-command, clean-environment reproduction until those dependencies are versioned or deposited with permitted
checksums and setup instructions.

## What is and is not in Git

| Artifact | Repository status | Reproduction implication |
|---|---|---|
| Python/shell analysis and evaluation scripts; YAML configs; tests; manuscript/protocol docs | Versioned | Code and intended settings can be reviewed from a clone. The new confirmatory configs are portable; legacy exploratory configs/runners retain machine-specific absolute paths. |
| Memorization/novelty/full-corpus result JSONs, trade-off CSVs/PNGs, runtime audit | Versioned in this project | The reported descriptive summaries can be inspected. Check JSON provenance fields and matching corpus fingerprint before reuse. |
| Raw base corpus and confirmatory `corpus.txt`/tokenized data | Git-ignored/local | The exact base subset can be reacquired and the three confirmatory corpora rebuilt deterministically; users must comply with the upstream license. Legacy exploratory processed data remains local. |
| Tokenizer artifact | Versioned under `artifacts/tokenizer_tinystories_v2/` with SHA-256 | A clone has the exact 4,096-token BPE files; external redistribution still awaits the owner's license review. |
| All 106 exploratory best/final checkpoints | Local under `models/`; Git-ignored | The checkpoint audit is evidence of local validation, not public weight availability. A model/Zenodo release is still needed. |
| `results/annotations/private_manifest.json` | Git-ignored/private | Do not publish or send to raters. It maps blinded sample IDs back to study conditions. |
| Legacy condition-revealing `results/labelling/*.txt` | Untracked local files | These are excluded from blinded analysis and should not be staged in the paper-support commit. |

## Existing-artifact checks

From the repository root, with Python and the dependencies used by the project available:

```bash
python -m pytest tests/
python scripts/analyze_tradeoff.py --results-dir results --baseline-dir results \
  --out-csv results/tradeoff.csv --out-plot results/tradeoff.png
python scripts/analyze_tradeoff.py --results-dir results --baseline-dir results \
  --canaries char_nira,char_boro,char_suri,plot_song,plot_lantern \
  --out-csv results/tradeoff_clean.csv --out-plot results/tradeoff_clean.png
```

The pinned local environment and exact training inputs can be checked separately:

```bash
python scripts/check_reproducibility.py --mode analysis
python scripts/check_reproducibility.py --mode training
```

Analysis mode checks the package versions in `requirements-research.lock`. Training mode additionally checks the
pinned `aarav-lm` Git revision and the byte hashes of the base-corpus subset and tokenizer files recorded in
`reproducibility/inputs.lock.json`. The fresh-clone smoke record is in `results/clean_room_smoke.json`.

Before confirmatory training or a resumed cell, run the stricter non-outcome gate:

```bash
python scripts/check_confirmatory_start_gate.py --json-out results/confirmatory_start_gate.json
python scripts/run_confirmatory_queue.py --check-only
```

The checker validates the 24 configs,
all three corpus hashes, committed pre-outcome locks, ethics record, and the selected artifact filesystem. The
queue uses `AARAV_LM_DIR` and optional `CONFIRMATORY_ARTIFACT_ROOT`, acquires one global lock across scales, refuses
an existing Python training process, and checks the frozen 25-GiB threshold before every cell. The computational
grid has completed; the separate human-annotation gate remains closed. The outcome workflow is frozen: it runs the
1,025-candidate evaluator, enriches all 320 generations per cell against the exact content-hash-selected training
split, verifies JSON/checkpoint/corpus provenance, and only then removes rolling checkpoints while retaining
best/final. The blinded-batch builder ran after all 24 evaluated cells existed and produced two external-rater
sheets plus one separate self-sensitivity sheet with 7,680 blank rows apiece.

The confirmatory exposure-only analysis can be regenerated without human labels:

```bash
python scripts/build_confirmatory_exposure_table.py
python scripts/analyze_confirmatory.py \
  --exposure-csv results/confirmatory/exposure_analysis_input.csv \
  --output results/confirmatory/exposure_analysis.json
```

The exposure-table builder stores each result path relative to the confirmatory result root so the CSV is byte-
reproducible across checkout locations. The model output is independent of the provenance-path field.

Do not add `--novelty-csv` until complete external labels have been independently collected, adjudicated, and
unblinded under the frozen protocol.

Release readiness is a separate, deliberately failing gate:

```bash
python scripts/check_release_gate.py --json-out results/release_gate.json
```

It requires an owner-authorized license and redistribution decision, completed confirmatory training and human
annotation, full-cell clean-room reproduction, a real permanent archive, and a DOI matching `CITATION.cff`. The
checker reports missing evidence but cannot authorize a release or mint a DOI.

These commands reproduce automated descriptive tables/figures from the committed result JSONs; they do not train
models and do not create human novelty scores. Do not pass a labelled CSV until human annotations have been
returned, validated, locked, and adjudicated as described in `ANNOTATION_PROTOCOL.md`.

Rebuild a checksum inventory after staging any newly versioned artifact:

```bash
python scripts/create_artifact_manifest.py
```

The generated `results/artifact_manifest.json` covers files known to Git's index, records byte size and SHA-256,
and excludes itself. It does not hash ignored corpora, checkpoints, or the private annotation key; those require a
separate permitted release process.

To reproduce one full-corpus overlap output, first obtain the exact frequency-specific training corpus and then
run (example for baseline frequency 100):

```bash
python scripts/eval_full_corpus_overlap.py \
  --input results/novelty_baseline_freq100.json \
  --corpus data/processed/freq_100/corpus.txt \
  --output results/full_corpus_overlap/novelty_baseline_freq100_full_corpus.json \
  --index results/full_corpus_overlap/index_freq_100.sqlite
```

The corpus must match the checkpoint's training corpus; the evaluator records a SHA-256 and story count and
refuses a stale index. Exact word-four-gram overlap is a copying diagnostic, not semantic matching.

## Reproducing training (not yet clean-room verified)

For the confirmatory study, acquire and rebuild the exact inputs from a clone:

```bash
python scripts/acquire_tinystories_subset.py
python scripts/generate_confirmatory_bank.py --check
for seed in 20261016 20261017 20261018; do
  python scripts/prepare_confirmatory_corpus.py --seed "$seed"
done
python scripts/make_confirmatory_configs.py
```

The three committed corpus manifests record 5,288 insertions each, exact output hashes, source story indices, and
train/validation/test counts. Every inserted story is proven to hash to the training split under the pinned
aarav-lm split algorithm. The 24 configs use relative paths, one common 49.152M-token budget and learning rate,
and identical mixed-frequency corpora across architectures within each seed. The exact tokenizer is now packaged.
On 2026-10-16, fresh GitHub clones reacquired the exact base subset, rebuilt and hash-matched the seed-20261016
confirmatory corpus, validated all pinned inputs, tokenized the unmodified base, and completed one CPU-only 14M
training step with zero MPS memory. This verifies the engineering path but is not an independent full-cell
reproduction and produced no confirmatory scientific outcome. The same scripted smoke test was rerun on 2026-10-25
from a fresh GitHub clone at commit `02b01faa1c96c4a1487c92fd1d6ee94f94178dce`; it reacquired the 59,999,181-byte
base prefix, matched its SHA-256, rebuilt the seed-20261016 corpus to hash
`6722a5a3f6a8ec901f7ec82a8c60b8a2a1eb80cf25007ab93369394261553e58`, checked the pinned tokenizer and training
dependency, tokenized the unmodified base, and completed one CPU training step. The exact run record is in
`results/clean_room_smoke.json`. The Python packages were already installed, so this was not a new virtualenv
rebuild. A full 24-cell independent reproduction remains unrun: local free space is about 27 GiB, while the
frozen storage plan requires at least 25 GiB free before every cell on the selected artifact filesystem. No
separate validated artifact filesystem is configured. Do not start a duplicate grid until that headroom can be
maintained throughout the run. Re-run the engineering smoke test with:

```bash
AARAV_LM_DIR=/path/to/pinned/MY-LLM bash scripts/run_clean_room_smoke.sh
```

1. Obtain the exact base corpus, tokenizer, and compatible `aarav-lm` revision. Record their versions and hashes;
   confirm data-use permission before redistribution.
2. For the portable confirmatory path, rebuild the ignored corpus/tokenized data and set `AARAV_LM_DIR` plus,
   optionally, `CONFIRMATORY_ARTIFACT_ROOT`; no committed confirmatory YAML needs a machine-specific absolute-path
   edit. Legacy exploratory configs and runners still contain local paths. Keep every recorded seed, token budget,
   architecture, and schedule unchanged for an exact replicate.
3. Run cells sequentially on the intended device. `scripts/run_48m_scale_experiments.sh` supports
   `WAIT_FOR_PID=<pid>` to wait before using MPS; never run the 14M and 48M queues concurrently on the same
   machine. It removes rolling checkpoints only after retaining and verifying best/final checkpoints.
4. Run memorization, novelty, and matching-corpus overlap evaluation for every checkpoint; validate summary step
   count, parameter count, output row/group counts, corpus hash, and checkpoint load before analysis.
5. Freeze and hash inputs/results. A recovery after a failed cell must retain the failure log and document the
   exact verified resume checkpoint; do not replace the failed attempt in the audit trail.

The initial 48M baseline/frequency-0 cell had a disk-full checkpoint-write failure and recovered from a valid
step-1,000 checkpoint. Its completed result is included in the final audit; that recovery does not erase the
failure. The recorded local validation covered 53 completed summaries, 106 best/final checkpoints, 175 result
JSONs, and 50 matching-corpus overlap reports / 16,000 generations. These counts are local audit facts; a clean
machine has not independently reproduced training.

## Before an external artifact release

- Review and retain `CITATION.cff`; add the final paper DOI, archive DOI, version, release date, ORCID, and
  affiliation only after those values genuinely exist or are confirmed. The current file deliberately contains
  no DOI, license, release date, affiliation, or ORCID.
- Make paths configurable rather than absolute; add a pinned dependency/environment lock and a clean-clone smoke
  test.
- Publish permitted corpus instructions or a content-addressed data acquisition process, tokenizer, checkpoints,
  and checksums, with any required license/privacy restrictions.
- Regenerate `results/artifact_manifest.json` after all intended files are staged, and tag the exact source revision.
- Render figures at publication quality, check color-independent/gray-scale legibility, and archive editable
  source plus figure data.
- Deposit code, permitted data, weights, derived outputs, and manuscript in a permanent archive with DOI. GitHub
  alone is mutable and does not make ignored local artifacts available.
- Complete author, affiliation, ethics/consent, funding, conflicts, data/code availability, limitations, and
  venue-specific AI-use disclosures.
