"""Run only the two new current main-phase transition production cases."""
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


RELATIVE_SOURCE = "ck3_autonomous_player/src/xar_autoplayer/simulation"
TEST_RELATIVE = "ck3_autonomous_player/tests/unit/test_battle_current_phase_transition.py"
SUPPORT_MODULES = ("battle_current_pursuit", "battle_current_terminal")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _worker(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(args.baseline / "ck3_autonomous_player/src"))
    import xar_autoplayer.simulation  # noqa: F401

    if args.next_day_root is not None:
        _load("xar_autoplayer.simulation.battle_current_next_day",
              args.next_day_root / RELATIVE_SOURCE / "battle_current_next_day.py")
    if args.support_root is not None:
        for name in SUPPORT_MODULES:
            _load(f"xar_autoplayer.simulation.{name}",
                  args.support_root / RELATIVE_SOURCE / f"{name}.py")
    _load("xar_autoplayer.simulation.battle_current_phase_transition",
          args.producer_root / RELATIVE_SOURCE / "battle_current_phase_transition.py")
    test = _load("test_battle_current_phase_transition", args.fixture_root / TEST_RELATIVE)
    suite = unittest.defaultTestLoader.loadTestsFromModule(test)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "python_optimization": sys.flags.optimize, "actual_game_calls": 0,
    }
    (args.artifacts / "TEST-RESULT.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0 if result.wasSuccessful() and result.testsRun == 2 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--producer-root", type=Path, required=True)
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--support-root", type=Path,
                        help="Optional frozen v57 new-module projection, without its old tests")
    parser.add_argument("--next-day-root", type=Path,
                        help="Optional frozen P2 carry module projection, without its old tests")
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    if args.worker:
        return _worker(args)
    paths = [
        args.producer_root / RELATIVE_SOURCE / "battle_current_phase_transition.py",
        args.fixture_root / TEST_RELATIVE,
        Path(__file__).resolve(),
    ]
    paths.extend(args.baseline / RELATIVE_SOURCE / f"{name}.py" for name in (
        "battle_current_adapter", "battle_current_runner", "combat_core"))
    if args.support_root is not None:
        paths.extend(args.support_root / RELATIVE_SOURCE / f"{name}.py"
                     for name in SUPPORT_MODULES)
    if args.next_day_root is not None:
        paths.append(args.next_day_root / RELATIVE_SOURCE / "battle_current_next_day.py")
    command = [sys.executable, "-O", str(Path(__file__).resolve()),
               "--baseline", str(args.baseline),
               "--producer-root", str(args.producer_root),
               "--fixture-root", str(args.fixture_root),
               "--artifacts", str(args.artifacts), "--worker"]
    if args.support_root is not None:
        command.extend(("--support-root", str(args.support_root)))
    if args.next_day_root is not None:
        command.extend(("--next-day-root", str(args.next_day_root)))
    started = time.monotonic()
    completed = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), check=False)
    (args.artifacts / "run.log").write_text(completed.stdout + completed.stderr,
                                           encoding="utf-8", newline="\n")
    summary_path = args.artifacts / "TEST-RESULT.json"
    result = {
        "schema": "battle-current-phase-transition-focused/v1",
        "status": "FIXTURE-GREEN" if completed.returncode == 0 else "FIXTURE-RED",
        "readiness": "static-ready" if completed.returncode == 0 else "research",
        "exit_code": completed.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "source_pins": [{"path": str(path),
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                        for path in paths],
        "test_summary": (json.loads(summary_path.read_text(encoding="utf-8"))
                         if summary_path.exists() else None),
        "command": command, "actual_game_calls": 0,
        "sdk_or_bridge_pipe_calls": 0, "window_operations": 0,
        "git_mutations": 0, "native_builds": 0, "old_test_suites_run": 0,
    }
    (args.artifacts / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"],
                      "result": str(args.artifacts / "RESULT.json")}))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
