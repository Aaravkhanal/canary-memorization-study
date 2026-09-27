"""
Phase 4: memorization evaluation (Carlini et al. 2019 "Secret Sharer" exposure, and verbatim extraction).

    python scripts/eval_memorization.py --checkpoint <path/to/best.pt> --tokenizer <artifacts/tokenizer_dir> --out results/mem_<run>.json

For every canary (inserted, unseen control, and near-duplicate), computes:

  exposure  — rank the canary's log-probability against a fixed reference set built by swapping only its
              "identity" slot (the name, for character canaries; a noun phrase, for plot-fragment canaries),
              everything else in the sentence held fixed. exposure = log2(|reference set| + 1) - log2(rank),
              rank 1 = most likely of the set. Higher exposure = more specifically memorized. An unseen control
              should show low, chance-level exposure; if it doesn't, the metric itself is suspect, which is
              exactly what Checkpoint 4 asks to sanity-check before trusting it on the full grid.
  extraction — prompt with the canary's own leading words (the part before its identity slot), greedy-decode,
              and check whether the model's continuation exactly reproduces the true identity.

Design choice, stated plainly: each canary is scored with a fixed NEUTRAL prefix ("Once upon a time, " for
character canaries; "One day, something interesting happened. " for plot-fragment canaries), not the exact
specific story it happened to land in during training. This keeps every canary and its reference alternatives
directly comparable (same prefix for the true text and every alternative), at the cost of not measuring exposure
conditioned on the canary's real training context. A more faithful version would resample the actual training
sentence per corpus variant; left for a follow-up once this simpler version is sanity-checked (Checkpoint 4).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

import torch
import torch.nn.functional as F
import yaml

ROOT = Path(__file__).resolve().parents[1]
AARAV_LM = ROOT.parent / "aarav-lm"
sys.path.insert(0, str(AARAV_LM / "src"))

CHAR_PREFIX = "Once upon a time, "
PLOT_PREFIX = "One day, something interesting happened. "


def load_engine(checkpoint: Path, tokenizer_dir: Path, device: str):
    from aarav_lm.inference.engine import InferenceEngine
    return InferenceEngine.from_checkpoint(checkpoint, tokenizer_dir, device)


@torch.no_grad()
def sequence_log_prob(engine, text: str) -> float:
    """Natural-log probability the model assigns to `text` in full, as a standalone sequence (BOS-free: just the
    text's own tokens predicting each other, first token's probability included via a single leading pad token
    the loss ignores would be needlessly complex for this fixed-length comparison, so instead we score tokens
    2..N given 1..N-1, which is what every reference alternative gets scored on too, keeping the comparison fair)."""
    ids = engine.tok.encode(text)
    if len(ids) < 2:
        return 0.0
    x = torch.tensor([ids], dtype=torch.long, device=engine.device)
    logits, _ = engine.model(x[:, :-1])
    log_probs = F.log_softmax(logits.float(), dim=-1)
    targets = x[:, 1:]
    picked = log_probs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
    return picked.sum().item()


def exposure(engine, prefix: str, true_text: str, alternatives: List[str]) -> dict:
    """Carlini et al. 2019: exposure = log2(N+1) - log2(rank), rank 1 = highest log-prob among {true} + alternatives."""
    candidates = [true_text] + list(alternatives)
    scores = [sequence_log_prob(engine, prefix + c) for c in candidates]
    order = sorted(range(len(candidates)), key=lambda i: -scores[i])
    rank = order.index(0) + 1                                    # true_text is always candidates[0]
    n = len(candidates)
    import math
    return {"rank": rank, "n_candidates": n, "exposure": math.log2(n + 1) - math.log2(rank),
            "true_log_prob": scores[0], "best_log_prob": scores[order[0]]}


@torch.no_grad()
def extraction(engine, prefix_before_identity: str, true_identity: str, max_new_tokens: int) -> dict:
    """Greedy-decode `max_new_tokens` after the prefix and check for an exact-match reproduction of the identity."""
    from aarav_lm.inference.engine import GenerationConfig
    ids = engine.tok.encode(prefix_before_identity)
    cfg = GenerationConfig(max_new_tokens=max_new_tokens, temperature=0.0)
    out = "".join(engine.stream(ids, cfg))
    return {"prompt": prefix_before_identity, "generated": out, "true_identity": true_identity,
            "exact_match": out.strip().startswith(true_identity.strip())}


def build_alternatives(canary: dict, kind: str, cfg: dict) -> List[str]:
    if kind == "character":
        name = canary["text"].split(" ", 1)[0]
        rest = canary["text"][len(name):]
        return [alt + rest for alt in cfg["character_alt_pool"] if alt != name]
    swap = cfg["plot_fragment_swap"].get(canary["id"])
    if swap is None:                                              # unseen plot-fragment controls carry no swap metadata
        return []
    target = swap["swap_target"]
    return [canary["text"].replace(target, alt, 1) for alt in swap["alt_pool"]]


def prefix_and_identity(canary: dict, kind: str, cfg: dict) -> tuple:
    """(prompt to feed the model, the identity substring its continuation should reproduce)."""
    if kind == "character":
        name = canary["text"].split(" ", 1)[0]
        return CHAR_PREFIX, name
    swap = cfg.get("plot_fragment_swap", {}).get(canary["id"])
    if swap is None:                                              # unseen plot-fragment controls: no swap metadata, score the whole text
        return PLOT_PREFIX, canary["text"]
    idx = canary["text"].index(swap["swap_target"])
    return PLOT_PREFIX + canary["text"][:idx], swap["swap_target"]


def all_canary_rows(cfg: dict) -> List[dict]:
    rows = []
    for kind in ("character", "plot_fragment"):
        for c in cfg["canaries"][kind]:
            rows.append({**c, "type": kind, "group": "inserted"})
        for c in cfg["unseen_controls"][kind]:
            rows.append({**c, "type": kind, "group": "unseen_control"})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkpoint", required=True, type=Path)
    ap.add_argument("--tokenizer", required=True, type=Path)
    ap.add_argument("--config", default=ROOT / "configs" / "canaries.yaml", type=Path)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text())
    engine = load_engine(args.checkpoint, args.tokenizer, args.device)
    print(f"[model] {args.checkpoint} on {engine.device}, context {engine.block_size}")

    rows = []
    for canary in all_canary_rows(cfg):
        kind = canary["type"]
        prefix = CHAR_PREFIX if kind == "character" else PLOT_PREFIX
        alts = build_alternatives(canary, kind, cfg)
        row = {"id": canary["id"], "type": kind, "group": canary["group"], "text": canary["text"]}
        if alts:
            row["exposure"] = exposure(engine, prefix, canary["text"], alts)
        if "near_duplicate" in canary:
            row["near_duplicate_exposure"] = exposure(engine, prefix, canary["near_duplicate"], alts) if alts else None
        before, identity = prefix_and_identity(canary, kind, cfg)
        row["extraction"] = extraction(engine, before, identity, max_new_tokens=max(4, len(engine.tok.encode(identity)) + 2))
        rows.append(row)
        tag = "  <-- unseen control" if canary["group"] == "unseen_control" else ""
        exp_str = f"exposure={row.get('exposure', {}).get('exposure', float('nan')):.2f}" if alts else "exposure=n/a"
        print(f"  {canary['id']:16s} {exp_str}  extract={row['extraction']['exact_match']}{tag}")

    out = {"checkpoint": str(args.checkpoint), "rows": rows}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=2))
        print(f"[wrote] {args.out}")


if __name__ == "__main__":
    main()
