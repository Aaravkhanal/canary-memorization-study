# Blinded human-annotation protocol

**Version 1 status:** the sampling protocol and blank batches are frozen in the repository, but no human labels have
been collected. This is condition-blinding, not content-blinding: raters see the prompt and generated story, which
may reveal a canary or setting, but do not see architecture, exposure frequency, checkpoint, or automated scores.

## Purpose

The paper's primary novelty endpoint is the fraction of generations judged to be a genuine novel recombination,
not distinct-2. Automated overlap and diversity scores remain secondary diagnostics only.

## Sampling

- Include treatment frequencies 1, 10, 50, 100, and 500; exclude the zero-exposure control from the primary
  novelty endpoint.
- For every architecture-frequency cell, sample two of ten completions from each of the 32 pre-registered
  canary-setting groups. This produces 64 balanced samples per cell and 1,280 samples for a complete four-by-five
  grid.
- Selection and order are deterministic from a committed seed. Architecture, frequency, checkpoint, overlap,
  and edit-distance fields are hidden from annotators.
- Two annotators label the same samples independently. They must not inspect the private manifest, trade-off plots,
  or each other's labels until both files are locked.

The prepared files are `results/annotations/rater_a.csv` and `results/annotations/rater_b.csv`, with 1,280
condition-hidden rows each (4 architectures × 5 nonzero frequencies × 64 judgments). Before distribution, verify
that both contain identical `sample_id` sets and exactly the columns `sample_id,prompt,generation,label,confidence,notes`;
the last three fields must remain blank. The hidden key is `results/annotations/private_manifest.json`. It is
Git-ignored and must stay with the study custodian, not be sent to raters or staged for public release. Do not
inspect it while annotating. The text fields themselves can contain clues, so never promise perfect masking.

## Labels

- **V — Verbatim/near-verbatim:** the generation reproduces a training story or long distinctive span with only
  negligible edits.
- **T — Template copy:** the generation reuses the structure/events of a training story with superficial entity,
  attribute, or wording substitutions; the requested canary/setting is not meaningfully recomposed.
- **N — Genuine novel combination:** the generation meaningfully uses the requested canary identity or fragment
  in the requested unseen setting, with a narrative/event combination not copied from its training stories.

Annotators also record confidence (`low`, `medium`, or `high`) and may add a short note. The label is categorical;
confidence never changes the primary score. Do not infer V/T/N mechanically from overlap scores, filenames, or
other automated metrics. If a completion is empty, truncated, incoherent, or does not follow the prompt, do not
silently remove it or call it novel: assign the closest rubric label only if defensible and record the issue in
`notes` with low confidence. Escalate ambiguous cases for the planned adjudication; retain every sampled item in
the audit trail.

## Locking, agreement, and adjudication

1. Before release, record SHA-256 checksums for both blank CSVs and confirm identical sample-ID sets, expected row
   count, permitted empty fields, and absence of condition columns. Keep the manifest private. Do not rerun the batch
   generator over completed labels: it refuses to overwrite a file containing a label unless `--force` is supplied.
2. Raters work independently, do not discuss individual items, and return the complete CSV with sample IDs intact.
   A custodian checks schema, row count, duplicates, and allowed values (`V/T/N`, `low/medium/high`) without
   revealing conditions. The current scoring program validates labels and matching sample IDs; confidence and notes
   are retained as annotations but are not inputs to its score.
3. Run `scripts/score_blinded_annotations.py` before revealing conditions. It computes raw agreement, pairwise
   Cohen's kappa and nominal Krippendorff's alpha. It also produces per-condition V/T/N counts and N fractions with
   Wilson intervals plus a 2,000-replicate bootstrap that resamples the 32 `(canary_id, setting)` clusters (seed
   `20261007`). These intervals are descriptive for this fixed sample; the simple Wilson interval does not account
   for clustering and must not be presented as the sole inferential interval.
4. If any two-rater disagreement remains, the current scorer writes a condition-hidden disagreement file and
   stops before condition scores. A third adjudicator labels only those items from the same rubric, blind to
   conditions and original labels where feasible; the custodian then supplies adjudicated labels and reruns scoring.
   Preserve original labels, adjudications, and a decision log. Do not break ties by looking at automated overlap.
5. Only after the label files, agreement report, adjudication, and analysis outputs are checksum-locked may the
   custodian join the private manifest and compute the registered condition summaries. Archive a de-identified
   release where privacy permits; never publish the private key or story text without checking data rights.

## Statistics

Primary descriptive endpoint: the per-cell `N` fraction, accompanied by V/T/N counts and the cluster-bootstrap
interval. Report Wilson intervals only as a familiar sample-level reference, clearly noting their independence
assumption, and report both agreement coefficients before unblinding. The present code does not fit a mixed-effects
architecture-by-frequency model or a confidence-weighted model. Before unblinding, freeze any confirmatory
between-cell contrasts, effect scale, multiplicity family, and model; otherwise comparisons are exploratory.
Confidence-stratified and canary-type analyses are sensitivity analyses, not replacements for the all-item primary
result.

## Ethics and authorship

If annotators other than the author are recruited, obtain any ethics/consent determination required by the
author's institution before collecting labels. Annotation alone does not automatically qualify someone for
authorship; IEEE authorship requires significant intellectual contribution, manuscript contribution, and final
approval. Contributors who do not meet all criteria should be acknowledged with their consent.

## Pre-distribution checklist

- [ ] Ethics/consent determination and data-use permission documented before external recruitment.
- [ ] Two CSVs contain 1,280 rows apiece, identical sample IDs, hidden condition fields, and blank label/confidence/notes.
- [ ] SHA-256 checksums recorded; private manifest excluded from rater package, Git, and public artifact.
- [ ] Raters receive this rubric and instructions not to discuss labels or search for condition metadata.
- [ ] Custodian and adjudicator roles, secure return channel, retention, and de-identification plan agreed.
- [ ] No human labels are represented as complete until the signed/returned files pass schema and completeness checks.

Current blank-batch validation (2026-10-15): both files have 1,280 records, identical sample-ID sets, the six
expected columns, and blank label/confidence/notes fields. Their SHA-256 values are:

| Batch | SHA-256 |
|---|---|
| `rater_a.csv` | `bfa98dc2ef93c79d9bcbaad745ad5abfd25006d44d4d3f1ab4e9ddca7d65830a` |
| `rater_b.csv` | `54c86d1254fa8d295b1284b338dde6be1917c782d040ab9e8bab30f517029c47` |

These hashes identify the current blank files only; update them if files are edited, distributed with different
headers, or re-randomized. The private manifest was checked for presence but intentionally not opened.
