#!/usr/bin/env python3
"""Evaluate the confirmatory pre-outcome gate without inspecting scientific outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from check_ethics_record import validate_record


ROOT = Path(__file__).resolve().parents[1]
GATE_CONFIG = ROOT / "configs" / "confirmatory" / "start_gate.json"
STORAGE_CONFIG = ROOT / "configs" / "confirmatory" / "storage_plan.json"
ETHICS_CONFIG = ROOT / "configs" / "confirmatory" / "ethics_record.json"
SCALES = ("14m", "48m")
ARCHITECTURES = ("baseline", "learned_pos", "mha", "layernorm")
SEEDS = (20261016, 20261017, 20261018)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_storage(path: Path, minimum_free_bytes: int) -> dict:
    path.mkdir(parents=True, exist_ok=True)
    probe_ok = False
    error = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".confirmatory-probe-", dir=path, delete=False) as handle:
            probe = Path(handle.name)
            payload = os.urandom(4096)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        renamed = probe.with_suffix(".verified")
        probe.replace(renamed)
        probe_ok = renamed.read_bytes() == payload
        renamed.unlink()
    except OSError as exc:
        error = str(exc)
        try:
            probe.unlink(missing_ok=True)
        except (OSError, UnboundLocalError):
            pass
    free_bytes = shutil.disk_usage(path).free
    return {
        "path": str(path.resolve()),
        "write_read_fsync_rename_ok": probe_ok,
        "free_bytes": free_bytes,
        "minimum_free_bytes": minimum_free_bytes,
        "capacity_ok": free_bytes >= minimum_free_bytes,
        "error": error,
        "ok": probe_ok and free_bytes >= minimum_free_bytes,
    }


def check_corpora(root: Path) -> dict:
    rows = []
    for seed in SEEDS:
        directory = root / "data" / "confirmatory" / f"seed_{seed}"
        corpus = directory / "corpus.txt"
        manifest_path = directory / "manifest.json"
        ok = corpus.is_file() and manifest_path.is_file()
        expected = actual = None
        if ok:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected = manifest.get("corpus", {}).get("sha256")
            actual = sha256_file(corpus)
            ok = (
                expected == actual
                and manifest.get("total_insertions") == 5288
                and manifest.get("all_insertions_in_train") is True
            )
        rows.append({"seed": seed, "expected_sha256": expected, "actual_sha256": actual, "ok": ok})
    return {"items": rows, "ok": all(row["ok"] for row in rows)}


def check_configs(root: Path) -> dict:
    missing = []
    paths = []
    for scale in SCALES:
        for architecture in ARCHITECTURES:
            for seed in SEEDS:
                path = root / "configs" / "confirmatory" / "training" / scale / architecture / f"seed_{seed}.yaml"
                paths.append(path)
                if not path.is_file():
                    missing.append(str(path.relative_to(root)))
    return {"expected_count": 24, "actual_count": sum(path.is_file() for path in paths), "missing": missing,
            "ok": not missing}


def check_committed(root: Path, paths: list[Path]) -> dict:
    relative = [str(path.relative_to(root)) for path in paths]
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", *relative],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    changed = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", *relative]
    ).returncode != 0
    return {"tracked": tracked, "changed_since_head": changed, "ok": tracked and not changed}


def build_report(root: Path, artifact_root: Path) -> dict:
    gate = json.loads((root / GATE_CONFIG.relative_to(ROOT)).read_text(encoding="utf-8"))
    storage = json.loads((root / STORAGE_CONFIG.relative_to(ROOT)).read_text(encoding="utf-8"))
    ethics = json.loads((root / ETHICS_CONFIG.relative_to(ROOT)).read_text(encoding="utf-8"))
    manual = gate["manual_gates"]
    required_manual = gate["training_required_manual_gates"]
    manual_ok = all(manual.get(name) is True for name in required_manual)
    ethics_validation = validate_record(ethics)
    ethics_ok = ethics_validation["ok"]
    locked_paths = [
        root / "docs" / "CONFIRMATORY_STUDY_PROTOCOL.md",
        root / "docs" / "CONFIRMATORY_EXECUTION_PLAN.md",
        root / "docs" / "STORAGE_AND_RECOVERY_PLAN.md",
        root / "docs" / "DISK_CAPACITY_AUDIT.md",
        root / "docs" / "ETHICS_AND_CONSENT_PLAN.md",
        root / "docs" / "EXTERNAL_RATER_INFORMATION_AND_CONSENT_TEMPLATE.md",
        root / "configs" / "confirmatory" / "canary_bank.json",
        root / "configs" / "confirmatory" / "analysis_plan.json",
        root / "configs" / "confirmatory" / "evaluation_plan.json",
        root / "configs" / "confirmatory" / "ethics_record.json",
        root / "configs" / "confirmatory" / "start_gate.json",
        root / "configs" / "confirmatory" / "storage_plan.json",
        root / "results" / "confirmatory_power.json",
        root / "reproducibility" / "inputs.lock.json",
        root / "scripts" / "check_confirmatory_start_gate.py",
        root / "scripts" / "check_ethics_record.py",
        root / "scripts" / "audit_storage_capacity.py",
        root / "scripts" / "eval_confirmatory.py",
        root / "scripts" / "eval_full_corpus_overlap.py",
        root / "scripts" / "prepare_confirmatory_annotation.py",
        root / "scripts" / "run_confirmatory_queue.py",
    ]
    existence = {str(path.relative_to(root)): path.is_file() for path in locked_paths}
    checks = {
        "locked_inputs_exist": {"items": existence, "ok": all(existence.values())},
        "corpora": check_corpora(root),
        "training_configs": check_configs(root),
        "manual_gates": {"items": manual, "required_for_training": required_manual, "ok": manual_ok},
        "ethics_record": {"annotation_mode": ethics.get("annotation_mode"),
                          "training_start_clearance": ethics.get("training_start_clearance"),
                          "problems": ethics_validation["problems"], "ok": ethics_ok},
        "storage": probe_storage(artifact_root, storage["minimum_free_bytes_at_queue_start"]),
        "preoutcome_lock_committed": check_committed(root, locked_paths),
    }
    return {
        "schema_version": 1,
        "artifact_root": str(artifact_root.resolve()),
        "checks": checks,
        "start_allowed": all(check["ok"] for check in checks.values()),
        "release_allowed": all(manual.get(name) is True for name in gate["release_only_manual_gates"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    artifact_root = args.artifact_root or Path(os.environ.get(
        "CONFIRMATORY_ARTIFACT_ROOT", root / "models" / "confirmatory"
    ))
    report = build_report(root, artifact_root)
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["start_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
