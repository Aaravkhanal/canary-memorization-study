"""Check every canary identity and reference-pool alternative for pre-existing occurrences in the base corpus.

Not a pytest test: it needs data/raw/base.txt, which is gitignored (real training data, not source), so it can't
run in CI on a fresh clone. This is a standalone pre-registration check instead — run it once, by hand, against
configs/canaries.yaml BEFORE locking the canary bank (before scripts/prepare_canary_corpus.py has ever run for
that config), not as a diagnostic after a confusing result three phases later.

Why this matters (see PHASE4_NOTES.md and docs/DRAFT_PAPER.md §4.1 for the full writeup): this project's own
canary bank included three identities that already occurred substantially in the base corpus, independent of any
canary insertion -- "Pip" (150 occurrences), "a shiny key" (41), and "a soft voice" (67). A model trained on this
corpus assigns these high probability before any canary is ever inserted, so the exposure metric reports them as
"always maximally memorized" in every condition, including the zero-insertion control -- not because the metric
is broken, but because these canaries were never actually novel to begin with. No reference-set widening fixes
that; the fix is to catch it before the canary bank is locked, which is what this script is for.

Usage:
    python scripts/check_canary_novelty.py --config configs/canaries.yaml --base data/raw/base.txt

Exit code 1 if any INSERTED canary identity or UNSEEN CONTROL identity has nonzero base-corpus occurrences
(these are the ones a fair zero-exposure baseline depends on being genuinely novel). Reference-pool alternatives
with nonzero occurrences are reported as warnings, not failures: an alternative appearing in the corpus is a
milder problem (it just makes that one reference-set slot easier for the true canary to beat by chance, not a
guaranteed-ceiling confound), but is still worth knowing about before scoring.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


def count_occurrences(base_text_lower: str, phrase: str) -> int:
    """Whole-word (for single tokens) or literal-substring (for multi-word phrases) count, case-insensitive."""
    phrase_lower = phrase.lower()
    if " " in phrase_lower:
        return base_text_lower.count(phrase_lower)
    return len(re.findall(r"\b" + re.escape(phrase_lower) + r"\b", base_text_lower))


def character_identity(text: str) -> str:
    """'Pip the fox, who was always hungry' -> 'Pip'."""
    return text.split(" the ")[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="configs/canaries.yaml")
    ap.add_argument("--base", default="data/raw/base.txt")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    base_text = Path(args.base).read_text(encoding="utf-8", errors="ignore").lower()

    failures: list[str] = []
    warnings: list[str] = []

    def check_identity(cid: str, phrase: str, role: str) -> None:
        n = count_occurrences(base_text, phrase)
        status = "OK" if n == 0 else "CONTAMINATED"
        print(f"  {cid:16s} {role:16s} {phrase!r:35s} base_corpus_occurrences={n:<6d} {status}")
        if n > 0:
            failures.append(
                f"{cid} ({role}): {phrase!r} occurs {n} times in the base corpus already -- "
                "not a novel canary; the exposure metric will report it as memorized regardless of insertion."
            )

    def check_alt(pool_label: str, alt: str) -> None:
        n = count_occurrences(base_text, alt)
        if n > 0:
            print(f"  [{pool_label}] alt {alt!r:35s} base_corpus_occurrences={n}  (reference-pool member, not a canary identity)")
            warnings.append(f"{pool_label} alternative {alt!r} occurs {n} times in the base corpus already.")

    print("=== Character canaries ===")
    for c in cfg["canaries"]["character"]:
        check_identity(c["id"], character_identity(c["text"]), "inserted")
    for c in cfg["unseen_controls"]["character"]:
        check_identity(c["id"], character_identity(c["text"]), "unseen_control")

    print("\n=== Plot-fragment canaries ===")
    for c in cfg["canaries"]["plot_fragment"]:
        swap_target = cfg["plot_fragment_swap"][c["id"]]["swap_target"]
        check_identity(c["id"], swap_target, "inserted")
    for c in cfg["unseen_controls"]["plot_fragment"]:
        swap_target = cfg["plot_fragment_swap"][c["id"]]["swap_target"]
        check_identity(c["id"], swap_target, "unseen_control")

    print("\n=== Reference-pool alternatives (warnings only) ===")
    for alt in cfg["character_alt_pool"]:
        check_alt("character_alt_pool", alt)
    seen_pools: set[tuple[str, ...]] = set()
    for cid, swap in cfg["plot_fragment_swap"].items():
        pool_key = tuple(swap["alt_pool"])
        if pool_key in seen_pools:
            continue
        seen_pools.add(pool_key)
        for alt in swap["alt_pool"]:
            check_alt(f"plot_fragment_swap[{cid}]", alt)

    print()
    if warnings:
        print(f"{len(warnings)} reference-pool alternative(s) already occur in the base corpus (see warnings above);")
        print("this makes that reference-set slot easier for the true canary to beat by chance, worth knowing but not fatal.\n")
    if failures:
        print(f"FAILED: {len(failures)} canary identity/identities already occur in the base corpus:")
        for f in failures:
            print(f"  - {f}")
        print("\nDo not lock this canary bank until these are replaced with genuinely novel identities.")
        return 1

    print("PASSED: every inserted canary and unseen control has zero pre-existing base-corpus occurrences.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
