"""One MSVC O2 fixture for the actual readonly Tenet source provider/serializer."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    native = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    temp = output / "tmp"
    temp.mkdir(exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    sources = [native / "src" / (name + ".cpp") for name in (
        "ck3_12002", "religion_reform12002_window", "religion_doctrine12002_tenet_rows",
        "religion_reform12002_tenet_sources", "religion_reform12002_tenet_sources_test")]
    exe = output / "tenet-sources-test.exe"
    command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/O2",
        "/W4", "/WX", "/utf-8", "/I" + str(native / "include"), *map(str, sources), "/Fe:" + str(exe)])
    batch = output / "build.cmd"
    batch.write_text('@echo off\ncall "' + str(Path(installed) / "VC/Auxiliary/Build/vcvars64.bat") +
        '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' + command + '\nexit /b %errorlevel%\n', encoding="utf-8")
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
    built = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=output, env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    (output / "build.log").write_text(built.stdout + built.stderr, encoding="utf-8")
    if built.returncode:
        raise RuntimeError("Compile failed: " + str(output / "build.log"))
    run = subprocess.run([str(exe), str(output)], cwd=output, env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    (output / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode:
        raise RuntimeError("Fixture failed: " + str(output / "test.log"))
    wires = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in output.glob("*.json") if p.name != "result.json"}
    actual = wires["actual-multiple-sources"]
    assert actual["schema"] == "ck3_12002_current_draft_tenet_sources_v1"
    assert actual["slots_share_source_predicate"] and len(actual["sources"]) == 8
    assert [slot["slot_index"] for slot in actual["slots"]] == [7, 11]
    assert actual["sources"][3]["native_status_raw"] == 0 and actual["sources"][3]["final_selectable"]
    assert actual["sources"][4]["source_can_materialize"] and not actual["sources"][4]["native_can_pick"]
    assert wires["actual-category-exemption"]["raw_category_exemption_key"] == "tenet_0"
    assert wires["actual-empty-source-collections"]["tenet_gates_complete"]
    assert not wires["window-absent"]["draft_observed"]
    assert not wires["native-query-unavailable"]["available"]
    pins = sources + [native / "include/xar_bridge/religion_reform12002_tenet_sources.hpp"]
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_provider": True, "actual_serializer": True,
        "native_functions_stubbed": True, "compiler": "MSVC /O2 /W4 /WX", "case_count": 8,
        "actual_cpp_json_cases": len(wires), "stdout": run.stdout.strip(),
        "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in pins},
        "wire_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob("*.json") if p.name != "result.json"},
        "executable_sha256": hashlib.sha256(exe.read_bytes()).hexdigest()}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(run.stdout.strip())


if __name__ == "__main__":
    main()
