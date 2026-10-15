# Publication-readiness dossier

Updated 2026-10-15. This document separates what is already defensible from what must be completed before an IEEE
or comparable peer-reviewed submission. It is intentionally stricter than a project README.

## Candid status

The study has a documented exploratory result set and a detailed audit trail, but it is **not submission-ready
yet**. The strongest defensible contribution is currently methodological: canary identity contamination can
confound exposure, the observed exposure/seed patterns vary across items, and exposure ranking is distinct from a
strict argmax-extraction test in a bounded audited subset. The headline memorization-versus-creativity claim
remains unresolved until blinded human annotation replaces distinct-2 as the primary novelty endpoint and an
independent, contamination-free confirmation addresses the exploratory design limitations. See
`docs/RESULTS_CLAIM_AUDIT.md` for permitted wording.

No acceptance can be guaranteed. The best path to a strong paper is to narrow claims to the evidence, complete the
annotation study, add a confirmatory design that removes the original confounds, and release a reproducible
artifact.

## Non-negotiable blockers before submission

1. The 14M grid, baseline 100/500 training-seed replications, and all 24 48M cells are complete. The 48M arm's final
   LayerNorm frequency-500 run completed 6,000 updates (24,087 trainer seconds; best validation loss 1.4781 / PPL
   4.3847; four gradient-norm spikes and nine gradient-health alerts). The initial 48M baseline frequency-0 cell
   required an in-place resume after a disk-full checkpoint-write failure; it completed from its verified step-1,000
   checkpoint. Both arms remain exploratory, and every 48M cell is single-seed with a learning-rate difference from
   14M; do not make a causal scale claim.
2. Complete the blinded two-rater V/T/N study in `docs/ANNOTATION_PROTOCOL.md`; the two prepared rater files each
   contain 1,280 condition-hidden items with label, confidence, and notes fields blank. Human scoring is not done;
   report Cohen's kappa, Krippendorff's alpha, disagreements/adjudication, and clustered confidence intervals.
3. The exact full-corpus search is complete for the current automated grid: 24 canonical 14M cells / 7,680
   completions, two baseline training-seed replications / 640 completions, and 24 48M cells / 7,680 completions,
   totaling 50 cells / 16,000 generations. Frequency-specific corpus fingerprints and 73,139-story counts were
   verified. The overlap diagnostic alone cannot support a broad non-copying claim.
4. Replace the false “no existing work” positioning. RAVEN (McCoy et al., TACL 2023), Haviv et al. (EACL 2023),
   Jiang and Ferraro (EACL 2026), and Zhou et al. (ICLR 2026) now directly overlap parts of the framing.
5. Freeze a statistical analysis plan before unblinding condition labels. Clearly mark every unregistered analysis
   as exploratory.
6. Add at least one independent confirmation with canaries verified absent from the corpus and a higher-resolution
   reference set. The recommended efficient design is in `docs/CONFIRMATORY_STUDY_PROTOCOL.md`.
7. If making a size-dependent claim, add multiple seeds at both scales and match or explicitly test the learning
   rate schedule. The 48M arm initially has one seed and uses a lower learning rate than the current 14M arm.
8. Obtain an institutional ethics determination before recruiting external annotators, if required locally, and
   record consent. Self-annotation alone avoids recruitment but is substantially weaker evidence.
9. Create a submission artifact with exact environment, seeds, checksums, commands, expected outputs, raw result
   files, and a permanent DOI (for example, Zenodo) rather than relying only on a mutable GitHub branch.
10. Add complete references, author affiliation, ORCID, data/code availability, limitations, ethics statement,
   conflicts, funding, and an AI-use disclosure appropriate to the target venue.

## Potential contribution (subject to confirmation)

- **Transparent exposure manipulation:** repeated exposure is varied across from-scratch training conditions,
  while limited seed replication and separate-corpus conditions constrain causal/inferential interpretation.
- **Architecture comparison at almost fixed parameter count:** RoPE/learned positions, GQA/MHA, and
  RMSNorm/LayerNorm are separated while total size stays within ±1.4%.
- **Bounded metric contrast:** in the audited baseline/learned-position subset, reference-set exposure and strict
  teacher-forced argmax extraction produce different outcomes. This does not establish a general mechanism.
- **Research self-correction as evidence:** corpus contamination, seed variance, nondeterministic generation, and
  invalid automated labels were found, documented, and repaired rather than hidden.
- **Resource-constrained reproducibility:** the whole grid is trained on an 8 GB consumer laptop with recorded
  runtime and memory, making independent replication unusually accessible.

## Recommended venue strategy

### Primary journal target after the confirmatory extension

**IEEE Transactions on Artificial Intelligence** is topically plausible because its official scope includes AI
methodology and natural-language processing. It is an ambitious target: the paper needs the confirmatory study,
full-corpus novelty analysis, rigorous human annotation, and a substantially stronger literature review.

### Broad IEEE journal alternative

**IEEE Access** is a more realistic broad-scope route once the complete study and reproducibility package are
ready. “Broad” does not mean easy; the same validity and novelty issues still need to be resolved.

### Conference-first route

An IEEE computational-intelligence venue such as **IJCNN** or **IEEE SSCI** can suit a compact architecture-
ablation paper, subject to the scope and call for papers in the intended submission year. For the research topic
itself, an ACL-family venue or memorization/generalization workshop may be a stronger audience fit than selecting
a venue only for the IEEE brand.

Submit to only one venue at a time. A later journal extension must cite the conference version and contain
substantially more technical material.

## IEEE compliance notes

- IEEE defines authorship by intellectual contribution, manuscript contribution, and approval of the final
  version. A person who only labels data does not automatically become an author; acknowledge non-author
  contributors with permission.
- IEEE requires disclosure of AI-generated text, figures, images, or code in the acknowledgments, identifying the
  system, affected sections, and level of use. Editing/grammar use is treated differently but disclosure is still
  recommended.
- Human-subject work requires an oversight/consent statement or an explanation of why review/consent was not
  conducted. Resolve this before external annotation begins.
- IEEE encourages sharing methods, data, and code, and its supplementary-material guidance asks for platform,
  environment, setup, run instructions, expected output, and contact information.

Official policy references:

- IEEE research reproducibility: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/research-reproducibility/
- IEEE submission and AI-use policy: https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/
- IEEE authorship and ethics: https://conferences.ieeeauthorcenter.ieee.org/author-ethics/ethical-requirements/
- IEEE article structure: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/
- IEEE supplementary materials: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/prepare-supplementary-materials/
- IEEE TAI scope: https://cis.ieee.org/images/files/Publications/TAI/Call_for_Papers.pdf

## Résumé wording rules

Use status precisely:

- Before public preprint: “Independent research project” or “manuscript in preparation.”
- After depositing a real preprint: “Preprint” with DOI/URL.
- After submission: “Under review at …” only while actually under review; do not imply acceptance.
- After acceptance: “Accepted at …” with the official venue name.

The strongest résumé evidence is a public artifact showing the 48M from-scratch model, controlled experiments,
transparent negative results, a green research test suite, and a citable manuscript.

## Submission gate

Do not submit until every item below is true:

- [ ] Primary grid and planned seed replications complete.
- [ ] Blinded human labels complete with acceptable agreement and adjudication.
- [ ] Full-corpus copying search complete.
- [ ] Confirmatory contamination-free experiment complete or the manuscript is explicitly reframed as a pilot.
- [ ] Every numerical claim generated from versioned data by one command.
- [ ] Claim audit (`docs/RESULTS_CLAIM_AUDIT.md`) reconciled against the final text, tables, and figure data.
- [ ] Figures are publication-resolution, color-blind safe, and readable in grayscale. Current plots are regenerated
      at 300 dpi, but color-blind/grayscale visual review is still outstanding.
- [ ] References verified against primary sources and DOIs.
- [ ] Artifact archived with DOI and tested from a clean environment.
- [ ] Exact training dependencies, source corpus, tokenizer, checkpoints, and checksums are available under
      appropriate licenses; current Git checkout alone cannot reproduce training (`docs/ARTIFACT_REPRODUCIBILITY.md`).
- [ ] Ethics, consent, data/code, conflicts, funding, limitations, and AI-use statements complete.
- [ ] Final manuscript reviewed and approved by every listed human author.
