"""Build the actual reader against fixture-owned graphs; never connects to CK3."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    bridge = root / "ck3_autonomous_player/native_bridge"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("native_msvc", root / "tools/run_native_msvc.py")
    helper = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(helper)
    environment = helper.child_environment(output)
    installation = helper.visual_studio_installation(None, environment)
    environment, tools = helper.initialize_msvc(installation, output, environment)
    sources = [bridge / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_world.cpp", "ck3_12002_province.cpp",
        "ck3_12002_army.cpp", "ck3_12002_prisoner_war_retention.cpp",
        "ck3_12002_prisoner_war_retention_test.cpp")]

    def run(mode: str) -> dict:
        cell = output / mode
        cell.mkdir(exist_ok=True)
        executable = cell / "ck3_12002_prisoner_war_retention_test.exe"
        command = [tools["cl"], "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX",
                   "/utf-8", "/" + mode, "/I" + str(bridge / "include"),
                   *map(str, sources), "/Fe" + str(executable)]
        compiled = subprocess.run(command, cwd=cell, env=environment, capture_output=True)
        (cell / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
        row = {"mode": mode, "compile_returncode": compiled.returncode}
        if compiled.returncode == 0:
            # This fixture has no command-line arguments. In particular no
            # frozen EXE is passed as a possible output file to its process.
            test = subprocess.run([str(executable)], cwd=cell, env=environment, capture_output=True)
            (cell / "test.log").write_bytes(test.stdout + test.stderr)
            row.update(test_returncode=test.returncode,
                       output=(test.stdout + test.stderr).decode("utf-8", errors="replace"),
                       executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
        return row

    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(run, ("Od", "O2")))
    ok = all(row.get("test_returncode") == 0 for row in rows)
    report = {"schema": "xar.ck3_12002_prisoner_war_retention_fixture.v1",
              "status": "GREEN" if ok else "RED", "local_ck3_used": False,
              "live_verified": False, "results": rows,
              "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sources}}
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return int(not ok)


if __name__ == "__main__":
    raise SystemExit(main())
