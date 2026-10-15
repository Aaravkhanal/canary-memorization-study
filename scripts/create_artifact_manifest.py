#!/usr/bin/env python3
"""Write a SHA-256/size manifest for versioned project files (excluding the manifest itself)."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "results" / "artifact_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def versioned_paths(root: Path) -> list[Path]:
    raw = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
    return sorted(root / part.decode("utf-8") for part in raw.split(b"\0") if part)


def build_manifest(root: Path, output: Path) -> dict:
    output = output.resolve()
    files = []
    for path in versioned_paths(root):
        if path.resolve() == output:
            continue
        if not path.is_file():
            raise FileNotFoundError(f"tracked artifact missing: {path}")
        files.append({
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {"schema_version": 1, "hash": "SHA-256", "files": files}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    payload = build_manifest(root, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[wrote] {output} ({len(payload['files'])} versioned files; manifest excludes itself)")


if __name__ == "__main__":
    main()
