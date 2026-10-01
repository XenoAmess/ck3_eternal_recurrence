"""Compile and run real copied Sway Execute-source history using fixture-owned memory."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    native = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "tmp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment

    environment = _visual_studio_environment()
    environment["TEMP"] = environment["TMP"] = str(temporary)
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_sway_completion_execution.cpp",
        "ck3_12002_sway_completion_execution_test.cpp")]
    pins = sources + [Path(__file__).resolve(),
                      native / "include/xar_bridge/ck3_12002_sway_completion_execution.hpp",
                      native / "include/xar_bridge/ck3_12002_event_window_context.hpp",
                      native / "include/xar_bridge/ck3_12002.hpp",
                      native.parents[1] / "research/sway_completion12002_history_abi.json"]
    suites: list[dict] = []
    result = {
        "schema": "xar.ck3.sway-completion12002-execution-fixture.v1",
        "status": "RED", "readiness": "static-ready", "live_verified": False,
        "game_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "ck3_touched": False, "actual_production_reader": True,
        "actual_copied_recorder": True, "actual_production_recorder_query": True,
        "actual_serializer": True,
        "actual_msvc_identifier_callback_strings": True,
        "fixture_observer_attached_input": True,
        "native_entry_installed": False,
        "real_observer_installed_in_game": False,
        "native_material_or_terminal_postcondition_verified": False,
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in pins},
        "suites": suites,
    }
    receipt = output / "result.json"
    try:
        for mode, optimization in (("Debug", "/Od"), ("Release", "/O2")):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            executable = cell / "sway-completion-execution.exe"
            command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
                       "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                       "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", optimization,
                       "/I" + str(native / "include"), *map(str, sources),
                       "/Fe:" + str(executable)]
            compiled = subprocess.run(command, cwd=cell, env=environment,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")
            (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
            if compiled.returncode:
                raise RuntimeError(f"Compile RED {mode}: {cell / 'compile.log'}")
            executed = subprocess.run([str(executable), str(cell)], cwd=cell, env=environment,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")
            (cell / "run.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
            if executed.returncode:
                raise RuntimeError(f"Fixture RED {mode}: {cell / 'run.log'}")
            wires = {}
            for path in sorted(cell.glob("*-wire.json")):
                wire = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(wire, dict):
                    raise RuntimeError(f"Actual serializer did not emit a JSON object: {path}")
                if wire.get("material_effect_observed") is not False or wire.get("native_terminal_state_observed") is not False:
                    raise RuntimeError(f"Executing input must not claim material or terminal effects: {path}")
                for record in wire.get("records", []):
                    if (record.get("executing_input_observed") is not True
                            or record.get("exact_scope_join_ready") is not True
                            or record.get("message_enqueue_observed") is not False
                            or record.get("material_effect_observed") is not False
                            or record.get("native_terminal_state_observed") is not False):
                        raise RuntimeError(f"Copied source record has incorrect evidence boundary: {path}")
                wires[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            suites.append({
                "mode": mode, "status": "GREEN", "compiler": "MSVC /W4 /WX",
                "optimization": optimization, "runtime": "/MD _ITERATOR_DEBUG_LEVEL=0",
                "exe_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                "wires_sha256": wires, "output": executed.stdout.strip(),
            })
            print(mode, executed.stdout.strip())
        result["status"] = "GREEN"
    except Exception as error:
        result["failure"] = str(error)
        raise
    finally:
        receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
