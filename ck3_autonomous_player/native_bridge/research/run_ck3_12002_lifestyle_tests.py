"""Compile and run 1.20 LIFE fixtures without CK3 or a process connection."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def msvc_environment(output: Path) -> dict[str, str]:
    locator = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    query = subprocess.run([str(locator), "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"], check=True, capture_output=True, text=True)
    vcvars = Path(query.stdout.strip()) / "VC/Auxiliary/Build/vcvars64.bat"
    capture = output / "capture-msvc.cmd"
    capture.write_text(f'@call "{vcvars}" >nul\n@set\n', encoding="utf-8")
    query = subprocess.run(["cmd.exe", "/d", "/c", str(capture)], check=True, capture_output=True, text=True)
    environment = os.environ.copy()
    for line in query.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            environment[key] = value
    environment["TEMP"] = str(output)
    environment["TMP"] = str(output)
    return environment


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    bridge = root / "ck3_autonomous_player/native_bridge"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    environment = msvc_environment(output)
    compiler = shutil.which("cl.exe", path=environment.get("Path", environment.get("PATH")))
    if compiler is None:
        raise RuntimeError("MSVC compiler unavailable")
    sources = [bridge / "src" / name for name in (
        "ck3_12002_lifestyle_state.cpp", "ck3_12002_lifestyle_focus.cpp",
        "ck3_12002_lifestyle_perk.cpp", "ck3_12002_lifestyle_commands.cpp",
        "ck3_12002_lifestyle_action.cpp", "ck3_12002.cpp",
        "ck3_12002_commands.cpp", "player_lifestyle_window_candidates_v1.cpp",
        "ck3_12002_lifestyle_test.cpp")]
    results = []
    for optimization in ("Od", "O2"):
        cell = output / optimization
        cell.mkdir(exist_ok=True)
        executable = cell / "ck3_12002_lifestyle_test.exe"
        command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8", f"/{optimization}", "/I" + str(bridge / "include"), *map(str, sources), "/Fe" + str(executable)]
        compiled = subprocess.run(command, cwd=cell, env=environment, capture_output=True, text=True)
        (cell / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
        row = {"mode": optimization, "command": command, "compile_returncode": compiled.returncode}
        if compiled.returncode == 0:
            snapshot = cell / "native-lifestyle-state.json"
            executed = subprocess.run([str(executable), str(snapshot)], cwd=cell, env=environment, capture_output=True, text=True)
            (cell / "test.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
            row.update(test_returncode=executed.returncode, output=executed.stdout + executed.stderr, executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
            if snapshot.is_file():
                row["native_lifestyle_snapshot_sha256"] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        results.append(row)
        print(json.dumps(row, ensure_ascii=True))
    success = all(row.get("test_returncode") == 0 for row in results)
    report = {"schema": "xar.ck3_12002_lifestyle_offline_result.v1", "status": "GREEN" if success else "RED", "game_started": False, "native_process_access": False, "results": results, "source_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}}
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
