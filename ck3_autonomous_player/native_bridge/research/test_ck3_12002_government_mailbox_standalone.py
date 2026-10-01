#!/usr/bin/env python3
"""Exercise the production 1.20 government caller through a fixture mailbox."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from test_government_runtime_adapter_12002_standalone import COMMON_SOURCES, run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import (
    visual_studio_developer_shell,
)


SOURCES = COMMON_SOURCES + (
    "main_thread_query_mailbox_v1.cpp",
    "ck3_12002_government_mailbox.cpp",
)
TEST_SOURCE = "ck3_12002_government_mailbox_test.cpp"


def build_mode(root: Path, shell: Path, output_root: Path, optimized: bool) -> dict:
    mode = "O2" if optimized else "Od"
    output = output_root / mode
    output.mkdir(parents=True, exist_ok=True)
    native = root / "ck3_autonomous_player/native_bridge"
    compiler = [
        "cl.exe", "/nologo", "/std:c++20", "/EHsc", "/permissive-",
        "/Zc:__cplusplus", "/W4", "/WX", "/utf-8", "/DNOMINMAX",
        "/DWIN32_LEAN_AND_MEAN", "/DUNICODE", "/D_UNICODE", f"/{mode}",
        "/DXAR_CK3_ENABLE_G2_GOVERNMENT_RUNTIME_ADAPTER_PRIVATE_QUERY_V1=1",
        "/DXAR_GOVERNMENT_MAILBOX_STANDALONE_NATIVE_ADAPTER=1",
        f"/I{native / 'include'}",
    ]
    run_batch(
        command=compiler + ["/c", "/MP64"] + [
            str(native / "src" / source) for source in SOURCES
        ], shell=shell, output=output, tag="common",
    )
    executable = output / "ck3_12002_government_mailbox_test.exe"
    run_batch(
        command=compiler + [str(native / "src" / TEST_SOURCE)] + [
            str(output / Path(source).with_suffix(".obj")) for source in SOURCES
        ] + ["User32.lib", f"/Fe:{executable}"],
        shell=shell, output=output, tag="caller-fixture",
    )
    wire_json = output / "wire/caller-unavailable.json"
    wire_json.parent.mkdir(exist_ok=True)
    completed = subprocess.run(
        [str(executable), "--wire-json", str(wire_json)],
        cwd=output, capture_output=True, text=True, encoding="utf-8",
        errors="replace", check=False, timeout=15,
    )
    (output / "caller-fixture.log").write_text(
        completed.stdout + completed.stderr, encoding="utf-8"
    )
    if completed.returncode:
        raise RuntimeError(f"{mode} caller fixture failed: {completed.stdout}{completed.stderr}")
    envelope = json.loads(wire_json.read_text(encoding="utf-8"))
    payload = envelope["result"]["government_runtime_adapter"]
    if (
        envelope["type"] != "command_result"
        or envelope["request_id"] != "caller-fixture"
        or not envelope["ok"]
        or envelope["result"]["step"] != "query-government-runtime-adapter-v1"
        or envelope["result"]["snapshot_revision"] != 701
        or envelope["result"]["accepted"] is not True
        or envelope["result"]["private_build"] is not True
        or envelope["result"]["read_only"] is not True
        or envelope["result"]["advertised"] is not False
        or payload["status"] != "unavailable"
        or payload["snapshot_revision"] != 701
        or payload["build"]["version"] != "1.20.0.2"
        or not payload["unavailable_reason"]
        or payload["readiness"]["core_adapter_ready"]
    ):
        raise RuntimeError(f"{mode} caller wire payload failed")
    return {
        "mode": mode,
        "compile": "GREEN_W4_WX",
        "fixture": completed.stdout.strip(),
        "wire_unavailable_reason": payload["unavailable_reason"],
        "wire_json_sha256": hashlib.sha256(wire_json.read_bytes()).hexdigest(),
        "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve()
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[3]
    shell = visual_studio_developer_shell()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(
            build_mode, root, shell, output, optimized
        ) for optimized in (False, True)]
        results = [future.result() for future in futures]
    receipt = {
        "status": "GREEN",
        "contract": "ck3-12002-government-production-caller",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "source_sha256": {
            source: hashlib.sha256((root / "ck3_autonomous_player/native_bridge/src" / source).read_bytes()).hexdigest()
            for source in SOURCES + (TEST_SOURCE,)
        },
        "ck3_launched": False,
        "ck3_process_queried": False,
        "ck3_pipe_opened": False,
        "desktop_hook_installed": False,
        "scope": "actual production caller, existing mailbox and private provider; absent CK3 roots yield typed unavailable",
        "native_adapter_unwrap": "standalone linker stand-in for bare FakeAdapter identity only; existing WorkerAdapter unwrap fixtures and full bridge link use actual implementation",
        "live_status": "not_run",
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
