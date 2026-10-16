#!/usr/bin/env python3
"""Read-only capacity audit for the confirmatory artifact filesystem and known large local paths."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = (
    ROOT / "models",
    ROOT / "results",
    ROOT / "data",
    ROOT.parent / "aarav-lm" / "experiments",
    ROOT.parent / "aarav-lm" / "data",
    Path.home() / ".cache",
    Path.home() / "Library" / "Caches",
    Path.home() / "Downloads",
)


def allocated_bytes(path: Path) -> int:
    """Return allocated bytes without following symlinks."""
    if not path.exists():
        return 0
    if path.is_symlink():
        return 0
    if path.is_file():
        return path.stat().st_blocks * 512
    total = path.stat().st_blocks * 512
    for child in path.iterdir():
        try:
            total += allocated_bytes(child)
        except (FileNotFoundError, PermissionError, OSError):
            continue
    return total


def build_report(artifact_root: Path, minimum_free_bytes: int, paths: tuple[Path, ...] = DEFAULT_PATHS) -> dict:
    artifact_root.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(artifact_root)
    return {
        "schema_version": 1,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "read_only_audit": True,
        "artifact_root": str(artifact_root.resolve()),
        "filesystem": {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free},
        "minimum_free_bytes": minimum_free_bytes,
        "capacity_ok": usage.free >= minimum_free_bytes,
        "paths": [
            {"path": str(path.resolve()), "exists": path.exists(), "allocated_bytes": allocated_bytes(path)}
            for path in paths
        ],
        "action_taken": "none",
        "warning": "This audit never deletes or moves files. Cache cleanup or artifact relocation requires owner action; preserve exploratory checkpoints.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=ROOT / "models" / "confirmatory")
    parser.add_argument("--minimum-free-gib", type=float, default=25.0)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "storage_capacity_audit.json")
    args = parser.parse_args()
    report = build_report(args.artifact_root, int(args.minimum_free_gib * 1024**3))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["capacity_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
