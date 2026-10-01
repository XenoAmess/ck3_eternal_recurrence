"""Build recovery12002 actual caller/mailbox/provider packets without CK3 access."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

NATIVE = Path(__file__).resolve().parent.parent
SOURCES = [NATIVE / "src" / name for name in (
    "ck3_12002_epidemic_recovery_mailbox.cpp", "ck3_12002_epidemic_recovery_mailbox_test.cpp",
    "ck3_12002_epidemic_recovery.cpp", "ck3_12002.cpp", "ck3_12002_phase_definitions.cpp",
    "player_epidemic_recovery_v1.cpp", "ck3_12002_query_mailbox.cpp",
    "ck3_12002_thread_runtime.cpp", "main_thread_query_mailbox_v1.cpp", "protocol.cpp")]
RESULT_KEYS = {"step", "accepted", "status", "query_sequence", "observation_revision",
               "snapshot_revision", "player_epidemic_recovery", "private_build", "read_only",
               "advertised", "backend_id"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def packet_receipts(directory: Path) -> list[dict[str, object]]:
    receipts = []
    for path in sorted(directory.glob("*.json")):
        packet = json.loads(path.read_text(encoding="utf-8"))
        result = packet["result"]
        if (set(packet) != {"type", "protocol_version", "request_id", "ok", "result"}
                or packet["type"] != "command_result" or packet["protocol_version"] != 1
                or packet["ok"] is not True or set(result) != RESULT_KEYS
                or result["accepted"] is not True or result["private_build"] is not True
                or result["read_only"] is not True or result["advertised"] is not False
                or result["backend_id"] != "native-headless"
                or result["query_sequence"] <= 0 or result["observation_revision"] <= 0):
            raise ValueError(f"actual caller transport packet mismatch: {path}")
        native = result["player_epidemic_recovery"]
        if native["snapshot_revision"] != result["snapshot_revision"]:
            raise ValueError(f"actual native and packet revision mismatch: {path}")
        receipts.append({"name": path.name, "path": str(path), "sha256": digest(path),
                         "request_id": packet["request_id"], "step": result["step"],
                         "status": result["status"], "query_sequence": result["query_sequence"],
                         "observation_revision": result["observation_revision"],
                         "snapshot_revision": result["snapshot_revision"],
                         "date_raw": native["date_raw"], "played_character_id": native["played_character_id"],
                         "requested_title_id": native["requested_title_id"], "counties": native["counties"]})
    return receipts


def run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(temporary)
    os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    attempts = []
    for mode in ("Od", "O2"):
        cell = output / mode
        cell.mkdir(exist_ok=True)
        executable = cell / "recovery-mailbox-fixture.exe"
        command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8",
                   "/permissive-", "/DNOMINMAX", "/DXAR_EPIDEMIC_RECOVERY_MAILBOX_STANDALONE_NATIVE_ADAPTER",
                   f"/{mode}", "/Gy", f"/I{NATIVE / 'include'}", *map(str, SOURCES),
                   f"/Fe:{executable}", "/link", "/OPT:REF", "User32.lib"]
        completed = subprocess.run(command, cwd=cell, env=environment, capture_output=True, text=True)
        (cell / "compile.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        attempt = {"mode": mode, "compile_returncode": completed.returncode, "compile_command": command}
        if completed.returncode == 0:
            wire = cell / "wire"
            completed = subprocess.run([str(executable), "--output", str(wire)], cwd=cell,
                                       env=environment, capture_output=True, text=True)
            (cell / "fixture.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
            attempt.update(fixture_returncode=completed.returncode, stdout=completed.stdout,
                           stderr=completed.stderr, executable_sha256=digest(executable))
            if completed.returncode == 0:
                attempt["wire"] = packet_receipts(wire)
        attempts.append(attempt)
    result = {"schema": "xar.ck3_12002.epidemic-recovery-mailbox-fixture.v1",
              "status": "GREEN" if all(row.get("fixture_returncode") == 0 for row in attempts) else "RED",
              "readiness": "static-ready", "game_started": False, "real_ck3_process_access": False,
              "fixture_self_memory_reads": True, "frozen_provider_checks_rerun": False,
              "wire_origin": "actual common controller, installed named callback, recovery12002 provider and unchanged v1 serializer; fixture-owned bindings",
              "source_sha256": {str(path.relative_to(NATIVE)): digest(path) for path in SOURCES},
              "attempts": attempts}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output.resolve())
    print(json.dumps({"status": report["status"], "result": str(args.output / "result.json"),
                      "sha256": digest(args.output / "result.json"),
                      "attempts": [{key: row.get(key) for key in ("mode", "compile_returncode", "fixture_returncode", "stdout")}
                                   for row in report["attempts"]]}, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "GREEN" else 1)
