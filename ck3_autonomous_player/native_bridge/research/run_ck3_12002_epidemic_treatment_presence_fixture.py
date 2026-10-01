#!/usr/bin/env python3
"""Build two actual treatment presence reader fixtures; no CK3 access."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
ROOT = HERE.parents[2]
SOURCE_NAMES = ("ck3_12002.cpp", "ck3_12002_epidemic_treatment_presence.cpp",
                "player_epidemic_treatment_presence_v1.cpp", "ck3_12002_epidemic_treatment_presence_test.cpp")
WIRE_NAMES = ("present.json", "absent.json", "empty-extension.json", "empty-rows.json",
              "rows-unavailable.json", "definition-unavailable.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("xar_treatment_msvc", ROOT / "tools/run_native_msvc.py")
    msvc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(msvc)
    environment = msvc.child_environment(output)
    installation = msvc.visual_studio_installation(None, environment)
    environment, tools = msvc.initialize_msvc(installation, output, environment)

    def suite(configuration: str) -> dict:
        directory = output / configuration
        directory.mkdir(exist_ok=True)
        executable = directory / "treatment-presence-fixture.exe"
        flags = ["/Od", "/MDd"] if configuration == "Debug" else ["/O2", "/MD"]
        sources = [NATIVE / "src" / name for name in SOURCE_NAMES]
        command = [tools["cl"], "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-", "/EHsc",
                   *flags, f'/I{NATIVE / "include"}', *(str(p) for p in sources), f"/Fe:{executable}"]
        compiled = subprocess.run(command, cwd=directory, env=environment, capture_output=True)
        (directory / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
        if compiled.returncode:
            raise RuntimeError(f"Compile RED: {directory}; exit {compiled.returncode}")
        wire_dir = directory / "wire"
        # The sole fixture argument is its own artifact output directory.
        # Never pass the frozen game EXE as a positional output argument.
        executed = subprocess.run([str(executable), str(wire_dir)], cwd=directory,
                                  env=environment, capture_output=True)
        log = executed.stdout + executed.stderr
        (directory / "run.log").write_bytes(log)
        if executed.returncode:
            raise RuntimeError(f"Fixture RED: {directory}; exit {executed.returncode}")
        match = re.search(rb"PASS checks=(\d+)", log)
        if match is None:
            raise RuntimeError(f"No actual fixture check count: {directory}")
        wires = []
        for name in WIRE_NAMES:
            path = wire_dir / name
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload["schema"] != "player-epidemic-treatment-presence-v1" or payload["modifier_key"] != "ce1_unorthodox_epidemic_treatment":
                raise RuntimeError(f"Actual wire schema/key mismatch: {path}")
            if payload["snapshot_revision"] != 123 or payload["date_raw"] != 53350560 or payload["played_character_id"] != 0x03000004:
                raise RuntimeError(f"Actual wire frame mismatch: {path}")
            expected_presence = True if name == "present.json" else (None if "unavailable" in name else False)
            if payload["present"] is not expected_presence:
                raise RuntimeError(f"Actual presence distinction missing: {path}")
            if payload["remaining_days"] != {"status": "unavailable", "value": None,
                                              "unavailable_reason": "duration_abi_not_verified"}:
                raise RuntimeError(f"Duration contract drifted: {path}")
            wires.append({"path": str(path), "name": name, "sha256": sha(path)})
        return {"configuration": configuration, "status": "GREEN", "checks": int(match[1]),
                "executable": str(executable), "executable_sha256": sha(executable), "wire": wires}

    with ThreadPoolExecutor(max_workers=2) as pool:
        suites = list(pool.map(suite, ("Debug", "Release")))
    if [w["sha256"] for w in suites[0]["wire"]] != [w["sha256"] for w in suites[1]["wire"]]:
        raise RuntimeError("Debug/Release actual serialized wires differ")
    paths = [NATIVE / "src" / name for name in SOURCE_NAMES] + [
        NATIVE / "include/xar_bridge/ck3_12002_epidemic_treatment_presence.hpp",
        Path(__file__), NATIVE / "include/xar_bridge/player_epidemic_treatment_presence_v1.hpp"]
    report = {"schema": "xar.ck3.12002.treatment-presence-fixture.v1", "status": "GREEN",
              "evidence_scope": "fixture-owned current-process objects and callbacks; actual core/reader/legacy serializer",
              "ck3_build": "1.20.0.2",
              "ck3_exe_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
              "local_ck3_contacted": False, "game_started": False,
              "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
              "same_byte_wire": True, "suites": suites, "readiness": "static-ready"}
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir.resolve())
    print(json.dumps({"status": result["status"], "checks": {r["configuration"]: r["checks"] for r in result["suites"]},
                      "same_byte_wire": result["same_byte_wire"], "result": str(args.output_dir / "result.json")}))
