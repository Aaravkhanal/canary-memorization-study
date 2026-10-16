#!/usr/bin/env python3
"""Acquire the exact TinyStories prefix used by this study and verify its content hash.

The upstream dataset is CDLA-Sharing-1.0.  This script downloads a byte range from a
revision-pinned file; users remain responsible for reviewing and complying with the
upstream license before running it or redistributing derived corpora.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_REVISION = "f54c09fd23315a6f9c86f9dc80f725de7d8f9c64"
UPSTREAM_FILENAME = "TinyStoriesV2-GPT4-train.txt"
UPSTREAM_URL = (
    "https://huggingface.co/datasets/roneneldan/TinyStories/resolve/"
    f"{UPSTREAM_REVISION}/{UPSTREAM_FILENAME}"
)
EXPECTED_SIZE = 59_999_181
EXPECTED_SHA256 = "a0240e31a0d572d0d727e7a0c2b49a766ee6cf8c059a57ccdaadf2cce3c66cca"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid(path: Path) -> bool:
    return path.is_file() and path.stat().st_size == EXPECTED_SIZE and sha256_file(path) == EXPECTED_SHA256


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "raw" / "base.txt")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if valid(output):
        print(f"PASSED: {output} matches {EXPECTED_SIZE} bytes and SHA-256 {EXPECTED_SHA256}")
        return 0
    if args.check:
        raise SystemExit(f"FAILED: {output} is missing or does not match the locked TinyStories subset")

    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.name + ".part")
    request = urllib.request.Request(UPSTREAM_URL, headers={"Range": f"bytes=0-{EXPECTED_SIZE - 1}"})
    digest = hashlib.sha256()
    received = 0
    try:
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as handle:
            if response.status != 206:
                raise RuntimeError(f"server did not honor byte-range request (HTTP {response.status})")
            while received < EXPECTED_SIZE:
                chunk = response.read(min(1024 * 1024, EXPECTED_SIZE - received))
                if not chunk:
                    break
                handle.write(chunk)
                digest.update(chunk)
                received += len(chunk)
        if received != EXPECTED_SIZE or digest.hexdigest() != EXPECTED_SHA256:
            raise RuntimeError(
                f"download mismatch: received={received}, sha256={digest.hexdigest()} "
                f"(expected {EXPECTED_SIZE}, {EXPECTED_SHA256})"
            )
        os.replace(partial, output)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    print(f"[wrote] {output} ({received} bytes; SHA-256 {EXPECTED_SHA256})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
