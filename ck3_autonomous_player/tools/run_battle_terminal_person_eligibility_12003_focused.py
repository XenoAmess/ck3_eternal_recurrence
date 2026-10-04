"""Execute the single new real-producer terminal/person composition case."""
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


def pin(p):
    p = Path(p); b = p.read_bytes()
    return {"path": str(p), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}


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
    rel = "ck3_autonomous_player/tests/unit/test_battle_terminal_person_eligibility_12003.py"
    path = args.projection_root / rel
    spec = importlib.util.spec_from_file_location("terminal_person_v62_focused", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite = unittest.TestSuite((module.TerminalPersonComposition12003Tests(
        "test_real_producers_pending_commit_and_independent_stock_guards"),))
    stream = io.StringIO()
    tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = args.output_dir / "focused.log"
    log.write_bytes(stream.getvalue().encode("utf-8"))
    result = {"status": "GREEN" if tested.wasSuccessful() else "RED",
        "date": "2026-10-05", "iso_week": "2026-W41", "cases": tested.testsRun,
        "failures": len(tested.failures), "errors": len(tested.errors),
        "skipped": len(tested.skipped), "python_optimized": bool(sys.flags.optimize),
        "elapsed_seconds": time.perf_counter() - started,
        "production_helper": pin(args.projection_root / (
            "ck3_autonomous_player/src/xar_autoplayer/simulation/battle_terminal_person_eligibility_12003.py")),
        "existing_producers": [pin(args.source_root / ("ck3_autonomous_player/src/xar_autoplayer/simulation/" + name))
            for name in ("battle_current_named_person_outcomes_12003.py", "battle_current_normal_finalizer.py")],
        "focused_test": pin(path), "runner": pin(Path(__file__)), "log": pin(log),
        "old_v61_cases_rerun": 0, "native_builds": 0,
        "sdk_ck3_pipe_game_window_git_shared_operations": 0,
        "new_live_observations": 0, "new_game_days": 0,
        "readiness": "static-ready covered terminal-person guard composition"}
    out = args.output_dir / "RESULT.json"
    out.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": result["status"], "result": str(out)}))
    return 0 if tested.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
