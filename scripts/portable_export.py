"""portable_export.py

Utility to generate a versioned export manifest for the repository, verify imports,
and perform a round‑trip test to ensure portability.

Features
--------
- ``--export``: Walk the repository (excluding common non‑portable dirs) and emit a JSON
  manifest with file paths (relative to repo root), SHA‑256 hashes, file size and modification
  timestamp. A ``version`` field contains the current ISO timestamp and, if the repository is a
  git repo, the latest commit hash.
- ``--verify``: Validate that the files on disk match the hashes recorded in a manifest.
- ``--test``: Execute a full export → copy → verify round‑trip using a temporary directory.

Usage examples
--------------
```bash
# Generate a manifest
python scripts/portable_export.py --export manifest.json

# Verify current repo against a manifest
python scripts/portable_export.py --verify manifest.json

# Run a round‑trip test (exports to a temp dir, copies files, verifies)
python scripts/portable_export.py --test
```
"""

import argparse
import json
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_ignored(path: Path, repo_root: Path) -> bool:
    """Return True if *path* should be ignored for the export.

    Currently excludes typical VCS and cache directories.
    """
    relative = path.relative_to(repo_root)
    parts = set(relative.parts)
    # Common directories that are not needed for a portable export
    ignore_dirs = {".git", ".gitignore", "__pycache__", ".pytest_cache", "logs", "results", "models"}
    # Ignore the manifest itself if present in the repo
    if relative.name.startswith("manifest") and relative.suffix == ".json":
        return True
    return any(part in ignore_dirs for part in parts)


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of *file_path* in a memory‑efficient way."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def collect_files(repo_root: Path) -> list[dict]:
    """Traverse *repo_root* and return a list of file metadata dictionaries.

    Each dict contains ``path`` (POSIX relative), ``sha256``, ``size`` and ``mtime``.
    """
    records = []
    for path in repo_root.rglob("*"):
        if path.is_file() and not is_ignored(path, repo_root):
            rel = path.relative_to(repo_root).as_posix()
            records.append({
                "path": rel,
                "sha256": compute_sha256(path),
                "size": path.stat().st_size,
                "mtime": int(path.stat().st_mtime),
            })
    return records


def get_git_commit(repo_root: Path) -> str | None:
    """Return the short git commit hash if the repository is a git repo.

    Falls back to ``None`` when ``git`` is unavailable or the directory is not a repo.
    """
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        return None
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def generate_manifest(repo_root: Path) -> dict:
    """Create the manifest dictionary for *repo_root*."""
    files = collect_files(repo_root)
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "version": get_git_commit(repo_root) or "unknown",
        "file_count": len(files),
        "files": files,
    }
    return manifest


def write_manifest(manifest: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2))
    print(f"[portable_export] Wrote manifest with {manifest['file_count']} files to {out_path}")


def verify_manifest(manifest_path: Path, repo_root: Path) -> bool:
    """Verify that each file listed in *manifest_path* exists and matches its hash.

    Returns ``True`` if all files match, otherwise prints mismatches and returns ``False``.
    """
    manifest = json.loads(manifest_path.read_text())
    all_ok = True
    for entry in manifest.get("files", []):
        file_path = repo_root / entry["path"]
        if not file_path.is_file():
            print(f"[ERROR] Missing file: {entry['path']}")
            all_ok = False
            continue
        actual_hash = compute_sha256(file_path)
        if actual_hash != entry["sha256"]:
            print(f"[ERROR] Hash mismatch: {entry['path']} (expected {entry['sha256']}, got {actual_hash})")
            all_ok = False
    if all_ok:
        print("[portable_export] Verification succeeded – all files match the manifest.")
    else:
        print("[portable_export] Verification failed – see errors above.")
    return all_ok


def copy_files_to(dest_dir: Path, manifest: dict, repo_root: Path) -> None:
    """Copy all files described in *manifest* to *dest_dir*, preserving relative paths."""
    for entry in manifest.get("files", []):
        src = repo_root / entry["path"]
        dst = dest_dir / entry["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except OSError as e:
            print(f"[portable_export] Warning: could not copy {src} to {dst}: {e}")
    print(f"[portable_export] Copied {len(manifest['files'])} files to temporary directory {dest_dir}")


def round_trip_test(repo_root: Path) -> bool:
    """Perform an export → copy → verify round‑trip and return the success status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        manifest = generate_manifest(repo_root)
        # Export manifest to the temp dir for completeness
        manifest_path = temp_path / "manifest.json"
        write_manifest(manifest, manifest_path)
        # Copy files according to the manifest
        copy_files_to(temp_path, manifest, repo_root)
        # Verify the copied files against the manifest
        return verify_manifest(manifest_path, temp_path)

# ---------------------------------------------------------------------------
# CLI handling
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Portable export / import utility for the repository")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--export", metavar="OUT", help="Path to write the export manifest JSON")
    group.add_argument("--verify", metavar="MANIFEST", help="Verify repository against an existing manifest")
    group.add_argument("--test", action="store_true", help="Run export‑import round‑trip test in a temp directory")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]

    if args.export:
        out_path = Path(args.export)
        manifest = generate_manifest(repo_root)
        write_manifest(manifest, out_path)
    elif args.verify:
        manifest_path = Path(args.verify)
        if not manifest_path.is_file():
            sys.exit(f"[ERROR] Manifest file not found: {manifest_path}")
        ok = verify_manifest(manifest_path, repo_root)
        sys.exit(0 if ok else 1)
    elif args.test:
        success = round_trip_test(repo_root)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
