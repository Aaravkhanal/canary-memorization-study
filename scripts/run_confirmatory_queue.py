#!/usr/bin/env python3
"""Run the frozen confirmatory training queue sequentially after every start gate passes.

This runner intentionally refuses to train while the machine-readable pre-outcome gate is open. It owns one
global lock across both scales, checks storage before every cell, resumes only a verified matching run, and
completes the frozen raw evaluation plus exact training-split overlap before rolling checkpoints may be removed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

from check_confirmatory_start_gate import ARCHITECTURES, ROOT, SEEDS, build_report


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_checkpoint(path: Path) -> dict:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or not any(key in payload for key in ("model", "model_state_dict")):
        raise ValueError(f"checkpoint lacks model payload: {path}")
    return payload


def active_training_processes() -> list[str]:
    result = subprocess.run(["ps", "-axo", "pid=,command="], text=True, capture_output=True, check=True)
    matches = []
    own_pid = os.getpid()
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        pid_text = stripped.split(maxsplit=1)[0]
        if pid_text.isdigit() and int(pid_text) == own_pid:
            continue
        command = stripped.split(maxsplit=1)[1] if len(stripped.split(maxsplit=1)) == 2 else ""
        executable = Path(command.split(maxsplit=1)[0]).name if command else ""
        is_python = executable.startswith("python")
        if is_python and ("scripts/train.py" in command or "run_confirmatory_queue.py" in command):
            matches.append(stripped)
    return matches


def acquire_lock(lock_dir: Path) -> None:
    try:
        lock_dir.mkdir(parents=True)
    except FileExistsError as exc:
        raise SystemExit(f"confirmatory queue lock already exists: {lock_dir}") from exc
    (lock_dir / "owner.json").write_text(json.dumps({
        "pid": os.getpid(), "started_utc": datetime.now(timezone.utc).isoformat()
    }, indent=2) + "\n", encoding="utf-8")


def release_lock(lock_dir: Path) -> None:
    try:
        (lock_dir / "owner.json").unlink(missing_ok=True)
        lock_dir.rmdir()
    except OSError:
        pass


def run_directories(cell_root: Path) -> list[Path]:
    return sorted((path for path in cell_root.glob("exp_*_*") if path.is_dir()), key=lambda p: p.stat().st_mtime)


def completed(run_dir: Path) -> bool:
    summary_path = run_dir / "summary.json"
    if not summary_path.is_file():
        return False
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return summary.get("status") == "completed" and summary.get("steps") == 6000


def verify_completed_cell(run_dir: Path) -> dict:
    if not completed(run_dir):
        raise ValueError(f"run is not a completed 6,000-step cell: {run_dir}")
    rows = {}
    for name in ("best.pt", "final.pt"):
        path = run_dir / "checkpoints" / name
        load_checkpoint(path)
        rows[name] = {"size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
    report = {
        "schema_version": 1,
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir.resolve()),
        "training_complete": True,
        "checkpoints": rows,
        "evaluation_complete": False,
        "rolling_checkpoints_deleted": False,
    }
    (run_dir / "cell_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def runtime_path_overrides(root: Path, seed: int) -> list[str]:
    """Translate portable study-relative paths for aarav-lm's repository-root resolver."""
    seed_root = root / "data" / "confirmatory" / f"seed_{seed}"
    return [
        f"data.sources=[{seed_root / 'corpus.txt'}]",
        f"data.out_dir={seed_root / 'tokenized'}",
        f"tokenizer.artifact_dir={root / 'artifacts' / 'tokenizer_tinystories_v2'}",
    ]


def ensure_tokenized(root: Path, aarav_lm: Path, python: Path, config: Path, seed: int, env: dict) -> None:
    manifest = root / "data" / "confirmatory" / f"seed_{seed}" / "tokenized" / "manifest.json"
    if not manifest.is_file():
        subprocess.run(
            [str(python), str(aarav_lm / "scripts" / "prepare_data.py"), "--config", str(config),
             *runtime_path_overrides(root, seed)],
            cwd=root, env=env, check=True,
        )
    if not manifest.is_file():
        raise RuntimeError(f"data preparation did not create {manifest}")


def validate_evaluation(path: Path, checkpoint_hash: str, corpus_hash: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload.get("novelty_groups", [])
    completion_count = sum(len(group.get("completions", [])) for group in groups)
    overlap = payload.get("full_corpus_overlap", {})
    problems = []
    if payload.get("provenance", {}).get("checkpoint_sha256") != checkpoint_hash:
        problems.append("checkpoint hash")
    if payload.get("provenance", {}).get("corpus_sha256") != corpus_hash:
        problems.append("provenance corpus hash")
    if len(payload.get("exposure_rows", [])) != 48:
        problems.append("exposure row count")
    if len(groups) != 160 or completion_count != 320:
        problems.append("novelty group/completion count")
    if payload.get("full_training_corpus_overlap_complete") is not True:
        problems.append("full training-corpus completion flag")
    if overlap.get("scope") != "training_split" or overlap.get("corpus_sha256") != corpus_hash:
        problems.append("training-split overlap provenance")
    if payload.get("human_annotation_complete") is not False:
        problems.append("human annotation must remain incomplete")
    if problems:
        raise ValueError(f"invalid confirmatory evaluation {path}: {', '.join(problems)}")
    return {
        "path": str(path.resolve()), "sha256": sha256_file(path), "groups": len(groups),
        "completions": completion_count, "exposure_rows": 48,
    }


def evaluate_cell(root: Path, aarav_lm: Path, python: Path, run_dir: Path, result_root: Path,
                  artifact_root: Path, scale: str, architecture: str, seed: int, env: dict) -> dict:
    checkpoint = run_dir / "checkpoints" / "best.pt"
    checkpoint_hash = sha256_file(checkpoint)
    corpus_manifest_path = root / "data" / "confirmatory" / f"seed_{seed}" / "manifest.json"
    corpus_manifest = json.loads(corpus_manifest_path.read_text(encoding="utf-8"))
    corpus_path = root / corpus_manifest["corpus"]["path"]
    corpus_hash = corpus_manifest["corpus"]["sha256"]
    cell_results = result_root / scale / architecture / f"seed_{seed}"
    raw = cell_results / "raw.json"
    final = cell_results / "evaluated.json"
    if not raw.is_file():
        subprocess.run([
            str(python), str(root / "scripts" / "eval_confirmatory.py"),
            "--checkpoint", str(checkpoint), "--corpus-manifest", str(corpus_manifest_path),
            "--scale", scale, "--architecture", architecture, "--training-seed", str(seed),
            "--aarav-lm-dir", str(aarav_lm), "--device", "mps", "--out", str(raw),
        ], cwd=root, env=env, check=True)
    else:
        raw_payload = json.loads(raw.read_text(encoding="utf-8"))
        if raw_payload.get("provenance", {}).get("checkpoint_sha256") != checkpoint_hash:
            raise ValueError(f"stale raw evaluation belongs to another checkpoint: {raw}")
    if not final.is_file():
        index = artifact_root / ".indexes" / f"seed_{seed}_train.sqlite"
        subprocess.run([
            str(python), str(root / "scripts" / "eval_full_corpus_overlap.py"),
            "--input", str(raw), "--corpus", str(corpus_path), "--output", str(final),
            "--index", str(index), "--training-split-seed", str(corpus_manifest["split_seed"]),
        ], cwd=root, env=env, check=True)
    return validate_evaluation(final, checkpoint_hash, corpus_hash)


def finalize_cell(run_dir: Path, evaluation: dict) -> None:
    verification_path = run_dir / "cell_verification.json"
    report = json.loads(verification_path.read_text(encoding="utf-8"))
    report["evaluation"] = evaluation
    report["evaluation_complete"] = True
    rolling = sorted((run_dir / "checkpoints").glob("step_*.pt"))
    report["removed_rolling_checkpoints"] = [path.name for path in rolling]
    for path in rolling:
        path.unlink()
    report["rolling_checkpoints_deleted"] = True
    verification_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def run_cell(root: Path, aarav_lm: Path, python: Path, artifact_root: Path, result_root: Path, scale: str,
             architecture: str, seed: int, minimum_free: int) -> None:
    if shutil.disk_usage(artifact_root).free < minimum_free:
        raise RuntimeError("free space fell below the frozen threshold before the next cell")
    cell_root = artifact_root / scale / architecture / f"seed_{seed}"
    cell_root.mkdir(parents=True, exist_ok=True)
    runs = run_directories(cell_root)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(aarav_lm / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    config = root / "configs" / "confirmatory" / "training" / scale / architecture / f"seed_{seed}.yaml"
    ensure_tokenized(root, aarav_lm, python, config, seed, env)
    if runs and completed(runs[-1]):
        latest = runs[-1]
    elif runs:
        run_dir = runs[-1]
        checkpoints = sorted((run_dir / "checkpoints").glob("step_*.pt"), key=lambda p: p.stat().st_mtime)
        if not checkpoints:
            raise RuntimeError(f"incomplete run has no resumable checkpoint: {run_dir}")
        load_checkpoint(checkpoints[-1])
        command = [str(python), str(aarav_lm / "scripts" / "train.py"), "--resume", str(run_dir)]
    else:
        command = [str(python), str(aarav_lm / "scripts" / "train.py"), "--config", str(config),
                   "--exp-root", str(cell_root), *runtime_path_overrides(root, seed)]
    if not (runs and completed(runs[-1])):
        subprocess.run(command, cwd=root, env=env, check=True)
        latest = run_directories(cell_root)[-1]
    verify_completed_cell(latest)
    evaluation = evaluate_cell(
        root, aarav_lm, python, latest, result_root, artifact_root, scale, architecture, seed, env
    )
    finalize_cell(latest, evaluation)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--aarav-lm-dir", type=Path,
                        default=Path(os.environ.get("AARAV_LM_DIR", ROOT.parent / "aarav-lm")))
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    artifact_root = args.artifact_root or Path(os.environ.get(
        "CONFIRMATORY_ARTIFACT_ROOT", ROOT / "models" / "confirmatory"
    ))
    result_root = Path(os.environ.get("CONFIRMATORY_RESULT_ROOT", ROOT / "results" / "confirmatory"))
    report = build_report(ROOT, artifact_root)
    print(json.dumps(report, indent=2))
    if not report["start_allowed"]:
        print("confirmatory start gate is closed; no training started", file=sys.stderr)
        return 1
    if args.check_only:
        return 0
    active = active_training_processes()
    if active:
        raise SystemExit("another training process is active:\n" + "\n".join(active))
    lock_dir = ROOT / ".runtime" / "confirmatory-global.lock"
    acquire_lock(lock_dir)
    minimum_free = report["checks"]["storage"]["minimum_free_bytes"]
    try:
        for scale in ("14m", "48m"):
            for seed in SEEDS:
                for architecture in ARCHITECTURES:
                    run_cell(ROOT, args.aarav_lm_dir.resolve(), args.python.resolve(), artifact_root.resolve(),
                             result_root.resolve(), scale, architecture, seed, minimum_free)
    finally:
        release_lock(lock_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
