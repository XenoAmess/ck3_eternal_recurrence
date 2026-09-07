#!/usr/bin/env python3
"""Relay the exact late-save promotion recovery onto ``WinSta0\\Default``.

The child command is fixed to
``tools/recover_zg361_phase2_promotion_source_session.py`` under the selected
source root.  The default mode is a strict no-launch preflight; only an
explicit ``--execute`` creates the recovery child process.
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


RECOVERY_RELATIVE_PATH = Path(
    "tools/recover_zg361_phase2_promotion_source_session.py"
)
ALLOWED_STARTUP_MODES = (
    "continue-last-save",
    "bridge-frontend-first",
)


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
    python_path: Path,
    source_root: Path,
    recovery_arguments: Sequence[str],
) -> tuple[Path, Path, tuple[str, ...], str]:
    python_path = python_path.resolve()
    source_root = source_root.resolve()
    recovery = (source_root / RECOVERY_RELATIVE_PATH).resolve()
    if not python_path.is_file():
        raise ValueError(f"Python executable is missing: {python_path}")
    if not recovery.is_file():
        raise ValueError(f"late-save promotion recovery is missing: {recovery}")
    if not recovery_arguments:
        raise ValueError("late-save promotion recovery arguments are required after --")
    arguments = tuple(recovery_arguments)
    if arguments[0] == "--":
        arguments = arguments[1:]
    if not arguments:
        raise ValueError("late-save promotion recovery arguments are required after --")
    startup_mode_positions = [
        index for index, value in enumerate(arguments) if value == "--startup-mode"
    ]
    if len(startup_mode_positions) != 1:
        raise ValueError("exactly one --startup-mode argument is required")
    startup_mode_position = startup_mode_positions[0]
    if startup_mode_position + 1 >= len(arguments):
        raise ValueError("--startup-mode requires a value")
    startup_mode = arguments[startup_mode_position + 1]
    if startup_mode not in ALLOWED_STARTUP_MODES:
        raise ValueError(
            "Default-desktop late-save recovery requires --startup-mode "
            + " or ".join(ALLOWED_STARTUP_MODES)
        )
    return python_path, recovery, arguments, startup_mode


def preflight_payload(
    python_path: Path,
    source_root: Path,
    recovery_arguments: Sequence[str],
    stdout_log: Path,
    stderr_log: Path,
) -> dict[str, object]:
    python_path, recovery, arguments, startup_mode = resolve_inputs(
        python_path, source_root, recovery_arguments
    )
    command = (str(python_path), str(recovery), *arguments)
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
        "recovery": {
            "path": str(recovery),
            "sha256": sha256(recovery),
        },
        "working_directory": str(source_root.resolve()),
        "stdout_log": str(stdout_log.resolve()),
        "stderr_log": str(stderr_log.resolve()),
        "command": list(command),
        "startup_mode": startup_mode,
        "desktop_contract": (
            "CreateProcessW STARTUPINFO.lpDesktop is exactly " + TARGET_DESKTOP
        ),
        "child_contract": (
            "the child script is fixed to the exact "
            "tools/recover_zg361_phase2_promotion_source_session.py under "
            "the selected source root and startup mode is explicitly limited "
            "to the audited late-save recovery modes"
        ),
        "legal_commerce_contract": (
            "unchanged: the fixed late-save promotion recovery retains the "
            "authorized CK3 legal-consent classifier; external real-money "
            "purchase/payment/order/checkout/store actions remain unauthorized"
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
    parser.add_argument("recovery_arguments", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = preflight_payload(
            args.python,
            args.source_root,
            args.recovery_arguments,
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
