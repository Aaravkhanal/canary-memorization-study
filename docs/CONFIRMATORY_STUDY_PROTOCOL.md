# Confirmatory study protocol: contamination-free mixed-frequency replication

**Protocol v1 is frozen by this commit; no confirmatory corpus or model has been generated or trained.** The design
is not approved to start until the power/sensitivity gate, compute budget, data rights, and (if applicable)
ethics/consent review below are resolved. Log changes as dated amendments before looking at outcomes; never
silently revise after seeing results.

## Motivation

The separate 48M exploratory scale-transfer arm is specified in `docs/SCALE_48M_PROTOCOL.md`; it does not replace
this contamination-free confirmation.

The exploratory grid found three design limitations: three of eight canaries already occurred in the base corpus;
the 10/20-candidate exposure reference sets saturate too easily; and separate frequency-specific training runs
confound exposure frequency with training stochasticity. This confirmatory study removes all three while using
fewer training runs than repeating the original full grid.

## Confirmatory questions

1. Does exposure increase monotonically with planted frequency for corpus-absent narrative canaries?
2. Does the human-labelled genuine-recombination rate change with exposure after controlling for canary and
   prompt setting?
3. Do position encoding, attention type, or normalization change either slope?

The direction of the novelty association is not forced: memorization may reduce, leave unchanged, or support
composition. All three are scientifically meaningful outcomes.

## Design

- Use one **mixed-frequency corpus** per seed containing different canaries assigned to 1, 10, 50, 100, or 500
  insertions. Train every architecture on the same corpus for that seed.
- Use four character and four plot-fragment canaries per frequency: 40 inserted canaries total, plus at least eight
  zero-exposure controls.
- Verify the complete canary identity and every reference alternative have zero exact occurrences in train,
  validation, and test text **before locking** the bank.
- Allocate insertion stories disjointly across canaries. Total insertion demand is 5,288 stories per corpus,
  comfortably below the current corpus size.
- Use at least three independent training seeds for all four architectures: 12 matched training runs. If compute
  permits, use five seeds and rotate identity-to-frequency assignments across seeds. Three seeds are a floor, not
  evidence of adequate power. Before training, simulate power/interval width for the registered primary effects
  over plausible canary- and setting-level variance, choose a smallest effect of scientific interest, and either
  increase seeds or label the study underpowered if the pre-set precision/power target is not met.
- Every architecture for a given seed must use byte-identical mixed-frequency train/validation/test splits and
  the same insertion assignment. Rotate frequency-to-identity assignment across seeds using a committed schedule
  so identity difficulty is not confounded with frequency. Keep tokenizer, token budget, context, optimizer,
  schedule, batch size, checkpoint-selection rule, and evaluation prompts fixed across architectures; any
  architecture-specific adjustment must be justified and recorded before runs.
- Generate train/validation/test from a frozen base corpus and prove inserted story IDs are disjoint across splits.
  Record pre-insertion and post-insertion corpus hashes, story counts, tokenizer hash, canary-bank hash, assignment
  seed, full config, code revision, and checkpoint hash. A matching run is not “same data” unless these artifacts
  verify.

## Higher-resolution exposure

- Pre-register a fixed reference-set size of 1,024 alternatives per identity slot (maximum exposure ≥10 bits),
  selected from a documented generation process and screened against all splits. If that computationally or
  linguistically fails, amend the protocol before training and lock one replacement size of at least 256
  alternatives (maximum exposure ≥8 bits); do not mix reference-set sizes across conditions.
- Report rank, exposure, true log probability, margin to the strongest alternative, first-token rank, full identity
  token ranks, top-k recall, and greedy/beam extraction separately.
- Never use an alternative found in the base corpus without recording and matching its corpus frequency.

## Novelty and copying

- Generate unseen-setting completions with committed prompts and seeds.
- Use the blinded two-rater protocol in `docs/ANNOTATION_PROTOCOL.md` as the primary endpoint.
- Freeze the generation temperature, number of completions, decoding limits, prompt template, and random seeds
  before generation. Sample the same number of items per canary-setting group and condition; retain failed,
  empty, truncated, and noncompliant outputs with pre-registered status codes rather than silently dropping them.
- Search every generation against the entire training corpus with an indexed n-gram retrieval stage followed by
  exact overlap/edit scoring of candidates. Report both local sequential novelty and semantic/prompt compliance;
  do not equate distinct-n with creativity.
- Pre-register handling for empty, truncated, incoherent, or prompt-noncompliant generations. They must not be
  silently counted as novel.

## Statistical plan and preregistration gate

- **Primary exposure endpoint:** canary exposure as a function of log10 insertion frequency, architecture, and
  their interaction, with repeated observations grouped by seed and canary identity. Specify the exact model/link,
  contrasts, convergence fallback, and treatment of ceiling values in a versioned analysis script before data
  lock. Report effect estimates and 95% intervals, not only p-values.
- **Primary novelty endpoint:** human `N` versus `V/T`, with the same planned fixed effects and grouping by
  seed/canary/setting. The precise mixed-effects model must be power-checked and locked before annotation labels
  are unblinded. The existing exploratory annotation scorer reports agreement and descriptive cluster-bootstrap
  intervals; it is not this confirmatory inferential model.
- Name one primary exposure contrast and one primary novelty contrast in the preregistration. Define the family of
  architecture interactions and control it (Holm across the three planned architecture-interaction tests, if all
  remain in scope). Specify missing/ambiguous labels, adjudication, model failures, and exclusions in advance.
- The power/sensitivity simulation must use the planned number of seeds, canary-setting clusters, and expected
  label prevalence; publish its code, assumptions, target effect, and resulting minimum sample size. If the design
  cannot achieve the target within the budget, narrow the confirmatory questions or run more seeds before data
  collection. No outcomes may be inspected to decide whether to add seeds.
- Report the full outcome table even if H1/H2 are null. Do not select canaries, seeds, or frequency ranges after
  observing results.
- Sensitivity analyses: all canaries vs. character/plot subsets; high-confidence labels only; V/T/N ordinal
  treatment; full-corpus overlap thresholds; and leave-one-canary-out analysis.
- Report both the all-canary primary model and clean-canary sensitivity subset; the contamination exclusion rule
  is based solely on a pre-outcome corpus scan. Include all null and adverse results and a complete deviation log.

## Stopping and exclusions

- A run may be excluded only for a pre-specified technical failure: corrupted data/checkpoint, non-finite loss,
  or failure to reach the fixed training budget after documented recovery attempts.
- Poor validation loss, weak exposure, inconvenient direction, or disagreement with the exploratory study are not
  exclusion reasons.
- No early stopping based on the confirmatory effect. Complete the planned seed set.

## Reporting

Label the existing study “exploratory” and this extension “confirmatory.” Report every protocol amendment, all
failed runs, compute cost, and all null results. Archive code, locked configs, corpus-assignment manifests, raw
metrics, labels, and analysis outputs under a permanent release/DOI.

## Start gate (must be checked before any run)

- [ ] This protocol, canary bank, assignment schedule, configs, prompts, analysis script, and power simulation are
  committed and content-hashed; no confirmatory outcomes have been inspected.
- [ ] Every canary and alternative is absent from train, validation, and test splits; exact and normalization-aware
  checks are recorded with corpus hashes.
- [ ] Power/precision target and seed count are justified; compute time/storage and recovery plan are feasible.
- [ ] Ethics/data-rights/consent determination is documented before external human annotation, if applicable.
- [ ] The independent exploratory labeling workflow is complete or its limitations are explicitly separated from
  confirmation; annotators remain blinded to conditions.
- [ ] Code, software environment, deterministic settings, and artifact-retention plan are frozen.

Until all boxes are checked, do not start training and do not call results confirmatory. The current five-frequency,
four-architecture 48M sweep is an exploratory scale-transfer arm and is not this study.

## Amendment 1 — two-scale implementation lock (2026-10-16, before outcomes)

The implementation covers both 14M and 48M scales with the same mixed-frequency assignments. Five assignment
seeds were generated and frozen; seeds 20261016–20261018 are the planned floor and 20261019–20261020 are a
pre-outcome contingency only. The deterministic bank contains 20 character and 20 plot canaries, eight controls,
and shared 1,024-item character and plot reference pools. All 2,096 identities/alternatives have zero normalized
occurrences in the complete 59,999,181-byte base-corpus subset. Bank content hash:
`f9afb1e6c0c6db87483c5e0c39578f20abe06583fd767fd49994e61ca62072d2`.

During pre-outcome implementation of the 1,025-candidate evaluator, a disjointness audit found that three inserted
character identities also appeared in the original synthetically generated character reference pool. None had
appeared in the base corpus, but treating a true identity as its own alternative would invalidate the registered
rank denominator for those canaries. Before any model training or outcome inspection, the deterministic generator
was repaired to exclude all inserted/control identities and append screened replacements while retaining exactly
1,024 alternatives. Corpus bytes and schedules were unchanged; their manifests were regenerated solely to record
the corrected bank hash. This correction is part of the pre-outcome lock, not an outcome-driven amendment.

The registered smallest effects of scientific interest for the planning simulation are 0.5 exposure bits per
log10 frequency decade and a 1.5 novelty odds ratio per decade. The simulation uses four settings and two
completions per canary/model, canary-clustered uncertainty, 80% power, maximum median 95% interval widths of 0.75
exposure bits and 0.70 log-odds, and 250 Monte Carlo replicates. Under the stated variance assumptions, three seeds
pass both gates; therefore the planned design is 3 seeds × 4 architectures × 2 scales = 24 cells. The simulation
and all assumptions are recorded in `results/confirmatory_power.json`; deviations require a dated pre-training
amendment. Passing a simulation under assumed variance is not an empirical result and does not remove the remaining
storage, corpus/config, rights, ethics, or clean-room gates.

## Amendment 2 — inferential model lock (2026-10-17, before outcomes)

The executable model specification is frozen in `configs/confirmatory/analysis_plan.json` and
`scripts/analyze_confirmatory.py`. The primary exposure model is OLS with canary-clustered sandwich covariance,
canary and seed fixed effects, sum-coded architecture/scale effects, and log10 frequency interactions. The primary
coefficient is therefore the balanced grand-mean frequency slope. The primary human novelty model is a binomial
GEE for adjudicated N versus V/T with canary clusters, exchangeable working correlation, seed/setting fixed
effects, and the same sum-coded interactions; its predeclared fallback is independence-working-correlation GEE.
Blank, automated, or non-V/T/N labels are fatal. Holm correction is applied to the three architecture-by-frequency
interaction coefficients within each endpoint. Exposure ceiling values remain in the primary model, with a
non-ceiling sensitivity analysis when the indicator is available. All estimates, intervals, raw/adjusted p-values,
cluster counts, failures, and fallbacks must be reported; outcome-driven exclusions or seed additions are barred.

## Amendment 3 — storage and recovery lock (2026-10-17, before outcomes)

The queue requires 25 GiB free on its selected artifact filesystem at launch and before every cell. The default
path is `models/confirmatory`; `CONFIRMATORY_ARTIFACT_ROOT` may point to a validated external filesystem. The
machine-readable plan and full retention rules are in `configs/confirmatory/storage_plan.json` and
`docs/STORAGE_AND_RECOVERY_PLAN.md`. One global queue lock prevents overlapping 14M/48M or duplicate jobs. An
interrupted cell may resume only from a successfully deserialized rolling checkpoint in the same run. Best/final
checkpoints, logs, summaries, configs, metrics, hashes, and failure records are retained. Rolling checkpoints may
be removed only after training and all required evaluations verify. This amendment does not open the gate: local
space is below threshold and the ethics mode was unresolved at that point. The evaluator was subsequently frozen
in Amendment 4, and annotation roles were selected in Amendment 5 below without claiming ethics approval.

## Amendment 4 — outcome evaluation workflow lock (2026-10-17, before outcomes)

`configs/confirmatory/evaluation_plan.json` freezes the evaluation settings. Every cell scores 40 inserted
canaries plus eight controls against 1,024 target-disjoint alternatives (1,025 candidates including truth), with
exposure defined as $\log_2(1025)-\log_2(\mathrm{rank})$. The evaluator records true log probability, best-
alternative margin, first-token and full-identity token ranks, top-1/5/10 recall, teacher-forced argmax, greedy
extraction, and width-5 beam extraction. The four registered novel settings and two completions per setting yield
320 retained generations per cell and 7,680 across 24 cells; decoding uses temperature 0.8, top-k 50, top-p 0.95,
150-token limits, and deterministic cell-specific seeds. Empty, length-truncated, and timed-out generations remain
in the output with status codes.

Every generation is enriched using an exact word-four-gram inverted index restricted to the content-hash-selected
training split, not validation/test documents. Cell JSON is accepted only if its checkpoint/corpus hashes, 48
exposure rows, 160 groups, 320 completions, and overlap provenance verify. The annotation batch builder refuses a
partial grid, writes 7,680 condition-hidden rows into two independently shuffled external-rater sheets and one
separately shuffled self-sensitivity sheet, and leaves label, confidence, and notes blank. Its condition key is
private and ignored by Git. No automated V/T/N label is created.
Rolling checkpoints may be deleted only after this automated evaluation verifies; best/final checkpoints remain.

## Amendment 5 — annotation-role decision (2026-10-17, before outcomes)

The primary human endpoint will use two independent external raters. The repository owner will also complete a
third, independently shuffled condition-hidden sheet as a self-annotation sensitivity analysis. Self-ratings are
never pooled with the primary external-rater endpoint, do not count toward external inter-rater agreement, and do
not replace condition-hidden adjudication. The batch builder therefore prepares two external sheets and one self-
sensitivity sheet, all with identical sample IDs and blank annotation fields. No recruitment or annotation may
begin until the applicable institutional determination, finalized consent process, compensation, withdrawal,
retention, and explicit clearances are recorded. This pre-outcome role decision is not ethics approval and does
not open the training gate.
