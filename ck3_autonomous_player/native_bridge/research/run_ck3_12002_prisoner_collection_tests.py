"""Compile the production Crozier collection reader against fixture memory."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
SOURCES = [NATIVE / "src/ck3_12002_prisoner_collection.cpp",
           NATIVE / "src/ck3_12002_prisoner_collection_test.cpp"]


def run(build: Path, *, wire: bool = False) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    temporary = build / "tmp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(temporary)
    os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import (
        _visual_studio_environment,
    )
    env = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=env.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    sources = SOURCES if not wire else [
        NATIVE / "src/ck3_12002_prisoner_collection.cpp",
        NATIVE / "src/ck3_12002_prisoner_wire.cpp",
        NATIVE / "src/ck3_12002_prisoner_wire_test.cpp",
        NATIVE / "src/player_prisoner_ransom_wire_v1.cpp",
        NATIVE / "src/player_prisoner_collection_query_v1_private.cpp",
    ]
    suites = []
    for mode, flags in (("Debug", ["/Od", "/MDd"]),
                        ("Release", ["/O2", "/MD"])):
        label = "prisoner-wire" if wire else "prisoner-collection"
        output = build / f"{label}-{mode}.exe"
        command = [compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                   "/permissive-", "/EHsc", "/DNOMINMAX", *flags,
                   f"/I{NATIVE / 'include'}", *map(str, sources), f"/Fe:{output}"]
        if wire:
            command += ["/Gy", "/link", "/OPT:REF"]
        completed = subprocess.run(command, cwd=build, env=env,
                                   capture_output=True, text=True)
        (build / f"compile-{mode}.log").write_text(
            completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError(f"{mode} compile RED: {completed.stdout}{completed.stderr}")
        wire_directory = build / f"wire-{mode}"
        invocation = [str(output), str(wire_directory)] if wire else [str(output)]
        completed = subprocess.run(invocation, cwd=build, env=env,
                                   capture_output=True, text=True)
        (build / f"run-{mode}.log").write_text(
            completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError(f"{mode} fixture RED: {completed.stdout}{completed.stderr}")
        suite = {"mode": mode, "status": "GREEN",
                       "output": completed.stdout.strip(),
                       "executable_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        if wire:
            emitted = {}
            for name in ("two-prisoners.json", "empty.json", "old-executable-unavailable.json"):
                path = wire_directory / name
                value = json.loads(path.read_text(encoding="utf-8"))
                emitted[name] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                 "status": value["status"], "rows": len(value["prisoners"])}
            suite["wire_files"] = emitted
        suites.append(suite)
    result = {"status": "GREEN", "readiness": "static-ready",
              "evidence_scope": "production collection reader plus synthetic exact-layout memory",
              "live_validation": False, "process_access": False,
              "wire_origin": "actual C++ production getter and serializer; synthetic memory and ransom DTO controls" if wire else None,
              "fixture_source_sha256": hashlib.sha256(
                  (NATIVE / "src/ck3_12002_prisoner_collection_test.cpp").read_bytes()).hexdigest(),
              "source_sha256": {str(path.relative_to(NATIVE)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sources}, "suites": suites}
    (build / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--wire", action="store_true", help="Run only the dedicated production-wire target")
    args = parser.parse_args()
    print(json.dumps(run(args.build_root.resolve(), wire=args.wire), indent=2))
