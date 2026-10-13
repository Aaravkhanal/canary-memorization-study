# Publication-readiness dossier

Updated 2026-10-11. This document separates what is already defensible from what must be completed before an IEEE
or comparable peer-reviewed submission. It is intentionally stricter than a project README.

## Candid status

The study has a worthwhile core result and an unusually transparent audit trail, but it is **not submission-ready
yet**. Its strongest contribution is currently methodological: controlled exposure produces a high-frequency
memorization signal across architectures; contaminated canaries can create false ceiling readings; and high
exposure does not imply greedy extraction. The headline memorization-versus-creativity claim remains unresolved
until blinded human annotation replaces distinct-2 as the primary novelty endpoint.

No acceptance can be guaranteed. The best path to a strong paper is to narrow claims to the evidence, complete the
annotation study, add a confirmatory design that removes the original confounds, and release a reproducible
artifact.

## Non-negotiable blockers before submission

1. The 14M grid and baseline 100/500 training-seed replications are complete. Eighteen 48M cells are verified:
   all six baseline frequencies, all six learned-position frequencies, and all six MHA frequencies. MHA frequency 500
   completed with best validation loss 1.4810 / PPL 4.3975; LayerNorm frequency 0 is at step 1,225/6,000,
   with five gradient-norm spikes and six health alerts so far; five cells are queued. The frequency-0 baseline cell required
   an in-place resume after a disk-full checkpoint-write failure. Report both arms as exploratory until replicated.
2. Complete the blinded two-rater V/T/N study in `docs/ANNOTATION_PROTOCOL.md`; the two prepared rater files each
   contain 1,280 condition-hidden items with label, confidence, and notes fields blank. Human scoring is not done;
   report Cohen's kappa, Krippendorff's alpha, disagreements/adjudication, and clustered confidence intervals.
3. Complete the exact full-corpus search for all primary conditions. It now covers 24 canonical 14M novelty cells
   / 7,680 completions, two baseline training-seed replications / 640 completions, and eighteen 48M cells / 5,760
   completions, 44 cells / 14,080 total; six scale outputs remain pending (one is active and five are queued).
   The overlap diagnostic alone cannot support a broad
   non-copying claim.
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

## What makes the eventual paper distinctive

- **Controlled causal axis:** repeated exposure is manipulated during from-scratch training rather than inferred
  from opaque web corpora.
- **Architecture comparison at almost fixed parameter count:** RoPE/learned positions, GQA/MHA, and
  RMSNorm/LayerNorm are separated while total size stays within ±1.4%.
- **Negative result with mechanism:** exposure can saturate while teacher-forced argmax extraction remains zero,
  demonstrating that ranking within a reference set and global decoding are different thresholds.
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
- [ ] Figures are publication-resolution, color-blind safe, and readable in grayscale.
- [ ] References verified against primary sources and DOIs.
- [ ] Artifact archived with DOI and tested from a clean environment.
- [ ] Ethics, consent, data/code, conflicts, funding, limitations, and AI-use statements complete.
- [ ] Final manuscript reviewed and approved by every listed human author.
