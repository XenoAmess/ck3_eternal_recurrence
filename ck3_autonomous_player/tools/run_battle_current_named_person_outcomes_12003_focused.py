"""Run only the two named-person consequence cases, without native/game work."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
import unittest


def pin(path):
    p = Path(path)
    data = p.read_bytes()
    return {"path": str(p), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    import xar_autoplayer.simulation as simulation
    simulation.__path__.insert(0, str(args.projection_root /
        "ck3_autonomous_player/src/xar_autoplayer/simulation"))
    test_path = args.projection_root / (
        "ck3_autonomous_player/tests/unit/test_battle_current_named_person_outcomes_12003.py")
    spec = importlib.util.spec_from_file_location("named_person_v61_focused", test_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = module.NamedPersonPrimaryConsequences12003Tests
    suite = unittest.TestSuite(case(name) for name in (
        "test_selection_enqueue_and_actual_full_id_writeback_are_distinct",
        "test_ordered_death_flush_guards_full_u64_metadata_and_cleanup_reference"))
    stream = io.StringIO()
    outcome = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = args.output_dir / "focused.log"
    log.write_bytes(stream.getvalue().encode("utf-8"))
    production = args.projection_root / (
        "ck3_autonomous_player/src/xar_autoplayer/simulation/battle_current_named_person_outcomes_12003.py")
    result = {
        "status": "GREEN" if outcome.wasSuccessful() else "RED",
        "cases": outcome.testsRun, "failures": len(outcome.failures),
        "errors": len(outcome.errors), "skipped": len(outcome.skipped),
        "elapsed_seconds": time.perf_counter() - started,
        "python_optimized": bool(sys.flags.optimize),
        "production_module": pin(production), "focused_test": pin(test_path),
        "source_root": str(args.source_root), "runner": pin(Path(__file__)),
        "log": pin(log), "old_tests_run": 0,
        "native_builds": 0, "native_invocations": 0,
        "sdk_pipe_game_window_git_shared_calls": 0,
        "new_live_observations": 0, "new_game_days": 0,
        "readiness": "static-ready bounded caller-conditioned person consequences",
    }
    path = args.output_dir / "RESULT.json"
    path.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": result["status"], "result": str(path)}))
    return 0 if outcome.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
