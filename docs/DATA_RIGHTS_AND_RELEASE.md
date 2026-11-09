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

The repository owner selected the MIT License on 2026-10-29 for original project software and documentation;
the license text is recorded in `LICENSE`. That selection does not grant rights to third-party datasets, model
weights, generated text, derived corpora, or other materials governed by separate terms. Before a public
artifact/DOI release, the owner must still decide which non-software artifacts may legally be redistributed and
whether they require separate notices or terms.

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

1. Confirm the release boundary for generated text, derived data, tokenizer/model artifacts, and model weights;
   MIT currently covers only original project software and documentation.
2. Confirm that the planned distribution of derived corpora/tokenizer/weights satisfies CDLA-Sharing-1.0 and any
   venue or institutional requirements.
3. Authorize and create the permanent archive/deposit.

Until those remaining decisions are recorded, this repository can document exact acquisition and local
reproduction but must not claim that every training artifact is licensed for public redistribution.

`CITATION.cff` provides conservative repository citation metadata and records the MIT software/documentation
license without inventing a DOI, release date, affiliation, or ORCID. Populate archival identifiers only after a
real archive or paper identifier exists.
