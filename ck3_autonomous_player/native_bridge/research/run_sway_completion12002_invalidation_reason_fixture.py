"""Run only the new selected-notification reader fixture; no CK3 or installer."""
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
        "ck3_12002_sway_completion_invalidation_reason.cpp",
        "ck3_12002_sway_completion_invalidation_reason_test.cpp")]
    pins = sources + [Path(__file__).resolve(),
        native / "include/xar_bridge/ck3_12002_sway_completion_invalidation_reason.hpp",
        native / "src/ck3_12002_sway_completion_termination_test.cpp",
        native.parent.parent / "research/sway_completion12002_invalidation_context_abi.json"]
    result = {"schema": "xar.ck3.sway-invalidation-reason-fixture.v1", "status": "RED",
        "readiness": "static-ready", "live_verified": False, "ck3_touched": False,
        "previous_native_matrices_executed": False, "new_installer": False,
        "actual_reader_and_copied_query": True, "native_lookup_calls": "fixture typed callback, native ABI proven separately",
        "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins}, "suites": []}
    try:
        for mode, optimization in (("Debug", "/Od"), ("Release", "/O2")):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            executable = cell / "sway-invalidation-reason.exe"
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
                for key in ("native_terminal_state_observed", "native_end_cause_observed", "message_enqueue_observed", "render_observed", "material_effect_observed"):
                    assert wire[key] is False
                for record in wire["records"]:
                    assert record["scheme_scope_kind"] == 9 and record["root_scope_kind"] == 4
                    assert record["selected_notification_branch_observed"] is True
                wires[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            result["suites"].append({"mode": mode, "status": "GREEN", "optimization": optimization,
                "compiler": "MSVC /W4 /WX", "output": executed.stdout.strip(),
                "exe_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(), "wire_sha256": wires})
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
