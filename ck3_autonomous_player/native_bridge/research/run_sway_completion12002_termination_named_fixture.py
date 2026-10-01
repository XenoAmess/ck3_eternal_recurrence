"""Run one release-optimized actual Sway terminal-record query through the named mailbox queue."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_wire(path: Path) -> dict:
    packet = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(packet, dict) or packet.get("type") != "command_result"
            or packet.get("protocol_version") != 1 or packet.get("ok") is not True
            or not isinstance(packet.get("request_id"), str)):
        raise RuntimeError("Actual termination formatter did not emit a full command_result")
    result = packet.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("Actual termination command_result body missing")
    for key, expected in {
        "step": "query-sway-completion-termination-v1-private",
        "accepted": True, "status": "available", "private_build": True,
        "read_only": True, "advertised": False, "build_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "backend_id": "native-headless",
    }.items():
        if result.get(key) != expected:
            raise RuntimeError(f"Actual termination command_result {key} mismatch")
    state = result.get("sway_completion_termination")
    if (not isinstance(state, dict) or state.get("schema") != "xar.ck3.sway-completion-termination.v1"
            or state.get("available") is not True or state.get("observer_attached") is not True
            or state.get("session_records_only") is not True
            or state.get("material_effect_observed") is not False
            or len(state.get("records", [])) != 1):
        raise RuntimeError("Named termination query did not publish exactly one actual copied source")
    record = state["records"][0]
    if (record.get("source_class") != "end_scheme_command_execute"
            or record.get("executing_source_observed") is not True
            or record.get("pre_status") != 0 or record.get("post_status") != 1
            or record.get("post_owner") != 0xFFFFFFFF
            or record.get("post_status_observed") is not True
            or record.get("post_exact_instance_join_ready") is not True
            or record.get("native_terminal_state_observed") is not True
            or record.get("native_terminal_transition_observed") is not True
            or record.get("material_effect_observed") is not False
            or record.get("specific_invalidation_reason") is not None):
        raise RuntimeError("Named termination query must preserve actual fixture pre/post transition and reason boundary")
    for key in ("actor_character_id", "target_character_id", "scheme_instance_id"):
        if record.get(key) != state.get(key):
            raise RuntimeError(f"Named termination query copied full identity mismatch: {key}")
    return {
        "sha256": _sha256(path), "status": result["status"], "record_count": 1,
        "source_class": record["source_class"],
        "actor_character_id": state["actor_character_id"],
        "target_character_id": state["target_character_id"],
        "scheme_instance_id": state["scheme_instance_id"],
        "pre_status": record["pre_status"], "post_status": record["post_status"],
        "native_terminal_transition_observed": record["native_terminal_transition_observed"],
        "snapshot_revision": result.get("snapshot_revision"), "date_raw": result.get("date_raw"),
    }


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
        "ck3_12002.cpp", "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp",
        "ck3_12002_sway_completion_termination.cpp",
        "ck3_12002_sway_completion_termination_mailbox.cpp",
        "ck3_12002_sway_completion_termination_serializer.cpp",
        "r5_sway_completion_termination_named_test.cpp")]
    pins = sources + [Path(__file__).resolve(),
                      native / "src/ck3_12002_sway_completion_termination_test.cpp",
                      native / "include/xar_bridge/ck3_12002_sway_completion_termination.hpp",
                      native / "include/xar_bridge/ck3_12002_sway_completion_termination_mailbox.hpp",
                      native / "include/xar_bridge/ck3_12002_query_mailbox.hpp",
                      native / "include/xar_bridge/main_thread_query_mailbox_v1.hpp",
                      native / "include/xar_bridge/game_adapter.hpp",
                      native / "include/xar_bridge/ck3_12002.hpp",
                      native / "research/sway_completion12002_termination_abi.json"]
    result = {
        "schema": "xar.ck3.sway-completion12002-termination-named-fixture.v1",
        "status": "RED", "readiness": "static-ready", "live_verified": False,
        "game_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "ck3_touched": False,
        "actual_fixture_typed_source_install": True,
        "actual_capture_before_and_after": True,
        "actual_typed_original_fixture_callback": True,
        "actual_copied_recorder": True,
        "actual_named_mailbox_install": True,
        "actual_named_environment_copy": True,
        "actual_try_submit": True,
        "actual_owner_pump_observation_and_drain": True,
        "actual_wait_and_reclaim": True,
        "actual_owner_query_envelope": True,
        "actual_full_command_formatter": True,
        "fixture_iat_memory_override": True,
        "fixture_pump_profile": True,
        "fixture_frame_adapter": True,
        "native_execute_entry_installed_in_game": False,
        "shared_worker_dispatch_included": False,
        "native_terminal_transition_observed_in_fixture": True,
        "live_native_terminal_transition_observed": False,
        "native_material_effect_or_specific_invalidation_reason_verified": False,
        "previous_source_and_transport_matrices_reexecuted": False,
        "named_executor_field": "permitted_executor_sway_completion_termination12002",
        "cases": ["actual fixture command terminal transition queried through named installation/drain/wait/reclaim"],
        "source_sha256": {str(path): _sha256(path) for path in pins},
        "suites": [],
    }
    receipt = output / "result.json"
    try:
        cell = output / "Release"
        cell.mkdir(exist_ok=True)
        executable = cell / "sway-completion-termination-named.exe"
        compile_command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
                           "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                           "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", "/O2",
                           "/I" + str(native / "include"), *map(str, sources),
                           "/Fe:" + str(executable), "User32.lib"]
        compiled = subprocess.run(compile_command, cwd=cell, env=environment,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
        (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
        if compiled.returncode:
            raise RuntimeError(f"Compile RED Release: {cell / 'compile.log'}")
        run_command = [str(executable), str(cell)]
        executed = subprocess.run(run_command, cwd=cell, env=environment,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
        (cell / "run.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
        if executed.returncode:
            raise RuntimeError(f"Fixture RED Release: {cell / 'run.log'}")
        wire_paths = sorted(cell.glob("*.json"))
        if len(wire_paths) != 1:
            raise RuntimeError(f"Expected one new actual named termination command_result, got {len(wire_paths)}")
        wires = {path.name: _validate_wire(path) for path in wire_paths}
        result["suites"].append({
            "mode": "Release", "status": "GREEN", "compiler": "MSVC /W4 /WX",
            "optimization": "/O2", "runtime": "/MD _ITERATOR_DEBUG_LEVEL=0",
            "exe_sha256": _sha256(executable),
            "commands": {"compile": compile_command, "run": run_command},
            "wires": wires, "output": executed.stdout.strip(),
        })
        print("Release", executed.stdout.strip())
        result["status"] = "GREEN"
    except Exception as error:
        result["failure"] = str(error)
        raise
    finally:
        receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
