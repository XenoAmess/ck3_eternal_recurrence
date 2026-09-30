"""Explicit project inputs for a new H3937 read-only attempt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from types import ModuleType


_FIELDS = {
    "schema", "round", "live_run_id", "live_execution_id", "pipe",
    "task_bus_dir", "task_bus_cli_sha256", "screen_task_id",
    "no_launch_dir", "output_dir", "go_receipt", "screen_attempt_dir",
    "python_executable", "python_version", "game_dir",
}
_PATH_FIELDS = {
    "task_bus_dir", "no_launch_dir", "output_dir", "go_receipt",
    "screen_attempt_dir", "python_executable", "game_dir",
}


def apply_run_config(runner: ModuleType, path: Path) -> dict[str, object]:
    """Read a supplied tuple without allocating IDs, creating state or granting GO."""
    path = path.resolve()
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError("H3937 config must supply the complete new attempt tuple")
    if value["schema"] != "xar.h3937.run-config.v1":
        raise ValueError("H3937 config schema differs")
    if any(not isinstance(item, str) or not item.strip() for item in value.values()):
        raise ValueError("H3937 config fields must be nonempty strings")
    if re.fullmatch(r"R[1-9][0-9]*", value["round"]) is None:
        raise ValueError("H3937 config round is invalid")
    if re.fullmatch(r"[0-9A-Fa-f]{64}", value["task_bus_cli_sha256"]) is None:
        raise ValueError("H3937 config task-bus SHA is invalid")
    paths = {key: Path(value[key]) for key in _PATH_FIELDS}
    if any(not item.is_absolute() for item in paths.values()):
        raise ValueError("H3937 config paths must be explicit absolute paths")
    runner.ROUND = value["round"]
    runner.LIVE_RUN_ID = value["live_run_id"]
    runner.LIVE_EXECUTION_ID = value["live_execution_id"]
    runner.PIPE = value["pipe"]
    runner.TASK_BUS = paths["task_bus_dir"]
    runner.BUS_CLI_SHA256 = value["task_bus_cli_sha256"].upper()
    runner.SCREEN_TASK_ID = value["screen_task_id"]
    runner.NO_LAUNCH = paths["no_launch_dir"]
    runner.FROZEN_PYTHON = paths["python_executable"]
    runner.FROZEN_PYTHON_VERSION = value["python_version"]
    runner.STATE = runner.NO_LAUNCH / "state"
    runner.OUTPUT = paths["output_dir"]
    runner.GO = paths["go_receipt"]
    runner.SCREEN = paths["screen_attempt_dir"]
    runner.LIVE_IDENTITY = runner.NO_LAUNCH / "live-run-identity.json"
    runner.GAME = paths["game_dir"]
    runner.DLL = runner.NO_LAUNCH / "source-verified/xar_ck3_bridge.dll"
    runner.INJECTOR = runner.NO_LAUNCH / "source-verified/xar_ck3_bridge_injector.exe"
    runner.RUN_CONFIG_PATH = path
    runner.RUN_CONFIG_SHA256 = hashlib.sha256(raw).hexdigest().upper()
    runner.RUN_CONFIG_BYTES = raw
    return {"path": str(path), "sha256": runner.RUN_CONFIG_SHA256, **value}


def main_for_runner(runner: ModuleType, entry: Path, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="H3937 same-frame read-only project runner")
    parser.add_argument("--config", type=Path, required=True, help="explicit new attempt tuple; never creates approval")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--issue-screen-challenge", action="store_true")
    actions.add_argument("--worker", metavar="NONCE")
    options = parser.parse_args(argv)
    apply_run_config(runner, options.config)
    if options.issue_screen_challenge:
        print(json.dumps(runner.issue_screen_challenge(entry), ensure_ascii=False))
        return 0
    if options.worker is not None:
        return runner.main(options.worker)
    return runner.supervise_exact_once(entry)
