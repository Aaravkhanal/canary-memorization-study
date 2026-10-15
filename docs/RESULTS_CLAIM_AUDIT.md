# Results claim audit

**Purpose.** A compact source-of-truth for the manuscript, abstract, figures, talks, and project summary. This
records the evidence available in the repository as of 2026-10-15. “Allowed wording” is deliberately narrower than
the historical exploratory narrative. It is not a substitute for re-running the cited analysis or reviewing the
underlying data before submission.

| Claim area | Evidence in this repository | Allowed wording now | Do not claim |
|---|---|---|---|
| 14M training grid | Four parameter-matched architecture variants × six frequency conditions; 24 canonical cells, each at 6,000 updates. Two extra baseline training-seed replications at 100/500. See `test_results_summary.md`, `results/trainer_runtime_audit.md`, configs and result JSONs. | “The exploratory 14M grid and the two additional baseline seed controls completed.” | That the entire architecture × frequency factorial is replicated across seeds, or that between-cell differences are causal/inferential. |
| Exposure / dose-response | Descriptive clean-canary means and full results in `results/tradeoff_clean.csv` and `results/tradeoff.csv`; per-canary measurements in `results/mem_*.json`. Baseline seed sensitivity is separately calculated in `results/seed_sensitivity_clean.csv`. | “Exposure summaries vary with frequency and architecture; several cells show higher clean-canary mean lift at higher frequencies, with plateaus/reversals.” | “A universal monotonic dose-response,” “noise cannot explain the pattern,” or a population-level effect based on two seeds. |
| Training-seed sensitivity | `results/seed_sensitivity_clean.csv`; paired baseline runs hold `data.seed` fixed and vary `train.seed` at 0/1/10/100/500. Mean-lift differences at frequencies 1/10/100/500 are −0.588/+0.564/−0.636/−0.436; largest absolute per-canary differences are 3.044/1.862/2.459/2.459. | “A two-seed, one-architecture sensitivity check found appreciable canary-specific changes.” | “Noise band,” “confidence bound,” variance estimate, or evidence that a treatment effect is significant/insignificant. |
| Pre-existing canary contamination | `scripts/check_canary_novelty.py`, corpus audit and `docs/DRAFT_PAPER.md` §4.1: `char_pip`/“Pip” 150 occurrences, `plot_key`/“a shiny key” 41, `plot_voice`/“a soft voice” 67 in the base corpus. | “Three selected identities were not novel to the base corpus; clean-canary summaries exclude these three as a sensitivity analysis.” | That every canary was absent, or that contaminated identities measure only study-inserted exposure. |
| Extraction | Corrected teacher-forced `argmax_match` comparison: 0/120 in `baseline` and `variant_a_learned_pos` at five nonzero frequencies (see memorization JSONs and manuscript §3.4/§5). | “No teacher-forced argmax match was observed in this audited subset.” | “No model can extract these canaries,” any claim over all four architectures, all seeds, prompts, or decoding schemes. |
| Automated novelty/diversity | `results/tradeoff.csv` and `results/tradeoff_clean.csv`; generated completion metrics. Distinct-2 values differ by condition, without a consistent monotone decline across the grid. | “Distinct-2 summaries are descriptive automated diversity proxies; they do not show a consistent monotonic decline in these results.” | “Creativity,” “originality,” “human novelty,” or proof that there is no novelty cost. |
| Full-corpus copying diagnostic | `results/full_corpus_overlap/`: 24 canonical 14M cells (7,680 generations), two baseline training-seed cells (640), and 24 48M cells (7,680), total 50/16,000. Audit matched frequency-specific corpus SHA-256 and 73,139-story count. | “Exact maximum word-four-gram overlap was computed against each cell’s matching training corpus.” | Semantic plagiarism/originality, comprehensive paraphrase detection, or treating n-gram overlap as human judgment. |
| 48M arm | 24/24 cells at four architecture settings × six frequencies, 6,000 updates; all cells single-seed. Training schedule uses LR 5e-4 versus 8e-4 in 14M. Initial baseline/frequency-0 checkpoint-write failure recovered from valid step 1,000; final completed state is audited. See `docs/SCALE_48M_PROTOCOL.md` and runtime audit. | “A completed, single-seed exploratory 48M scale-transfer sweep is available.” | A causal model-size effect, a matched-scale causal comparison, or generalization to larger models. |
| Human endpoint | `results/annotations/rater_a.csv` and `rater_b.csv` each contain 1,280 condition-hidden rows; label/confidence/notes blank. No returned human annotations. | “Blinded annotation materials are prepared; human labeling has not started/completed.” | Any V/T/N rate, inter-rater reliability, adjudication outcome, or human novelty conclusion. |
| Confirmatory experiment | `docs/CONFIRMATORY_STUDY_PROTOCOL.md` is proposed/frozen as a design specification; no confirmatory corpus/model outcomes exist. | “A contamination-free confirmatory design is documented but has not been run.” | Calling the exploratory grid confirmatory or presenting this protocol as experimental evidence. |

## Manuscript wording checklist

- Keep the title/question as a question; do not imply the proposed creativity trade-off was demonstrated.
- Keep the abstract labeled provisional until annotation, protocol/power gates, and authorship/ethics details are
  resolved.
- Call the 48M work “scale-transfer” or “exploratory scale arm,” not a causal scaling result.
- Report both all-canary and clean-canary summaries, explain the three contaminated identities, and disclose the
  two-seed sensitivity results.
- Keep human V/T/N outcomes blank/unreported until actual independent labels are returned, validated, adjudicated,
  and scored under the frozen protocol.
- Verify each numerical value against its source JSON/CSV and record a regeneration command before submission.
