# Artifact reproducibility and release boundaries

**Status: content-addressed data acquisition and portable confirmatory configs are implemented; clean-room
reproduction and permanent archival remain outstanding.** The
repository records analysis code, configurations, result JSON/CSV files, figures, runtime notes, tests, and
protocols. A Git checkout alone is not sufficient to retrain the models or regenerate every result: the base
corpus, processed frequency-specific corpus text, tokenizer artifact, and model checkpoints are local/ignored
artifacts, and the training/evaluation code imports the sibling `aarav-lm` project. Do not describe this as a
one-command, clean-environment reproduction until those dependencies are versioned or deposited with permitted
checksums and setup instructions.

## What is and is not in Git

| Artifact | Repository status | Reproduction implication |
|---|---|---|
| Python/shell analysis and evaluation scripts; YAML configs; tests; manuscript/protocol docs | Versioned | Code and intended settings can be reviewed from a clone. The new confirmatory configs are portable; legacy exploratory configs/runners retain machine-specific absolute paths. |
| Memorization/novelty/full-corpus result JSONs, trade-off CSVs/PNGs, runtime audit | Versioned in this project | The reported descriptive summaries can be inspected. Check JSON provenance fields and matching corpus fingerprint before reuse. |
| Raw base corpus and confirmatory `corpus.txt`/tokenized data | Git-ignored/local | The exact base subset can be reacquired and the three confirmatory corpora rebuilt deterministically; users must comply with the upstream license. Legacy exploratory processed data remains local. |
| Tokenizer artifact and all 106 validated best/final checkpoints | Local under sibling/project paths; `models/` is Git-ignored | The experiments are not independently retrainable from this repository alone. The checkpoint audit is evidence of local validation, not public weight availability. |
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
`reproducibility/inputs.lock.json`. A local pass proves that this machine has the expected inputs; a fresh-clone
pass is still required before claiming clean-room reproduction.

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
and identical mixed-frequency corpora across architectures within each seed. Tokenizer packaging and a clean
checkout smoke run are still required before calling this clean-room verified.

1. Obtain the exact base corpus, tokenizer, and compatible `aarav-lm` revision. Record their versions and hashes;
   confirm data-use permission before redistribution.
2. Restore the ignored processed data and checkpoint paths, then edit machine-specific absolute paths in YAML
   configs and the runner scripts for the target machine. Keep the recorded `data.seed`, `train.seed`, token budget,
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
