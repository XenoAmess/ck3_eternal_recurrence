#!/usr/bin/env python3
"""Relay the exact phase-two seed runner onto the active Default desktop.

The normal Codex execution host is attached to an isolated desktop.  CK3's
authorized legal-consent handler uses Win32 desktop capture, so the runner must
itself execute on ``WinSta0\\Default``.  This wrapper only changes that process
desktop.  It does not classify UI, click anything, or alter the seed runner's
legal/commerce policy.

The default mode is a strict no-launch preflight.  ``--execute`` is deliberately
required to create the child process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Sequence

from default_desktop_process import (
    TARGET_DESKTOP,
    execute_on_default_desktop,
)

RUNNER_RELATIVE_PATH = Path("tools/run_zg361_phase2_seed_capture.py")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def resolve_inputs(
    python_path: Path, source_root: Path, runner_arguments: Sequence[str]
) -> tuple[Path, Path, tuple[str, ...]]:
    python_path = python_path.resolve()
    source_root = source_root.resolve()
    runner = (source_root / RUNNER_RELATIVE_PATH).resolve()
    if not python_path.is_file():
        raise ValueError(f"Python executable is missing: {python_path}")
    if not runner.is_file():
        raise ValueError(f"phase-two seed runner is missing: {runner}")
    if not runner_arguments:
        raise ValueError("phase-two seed runner arguments are required after --")
    arguments = tuple(runner_arguments)
    if arguments[0] == "--":
        arguments = arguments[1:]
    if not arguments:
        raise ValueError("phase-two seed runner arguments are required after --")
    return python_path, runner, arguments


def preflight_payload(
    python_path: Path,
    source_root: Path,
    runner_arguments: Sequence[str],
    stdout_log: Path,
    stderr_log: Path,
) -> dict[str, object]:
    python_path, runner, arguments = resolve_inputs(
        python_path, source_root, runner_arguments
    )
    command = (str(python_path), str(runner), *arguments)
    return {
        "schema_version": 1,
        "result": "READY_TO_RUN",
        "mode": "no-launch-preflight",
        "target_desktop": TARGET_DESKTOP,
        "child_process_started": False,
        "ck3_launch_attempted": False,
        "python": {
            "path": str(python_path),
            "sha256": sha256(python_path),
        },
        "runner": {
            "path": str(runner),
            "sha256": sha256(runner),
        },
        "working_directory": str(source_root.resolve()),
        "stdout_log": str(stdout_log.resolve()),
        "stderr_log": str(stderr_log.resolve()),
        "command": list(command),
        "desktop_contract": (
            "CreateProcessW STARTUPINFO.lpDesktop is exactly " + TARGET_DESKTOP
        ),
        "legal_commerce_contract": (
            "unchanged: the child is the exact run_zg361_phase2_seed_capture.py "
            "runner and retains its authorized CK3 legal-consent classifier; "
            "external real-money purchase/payment/order/checkout/store actions "
            "remain unauthorized"
        ),
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--stdout-log", type=Path, required=True)
    parser.add_argument("--stderr-log", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("runner_arguments", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = preflight_payload(
            args.python,
            args.source_root,
            args.runner_arguments,
            args.stdout_log,
            args.stderr_log,
        )
        if args.execute:
            command = tuple(str(value) for value in payload["command"])
            pid, exit_code = execute_on_default_desktop(
                command,
                args.source_root,
                args.stdout_log,
                args.stderr_log,
            )
            payload.update(
                {
                    "result": "GREEN" if exit_code == 0 else "RED",
                    "mode": "execute",
                    "child_process_started": True,
                    "ck3_launch_attempted": True,
                    "child_pid": pid,
                    "child_exit_code": exit_code,
                }
            )
        write_json(args.result, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
        return 0 if payload["result"] in {"READY_TO_RUN", "GREEN"} else 2
    except BaseException as error:
        failure = {
            "schema_version": 1,
            "result": "RED",
            "mode": "execute" if args.execute else "no-launch-preflight",
            "target_desktop": TARGET_DESKTOP,
            "child_process_started": False,
            "ck3_launch_attempted": False,
            "error": f"{type(error).__name__}: {error}",
        }
        write_json(args.result, failure)
        print(json.dumps(failure, ensure_ascii=False, indent=2), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
