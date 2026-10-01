"""Build and run the actual three-entry copied termination observer offline."""
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
        "ck3_12002.cpp", "ck3_12002_sway_completion_termination.cpp",
        "ck3_12002_sway_completion_termination_test.cpp")]
    pins = sources + [Path(__file__).resolve(),
        native / "include/xar_bridge/ck3_12002_sway_completion_termination.hpp",
        native / "research/sway_completion12002_termination_abi.json",
        native / "research/sway_completion12002_termination_tree.mmd"]
    result = {
        "schema": "xar.ck3.sway-completion12002-termination-fixture.v1",
        "status": "RED", "readiness": "static-ready", "live_verified": False,
        "ck3_touched": False, "real_observer_installed_in_game": False,
        "actual_install_function": True, "actual_pre_post_capture": True,
        "actual_copied_record_query": True, "fixture_owned_readonly_slots": True,
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in pins},
        "suites": [],
    }
    try:
        for mode, optimization in (("Debug", "/Od"), ("Release", "/O2")):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            executable = cell / "sway-completion-termination.exe"
            command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
                "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", optimization,
                "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(executable)]
            compiled = subprocess.run(command, cwd=cell, env=environment, capture_output=True,
                                      text=True, encoding="utf-8", errors="replace")
            (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
            if compiled.returncode:
                raise RuntimeError(f"Compile RED {mode}: {cell / 'compile.log'}")
            executed = subprocess.run([str(executable), str(cell)], cwd=cell, env=environment,
                                     capture_output=True, text=True, encoding="utf-8", errors="replace")
            (cell / "run.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
            if executed.returncode:
                raise RuntimeError(f"Fixture RED {mode}: {cell / 'run.log'}")
            wires = {}
            for path in sorted(cell.glob("*-wire.json")):
                wire = json.loads(path.read_text(encoding="utf-8"))
                assert wire["read_only"] and wire["session_records_only"]
                for record in wire["records"]:
                    assert record["material_effect_observed"] is False
                    if record["native_terminal_transition_observed"]:
                        assert record["pre_status"] == 0 and record["post_status"] == 1
                    if not record["post_status_observed"]:
                        assert record["post_status"] is None and not record["native_terminal_state_observed"]
                wires[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            result["suites"].append({"mode": mode, "status": "GREEN", "optimization": optimization,
                "compiler": "MSVC /W4 /WX", "runtime": "/MD _ITERATOR_DEBUG_LEVEL=0",
                "exe_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                "wire_sha256": wires, "output": executed.stdout.strip()})
            print(mode, executed.stdout.strip())
        result["status"] = "GREEN"
    except Exception as error:
        result["failure"] = str(error)
        raise
    finally:
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
