#!/usr/bin/env python3
"""Verify the new production treatment Handle through a fixture-owned mailbox."""

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
SOURCE_NAMES = (
    "ck3_12002.cpp", "ck3_12002_epidemic_treatment_presence.cpp",
    "player_epidemic_treatment_presence_v1.cpp", "ck3_12002_query_mailbox.cpp",
    "main_thread_query_mailbox_v1.cpp", "protocol.cpp",
    "ck3_12002_epidemic_treatment_mailbox.cpp", "ck3_12002_epidemic_treatment_mailbox_test.cpp",
)
WIRE_NAMES = ("present.json", "absent.json", "definition-unavailable.json")
ENVELOPE_KEYS = {
    "step", "accepted", "status", "query_sequence", "observation_revision",
    "snapshot_revision", "player_epidemic_treatment_presence", "private_build",
    "read_only", "advertised", "backend_id",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("xar_treatment_mailbox_msvc", ROOT / "tools/run_native_msvc.py")
    msvc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(msvc)
    environment = msvc.child_environment(output)
    installation = msvc.visual_studio_installation(None, environment)
    environment, tools = msvc.initialize_msvc(installation, output, environment)

    def suite(configuration: str) -> dict:
        directory = output / configuration
        directory.mkdir(exist_ok=True)
        executable = directory / "treatment-mailbox-fixture.exe"
        flags = ["/Od", "/MDd"] if configuration == "Debug" else ["/O2", "/MD"]
        sources = [NATIVE / "src" / name for name in SOURCE_NAMES]
        command = [tools["cl"], "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-", "/EHsc", "/utf-8", "/DNOMINMAX",
                   "/DXAR_CK3_ENABLE_G2_PLAYER_EPIDEMIC_TREATMENT_PRIVATE_QUERY_V1=1",
                   "/DXAR_TREATMENT_MAILBOX_STANDALONE_ADAPTER=1", *flags,
                   f'/I{NATIVE / "include"}', *(str(p) for p in sources), f"/Fe:{executable}", "user32.lib"]
        compiled = subprocess.run(command, cwd=directory, env=environment, capture_output=True)
        (directory / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
        if compiled.returncode:
            raise RuntimeError(f"Compile RED: {directory}; exit {compiled.returncode}")
        wire_dir = directory / "wire"
        # The sole positional argument is a fresh fixture output directory.
        executed = subprocess.run([str(executable), str(wire_dir)], cwd=directory,
                                  env=environment, capture_output=True)
        log = executed.stdout + executed.stderr
        (directory / "run.log").write_bytes(log)
        if executed.returncode:
            raise RuntimeError(f"Fixture RED: {directory}; exit {executed.returncode}")
        match = re.search(rb"PASS checks=(\d+)", log)
        if match is None:
            raise RuntimeError(f"No fixture check count: {directory}")
        wires = []
        for name in WIRE_NAMES:
            path = wire_dir / name
            packet = json.loads(path.read_text(encoding="utf-8"))
            envelope = packet["result"]
            if (set(packet) != {"type", "protocol_version", "request_id", "ok", "result"}
                    or packet["type"] != "command_result" or packet["protocol_version"] != 1
                    or packet["request_id"] != 'epidemic-treatment-"mailbox-fixture' or packet["ok"] is not True
                    or set(envelope) != ENVELOPE_KEYS):
                raise RuntimeError(f"Actual Handle packet/envelope changed: {path}")
            if (envelope["step"] != "query-player-epidemic-treatment-presence-v1"
                    or envelope["accepted"] is not True or envelope["private_build"] is not True
                    or envelope["read_only"] is not True or envelope["advertised"] is not False
                    or envelope["backend_id"] != "native-headless" or envelope["snapshot_revision"] != 123
                    or envelope["query_sequence"] != 1 or envelope["observation_revision"] <= 0
                    or envelope["observation_revision"] == envelope["snapshot_revision"]):
                raise RuntimeError(f"Actual Handle metadata changed: {path}")
            payload = envelope["player_epidemic_treatment_presence"]
            expected_presence = True if name == "present.json" else (None if "unavailable" in name else False)
            if (payload["schema"] != "player-epidemic-treatment-presence-v1"
                    or payload["modifier_key"] != "ce1_unorthodox_epidemic_treatment"
                    or payload["snapshot_revision"] != 123 or payload["date_raw"] != 53350560
                    or payload["played_character_id"] != 0x03000004 or payload["present"] is not expected_presence
                    or envelope["status"] != payload["status"]):
                raise RuntimeError(f"Actual Handle provider payload changed: {path}")
            if payload["remaining_days"] != {"status": "unavailable", "value": None,
                                              "unavailable_reason": "duration_abi_not_verified"}:
                raise RuntimeError(f"Frozen duration contract changed: {path}")
            wires.append({"path": str(path), "name": name, "sha256": sha(path),
                          "query_sequence": envelope["query_sequence"],
                          "observation_revision": envelope["observation_revision"]})
        if (wire_dir / "changed-frame.json").exists():
            raise RuntimeError("Changed frame produced a success packet")
        return {"configuration": configuration, "status": "GREEN", "checks": int(match[1]),
                "executable": str(executable), "executable_sha256": sha(executable), "wire": wires}

    with ThreadPoolExecutor(max_workers=2) as pool:
        suites = list(pool.map(suite, ("Debug", "Release")))
    if [w["sha256"] for w in suites[0]["wire"]] != [w["sha256"] for w in suites[1]["wire"]]:
        raise RuntimeError("Debug/Release actual Handle packets differ")
    paths = [NATIVE / "src" / name for name in SOURCE_NAMES] + [
        NATIVE / "include/xar_bridge/ck3_12002_epidemic_treatment_mailbox.hpp",
        NATIVE / "include/xar_bridge/main_thread_query_mailbox_v1.hpp",
        NATIVE / "include/xar_bridge/ck3_12002_query_mailbox.hpp", Path(__file__)]
    report = {"schema": "xar.ck3.12002.treatment-mailbox-fixture.v1", "status": "GREEN",
              "evidence_scope": "actual production Handle -> real queue/owner callback -> frozen provider -> stable serializer -> actual caller packet; fixture-owned memory/native callback bindings and bare NativeAdapter shim",
              "ck3_build": "1.20.0.2",
              "ck3_exe_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
              "local_ck3_contacted": False, "game_started": False, "provider_26_matrix_repeated": False,
              "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
              "same_byte_wire": True, "suites": suites, "readiness": "static-ready",
              "remaining": ["central R4 default-OFF build and registration", "paused real-game provider and full wrapper wire readback"]}
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir.resolve())
    print(json.dumps({"status": result["status"], "checks": {r["configuration"]: r["checks"] for r in result["suites"]},
                      "same_byte_wire": result["same_byte_wire"], "result": str(args.output_dir / "result.json")}))
