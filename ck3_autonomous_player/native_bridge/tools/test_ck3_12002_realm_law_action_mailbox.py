#!/usr/bin/env python3
"""Build and run the actual law action worker against fixture-owned native stores."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"
SOURCES = [
    "ck3_12002_realm_law_action_mailbox_test.cpp",
    "ck3_12002_realm_law_action_mailbox.cpp",
    "ck3_12002_query_mailbox.cpp",
    "ck3_12002_realm_law_source_adapter.cpp",
    "ck3_12002_realm_law_components.cpp",
    "ck3_12002_realm_law_active_collection.cpp",
    "ck3_12002_realm_law_candidate_collection.cpp",
    "ck3_12002_realm_law_final_terms.cpp",
    "ck3_12002_realm_law_enact_command_v1.cpp",
    "ck3_12002_realm_law_enact_mutation_abi_v1.cpp",
    "realm_law_final_terms_11906.cpp",
    "realm_law_governance_snapshot_v1.cpp",
    "realm_law_governance_source_adapter_v1.cpp",
    "realm_law_native_binder_v1.cpp",
    "realm_law_enact_action_v1.cpp",
    "protocol.cpp",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    args.artifacts = args.artifacts.resolve()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    sys.pycache_prefix = str(args.artifacts / ".python-cache")
    spec = importlib.util.spec_from_file_location("native_msvc", ROOT / "tools/run_native_msvc.py")
    assert spec and spec.loader
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    environment = helper.child_environment(args.artifacts)
    installation = helper.visual_studio_installation(None, environment)
    environment, tools = helper.initialize_msvc(installation, args.artifacts, environment)

    def configuration(mode: str) -> dict:
        directory = args.artifacts / mode
        directory.mkdir(exist_ok=True)
        exe = directory / "law-action-mailbox-fixture.exe"
        command = [tools["cl"], "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", f"/{mode}",
                   "/utf-8", "/DWIN32_LEAN_AND_MEAN", "/DNOMINMAX", f"/I{NATIVE / 'include'}",
                   f"/Fe{exe}", *[str(NATIVE / "src" / name) for name in SOURCES],
                   "/link", "bcrypt.lib", "user32.lib"]
        compile_result = subprocess.run(command, cwd=directory, env=environment, capture_output=True)
        (directory / "compile.log").write_bytes(compile_result.stdout + compile_result.stderr)
        record = {"mode": mode, "compile_returncode": compile_result.returncode}
        if compile_result.returncode:
            print((compile_result.stdout + compile_result.stderr).decode("mbcs", errors="replace"))
            return record
        run = subprocess.run([str(exe), str(directory)], cwd=directory, env=environment, capture_output=True)
        (directory / "run.log").write_bytes(run.stdout + run.stderr)
        record.update(run_returncode=run.returncode, executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest())
        record["wire"] = {}
        for path in sorted(directory.glob("wire-law-*.json")):
            json.loads(path.read_text(encoding="utf-8"))
            record["wire"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        print((run.stdout + run.stderr).decode("utf-8", errors="replace").strip())
        return record

    with ThreadPoolExecutor(max_workers=2) as pool:
        configurations = list(pool.map(configuration, ("Od", "O2")))
    passed = all(item.get("compile_returncode") == 0 and item.get("run_returncode") == 0
                 for item in configurations)
    report = {"schema": "xar.realm-law-action-mailbox-offline.v1", "status": "GREEN" if passed else "RED",
              "game_version": "1.20.0.2", "local_ck3_contacted": False, "configurations": configurations,
              "source_sha256": {name: hashlib.sha256((NATIVE / "src" / name).read_bytes()).hexdigest()
                                for name in SOURCES}}
    (args.artifacts / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
