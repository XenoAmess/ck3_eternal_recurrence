"""Run the new shared notification-sink path, optionally using an external candidate."""
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
    parser.add_argument("--installer-candidate-dir", type=Path,
        help="External projection with include/xar_bridge and src; native sources remain frozen")
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
    candidate = args.installer_candidate_dir.resolve() if args.installer_candidate_dir else None
    installer_root = candidate or native
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_sway_completion_execution.cpp",
        "ck3_12002_sway_completion_execution_install.cpp",
        "ck3_12002_sway_completion_invalidation_reason.cpp",
        "sway_completion12002_secondary_sink_test.cpp")]
    sources[2] = installer_root / "src/ck3_12002_sway_completion_execution_install.cpp"
    pins = sources + [Path(__file__).resolve(),
        native / "include/xar_bridge/ck3_12002_sway_completion_execution.hpp",
        installer_root / "include/xar_bridge/ck3_12002_sway_completion_execution_install.hpp",
        native / "include/xar_bridge/ck3_12002_sway_completion_invalidation_reason.hpp",
        native / "src/ck3_12002_sway_completion_execution_install_test.cpp"]
    result = {"schema": "xar.ck3.sway-secondary-sink-fixture.v1", "status": "RED",
        "readiness": "static-ready", "live_verified": False, "ck3_touched": False,
        "previous_native_matrices_executed": False, "second_installer": False,
        "actual_shared_installer_and_typed_original": True,
        "actual_hidden_and_reason_reader_and_copied_query": True,
        "installer_source_mode": "external_proposed_candidate" if candidate else "native_source",
        "installer_candidate_dir": str(candidate) if candidate else None,
        "source_apply_required": candidate is not None,
        "production_source_files_written": False,
        "fixture_owned_readonly_slot_memory": True, "production_image_mapped": False,
        "real_observer_installed_in_game": False,
        "native_material_or_terminal_postcondition_verified": False,
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in pins},
        "suites": []}
    try:
        for mode, optimization in (("Debug", "/Od"), ("Release", "/O2")):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            executable = cell / "sway-secondary-sink.exe"
            command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
                "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", optimization,
                "/I" + str(installer_root / "include"), "/I" + str(native / "include"),
                *map(str, sources), "/Fe:" + str(executable)]
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
                assert wire["available"] and wire["observer_attached"] and len(wire["records"]) == 1
                assert wire["material_effect_observed"] is False
                assert wire["native_terminal_state_observed"] is False
                wires[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            assert set(wires) == {"secondary-hidden-success-wire.json", "secondary-dead-reason-wire.json"}
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
