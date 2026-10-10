"""One new current-profile hidden native source -> registered normal/cold consumer FIRST.

Root is the sole executor. Owned native/backend inputs; no old suite replay,
Game access, native process injection, source/EXE hash or gameplay credit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-pin", required=True)
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
    sdk = native.parent
    executable = output / "current-sway-execution-first.exe"
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12004_abi_profile.cpp",
        "ck3_12002_sway_completion_execution.cpp",
        "ck3_12002_sway_completion_execution_install.cpp",
        "ck3_12002_sway_completion_execution_serializer.cpp",
        "ck3_12004_sway_execution_first.cpp",
    )]
    command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
               "/permissive-", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
               "/D_ITERATOR_DEBUG_LEVEL=0", "/MD", "/O2", "/Gy",
               "/I" + str(native / "include"), *map(str, sources),
               "/Fe:" + str(executable), "/link", "/OPT:REF", "/INCREMENTAL:NO"]
    packet = output / "current-hidden-phase-command-result.json"
    environment["PYTHONPATH"] = os.pathsep.join((str(sdk / "src"), str(sdk / "tests/unit")))
    environment["XAR_SWAY_EXECUTION_FIRST_PACKET"] = str(packet)
    test = "tests/unit/test_sway_execution_lifecycle_12004.py::test_current_native_hidden_phase_reaches_registered_normal_and_cold_turn"
    pytest_command = [sys.executable, "-B", "-X", "utf8", "-m", "pytest", "-q", test]
    receipt = {
        "schema": "xar.ck3.sway-execution12004-connected-first.v1",
        "status": "RED", "source_pin": args.source_pin,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "compile_argv": command, "native_argv": [str(executable), str(output)],
        "registered_compound_argv": pytest_command,
        "native_packet": str(packet), "native_operands": "owned fixture memory",
        "native_inputs": "current profile; empty Env32; inherited ScriptScopeData24; two hidden branches",
        "native_path": "existing actual capturer / three-slot owned installer / copied recorder / full serializer",
        "python_path": "registered MCP / real NativeDriver transport / Service / original once-start ledger / normal and cold turns",
        "independent_completion_and_opinion": "synthetic normalized sources; existing actual4 native qualification reused",
        "native_owner_mailbox_exercised": False,
        "game_touched": False, "old_producer_or_green_replay": False,
        "new_game_day_save_or_g2_credit": False,
    }
    start = time.perf_counter()
    try:
        for label, argv, cwd in (
            ("compile", command, output),
            ("native", receipt["native_argv"], output),
            ("registered-compound", pytest_command, sdk),
        ):
            result = subprocess.run(argv, cwd=cwd, env=environment, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            log = output / (label + ".log")
            log.write_text(result.stdout + result.stderr, encoding="utf-8")
            receipt[label + "_returncode"] = result.returncode
            if result.returncode:
                raise RuntimeError(f"{label} RED; original retained at {log}")
        receipt["status"] = "GREEN"
        print("GREEN one current-profile native hidden source -> registered normal/cold ledger compound; fixture only")
        return 0
    except Exception as error:
        receipt["failure"] = str(error)
        raise
    finally:
        receipt["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["elapsed_seconds"] = time.perf_counter() - start
        (output / "ROOT-FIRST-RESULT.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
