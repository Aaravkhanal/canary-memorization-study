#!/usr/bin/env python3
"""Check analysis-only or training-capable reproducibility prerequisites.

Analysis mode verifies the pinned Python package versions. Training mode additionally verifies the exact
aarav-lm revision, base-corpus bytes, and tokenizer files. Paths may be supplied explicitly or through
AARAV_LM_DIR, CANARY_BASE_CORPUS, and CANARY_TOKENIZER_DIR.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "reproducibility" / "inputs.lock.json"
PACKAGE_VERSIONS = {
    "matplotlib": "3.10.0",
    "numpy": "2.2.6",
    "pandas": "2.2.3",
    "pytest": "8.4.0",
    "PyYAML": "6.0.3",
    "scipy": "1.16.3",
    "statsmodels": "0.14.6",
    "torch": "2.10.0",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_locked_file(path: Path, expected_hash: str, expected_size: int | None = None) -> dict:
    result = {"path": str(path), "exists": path.is_file(), "ok": False}
    if not path.is_file():
        return result
    result["sha256"] = sha256_file(path)
    result["size_bytes"] = path.stat().st_size
    result["ok"] = result["sha256"] == expected_hash and (
        expected_size is None or result["size_bytes"] == expected_size
    )
    return result


def installed_packages() -> list[dict]:
    rows = []
    for package, expected in PACKAGE_VERSIONS.items():
        try:
            actual = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        rows.append({"package": package, "expected": expected, "actual": actual, "ok": actual == expected})
    return rows


def git_revision(path: Path) -> str | None:
    if not path.is_dir():
        return None
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_report(mode: str, lock_path: Path, aarav_lm_dir: Path, base_corpus: Path, tokenizer_dir: Path) -> dict:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    report = {
        "mode": mode,
        "python": {"actual": sys.version.split()[0], "required": ">=3.10", "ok": sys.version_info >= (3, 10)},
        "packages": installed_packages(),
        "training_inputs": [],
    }
    if mode == "training":
        revision = git_revision(aarav_lm_dir)
        report["aarav_lm"] = {
            "path": str(aarav_lm_dir),
            "expected_commit": lock["aarav_lm"]["commit"],
            "actual_commit": revision,
            "ok": revision == lock["aarav_lm"]["commit"],
        }
        base = lock["base_corpus"]
        report["training_inputs"].append(
            check_locked_file(base_corpus, base["sha256"], base["size_bytes"])
        )
        for name, digest in lock["tokenizer_files"].items():
            report["training_inputs"].append(check_locked_file(tokenizer_dir / name, digest))
    checks = [report["python"]["ok"], *(row["ok"] for row in report["packages"])]
    if mode == "training":
        checks.extend([report["aarav_lm"]["ok"], *(row["ok"] for row in report["training_inputs"])])
    report["ok"] = all(checks)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("analysis", "training"), default="analysis")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument(
        "--aarav-lm-dir", type=Path,
        default=Path(os.environ.get("AARAV_LM_DIR", ROOT.parent / "aarav-lm")),
    )
    parser.add_argument(
        "--base-corpus", type=Path,
        default=Path(os.environ.get("CANARY_BASE_CORPUS", ROOT / "data" / "raw" / "base.txt")),
    )
    parser.add_argument(
        "--tokenizer-dir", type=Path,
        default=Path(os.environ.get("CANARY_TOKENIZER_DIR", ROOT.parent / "aarav-lm" / "artifacts" / "tokenizer_tinystories_v2")),
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = build_report(args.mode, args.lock, args.aarav_lm_dir, args.base_corpus, args.tokenizer_dir)
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
