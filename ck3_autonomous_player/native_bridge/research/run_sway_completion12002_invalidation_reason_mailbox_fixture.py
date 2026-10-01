"""Verify selected invalidation notification source records through the actual owner mailbox."""
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
    if not isinstance(packet, dict) or packet.get("type") != "command_result" or packet.get("ok") is not True:
        raise RuntimeError(f"Actual formatter must emit a successful command_result envelope: {path}")
    if packet.get("protocol_version") != 1 or not isinstance(packet.get("request_id"), str):
        raise RuntimeError(f"Command-result protocol/request identity missing: {path}")
    result = packet.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"Command-result body missing: {path}")
    expected = {
        "step": "query-sway-completion-invalidation-reason-v1-private",
        "accepted": True, "private_build": True, "read_only": True,
        "advertised": False, "build_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "backend_id": "native-headless",
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise RuntimeError(f"Actual private command-result {key} mismatch: {path}")
    state = result.get("sway_completion_invalidation_reason")
    if not isinstance(state, dict) or state.get("schema") != "xar.ck3.sway-invalidation-notification-source.v1":
        raise RuntimeError(f"Actual copied invalidation source object missing from command-result: {path}")
    if state.get("session_records_only") is not True:
        raise RuntimeError(f"Copied sink must describe its current observer-session records: {path}")
    false_flags = ("message_enqueue_observed", "render_observed", "material_effect_observed",
                   "native_end_cause_observed", "native_terminal_state_observed")
    if any(state.get(key) is not False for key in false_flags):
        raise RuntimeError(f"Selected notification cannot claim independent rendered/end/material evidence: {path}")
    if result.get("status") != ("available" if state.get("available") else "unavailable"):
        raise RuntimeError(f"Private command-result status disagrees with actual recorder query: {path}")
    branches = []
    branch_keys = {
        "target_dead_notification_source": "sway_invalidated_dead",
        "out_of_range_notification_source": "scheme_target_not_in_diplomatic_range",
        "opaque_existing_stock_notification_source": "sway_invalidated_war",
    }
    for record in state.get("records", []):
        branch = record.get("source_branch")
        if (branch not in branch_keys or record.get("authored_reason_key") != branch_keys[branch]
                or record.get("authored_command") != "send_interface_toast"
                or record.get("authored_title") != "sway_invalidated_title"
                or record.get("selected_notification_branch_observed") is not True
                or record.get("exact_scope_join_ready") is not True
                or any(record.get(key) is not False for key in false_flags)):
            raise RuntimeError(f"Copied notification-source record has incorrect evidence boundary: {path}")
        if (record.get("actor_character_id") != state.get("actor_character_id")
                or record.get("target_character_id") != state.get("target_character_id")
                or record.get("scheme_instance_id") != state.get("scheme_instance_id")):
            raise RuntimeError(f"Copied notification-source record must correlate all full query IDs: {path}")
        branches.append(branch)
    return {
        "sha256": _sha256(path), "status": result["status"],
        "record_count": len(state.get("records", [])),
        "observer_attached": state.get("observer_attached"),
        "source_branches": branches,
        "unavailable_reason": state.get("unavailable_reason"),
        "actor_character_id": state.get("actor_character_id"),
        "target_character_id": state.get("target_character_id"),
        "scheme_instance_id": state.get("scheme_instance_id"),
        "snapshot_revision": result.get("snapshot_revision"),
        "date_raw": result.get("date_raw"),
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
        "ck3_12002.cpp", "ck3_12002_query_mailbox.cpp",
        "ck3_12002_sway_completion_termination.cpp",
        "ck3_12002_sway_completion_invalidation_reason.cpp",
        "ck3_12002_sway_completion_invalidation_reason_mailbox.cpp",
        "ck3_12002_sway_completion_invalidation_reason_serializer.cpp",
        "ck3_12002_sway_completion_invalidation_reason_mailbox_test.cpp")]
    handler = native / "src/ck3_12002_sway_completion_invalidation_reason_handler.cpp"
    pins = sources + [handler, Path(__file__).resolve(),
                      native / "src/ck3_12002_sway_completion_invalidation_reason_test.cpp",
                      native / "src/ck3_12002_sway_completion_termination_test.cpp",
                      native / "include/xar_bridge/ck3_12002_sway_completion_termination.hpp",
                      native / "include/xar_bridge/ck3_12002_sway_completion_invalidation_reason.hpp",
                      native / "include/xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp",
                      native / "include/xar_bridge/ck3_12002_query_mailbox.hpp",
                      native / "include/xar_bridge/game_adapter.hpp",
                      native / "include/xar_bridge/ck3_12002.hpp",
                      native.parents[1] / "research/sway_completion12002_history_abi.json"]
    suites: list[dict] = []
    result = {
        "schema": "xar.ck3.sway-completion12002-invalidation-reason-mailbox-fixture.v1",
        "status": "RED", "readiness": "static-ready", "live_verified": False,
        "game_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "ck3_touched": False, "actual_production_reader": True,
        "actual_copied_recorder": True, "actual_owner_mailbox": True,
        "actual_command_result_serializer": True, "handler_compile_only": True,
        "shared_worker_dispatch_included": False,
        "fixture_frame_adapter": True, "fixture_observer_attached_input": True,
        "native_execute_entry_installed_in_game": False,
        "native_end_cause_or_material_or_terminal_postcondition_verified": False,
        "previous_source_fixture_reexecuted": False,
        "cases": ["selected dead direct tooltip", "selected range direct description",
                  "existing selected stock notification kept opaque"],
        "source_sha256": {str(path): _sha256(path) for path in pins},
        "suites": suites,
    }
    receipt = output / "result.json"
    try:
        for mode, optimization in (("Debug", "/Od"), ("Release", "/O2")):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            executable = cell / "sway-invalidation-reason-mailbox.exe"
            common = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
                      "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                      "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", optimization,
                      "/I" + str(native / "include")]
            compile_command = [*common, *map(str, sources), "/Fe:" + str(executable)]
            compiled = subprocess.run(compile_command, cwd=cell, env=environment,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")
            (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
            if compiled.returncode:
                raise RuntimeError(f"Compile RED {mode}: {cell / 'compile.log'}")
            run_command = [str(executable), str(cell)]
            executed = subprocess.run(run_command, cwd=cell, env=environment,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")
            (cell / "run.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
            if executed.returncode:
                raise RuntimeError(f"Fixture RED {mode}: {cell / 'run.log'}")
            handler_command = [*common, "/c", str(handler),
                               "/Fo:" + str(cell / "invalidation-reason-handler.obj")]
            compiled_handler = subprocess.run(handler_command, cwd=cell, env=environment,
                                              capture_output=True, text=True,
                                              encoding="utf-8", errors="replace")
            (cell / "handler-compile.log").write_text(
                compiled_handler.stdout + compiled_handler.stderr, encoding="utf-8")
            if compiled_handler.returncode:
                raise RuntimeError(f"Handler compile RED {mode}: {cell / 'handler-compile.log'}")
            wire_paths = sorted(cell.glob("*-command-result.json"))
            if len(wire_paths) != 3:
                raise RuntimeError(f"Expected three new actual transport cases, got {len(wire_paths)}: {cell}")
            wires = {path.name: _validate_wire(path) for path in wire_paths}
            expected_branches = {
                "dead-command-result.json": "target_dead_notification_source",
                "range-command-result.json": "out_of_range_notification_source",
                "opaque-command-result.json": "opaque_existing_stock_notification_source",
            }
            for filename, branch in expected_branches.items():
                wire = wires.get(filename)
                if (wire is None or wire["status"] != "available"
                        or wire["observer_attached"] is not True
                        or wire["record_count"] != 1 or wire["source_branches"] != [branch]):
                    raise RuntimeError(f"Actual transport case did not retain its selected source: {filename}")
            suites.append({
                "mode": mode, "status": "GREEN", "compiler": "MSVC /W4 /WX",
                "optimization": optimization, "runtime": "/MD _ITERATOR_DEBUG_LEVEL=0",
                "exe_sha256": _sha256(executable),
                "handler_object_sha256": _sha256(cell / "invalidation-reason-handler.obj"),
                "commands": {"compile": compile_command, "run": run_command,
                             "handler_compile": handler_command},
                "wires": wires, "output": executed.stdout.strip(),
            })
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
