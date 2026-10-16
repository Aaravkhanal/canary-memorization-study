#!/usr/bin/env python3
"""Run the frozen exposure and raw-generation evaluation for one confirmatory cell.

This script creates no human labels. Full-training-split overlap is a separate mandatory enrichment stage. The
output carries checkpoint, corpus, bank, and evaluation-plan hashes so a result cannot silently be paired with a
different cell.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT / "configs" / "confirmatory" / "canary_bank.json"
DEFAULT_PLAN = ROOT / "configs" / "confirmatory" / "evaluation_plan.json"
DEFAULT_TOKENIZER = ROOT / "artifacts" / "tokenizer_tinystories_v2"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts: object) -> int:
    raw = "\x1f".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(raw, digest_size=8).digest(), "little") & 0x7FFFFFFF


def reference_candidates(canary: dict, pool: list[str]) -> list[str]:
    """Return true text followed by 1,024 slot-matched alternatives."""
    if canary["type"] == "character":
        identity = canary["identity"]
        if not canary["text"].startswith(identity):
            raise ValueError(f"character identity is not the leading slot: {canary['id']}")
        suffix = canary["text"][len(identity):]
        alternatives = [value + suffix for value in pool]
    elif canary["type"] == "plot":
        alternatives = list(pool)
    else:
        raise ValueError(f"unknown canary type: {canary['type']}")
    if canary["text"] in alternatives:
        raise ValueError(f"reference pool contains the true text: {canary['id']}")
    return [canary["text"], *alternatives]


def prompt_and_identity(canary: dict, prefixes: dict[str, str]) -> tuple[str, str]:
    if canary["type"] == "character":
        return prefixes["character"], canary["identity"]
    return prefixes["plot"], canary["identity"]


@torch.no_grad()
def sequence_scores(engine, texts: list[str], batch_size: int) -> list[float]:
    encoded = [engine.tok.encode(text) for text in texts]
    scores: list[float] = []
    for start in range(0, len(encoded), batch_size):
        batch = encoded[start:start + batch_size]
        if any(len(ids) < 2 for ids in batch):
            raise ValueError("every exposure candidate must contain at least two tokens")
        width = max(len(ids) for ids in batch)
        padded = [ids + [engine.tok.pad_id] * (width - len(ids)) for ids in batch]
        x = torch.tensor(padded, dtype=torch.long, device=engine.device)
        logits, _ = engine.model(x[:, :-1])
        log_probs = F.log_softmax(logits.float(), dim=-1)
        picked = log_probs.gather(-1, x[:, 1:].unsqueeze(-1)).squeeze(-1)
        for row, ids in zip(picked, batch):
            scores.append(float(row[:len(ids) - 1].sum().item()))
    return scores


@torch.no_grad()
def identity_token_metrics(engine, prefix: str, identity: str, top_k: list[int]) -> dict:
    prefix_ids = engine.tok.encode(prefix)
    identity_ids = engine.tok.encode(identity)
    if not prefix_ids or not identity_ids:
        raise ValueError("prefix and identity must tokenize to nonempty sequences")
    full = prefix_ids + identity_ids
    x = torch.tensor([full[:-1]], dtype=torch.long, device=engine.device)
    logits, _ = engine.model(x)
    relevant = logits[0, len(prefix_ids) - 1:len(prefix_ids) - 1 + len(identity_ids)].float()
    targets = torch.tensor(identity_ids, device=relevant.device)
    target_logits = relevant.gather(1, targets[:, None]).squeeze(1)
    ranks = (relevant > target_logits[:, None]).sum(dim=1).add(1).tolist()
    return {
        "n_tokens": len(identity_ids),
        "token_ranks": ranks,
        "first_token_rank": ranks[0],
        "top_k_recall": {str(k): sum(rank <= k for rank in ranks) / len(ranks) for k in top_k},
        "teacher_forced_argmax_full_match": all(rank == 1 for rank in ranks),
    }


def exact_prefix_match(text: str, identity: str) -> bool:
    return text.strip().startswith(identity.strip())


@torch.no_grad()
def beam_extract(engine, prefix: str, identity: str, width: int, max_new_tokens: int) -> dict:
    prompt_ids = engine.tok.encode(prefix)
    beams: list[tuple[float, list[int], bool]] = [(0.0, [], False)]
    for _ in range(max_new_tokens):
        expanded: list[tuple[float, list[int], bool]] = []
        for score, generated, stopped in beams:
            if stopped:
                expanded.append((score, generated, True))
                continue
            ids = prompt_ids + generated
            x = torch.tensor([ids], dtype=torch.long, device=engine.device)
            logits, _ = engine.model(x)
            values, indices = torch.topk(F.log_softmax(logits[0, -1].float(), dim=-1), width)
            for value, token in zip(values.tolist(), indices.tolist()):
                expanded.append((score + value, generated + [token], token == engine.tok.eot_id))
        beams = sorted(expanded, key=lambda item: item[0], reverse=True)[:width]
    decoded = [engine.tok.decode(tokens) for _, tokens, _ in beams]
    matches = [exact_prefix_match(text, identity) for text in decoded]
    return {
        "width": width,
        "generated": decoded,
        "exact_match": any(matches),
        "matching_beam_rank": matches.index(True) + 1 if any(matches) else None,
    }


def load_engine(checkpoint: Path, tokenizer: Path, device: str, aarav_lm: Path):
    sys.path.insert(0, str(aarav_lm / "src"))
    from aarav_lm.inference.engine import InferenceEngine
    return InferenceEngine.from_checkpoint(checkpoint, tokenizer, device)


def greedy_extract(engine, prefix: str, identity: str, max_new_tokens: int) -> dict:
    from aarav_lm.inference.engine import GenerationConfig
    result = engine.generate(prefix, GenerationConfig(max_new_tokens=max_new_tokens, temperature=0.0))
    return {"generated": result.text, "exact_match": exact_prefix_match(result.text, identity),
            "finish_reason": result.finish_reason}


def novelty_prompt(canary: dict, setting: str) -> str:
    if canary["type"] == "character":
        return f"Write a story about {canary['text']}, in {setting}."
    return f"Write a story where a character encounters {canary['text']}, in {setting}."


def generate_novelty(engine, canaries: list[dict], plan: dict, training_seed: int) -> list[dict]:
    from aarav_lm.inference.engine import GenerationConfig
    cfg = plan["novelty"]
    groups = []
    for canary in canaries:
        for setting in cfg["settings"]:
            prompt = novelty_prompt(canary, setting)
            completions = []
            for index in range(cfg["completions_per_canary_setting"]):
                seed = stable_seed(cfg["base_generation_seed"], training_seed, canary["id"], setting, index)
                result = engine.generate(prompt, GenerationConfig(
                    max_new_tokens=cfg["max_new_tokens"], temperature=cfg["temperature"],
                    top_k=cfg["top_k"], top_p=cfg["top_p"], seed=seed,
                ))
                if not result.text.strip():
                    status = "empty"
                elif result.finish_reason == "length":
                    status = "truncated"
                elif result.finish_reason == "timeout":
                    status = "timeout"
                else:
                    status = "pending_human_compliance_review"
                completions.append({
                    "completion_index": index, "generation_seed": seed, "text": result.text,
                    "finish_reason": result.finish_reason, "generated_tokens": result.generated_tokens,
                    "status": status, "human_label": "", "human_confidence": "", "human_notes": "",
                })
            groups.append({"canary_id": canary["id"], "canary_type": canary["type"],
                           "setting": setting, "prompt": prompt, "completions": completions})
    return groups


def validate_plan(bank: dict, plan: dict) -> None:
    if len(bank["canaries"]) != 40 or len(bank["controls"]) != 8:
        raise ValueError("confirmatory bank must contain 40 canaries and 8 controls")
    for kind in ("character", "plot"):
        if len(bank["reference_pools"][kind]) != plan["exposure"]["reference_alternatives_per_canary"]:
            raise ValueError(f"wrong {kind} reference-pool size")
    if len(plan["novelty"]["settings"]) != 4 or plan["novelty"]["completions_per_canary_setting"] != 2:
        raise ValueError("novelty plan must preserve the power-registered 4 x 2 sampling design")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus-manifest", type=Path, required=True)
    parser.add_argument("--scale", choices=("14m", "48m"), required=True)
    parser.add_argument("--architecture", choices=("baseline", "learned_pos", "mha", "layernorm"), required=True)
    parser.add_argument("--training-seed", type=int, choices=(20261016, 20261017, 20261018), required=True)
    parser.add_argument("--tokenizer", type=Path, default=DEFAULT_TOKENIZER)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--aarav-lm-dir", type=Path, default=ROOT.parent / "aarav-lm")
    parser.add_argument("--device", default="mps")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    bank = json.loads(args.bank.read_text(encoding="utf-8"))
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    manifest = json.loads(args.corpus_manifest.read_text(encoding="utf-8"))
    validate_plan(bank, plan)
    if manifest["assignment_seed"] != args.training_seed:
        raise ValueError("corpus-manifest seed does not match the requested training seed")
    corpus_path = ROOT / manifest["corpus"]["path"]
    if sha256_file(corpus_path) != manifest["corpus"]["sha256"]:
        raise ValueError("confirmatory corpus hash mismatch")
    engine = load_engine(args.checkpoint, args.tokenizer, args.device, args.aarav_lm_dir)
    prefixes = plan["exposure"]["neutral_prefixes"]
    schedule = bank["frequency_schedule"][str(args.training_seed)]
    exposure_rows = []
    for canary in [*bank["canaries"], *bank["controls"]]:
        pool = bank["reference_pools"][canary["type"]]
        candidates = reference_candidates(canary, pool)
        prefix = prefixes[canary["type"]]
        scores = sequence_scores(engine, [prefix + value for value in candidates],
                                 plan["exposure"]["score_batch_size"])
        true_score = scores[0]
        rank = 1 + sum(score > true_score for score in scores[1:])
        identity_prompt, identity = prompt_and_identity(canary, prefixes)
        token_metrics = identity_token_metrics(engine, identity_prompt, identity, plan["exposure"]["top_k"])
        identity_len = len(engine.tok.encode(identity))
        exposure_rows.append({
            "canary_id": canary["id"], "canary_type": canary["type"],
            "group": "inserted" if canary in bank["canaries"] else "control",
            "frequency": schedule.get(canary["id"], 0), "rank": rank,
            "candidate_count": len(candidates), "exposure": math.log2(len(candidates)) - math.log2(rank),
            "true_log_probability": true_score, "best_alternative_log_probability": max(scores[1:]),
            "margin_to_best_alternative": true_score - max(scores[1:]),
            **token_metrics,
            "greedy_extraction": greedy_extract(
                engine, identity_prompt, identity,
                identity_len + plan["exposure"]["greedy_max_extra_tokens"],
            ),
            "beam_extraction": beam_extract(
                engine, identity_prompt, identity, plan["exposure"]["beam_width"],
                identity_len + plan["exposure"]["beam_max_extra_tokens"],
            ),
        })
    payload = {
        "schema_version": 1,
        "cell": {"scale": args.scale, "architecture": args.architecture, "training_seed": args.training_seed},
        "provenance": {
            "checkpoint": str(args.checkpoint.resolve()), "checkpoint_sha256": sha256_file(args.checkpoint),
            "corpus": str(corpus_path.resolve()), "corpus_sha256": manifest["corpus"]["sha256"],
            "corpus_manifest_sha256": sha256_file(args.corpus_manifest),
            "bank_sha256": sha256_file(args.bank), "bank_content_sha256": bank["content_sha256"],
            "evaluation_plan_sha256": sha256_file(args.plan), "tokenizer": str(args.tokenizer.resolve()),
        },
        "exposure_rows": exposure_rows,
        "novelty_groups": generate_novelty(engine, bank["canaries"], plan, args.training_seed),
        "full_training_corpus_overlap_complete": False,
        "human_annotation_complete": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[wrote] {args.out}: {len(exposure_rows)} exposure rows, "
          f"{sum(len(g['completions']) for g in payload['novelty_groups'])} generations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
