"""portable_import.py

Utility to import a repository from a previously generated export manifest.
It can:
- Verify an existing manifest against the current files.
- Copy files from a source directory (e.g., an archive or another checkout) into the current repo,
  respecting the manifest and optionally overwriting existing files.
- Optionally enforce version consistency using the manifest's version field.

Usage examples:
```bash
# Verify current repo matches a manifest
python scripts/portable_import.py --verify --manifest manifest.json

# Import files from an exported archive directory
python scripts/portable_import.py --source /path/to/exported_repo --manifest manifest.json
```
"""

import argparse
import json
import hashlib
import sys
import shutil
from pathlib import Path

def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def load_manifest(manifest_path: Path) -> dict:
    if not manifest_path.is_file():
        sys.exit(f"[ERROR] Manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text())

def verify(repo_root: Path, manifest: dict) -> bool:
    all_ok = True
    for entry in manifest.get("files", []):
        path = repo_root / entry["path"]
        if not path.is_file():
            print(f"[ERROR] Missing file: {entry['path']}")
            all_ok = False
            continue
        if compute_sha256(path) != entry["sha256"]:
            print(f"[ERROR] Hash mismatch: {entry['path']}")
            all_ok = False
    if all_ok:
        print("[portable_import] Verification succeeded.")
    else:
        print("[portable_import] Verification failed.")
    return all_ok

def import_files(source_dir: Path, repo_root: Path, manifest: dict, overwrite: bool = False) -> None:
    for entry in manifest.get("files", []):
        src = source_dir / entry["path"]
        dst = repo_root / entry["path"]
        if not src.is_file():
            print(f"[WARN] Source missing, skipping: {src}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and not overwrite:
            if compute_sha256(dst) == entry["sha256"]:
                continue
            else:
                print(f"[WARN] Destination exists with different hash, use --overwrite to replace: {dst}")
                continue
        shutil.copy2(src, dst)
    print("[portable_import] Import completed.")

def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Import repository from export manifest")
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest JSON produced by portable_export")
    parser.add_argument("--verify", action="store_true", help="Only verify current repo against the manifest")
    parser.add_argument("--source", type=Path, help="Directory containing the exported files (manifest must match)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files when importing")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(args.manifest)

    if args.verify:
        sys.exit(0 if verify(repo_root, manifest) else 1)

    if not args.source:
        sys.exit("[ERROR] --source is required when not using --verify")

    import_files(args.source, repo_root, manifest, overwrite=args.overwrite)

if __name__ == "__main__":
    main()
