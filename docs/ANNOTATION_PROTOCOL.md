# Blinded human-annotation protocol

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

## Labels

- **V — Verbatim/near-verbatim:** the generation reproduces a training story or long distinctive span with only
  negligible edits.
- **T — Template copy:** the generation reuses the structure/events of a training story with superficial entity,
  attribute, or wording substitutions; the requested canary/setting is not meaningfully recomposed.
- **N — Genuine novel combination:** the generation meaningfully uses the requested canary identity or fragment
  in the requested unseen setting, with a narrative/event combination not copied from its training stories.

Annotators also record confidence (`low`, `medium`, or `high`) and may add a short note. The label is categorical;
confidence never changes the primary score.

## Locking, agreement, and adjudication

1. Generate batches with `scripts/prepare_blinded_annotations.py` only after all primary novelty JSON files exist.
2. Each annotator completes a separate CSV. Existing nonblank labels cannot be overwritten without an explicit
   `--force` flag.
3. `scripts/score_blinded_annotations.py` reports pairwise Cohen's kappa, nominal Krippendorff's alpha, and raw
   agreement before unblinding.
4. Disagreements are exported without condition metadata and must be adjudicated separately. Final condition
   scores are not produced while unresolved disagreements remain.

## Statistics

For each architecture-frequency condition, report V/T/N counts, the N fraction, a Wilson 95% interval, and a
cluster bootstrap 95% interval that resamples the 32 canary-setting groups rather than treating 64 completions as
fully independent. The paper must report both intervals and the agreement statistics. Any architecture or
frequency comparison not specified before unblinding is exploratory.

## Ethics and authorship

If annotators other than the author are recruited, obtain any ethics/consent determination required by the
author's institution before collecting labels. Annotation alone does not automatically qualify someone for
authorship; IEEE authorship requires significant intellectual contribution, manuscript contribution, and final
approval. Contributors who do not meet all criteria should be acknowledged with their consent.
