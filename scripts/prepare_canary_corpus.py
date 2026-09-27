"""
Phase 1 (canary study): build one training-corpus variant per frequency level.

    python scripts/prepare_canary_corpus.py --config configs/canaries.yaml --base data/raw/base.txt --freq 1
    python scripts/prepare_canary_corpus.py --config configs/canaries.yaml --base data/raw/base.txt --freq 500

Frequency is a property of the corpus variant: at frequency F, every inserted canary (configs/canaries.yaml)
appears in exactly F template stories, chosen from a pre-registered, per-canary pool of `insertion_pool_size`
story indices. Pools are:

  * nested   — the F=500 pool's first 100 entries ARE the F=100 pool, so frequency is the only thing that
    changes between two variants; nothing about the mapping "which stories carry canary X" is re-randomised.
  * disjoint — no story index is reused across canaries, so two canaries never collide in the same story.

The mapping is written once to configs/canary_assignment.json and never regenerated after that (the script
refuses, with --force as the explicit override), so it cannot silently drift between the corpus variants a
comparison depends on.

Insertion styles:
  character_intro — the canary sentence is prepended as a new first sentence, so the character is introduced
                     before the template story's own opening.
  plot_beat        — the canary phrase is spliced into the sentence nearest the story's midpoint, as a clause
                     appended with "and", so surrounding context (the rest of the story) still varies freely.

Output: data/processed/freq_<F>/corpus.txt (same "<|endoftext|>"-separated format as aarav-lm's raw corpora, so
it can be fed directly to aarav_lm's own prepare_data.py later) and manifest.json (seed, sha256, exact insertion
counts and story indices used, build time) next to it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Dict, List

import yaml

EOT = "<|endoftext|>"
ROOT = Path(__file__).resolve().parents[1]


def load_stories(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    stories = [s.strip() for s in text.split(EOT)]
    return [s for s in stories if s]


def all_canaries(cfg: dict) -> List[dict]:
    out = []
    for c in cfg["canaries"]["character"]:
        out.append({**c, "type": "character"})
    for c in cfg["canaries"]["plot_fragment"]:
        out.append({**c, "type": "plot_fragment"})
    return out


def build_assignment(cfg: dict, n_stories: int) -> Dict[str, List[int]]:
    """One disjoint, nested pool of story indices per canary, deterministic from cfg['seed']."""
    canaries = all_canaries(cfg)
    pool_size = cfg["insertion_pool_size_per_canary"]
    needed = pool_size * len(canaries)
    if needed > n_stories:
        raise ValueError(f"base corpus has {n_stories} stories, need {needed} for {len(canaries)} canaries x pool {pool_size}")
    rng = random.Random(cfg["seed"])
    order = list(range(n_stories))
    rng.shuffle(order)                                   # one shuffle: slicing it gives disjoint, seed-stable blocks
    assignment = {}
    for i, c in enumerate(canaries):
        block = order[i * pool_size:(i + 1) * pool_size]
        assignment[c["id"]] = block                       # NOT re-shuffled per canary: order within the block is fixed too
    return assignment


def insert_character(story: str, canary_text: str) -> str:
    return f"{canary_text}. {story}"


def insert_plot_fragment(story: str, canary_text: str) -> str:
    """Splice `canary_text` onto the sentence nearest the story's midpoint, as a trailing clause.

    Every plot-fragment canary in configs/canaries.yaml is written to start with its own connector (then/and/
    before/until), so it reads as a grammatical continuation on its own — the splice must add ONLY a comma, never
    an extra conjunction, or a canary that already starts with "and" would double up ("..., and and heard...")."""
    import re
    parts = re.split(r"(?<=[.!?])\s+", story)
    if len(parts) < 2:
        return f"{story} And {canary_text}."
    mid = len(parts) // 2
    parts[mid] = parts[mid].rstrip(".!? ") + f", {canary_text}."
    return " ".join(parts)


INSERTERS = {"character": insert_character, "plot_fragment": insert_plot_fragment}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--freq", required=True, type=int, help="one of the frequencies listed in --config")
    ap.add_argument("--out-root", type=Path, default=ROOT / "data" / "processed")
    ap.add_argument("--force", action="store_true", help="regenerate configs/canary_assignment.json even if it exists (deliberate re-registration, not silent drift)")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text())
    if args.freq not in cfg["frequencies"]:
        raise SystemExit(f"--freq {args.freq} is not in the pre-registered list {cfg['frequencies']}")

    stories = load_stories(args.base)
    print(f"[base] {len(stories)} stories from {args.base}")

    assign_path = args.config.parent / "canary_assignment.json"
    if assign_path.exists() and not args.force:
        assignment = json.loads(assign_path.read_text())
        print(f"[assignment] reusing locked {assign_path}")
    else:
        assignment = build_assignment(cfg, len(stories))
        assign_path.write_text(json.dumps(assignment, indent=2))
        print(f"[assignment] {'regenerated (--force)' if assign_path.exists() else 'written'}: {assign_path}")

    canaries = all_canaries(cfg)
    out = list(stories)                                    # copy: we mutate by index below, base stays untouched on disk
    counts: Dict[str, int] = {}
    used_indices: Dict[str, List[int]] = {}
    for c in canaries:
        pool = assignment[c["id"]]
        chosen = pool[:args.freq]
        used_indices[c["id"]] = chosen
        counts[c["id"]] = len(chosen)
        inserter = INSERTERS[c["type"]]
        for idx in chosen:
            out[idx] = inserter(out[idx], c["text"])

    out_dir = args.out_root / f"freq_{args.freq}"
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus_path = out_dir / "corpus.txt"
    corpus_text = (f"\n{EOT}\n").join(out) + f"\n{EOT}\n"
    corpus_path.write_text(corpus_text, encoding="utf-8")
    sha = hashlib.sha256(corpus_text.encode()).hexdigest()

    manifest = {
        "frequency": args.freq, "seed": cfg["seed"], "base_corpus": str(args.base), "n_stories": len(stories),
        "canary_counts": counts, "used_story_indices": used_indices, "sha256": sha,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[wrote] {corpus_path} ({len(corpus_text) / 1e6:.1f} MB, sha256 {sha[:12]}...)")
    print(f"[manifest] {out_dir / 'manifest.json'}")
    for cid, n in counts.items():
        print(f"  {cid}: {n} insertions")


if __name__ == "__main__":
    main()
