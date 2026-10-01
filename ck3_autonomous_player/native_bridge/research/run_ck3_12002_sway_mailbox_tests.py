"""Exercise actual Sway owning-envelope executor on fixture-owned native objects."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    native = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    temp = output / "tmp"; temp.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temp)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if not compiler: raise RuntimeError("MSVC unavailable")
    sources = [native / "src" / name for name in ("ck3_12002.cpp", "ck3_12002_commands.cpp",
        "ck3_12002_context.cpp", "ck3_12002_gift_opinion.cpp", "ck3_12002_query_mailbox.cpp",
        "ck3_12002_sway_state.cpp", "ck3_12002_sway_command.cpp", "ck3_12002_sway_serializer.cpp",
        "active_scheme_semantic_action_v1_private.cpp", "ck3_12002_sway_mailbox.cpp",
        "ck3_12002_sway_mailbox_test.cpp")]
    suites = []
    for name, mode in (("Debug", "/Od"), ("Release", "/O2")):
        exe = output / ("sway-mailbox-" + name + ".exe")
        command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/utf-8", "/DNOMINMAX",
            mode, "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(exe)]
        build = subprocess.run(command, cwd=output, env=environment, capture_output=True,
            text=True, encoding="utf-8", errors="replace")
        (output / ("build-" + name + ".log")).write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + name)
        run = subprocess.run([str(exe)], cwd=output, env=environment, capture_output=True,
            text=True, encoding="utf-8", errors="replace")
        (output / ("test-" + name + ".log")).write_text(run.stdout + run.stderr, encoding="utf-8")
        suites.append({"mode": name, "status": "GREEN" if not run.returncode else "RED",
            "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest()})
        if run.returncode: raise RuntimeError("Fixture failed: " + name)
        print(run.stdout.strip())
    pins = sources + [native / "src" / name for name in
        ("ck3_12002_sway_state_test.cpp", "ck3_12002_sway_command_test.cpp")]
    result = {"status": "GREEN", "readiness": "static-ready", "actual_owner_envelope": True,
        "actual_sway_executor": True, "worker_dispatch_included": False, "live_verified": False,
        "ck3_touched": False, "suites": suites,
        "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
