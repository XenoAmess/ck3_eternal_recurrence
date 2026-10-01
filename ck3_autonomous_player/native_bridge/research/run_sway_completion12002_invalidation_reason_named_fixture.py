"""Run one actual secondary notification sink through the named invalidation-source query queue."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from run_sway_completion12002_invalidation_reason_mailbox_fixture import _sha256, _validate_wire


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
        "ck3_12002_sway_completion_execution.cpp",
        "ck3_12002_sway_completion_execution_install.cpp",
        "ck3_12002_sway_completion_invalidation_reason.cpp",
        "ck3_12002_sway_completion_invalidation_reason_mailbox.cpp",
        "ck3_12002_sway_completion_invalidation_reason_serializer.cpp",
        "r6_sway_completion_invalidation_reason_named_test.cpp")]
    source_apply = output.parents[1] / "secondary-sink/source-apply-receipt.json"
    pins = sources + [Path(__file__).resolve(),
        native / "src/ck3_12002_sway_completion_execution_install_test.cpp",
        native / "research/run_sway_completion12002_invalidation_reason_mailbox_fixture.py",
        native / "include/xar_bridge/ck3_12002.hpp",
        native / "include/xar_bridge/game_adapter.hpp",
        native / "include/xar_bridge/ck3_12002_query_mailbox.hpp",
        native / "include/xar_bridge/main_thread_query_mailbox_v1.hpp",
        native / "include/xar_bridge/ck3_12002_sway_completion_execution.hpp",
        native / "include/xar_bridge/ck3_12002_sway_completion_execution_install.hpp",
        native / "include/xar_bridge/ck3_12002_sway_completion_invalidation_reason.hpp",
        native / "include/xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp",
        native / "research/ck3_sway_completion12002_execution_install_abi.json",
        native.parents[1] / "research/sway_completion12002_history_abi.json", source_apply]
    result = {
        "schema": "xar.ck3.sway-completion12002-invalidation-reason-named-fixture.v1",
        "status": "RED", "readiness": "static-ready", "live_verified": False,
        "game_version": "1.20.0.2",
        "executable_sha256": "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "ck3_touched": False,
        "actual_fixture_typed_source_install": True,
        "actual_installed_toast_slot": True,
        "actual_secondary_sink": True,
        "actual_selected_reason_capture_and_copied_record": True,
        "actual_typed_original_forwarded_once": True,
        "actual_named_mailbox_install_environment_copy_and_admission": True,
        "actual_try_submit_owner_pump_drain_wait_reclaim": True,
        "actual_owner_query_envelope": True,
        "actual_full_command_formatter": True,
        "fixture_owned_slots_originals_iat_profile_and_frame": True,
        "native_execute_entry_installed_in_game": False,
        "shared_worker_dispatch_included": False,
        "message_enqueue_render_material_endcause_terminal_observed": False,
        "previous_source_and_transport_matrices_reexecuted": False,
        "named_executor_field": "permitted_executor_sway_completion_invalidation_reason12002",
        "cases": ["actual installed secondary reason sink and named queue selected-dead command_result"],
        "source_sha256": {str(path): _sha256(path) for path in pins},
        "suites": [],
    }
    receipt = output / "result.json"
    try:
        cell = output / "Release"
        cell.mkdir(exist_ok=True)
        executable = cell / "sway-invalidation-reason-named.exe"
        compile_command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
            "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
            "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", "/O2",
            "/I" + str(native / "include"), *map(str, sources),
            "/Fe:" + str(executable), "User32.lib"]
        compiled = subprocess.run(compile_command, cwd=cell, env=environment, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace")
        (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
        if compiled.returncode:
            raise RuntimeError(f"Compile RED Release: {cell / 'compile.log'}")
        run_command = [str(executable), str(cell)]
        executed = subprocess.run(run_command, cwd=cell, env=environment, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace")
        (cell / "run.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
        if executed.returncode:
            raise RuntimeError(f"Fixture RED Release: {cell / 'run.log'}")
        wire = cell / "named-reason-command-result.json"
        wires = {wire.name: _validate_wire(wire)}
        summary = wires[wire.name]
        if (summary["status"] != "available" or summary["observer_attached"] is not True
                or summary["record_count"] != 1
                or summary["source_branches"] != ["target_dead_notification_source"]):
            raise RuntimeError("Actual named query did not return the installed sink's selected reason source")
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
