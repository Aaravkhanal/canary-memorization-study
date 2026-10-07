# Confirmatory study protocol: contamination-free mixed-frequency replication

**Status: proposed and not yet run.** Freeze this protocol in a commit before generating the new canary bank or
examining confirmatory outcomes. Changes after that point must be logged as amendments.

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
  permits, use five seeds and rotate identity-to-frequency assignments across seeds.
- Keep tokenizer, token budget, context, optimizer, schedule, batch size, and evaluation prompts fixed. Record
  hashes for corpus, assignment, config, tokenizer, and checkpoint.

## Higher-resolution exposure

- Pre-register at least 256 verified-absent alternatives per identity slot (maximum exposure ≥8 bits), preferably
  1,024 (≥10 bits), so the high-frequency result does not collapse to the current 3.46/4.39-bit ceiling.
- Report rank, exposure, true log probability, margin to the strongest alternative, first-token rank, full identity
  token ranks, top-k recall, and greedy/beam extraction separately.
- Never use an alternative found in the base corpus without recording and matching its corpus frequency.

## Novelty and copying

- Generate unseen-setting completions with committed prompts and seeds.
- Use the blinded two-rater protocol in `docs/ANNOTATION_PROTOCOL.md` as the primary endpoint.
- Search every generation against the entire training corpus with an indexed n-gram retrieval stage followed by
  exact overlap/edit scoring of candidates. Report both local sequential novelty and semantic/prompt compliance;
  do not equate distinct-n with creativity.
- Pre-register handling for empty, truncated, incoherent, or prompt-noncompliant generations. They must not be
  silently counted as novel.

## Statistical plan

- Primary memorization model: exposure as a function of log10 frequency, architecture, and their interaction,
  with seed and canary identity treated as repeated/random effects.
- Primary novelty model: binary genuine-recombination outcome (`N` vs. `V/T`) with the same fixed effects and
  clustering by canary-setting group; report effect sizes and 95% intervals, not only p-values.
- Correct the three architecture-interaction tests as one family (Holm correction).
- Report the full outcome table even if H1/H2 are null. Do not select canaries, seeds, or frequency ranges after
  observing results.
- Sensitivity analyses: all canaries vs. character/plot subsets; high-confidence labels only; V/T/N ordinal
  treatment; full-corpus overlap thresholds; and leave-one-canary-out analysis.

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
