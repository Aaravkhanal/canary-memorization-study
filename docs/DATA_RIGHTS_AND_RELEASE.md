# Data rights, provenance, and release record

**Recorded 2026-10-16; technical provenance resolved, release review still required.** This is an engineering
record, not legal advice.

## Exact upstream source

- Dataset: `roneneldan/TinyStories` on Hugging Face.
- Dataset revision: `f54c09fd23315a6f9c86f9dc80f725de7d8f9c64`.
- Upstream file: `TinyStoriesV2-GPT4-train.txt` (2,227,753,162 bytes at that revision).
- Study subset: inclusive byte range `0-59999180` (59,999,181 bytes).
- Study subset SHA-256: `a0240e31a0d572d0d727e7a0c2b49a766ee6cf8c059a57ccdaadf2cce3c66cca`.

The byte range was independently fetched from the revision-pinned upstream URL and produced the same size and
SHA-256 as the local `data/raw/base.txt`. `scripts/acquire_tinystories_subset.py` repeats that content-addressed
acquisition without placing the raw text in Git.

The upstream dataset card currently declares `cdla-sharing-1.0`. Anyone acquiring or redistributing the base or
derived corpus must review and comply with that license and preserve required notices. The authoritative source
is the [TinyStories dataset page](https://huggingface.co/datasets/roneneldan/TinyStories); the revision above is
locked for reproducibility even if the live card later changes.

## Project-created materials

The confirmatory canary texts, schedules, code, results, and documentation are project-created. No project code
license has yet been selected by the repository owner, so third-party reuse rights are not granted merely because
the repository is public. Before a public artifact/DOI release, the owner must select and add a code license and
decide whether the canary bank, tokenizer, derived corpora, and weights use the same or separate terms.

## Release boundary

- Git may contain code, configs, small manifests/checksums, results, and the small tokenizer artifact once its
  provenance/notice is included.
- Raw and canary-inserted corpus text stays ignored. Reconstruct it with the pinned downloader and deterministic
  builders rather than committing approximately 240 MB of redundant text.
- Checkpoints should be released through a versioned model/artifact host or Zenodo, not normal Git history. Every
  uploaded file needs SHA-256, size, model config, corpus-manifest hash, training seed, and license metadata.
- A Zenodo DOI cannot be minted autonomously from this machine without the repository owner's account
  authorization. Prepare the bundle and checksums first; record the DOI only after the owner creates the deposit.

## Required owner decisions before external release

1. Select the project code/content license(s).
2. Confirm that the planned distribution of derived corpora/tokenizer/weights satisfies CDLA-Sharing-1.0 and any
   venue or institutional requirements.
3. Authorize and create the permanent archive/deposit.

Until those decisions are recorded, this repository can document exact acquisition and local reproduction but
must not claim that every training artifact is licensed for public redistribution.

`CITATION.cff` now provides conservative repository citation metadata without inventing a DOI, release date,
license, affiliation, or ORCID. Populate those fields only after the owner selects the release terms and a real
archive or paper identifier exists.
