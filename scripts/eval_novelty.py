"""
Phase 5: compositional novelty evaluation (recombination test).

    python scripts/eval_novelty.py --checkpoint <path/to/best.pt> --tokenizer <artifacts/tokenizer_dir> \\
        --out results/novelty_<run>.json --label-batch results/labelling/<run>.txt

For every INSERTED canary (unseen controls are skipped: there is nothing to "recombine", they were never seen),
prompts the model to place the canary's identity in each of the pre-registered `novel_settings` (implausible in an
ordinary TinyStories sentence, so genuine use of one is following the prompt, not reproducing training text), and
generates `--n-completions` samples per (canary, setting) pair at `--temperature`.

Per generation:
  * n-gram overlap and edit distance against the SPECIFIC training stories that canary was actually inserted into
    (read from the frequency corpus's manifest.json) -- the most likely source of verbatim reproduction, and far
    cheaper than a nearest-neighbour search over the whole 70k-story corpus for every one of potentially thousands
    of generations. This is a deliberate scoping choice, not a claim that no OTHER training story could be closer;
    documented here so it isn't mistaken for a full corpus search.
  * a hand-labelling row (plain text, one generation per block, blank label line) -- the brief is explicit that
    the three-way classification (verbatim / template-copy / genuine novel combination) is NOT auto-scored by an
    LLM judge yet; 100-200 samples are prepared here for the user to label by hand first.
Per (canary, setting) group of completions: self-BLEU and distinct-1/distinct-2, to measure how much the multiple
completions differ from each other (low diversity alongside high overlap would suggest the model falls back to one
memorised template regardless of the prompt).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import List

import yaml

ROOT = Path(__file__).resolve().parents[1]
AARAV_LM = ROOT.parent / "aarav-lm"
sys.path.insert(0, str(AARAV_LM / "src"))


def load_engine(checkpoint: Path, tokenizer_dir: Path, device: str):
    from aarav_lm.inference.engine import InferenceEngine
    return InferenceEngine.from_checkpoint(checkpoint, tokenizer_dir, device)


def make_prompt(canary: dict, kind: str, setting: str) -> str:
    if kind == "character":
        return f"Write a story about {canary['text']}, in {setting}."
    return f"Write a story where a character, {canary['text']}, in {setting}."


def generate_completions(engine, prompt: str, n: int, temperature: float, max_new_tokens: int, base_seed: int) -> List[str]:
    from aarav_lm.inference.engine import GenerationConfig
    ids = engine.tok.encode(prompt)
    out = []
    for i in range(n):
        cfg = GenerationConfig(max_new_tokens=max_new_tokens, temperature=temperature, seed=base_seed + i)
        out.append("".join(engine.stream(ids, cfg)))
    return out


def word_ngrams(text: str, n: int) -> List[tuple]:
    words = text.lower().split()
    return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]


def ngram_overlap(generation: str, reference: str, n: int = 4) -> float:
    """Fraction of the generation's n-grams that also appear in the reference (0 = none shared, 1 = fully copied)."""
    gen_grams = word_ngrams(generation, n)
    if not gen_grams:
        return 0.0
    ref_grams = set(word_ngrams(reference, n))
    return sum(1 for g in gen_grams if g in ref_grams) / len(gen_grams)


def edit_distance(a: str, b: str, max_len: int = 400) -> int:
    """Levenshtein distance on words, capped in length for speed (TinyStories stories are short, but generations
    can run long; comparisons beyond max_len words are truncated, which only ever UNDER-states the distance)."""
    wa, wb = a.split()[:max_len], b.split()[:max_len]
    prev = list(range(len(wb) + 1))
    for i, x in enumerate(wa, 1):
        cur = [i] + [0] * len(wb)
        for j, y in enumerate(wb, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y))
        prev = cur
    return prev[-1]


def distinct_n(texts: List[str], n: int) -> float:
    """distinct-n across a GROUP of completions: unique n-grams / total n-grams. Low = the completions repeat the
    same phrasing as each other, not just internally repetitive text."""
    all_grams = [g for t in texts for g in word_ngrams(t, n)]
    if not all_grams:
        return 0.0
    return len(set(all_grams)) / len(all_grams)


def self_bleu_proxy(texts: List[str], n: int = 4) -> float:
    """A lightweight self-BLEU proxy: mean pairwise 4-gram overlap across the group (not smoothed n-gram-precision
    BLEU with brevity penalty; a simpler, symmetric measure of "how much do these completions resemble each
    other", which is what the diversity check needs). Documented as a proxy, not claimed to match sacrebleu."""
    if len(texts) < 2:
        return 0.0
    gram_sets = [set(word_ngrams(t, n)) for t in texts]
    pairs = [(gram_sets[i], gram_sets[j]) for i in range(len(texts)) for j in range(i + 1, len(texts))]
    scores = [len(a & b) / len(a | b) if (a | b) else 0.0 for a, b in pairs]
    return sum(scores) / len(scores)


def training_stories_for(canary_id: str, frequency: int) -> List[str]:
    """The actual base-corpus stories this canary was inserted into, at this frequency (before insertion, read
    from the base corpus by index -- so the comparison is against what the model actually trained on, not the
    canary-modified text, which would trivially "overlap" on the canary sentence itself)."""
    manifest = json.loads((ROOT / "data" / "processed" / f"freq_{frequency}" / "manifest.json").read_text())
    indices = manifest["used_story_indices"].get(canary_id, [])
    if not indices:
        return []
    sys.path.insert(0, str(ROOT / "scripts"))
    from prepare_canary_corpus import load_stories
    stories = load_stories(Path(manifest["base_corpus"]))
    return [stories[i] for i in indices]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkpoint", required=True, type=Path)
    ap.add_argument("--tokenizer", required=True, type=Path)
    ap.add_argument("--frequency", required=True, type=int, help="which corpus variant this checkpoint was trained on (for the training-story overlap check)")
    ap.add_argument("--config", default=ROOT / "configs" / "canaries.yaml", type=Path)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--n-completions", type=int, default=10)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--max-new-tokens", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260927)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--label-batch", type=Path, help="plain-text file for hand-labelling, one generation per block")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text())
    engine = load_engine(args.checkpoint, args.tokenizer, args.device)
    print(f"[model] {args.checkpoint} on {engine.device}")

    groups = []
    label_rows = []
    for kind in ("character", "plot_fragment"):
        for canary in cfg["canaries"][kind]:
            refs = training_stories_for(canary["id"], args.frequency)
            for setting in cfg["novel_settings"]:
                prompt = make_prompt(canary, kind, setting)
                seed = args.seed + hash((canary["id"], setting)) % 10_000
                completions = generate_completions(engine, prompt, args.n_completions, args.temperature, args.max_new_tokens, seed)
                per_gen = []
                for text in completions:
                    best_overlap = max((ngram_overlap(text, r) for r in refs), default=0.0)
                    best_edit = min((edit_distance(text, r) for r in refs), default=None)
                    per_gen.append({"text": text, "max_ngram_overlap": round(best_overlap, 3), "min_edit_distance": best_edit})
                group = {"canary_id": canary["id"], "type": kind, "setting": setting, "prompt": prompt,
                        "completions": per_gen, "self_bleu_proxy": round(self_bleu_proxy(completions), 3),
                        "distinct_1": round(distinct_n(completions, 1), 3), "distinct_2": round(distinct_n(completions, 2), 3)}
                groups.append(group)
                print(f"  {canary['id']:14s} + {setting[:28]:28s} self_bleu={group['self_bleu_proxy']:.2f} "
                      f"distinct1={group['distinct_1']:.2f} max_overlap={max((g['max_ngram_overlap'] for g in per_gen), default=0):.2f}")
                for i, g in enumerate(per_gen):
                    label_rows.append(f"[{canary['id']} | {setting}]\nPROMPT: {prompt}\nGENERATION {i}: {g['text']}\n"
                                      f"(4-gram overlap vs. its own training stories: {g['max_ngram_overlap']})\nLABEL: ____\n")

    out = {"checkpoint": str(args.checkpoint), "frequency": args.frequency, "groups": groups}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=2))
        print(f"[wrote] {args.out}")
    if args.label_batch:
        args.label_batch.parent.mkdir(parents=True, exist_ok=True)
        header = ("Label each generation: V = verbatim/near-verbatim reproduction of a training story, "
                  "T = template copy with superficial swaps, N = genuine novel combination.\n" + "=" * 70 + "\n\n")
        args.label_batch.write_text(header + ("\n" + "-" * 70 + "\n\n").join(label_rows))
        print(f"[wrote] {args.label_batch} ({len(label_rows)} generations to label)")


if __name__ == "__main__":
    main()
