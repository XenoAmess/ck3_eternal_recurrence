"""Run the actual Sway termination recorder/owning-envelope/full-wire path offline."""
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
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    names = (
        "ck3_12002.cpp", "ck3_12002_query_mailbox.cpp",
        "ck3_12002_sway_completion_termination.cpp",
        "ck3_12002_sway_completion_termination_mailbox.cpp",
        "ck3_12002_sway_completion_termination_serializer.cpp",
        "ck3_12002_sway_completion_termination_mailbox_test.cpp",
    )
    sources = [native / "src" / name for name in names]
    handler = native / "src/ck3_12002_sway_completion_termination_handler.cpp"
    pins = sources + [handler, native / "src/ck3_12002_sway_completion_termination_test.cpp", Path(__file__).resolve()] + [native / "include/xar_bridge" / name for name in (
        "ck3_12002_sway_completion_termination.hpp",
        "ck3_12002_sway_completion_termination_mailbox.hpp")]
    result = {"schema": "xar.ck3.sway-termination12002-mailbox-fixture.v1", "status": "RED",
              "readiness": "static-ready", "live_verified": False, "ck3_touched": False,
              "actual_capture_and_copied_recorder": True, "actual_owner_envelope": True,
              "actual_full_command_formatter": True, "named_queue_admission_included": False,
              "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in pins},
              "suites": []}
    try:
        for mode, flags in (("Debug", ["/Od", "/MDd"]), ("Release", ["/O2", "/MD"])):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            exe = cell / "sway-termination-mailbox.exe"
            common = [compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/EHsc", "/permissive-",
                      "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", *flags,
                      "/I" + str(native / "include")]
            build = subprocess.run([*common, *map(str, sources), "/Fe:" + str(exe)],
                                   cwd=cell, env=environment, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace")
            (cell / "compile.log").write_text(build.stdout + build.stderr, encoding="utf-8")
            if build.returncode:
                raise RuntimeError(f"Compile RED {mode}: {cell / 'compile.log'}")
            run = subprocess.run([str(exe), str(cell)], cwd=cell, env=environment, capture_output=True,
                                 text=True, encoding="utf-8", errors="replace")
            (cell / "run.log").write_text(run.stdout + run.stderr, encoding="utf-8")
            if run.returncode:
                raise RuntimeError(f"Fixture RED {mode}: {cell / 'run.log'}")
            for path in cell.glob("*-wire.json"):
                packet = json.loads(path.read_text(encoding="utf-8"))
                if packet["type"] != "command_result" or "sway_completion_termination" not in packet["result"]:
                    raise RuntimeError("No actual termination full-command wire: " + str(path))
            compiled_handler = subprocess.run([*common, "/c", str(handler),
                                               "/Fo:" + str(cell / "termination-handler.obj")],
                                              cwd=cell, env=environment, capture_output=True,
                                              text=True, encoding="utf-8", errors="replace")
            (cell / "handler-compile.log").write_text(
                compiled_handler.stdout + compiled_handler.stderr, encoding="utf-8")
            if compiled_handler.returncode:
                raise RuntimeError(f"Handler compile RED {mode}: {cell / 'handler-compile.log'}")
            result["suites"].append({"mode": mode, "status": "GREEN", "compiler": "MSVC /W4 /WX",
                                      "optimization": flags[0], "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
                                      "wires_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                                       for path in sorted(cell.glob("*-wire.json"))},
                                      "output": run.stdout.strip()})
            print(mode, run.stdout.strip())
        result["status"] = "GREEN"
    except Exception as error:
        result["failure"] = str(error)
        raise
    finally:
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
