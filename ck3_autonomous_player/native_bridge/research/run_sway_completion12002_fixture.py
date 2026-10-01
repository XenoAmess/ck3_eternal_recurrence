"""Run the actual Sway completion reader and owner-envelope production path offline."""
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
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_query_mailbox.cpp",
        "ck3_12002_sway_completion.cpp", "ck3_12002_sway_completion_mailbox.cpp",
        "ck3_12002_sway_completion_serializer.cpp", "ck3_12002_sway_completion_test.cpp")]
    handler = native / "src/ck3_12002_sway_completion_handler.cpp"
    pins = sources + [handler, Path(__file__).resolve()] + [native / "include/xar_bridge" / name for name in (
        "ck3_12002.hpp", "ck3_12002_sway_state.hpp",
        "ck3_12002_sway_completion.hpp", "ck3_12002_sway_completion_mailbox.hpp")]
    suites = []
    result = {
        "schema": "xar.ck3.sway-completion12002-fixture.v1",
        "status": "RED", "readiness": "static-ready", "live_verified": False,
        "game_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "ck3_touched": False, "actual_production_reader": True,
        "actual_owner_mailbox": True, "actual_serializer": True,
        "shared_worker_dispatch_included": False,
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in pins},
        "suites": suites,
    }
    receipt = output / "result.json"
    try:
        for mode, flags in (("Debug", ["/Od", "/MDd"]), ("Release", ["/O2", "/MD"])):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            exe = cell / "sway-completion.exe"
            common = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/permissive-",
                      "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", *flags,
                      "/I" + str(native / "include")]
            compiled = subprocess.run([*common, *map(str, sources), "/Fe:" + str(exe)],
                                      cwd=cell, env=environment, capture_output=True,
                                      text=True, encoding="utf-8", errors="replace")
            (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
            if compiled.returncode:
                raise RuntimeError(f"Compile RED {mode}: {cell / 'compile.log'}")
            executed = subprocess.run([str(exe), str(cell)], cwd=cell, env=environment,
                                      capture_output=True, text=True, encoding="utf-8", errors="replace")
            (cell / "run.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
            if executed.returncode:
                raise RuntimeError(f"Fixture RED {mode}: {cell / 'run.log'}")
            compiled_handler = subprocess.run([*common, "/c", str(handler),
                                               "/Fo:" + str(cell / "completion-handler.obj")],
                                              cwd=cell, env=environment, capture_output=True,
                                              text=True, encoding="utf-8", errors="replace")
            (cell / "handler-compile.log").write_text(
                compiled_handler.stdout + compiled_handler.stderr, encoding="utf-8")
            if compiled_handler.returncode:
                raise RuntimeError(f"Handler compile RED {mode}: {cell / 'handler-compile.log'}")
            wires = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(cell.glob("*-wire.json"))}
            suites.append({"mode": mode, "status": "GREEN", "compiler": "MSVC /W4 /WX",
                           "optimization": flags[0], "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
                           "wires_sha256": wires, "output": executed.stdout.strip()})
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
