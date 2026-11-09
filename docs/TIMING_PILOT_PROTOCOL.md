# Blinded annotation timing pilot

Status: **prepared, not yet completed**. This operational pilot does not open recruitment and does not produce
primary study labels.

## Purpose

Estimate realistic annotation time, fatigue, break needs, and compensation for the amended 1,920-item external-
rater workload. The pilot must not inspect experimental conditions or be used to change the sampling rule based
on observed model outputs.

## Who completes it

The repository owner completes the 80-item condition-hidden sheet as an investigator workflow pilot. These pilot
labels are never pooled with the two independent external-rater endpoints and do not count as participant data or
as an independent rater. If another person performs the pilot, obtain the applicable institutional determination
before involving them.

## Procedure

1. Open `results/confirmatory/annotation_amended/timing_pilot_80.html` in a browser. It embeds only the public
   condition-hidden fields, automatically records active seconds, pauses when the tab is hidden, saves progress
   locally, enforces four blocks and five-minute breaks, and exports the completed CSV. The blank source is
   `timing_pilot_80.csv`; do not open the private manifest.
2. Work in four blocks of 20 items. Record active seconds for every item, excluding breaks and interruptions.
3. Enter a provisional V/T/N label, confidence, and optional note only to reproduce the real workflow.
4. Take at least a five-minute break between blocks and record any fatigue or rubric ambiguity separately.
5. Do not search the repository, compare automated scores, or infer architecture/frequency conditions.
6. Run `python scripts/summarize_timing_pilot.py` after every row is complete.
7. Use the median, 75th percentile, and fatigue-by-block results to set session limits and compensation. Preserve
   the raw pilot privately; publish only aggregate timing results unless release is explicitly authorized.

## Completion rule

The pilot is complete only when all 80 rows contain an allowed label (`V`, `T`, or `N`), confidence
(`low`, `medium`, or `high`), and a positive number of active seconds. The summarizer refuses partial data.

## Decision rule

Estimate total active work as `1,920 × median seconds`, and the conservative workload as `1,920 × p75 seconds`.
Add paid onboarding/calibration time and paid breaks separately. Do not set final compensation below applicable
law or institutional policy. If the fourth-block median exceeds the first-block median by 25% or more, shorten
sessions and add rest/recalibration requirements before external recruitment.
