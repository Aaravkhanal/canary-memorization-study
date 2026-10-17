# Confirmatory Annotation Ethics and Consent Plan

Status: **external-rater primary endpoint plus separate self-annotation sensitivity selected; no ethics approval or determination is claimed**.

The repository owner selected two independent external raters for the primary endpoint and a third, separate self-annotation sheet for investigator sensitivity. Self-ratings are never pooled with the primary endpoint and do not count as an independent external rater. On 2026-10-17 the owner separately authorized computational model training, which does not recruit or collect data from humans. Recruitment, annotation, adjudication, and human-endpoint analysis remain blocked until the external-rater requirements below are completed in `configs/confirmatory/ethics_record.json`. The machine check in `scripts/check_ethics_record.py` reports training and annotation readiness separately; it cannot issue an institutional determination.

## Rejected primary alternative: self-only annotation

The repository owner performs all qualitative annotation and no external participant is recruited. Record `annotation_mode` as `self_only`, set `external_raters_planned` to `false`, and use the explicit not-applicable values accepted by the validator.

This route changes the frozen two-rater endpoint: it cannot estimate inter-rater agreement and is methodologically weaker. Before using it, add a dated protocol amendment that downgrades the two-rater endpoint and explains the resulting limitation. Do not silently substitute self-annotation for the planned blinded two-rater study.

## Selected primary route: external raters

Before recruitment, obtain the locally or institutionally required determination (for example approved, exempt, or not-human-subjects-research). Record the responsible authority, reference, date, outcome, consent procedure, compensation plan, withdrawal process, and both training/annotation clearances.

The companion external-rater information and consent document is a draft template only. It must be adapted to the actual institution and approved process before use.

## Separate self-annotation sensitivity

The owner will complete a separately shuffled, condition-hidden `self_sensitivity.csv` using the same rubric. These labels will be analyzed and reported separately after the two external files are locked. They may reveal investigator-versus-external differences but cannot improve external inter-rater agreement, replace adjudication, or rescue an incomplete primary endpoint.

## Privacy and data handling

- Collect only the minimum rater information needed to administer the study.
- Keep condition identities, private annotation keys, and identifiable administrative records outside public artifacts.
- Release only de-identified labels, adjudicated outcomes, and aggregate agreement statistics under the selected project terms.
- Record the retention and deletion schedule before annotation begins.
- Do not describe the study as ethics-approved unless a real authority issued that determination.

## Mechanical validation

Run:

```bash
/Users/aaravkhanal/miniforge3/bin/python scripts/check_ethics_record.py
```

A successful result means only that the selected route has a complete, machine-readable record. It does not grant approval, determine legal compliance, or replace institutional review.
