"""Verify one hidden-phase native overlay capture with empty Env32/inherited Script24."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_wire(path: Path) -> dict:
    packet = json.loads(path.read_text(encoding="utf-8"))
    assert packet["type"] == "command_result" and packet["protocol_version"] == 1
    assert packet["ok"] is True and packet["request_id"] == "execution-inherited-scope-overlay"
    result = packet["result"]
    assert result["executable_sha256"] == EXE_SHA256
    assert result["snapshot_revision"] == 18 and result["date_raw"] == 53220000
    assert result["step"] == "query-sway-completion-execution-v1-private"
    assert result["status"] == "available" and result["read_only"] is True
    state = result["sway_completion_execution"]
    assert state["available"] is True and state["observer_attached"] is True
    assert (state["actor_character_id"], state["target_character_id"], state["scheme_instance_id"]) == (
        0x03000001, 0x04000002, 0x0100000B)
    assert state["material_effect_observed"] is False
    assert state["native_terminal_state_observed"] is False
    assert len(state["records"]) == 1
    record = state["records"][0]
    assert record["source_branch"] == "hidden_phase_success_source"
    assert record["executing_input_observed"] is True and record["exact_scope_join_ready"] is True
    assert record["message_enqueue_observed"] is False and record["material_effect_observed"] is False
    assert record["native_terminal_state_observed"] is False
    return {"path": str(path), "sha256": sha256(path), "record_count": 1,
            "source_branch": record["source_branch"], "scheme_instance_id": record["scheme_instance_id"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--caller-proof", type=Path, required=True)
    args = parser.parse_args()
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
    native = Path(__file__).resolve().parents[1]
    repository = native.parents[1]
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_sway_completion_execution.cpp",
        "ck3_12002_sway_completion_execution_serializer.cpp",
        "ck3_12002_sway_completion_execution_scope_overlay_test.cpp")]
    pins = sources + [Path(__file__).resolve(),
        native / "src/ck3_12002_sway_completion_execution_command_domain_test.cpp",
        native / "include/xar_bridge/ck3_12002_sway_completion_execution.hpp",
        native / "include/xar_bridge/ck3_12002_sway_completion_execution_mailbox.hpp",
        native / "include/xar_bridge/ck3_12002.hpp",
        repository / "research/sway_completion12002_invalidation_context_abi.json",
        repository / "docs/ck3-native-ai/ck3-1.20.0.2-sway-completion-scope-overlay.md",
        args.caller_proof.resolve()]
    suites: list[dict] = []
    result = {
        "schema": "xar.ck3.sway-completion12002-scope-overlay-fixture.v1",
        "status": "RED", "readiness": "static-ready", "live_verified": False,
        "game_version": "1.20.0.2", "executable_sha256": EXE_SHA256,
        "ck3_touched": False, "actual_production_reader": True,
        "actual_copied_recorder": True, "actual_full_command_result_serializer": True,
        "actual_owner_mailbox": False, "native_entry_installed": False,
        "fixture_observer_attached_input": True, "old_matrix_reexecuted": False,
        "native_overlay_callback": "typed owned-memory implementation of 373B540 Env32-first/Script24 fallback ABI",
        "native_scope_globals": {"scheme": "0x5D4BD60", "owner": "0x5D4BD5C", "target": "0x5D4BD58"},
        "case": "one empty Env32 inherited ScriptScopeData24 source capture, copied retention, full wire",
        "caller_proof": str(args.caller_proof.resolve()),
        "source_sha256": {str(path): sha256(path) for path in pins}, "suites": suites,
    }
    try:
        for mode, optimization in (("Debug", "/Od"), ("Release", "/O2")):
            cell = output / mode
            cell.mkdir(exist_ok=True)
            executable = cell / "sway-completion-scope-overlay.exe"
            command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
                "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", optimization,
                "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(executable)]
            compiled = subprocess.run(command, cwd=cell, env=environment, capture_output=True,
                                      text=True, encoding="utf-8", errors="replace")
            (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
            if compiled.returncode:
                raise RuntimeError(f"Compile RED {mode}: {cell / 'compile.log'}")
            run_command = [str(executable), str(cell)]
            executed = subprocess.run(run_command, cwd=cell, env=environment, capture_output=True,
                                      text=True, encoding="utf-8", errors="replace")
            (cell / "run.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
            if executed.returncode:
                raise RuntimeError(f"Fixture RED {mode}: {cell / 'run.log'}")
            wire = validate_wire(cell / "inherited-scope-command-result.json")
            suites.append({"mode": mode, "status": "GREEN", "optimization": optimization,
                "compiler_flags": "/W4 /WX /MD /D_ITERATOR_DEBUG_LEVEL=0",
                "exe_sha256": sha256(executable), "commands": {"compile": command, "run": run_command},
                "wire": wire, "output": executed.stdout.strip()})
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
