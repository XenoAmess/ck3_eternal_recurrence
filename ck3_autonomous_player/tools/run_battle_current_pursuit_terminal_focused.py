"""Run only the two new current pursuit/terminal Python fixture cases."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest


MODULES = (
    "battle_current_pursuit",
    "battle_current_terminal",
)
TESTS = (
    "test_battle_current_pursuit",
    "test_battle_current_terminal",
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _paths(args: argparse.Namespace) -> list[Path]:
    return [
        args.producer_root / "ck3_autonomous_player/src/xar_autoplayer/simulation" / f"{name}.py"
        for name in MODULES
    ] + [
        args.fixture_root / "ck3_autonomous_player/tests/unit" / f"{name}.py"
        for name in TESTS
    ] + [
        args.baseline / "ck3_autonomous_player/src/xar_autoplayer/simulation/battle_current_adapter.py",
        args.baseline / "ck3_autonomous_player/src/xar_autoplayer/simulation/combat_core.py",
        args.baseline / "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py",
        Path(__file__).resolve(),
    ]


def _worker(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(args.baseline / "ck3_autonomous_player/src"))
    # Overlay only the two new producer modules; existing packages/dependencies
    # remain the frozen baseline. No partial namespace package overlay is used.
    import xar_autoplayer.simulation  # noqa: F401

    for name in MODULES:
        _load(
            f"xar_autoplayer.simulation.{name}",
            args.producer_root / "ck3_autonomous_player/src/xar_autoplayer/simulation" / f"{name}.py",
        )
    suite = unittest.TestSuite()
    for name in TESTS:
        module = _load(
            name,
            args.fixture_root / "ck3_autonomous_player/tests/unit" / f"{name}.py",
        )
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "python_optimization": sys.flags.optimize,
        "actual_game_calls": 0,
    }
    (args.artifacts / "TEST-RESULT.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return 0 if result.wasSuccessful() and result.testsRun == 2 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--producer-root", type=Path, required=True)
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    if args.worker:
        return _worker(args)
    paths = _paths(args)
    source_pins = [
        {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in paths
    ]
    command = [
        sys.executable, "-O", str(Path(__file__).resolve()),
        "--baseline", str(args.baseline),
        "--producer-root", str(args.producer_root),
        "--fixture-root", str(args.fixture_root),
        "--artifacts", str(args.artifacts), "--worker",
    ]
    started = time.monotonic()
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    completed = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=environment, check=False,
    )
    log = completed.stdout + completed.stderr
    (args.artifacts / "run.log").write_text(log, encoding="utf-8", newline="\n")
    summary_path = args.artifacts / "TEST-RESULT.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
    result = {
        "schema": "battle-current-pursuit-terminal-focused/v1",
        "status": "FIXTURE-GREEN" if completed.returncode == 0 else "FIXTURE-RED",
        "readiness": "static-ready" if completed.returncode == 0 else "research",
        "exit_code": completed.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "source_pins": source_pins,
        "test_summary": summary,
        "command": command,
        "actual_game_calls": 0,
        "sdk_or_bridge_pipe_calls": 0,
        "window_operations": 0,
        "git_mutations": 0,
        "native_builds": 0,
        "old_test_suites_run": 0,
    }
    (args.artifacts / "RESULT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"status": result["status"], "result": str(args.artifacts / "RESULT.json")}))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
