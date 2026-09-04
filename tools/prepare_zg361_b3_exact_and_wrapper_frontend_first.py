#!/usr/bin/env python3
"""Freeze the next B3 explicit-AND frontend-first autosave attempt.

This is a no-launch command builder.  It reuses the exact immutable product
whose explicit-AND live run reached Frontend, adds only the runner's managed
Frontend-first autosave choreography, runs formal preflight, and emits one
fresh pipe/artifact command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
from typing import Any, Sequence


EXPECTED_LIVE_VERDICT_SHA256 = (
    "abb706b08d6dcf8319bf7046567f27a28049d745fef4be104cb5cdeb38d260a2"
)
EXPECTED_SOURCE_TREE_SHA256 = (
    "d94c2d5d23e9ad254f4b20988fbf3c8e08408baa61070bd85f42b2d2fcbea35d"
)
EXPECTED_PROJECTION_SHA256 = (
    "241db7b5e2df451aadbfaeb4570b083c8563239bc0158530682b9a77da2f4acd"
)
EXPECTED_RUNNER_SHA256 = (
    "2dd1067f7a0de9076cacc552bd2f786c00f1b04af9ef969eaa258ea2e7a747c6"
)
EXPECTED_DLL_SHA256 = (
    "f3b7a6592f0ee75d2188844dd6fca21bd9d7434513941eb6407c12acb0b3aba8"
)
EXPECTED_INJECTOR_SHA256 = (
    "3100800d06a99153cfcab2ac8e183903c9b5246dad0b8717b2772db934ec13a2"
)
EXPECTED_CK3_SHA256 = (
    "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
)
PROJECTION_NAME = "b3-r5-exact-trigger-explicit-and-4d3c284"
LOAD_SAVE_NAME = "autosave"
FRONTEND_FIRST_TIMEOUT_SECONDS = 180


class PreparationError(ValueError):
    """An immutable input or no-launch precondition drifted."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _record(path: Path) -> dict[str, object]:
    path = path.resolve()
    if not path.is_file():
        raise PreparationError(f"required file is missing: {path}")
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise PreparationError(f"expected JSON object: {path}")
    return value


def _verify_projection(source: Path, manifest_path: Path) -> dict[str, object]:
    manifest = _load_json(manifest_path)
    if (
        manifest.get("kind") != "zg361_phase2_product_projection"
        or manifest.get("projection") != PROJECTION_NAME
        or manifest.get("source_tree_sha256") != EXPECTED_SOURCE_TREE_SHA256
    ):
        raise PreparationError("explicit-AND projection identity drifted")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 565:
        raise PreparationError("explicit-AND projection file list drifted")
    for row in files:
        if not isinstance(row, dict):
            raise PreparationError("projection file row is not an object")
        relative = row.get("path")
        if not isinstance(relative, str) or not relative:
            raise PreparationError("projection file row lacks a path")
        path = source / relative
        if (
            not path.is_file()
            or path.stat().st_size != row.get("bytes")
            or _sha256(path) != row.get("sha256")
        ):
            raise PreparationError(f"immutable product file drifted: {relative}")
    return {
        "green": True,
        "file_count": len(files),
        "source_tree_sha256": manifest.get("source_tree_sha256"),
        "formal_overlay_tree_sha256": manifest.get(
            "formal_overlay_tree_sha256"
        ),
        "file_list_sha256": manifest.get("file_list_sha256"),
    }


def _base_argv(
    *,
    python: Path,
    runner: Path,
    dll: Path,
    injector: Path,
    pipe: str,
    seed_contract: Path,
    source: Path,
    projection_manifest: Path,
) -> list[str]:
    return [
        str(python.resolve()),
        str(runner.resolve()),
        "--phase2-live-batch",
        "--bridge-dll",
        str(dll.resolve()),
        "--bridge-injector",
        str(injector.resolve()),
        "--bridge-pipe",
        pipe,
        "--phase2-seed-contract",
        str(seed_contract.resolve()),
        "--phase2-product-source",
        str(source.resolve()),
        "--phase2-product-projection",
        PROJECTION_NAME,
        "--phase2-product-projection-manifest",
        str(projection_manifest.resolve()),
        "--phase2-frontend-first-load-save-name",
        LOAD_SAVE_NAME,
        "--phase2-frontend-first-timeout-seconds",
        str(FRONTEND_FIRST_TIMEOUT_SECONDS),
    ]


def prepare(args: argparse.Namespace) -> dict[str, object]:
    output = args.output.resolve()
    source = args.product_source.resolve()
    projection_manifest = args.projection_manifest.resolve()
    live_verdict_path = args.live_verdict.resolve()
    runner = args.live_root.resolve() / "tools" / "run_zhongguo_acceptance.py"
    seed_contract = args.live_root.resolve() / "tools" / "zg361_phase2_seed_contract.json"
    if output.exists():
        raise PreparationError(f"fresh output directory already exists: {output}")
    if not source.is_dir():
        raise PreparationError(f"immutable product source is missing: {source}")
    expected_inputs = {
        live_verdict_path: EXPECTED_LIVE_VERDICT_SHA256,
        projection_manifest: EXPECTED_PROJECTION_SHA256,
        runner: EXPECTED_RUNNER_SHA256,
        args.dll.resolve(): EXPECTED_DLL_SHA256,
        args.injector.resolve(): EXPECTED_INJECTOR_SHA256,
        args.ck3_exe.resolve(): EXPECTED_CK3_SHA256,
    }
    for path, expected in expected_inputs.items():
        if not path.is_file() or _sha256(path) != expected:
            raise PreparationError(f"hash-bound input drifted: {path}")
    verdict = _load_json(live_verdict_path)
    inference = verdict.get("inference")
    terminal = verdict.get("terminal")
    if not (
        verdict.get("kind") == "zg361_b3_exact_trigger_explicit_and_live_verdict"
        and verdict.get("result") == "GREEN_EVIDENCE"
        and isinstance(inference, dict)
        and inference.get("explicit_and_wrapper_restored_frontend") is True
        and isinstance(terminal, dict)
        and terminal.get("reason_code") == "frontend_without_load_save"
        and terminal.get("full_acceptance_result") == "RED"
    ):
        raise PreparationError("prior explicit-AND live verdict is not eligible")
    projection_verification = _verify_projection(source, projection_manifest)

    output.mkdir(parents=True)
    pipe = rf"\\.\pipe\xar_ck3_bridge_zg361_{secrets.token_hex(16)}"
    if re.fullmatch(r"\\\\\.\\pipe\\xar_ck3_bridge_zg361_[0-9a-f]{32}", pipe) is None:
        raise PreparationError("fresh pipe does not satisfy the formal contract")
    artifacts = output / "artifacts-live"
    argv = _base_argv(
        python=args.python,
        runner=runner,
        dll=args.dll,
        injector=args.injector,
        pipe=pipe,
        seed_contract=seed_contract,
        source=source,
        projection_manifest=projection_manifest,
    )
    preflight_argv = [argv[0], argv[1], "--preflight", *argv[2:]]
    environment = os.environ.copy()
    environment["XAR_CK3_EXE"] = str(args.ck3_exe.resolve())
    completed = subprocess.run(
        preflight_argv,
        cwd=args.live_root.resolve(),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    preflight_log = output / "formal-no-launch-preflight.txt"
    preflight_log.write_text(
        completed.stdout + completed.stderr,
        encoding="utf-8",
        newline="\n",
    )
    preflight_green = (
        completed.returncode == 0
        and "ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN" in completed.stdout
    )
    if not preflight_green:
        raise PreparationError("frontend-first formal no-launch preflight is RED")
    if artifacts.exists():
        raise PreparationError("preflight unexpectedly created live artifacts")
    launch_argv = [*argv, "--artifacts-dir", str(artifacts), "--discard-userdir"]
    return {
        "schema_version": 1,
        "kind": "zg361_b3_explicit_and_frontend_first_no_launch_attempt",
        "status": "GREEN_NO_LAUNCH",
        "readiness": "frontend-first-autosave-live-pending",
        "ck3_launched": False,
        "purpose": (
            "Reach Frontend on the immutable explicit-AND product, then let the "
            "same managed pipe restart CK3 with the installed autosave."
        ),
        "prior_live_verdict": _record(live_verdict_path),
        "immutable_product": {
            "source": str(source),
            "projection_manifest": _record(projection_manifest),
            **projection_verification,
            "mutated": False,
        },
        "choreography": {
            "load_save_name": LOAD_SAVE_NAME,
            "frontend_first_timeout_seconds": FRONTEND_FIRST_TIMEOUT_SECONDS,
            "same_managed_pipe_required": True,
            "fresh_pipe": pipe,
            "fresh_artifacts": str(artifacts),
        },
        "inputs": {
            "python": _record(args.python),
            "runner": _record(runner),
            "seed_contract": _record(seed_contract),
            "bridge_dll": _record(args.dll),
            "bridge_injector": _record(args.injector),
            "ck3_exe": _record(args.ck3_exe),
        },
        "formal_no_launch_preflight": {
            "green": True,
            "returncode": completed.returncode,
            "argv": preflight_argv,
            "log": _record(preflight_log),
        },
        "launch": {
            "authorized_by_preflight": True,
            "executed": False,
            "argv": launch_argv,
            "windows_command": subprocess.list2cmdline(launch_argv),
        },
        "claim_boundary": (
            "This manifest authorizes one serial live attempt. It makes no "
            "Load Save, gameplay, B3-complete, T0-complete or footage claim."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--product-source", type=Path, required=True)
    parser.add_argument("--projection-manifest", type=Path, required=True)
    parser.add_argument("--live-verdict", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--injector", type=Path, required=True)
    parser.add_argument("--ck3-exe", type=Path, required=True)
    parser.add_argument("--live-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest = prepare(args)
        path = args.output.resolve() / "next-attempt-manifest.json"
        path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        digest = _sha256(path)
        (args.output.resolve() / "next-attempt-manifest.sha256").write_text(
            f"{digest}  next-attempt-manifest.json\n",
            encoding="ascii",
            newline="\n",
        )
    except (PreparationError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"RED: {type(error).__name__}: {error}")
        return 1
    print(
        json.dumps(
            {
                "result": manifest["status"],
                "ck3_launched": False,
                "output": str(args.output.resolve()),
                "manifest_sha256": digest,
                "command": manifest["launch"]["windows_command"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
