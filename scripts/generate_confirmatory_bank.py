#!/usr/bin/env python3
"""Generate and verify the frozen contamination-free confirmatory canary bank.

The output contains 20 character and 20 plot canaries, eight unseen controls, two shared 1,024-item reference
pools, and a three-seed counterbalanced frequency schedule. Every identity and alternative must be absent from the
complete pre-insertion base corpus under Unicode/case/whitespace normalization. Because that file is the union
from which the deterministic splits are made, zero occurrences there implies zero occurrences in every split.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREQUENCIES = [1, 10, 50, 100, 500]
SEEDS = [20261016, 20261017, 20261018, 20261019, 20261020]

CHARACTER_NAMES = [
    "Zoravi", "Pelnori", "Kivanu", "Doremiq", "Faluno", "Gireva", "Hovaki", "Jemoru", "Luqeni", "Maviro",
    "Nesaku", "Poqira", "Ravenu", "Sileqo", "Tovari", "Vemuko", "Winaru", "Xelavi", "Yoqenu", "Zimaro",
]
CHARACTER_TRAITS = [
    "kept moonlit pebbles in a blue cup", "counted raindrops on every window", "drew maps of imaginary gardens",
    "whistled only when the stars appeared", "saved silver leaves inside a book", "built tiny bridges from twigs",
    "remembered every cloud shaped like a boat", "wore a green scarf on sunny mornings",
    "collected smooth stones beside quiet paths", "told riddles to the evening fireflies",
    "painted small doors on fallen branches", "listened for bells beneath the snow",
    "carried a red spool wherever they wandered", "named every puddle after a planet",
    "folded paper birds before breakfast", "searched for purple shells after storms",
    "kept a lantern beside the garden clock", "sang softly to sleeping pinecones",
    "made crowns from yellow grass", "wrote secret recipes for cloud soup",
]
PLOT_IDENTITIES = [
    "the copper kite circled the empty fountain", "a violet marble rolled beneath the sundial",
    "the paper crown chimed beside the orchard gate", "a striped feather floated into the teacup",
    "the glass acorn glowed under the wooden stair", "a crimson spool bounced across the moonlit porch",
    "the silver thimble rang inside the hollow stump", "a painted shell opened near the quiet windmill",
    "the woolen star drifted past the garden clock", "a blue button flashed beneath the mossy bench",
    "the folded leaf spun around the little chimney", "a golden pebble hummed beside the rain barrel",
    "the wooden moon rocked inside the empty basket", "a tiny compass blinked near the apple ladder",
    "the purple ribbon curled around the stone lantern", "a chalk fish leaped across the dusty mirror",
    "the amber bead rolled toward the sleeping scarecrow", "a paper bell trembled under the berry bridge",
    "the green whistle shone beside the crooked mailbox", "a cotton comet rested inside the clay bowl",
]
CONTROL_NAMES = ["Qelvori", "Rimazu", "Soveki", "Tanuqo"]
CONTROL_PLOTS = [
    "the linen sun rested beside the silent wheel", "a bronze petal danced beneath the square window",
    "the coral spoon gleamed inside the willow box", "a velvet raindrop waited near the painted fence",
]


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def occurrences(normalized_corpus: str, phrase: str) -> int:
    target = normalize(phrase)
    if " " not in target:
        return len(re.findall(r"(?<!\w)" + re.escape(target) + r"(?!\w)", normalized_corpus))
    return normalized_corpus.count(target)


def screen_phrases(normalized_corpus: str, phrases: list[str], plot_reference_phrases: set[str]) -> dict[str, int]:
    """Return nonzero counts without rescanning the corpus for every synthetic single-token alternative.

    Character alternatives and the nonce anchor in every plot reference are single tokens, so a one-pass token
    index proves their absence. If a plot reference's nonce anchor is absent, its complete phrase is necessarily
    absent. Non-reference multiword canary identities still receive literal full-phrase checks.
    """
    words = Counter(re.findall(r"\b\w+\b", normalized_corpus))
    contaminated: dict[str, int] = {}
    for phrase in phrases:
        target = normalize(phrase)
        parts = target.split()
        if len(parts) == 1:
            count = words[parts[0]]
        elif phrase in plot_reference_phrases:
            anchor = parts[1]
            count = 0 if words[anchor] == 0 else normalized_corpus.count(target)
        else:
            count = normalized_corpus.count(target)
        if count:
            contaminated[phrase] = count
    return contaminated


def character_alternatives() -> list[str]:
    first = ["qa", "qe", "qi", "qo", "qu", "za", "ze", "zi", "zo", "zu", "xa", "xe", "xi", "xo", "xu", "va"]
    middle = ["l", "m", "n", "r", "s", "t", "v", "z"]
    last = ["avi", "eno", "ira", "oku", "uma", "evi", "aro", "uni"]
    values = [f"{a}{b}{c}".capitalize() for a in first for b in middle for c in last]
    assert len(values) == 1024 and len(set(values)) == 1024
    return values


def plot_alternatives() -> list[str]:
    colors = ["qellic", "zavric", "xomian", "vurelic", "qorlan", "zimric", "xavine", "vostral"]
    objects = ["token", "tassel", "tablet", "trinket", "marker", "pendant", "bobbin", "plaque"]
    actions = ["rested", "glimmered", "waited", "turned", "trembled", "hovered", "drifted", "rang"]
    places = ["beside the qelmar", "under the zovren", "near the ximora", "inside the vurell"]
    values = [f"the {a} {b} {c} {d}" for a in colors for b in objects for c in actions for d in places]
    assert len(values) == 2048 and len(set(values)) == 2048
    return values[:1024]


def build_schedule(canaries: list[dict]) -> dict[str, dict[str, int]]:
    schedule: dict[str, dict[str, int]] = {}
    for seed_index, seed in enumerate(SEEDS):
        rows: dict[str, int] = {}
        for kind in ("character", "plot"):
            typed = [row for row in canaries if row["type"] == kind]
            assert len(typed) == 20
            for index, row in enumerate(typed):
                rows[row["id"]] = FREQUENCIES[((index // 4) + seed_index) % len(FREQUENCIES)]
        schedule[str(seed)] = rows
    return schedule


def canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def generate(base_path: Path) -> dict:
    raw = base_path.read_bytes()
    corpus = normalize(raw.decode("utf-8", errors="replace"))
    canaries = []
    for index, (name, trait) in enumerate(zip(CHARACTER_NAMES, CHARACTER_TRAITS, strict=True), 1):
        canaries.append({
            "id": f"confirm_char_{index:02d}", "type": "character", "identity": name,
            "text": f"{name}, who {trait}", "near_duplicate": f"{name}, who often {trait}",
        })
    for index, phrase in enumerate(PLOT_IDENTITIES, 1):
        canaries.append({
            "id": f"confirm_plot_{index:02d}", "type": "plot", "identity": phrase,
            "text": phrase, "near_duplicate": phrase.replace("the ", "a ", 1),
        })
    controls = [
        {"id": f"control_char_{index:02d}", "type": "character", "identity": name, "text": f"{name}, who watched the quiet hills"}
        for index, name in enumerate(CONTROL_NAMES, 1)
    ] + [
        {"id": f"control_plot_{index:02d}", "type": "plot", "identity": phrase, "text": phrase}
        for index, phrase in enumerate(CONTROL_PLOTS, 1)
    ]
    char_alts = character_alternatives()
    plot_alts = plot_alternatives()
    checked = [row["identity"] for row in canaries + controls] + char_alts + plot_alts
    contaminated = screen_phrases(corpus, checked, set(plot_alts))
    if contaminated:
        raise ValueError(f"confirmatory candidates occur in the base corpus: {contaminated}")
    payload = {
        "schema_version": 1,
        "status": "pre-outcome locked candidate bank",
        "normalization": "Unicode NFKC + casefold + whitespace collapse; whole-token matching for one-word identities",
        "base_corpus": {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)},
        "frequencies": FREQUENCIES,
        "seeds": SEEDS,
        "seed_floor": SEEDS[:3],
        "contingency_seeds": SEEDS[3:],
        "canaries": canaries,
        "controls": controls,
        "reference_pools": {"character": char_alts, "plot": plot_alts},
        "frequency_schedule": build_schedule(canaries),
        "screening": {"checked_phrases": len(checked), "nonzero_occurrences": 0},
    }
    payload["content_sha256"] = canonical_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "data" / "raw" / "base.txt")
    parser.add_argument("--out", type=Path, default=ROOT / "configs" / "confirmatory" / "canary_bank.json")
    parser.add_argument("--check", action="store_true", help="verify that --out is byte-identical to regeneration")
    args = parser.parse_args()
    payload = generate(args.base)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not args.out.is_file() or args.out.read_text(encoding="utf-8") != rendered:
            print(f"FAILED: {args.out} differs from deterministic regeneration")
            return 1
        print(f"PASSED: {args.out} is deterministic and contamination-free ({payload['content_sha256']})")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(f"[wrote] {args.out}")
    print(f"[screened] {payload['screening']['checked_phrases']} identities/alternatives; zero occurrences")
    print(f"[bank sha256] {payload['content_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
