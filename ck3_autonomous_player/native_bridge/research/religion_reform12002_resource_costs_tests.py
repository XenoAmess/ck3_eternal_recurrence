#!/usr/bin/env python3
"""One O2 actual CostReader/base-fee adapter/serializer fixture; no CK3 access."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    native = here.parent
    root = here.parents[2]
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    temp = output / "tmp"; temp.mkdir(exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installation = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        check=True, capture_output=True, text=True).stdout.strip()
    vcvars = Path(installation) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in (
        "religion_reform12002_costs.cpp", "religion_reform12002_resource_costs.cpp",
        "religion_reform12002_resource_costs_test.cpp")]
    exe = output / "rite-creation-base-resource-costs-test.exe"
    argv = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/O2", "/W4", "/WX", "/utf-8",
            "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(exe)]
    batch = output / "build.cmd"
    batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
                     subprocess.list2cmdline(argv) + "\nexit /b %errorlevel%\n", encoding="utf-8")
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
    build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=output, env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    (output / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    if build.returncode:
        raise RuntimeError("O2 compile RED; preserved build.log")
    test = subprocess.run([str(exe), str(output)], cwd=output, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    (output / "test.log").write_text(test.stdout + test.stderr, encoding="utf-8")
    if test.returncode:
        raise RuntimeError("O2 fixture RED; preserved test.log")
    wires = {name: json.loads((output / name).read_text(encoding="utf-8")) for name in
             ("create-missing-piety.json", "edit-zero.json", "bindings-unavailable.json")}
    create = wires["create-missing-piety.json"]
    edit = wires["edit-zero.json"]
    unavailable = wires["bindings-unavailable.json"]
    assert create["native_base_fee_slots_raw"] == [0, 0, 155000000, 0, 0, 0, 0, 0, 0, 0]
    assert create["draft_kind"] == "create_rite_or_faith"
    assert not create["draft_quote"]["has_enough_piety"]
    assert edit["native_base_fee_slots_raw"] == [0] * 10 and edit["draft_kind"] == "edit_owned_current_rite"
    assert edit["draft_quote"]["piety_missing_signed_raw"] == -175500000
    assert unavailable["native_base_fee_slots_raw"] is None and not unavailable["available"]
    assert all(not q["actual_debit_observed"] and not q["post_action_net_resource_change_observed"]
               and not q["draft_quote"]["other_resource_costs_observed"] for q in wires.values())
    pins = sources + [native / "include/xar_bridge/religion_reform12002_resource_costs.hpp",
                       native / "include/xar_bridge/religion_reform12002_costs.hpp"]
    result = {"status": "GREEN", "readiness": "static-ready library",
              "compiler": "MSVC /O2 /W4 /WX", "returncode": test.returncode,
              "stdout": test.stdout.strip(), "actual_wire_cases": len(wires),
              "original_CostReader_executed": True, "actual_new_provider_and_serializer": True,
              "native_exe_callbacks_executed": False, "local_ck3_touched": False,
              "live_verified": False, "mcp_registered": False,
              "scope": "native command draft base-fee quote; not actual debit or total net outcome",
              "executable_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
              "source_sha256": {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest() for f in pins},
              "wire_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in wires}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
