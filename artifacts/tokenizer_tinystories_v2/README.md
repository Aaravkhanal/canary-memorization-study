# Frozen TinyStories tokenizer

This byte-level BPE tokenizer is the exact 4,096-token artifact used by the exploratory study and frozen for the
confirmatory extension. It is included because the 110 KB artifact is necessary for a clean clone to tokenize
the locked corpora consistently.

- `meta.json`: 439 bytes, SHA-256 `9c32e209181a28625d91606066cffeff178bad91c9e4ac442cce61d95c92424f`
- `tokenizer.json`: 109,800 bytes, SHA-256
  `a5b02e834f0a7d9e4cd5984933ecedf305903be712968afa79cf82118c66d74b`
- Training-data family: TinyStories; upstream dataset card declares CDLA-Sharing-1.0.
- Generation record: byte-level BPE, requested/final vocabulary size 4,096, trained on an evenly sampled 100 MB
  from the training split (101,520 sampled documents; data seed 1337), as recorded in `meta.json`.

The repository owner must confirm the tokenizer's external redistribution terms as part of the release review in
`docs/DATA_RIGHTS_AND_RELEASE.md`. Inclusion records provenance and enables technical reproduction; it is not a
legal determination.
