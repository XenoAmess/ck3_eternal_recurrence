"""Build production Feast Start/final-gate fixtures without contacting CK3."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--configuration", choices=("Debug", "Release", "both"), default="both")
    parser.add_argument("--include-legacy", action="store_true")
    args = parser.parse_args()
    build = args.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("xar_msvc", ROOT / "tools/run_native_msvc.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    env = module.child_environment(build)
    install = module.visual_studio_installation(None, env)
    env, tool = module.initialize_msvc(install, build, env)
    common_start = ["activity_feast_stage5_start_v1.cpp", "activity_feast_resource_balance_v1.cpp"]
    common_gate = ["activity_planner_diag_v1.cpp", "activity_stage5_canstart_read_v1.cpp"]
    fixtures = {
        "start-12002": common_start + ["ck3_12002_activity_feast_start_test.cpp"],
        "gate-12002": common_gate + ["ck3_12002_activity_stage5_canstart_test.cpp"],
    }
    if args.include_legacy:
        fixtures.update({
            "start-11906": common_start + ["activity_feast_stage5_start_v1_test.cpp"],
            "gate-11906": common_gate + ["activity_stage5_canstart_read_v1_test.cpp"],
        })
    modes = ("Debug", "Release") if args.configuration == "both" else (args.configuration,)

    def run(item: tuple[str, list[str], str]) -> dict:
        name, sources, mode = item
        output = build / f"{name}-{mode}"
        output.mkdir(exist_ok=True)
        exe = output / "fixture.exe"
        flags = ["/Od", "/RTC1"] if mode == "Debug" else ["/O2", "/DNDEBUG"]
        command = [tool["cl"], "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8",
                   *flags, f"/I{NATIVE / 'include'}", f"/Fe:{exe}",
                   *[str(NATIVE / "src" / source) for source in sources]]
        compiled = subprocess.run(command, cwd=output, env=env, capture_output=True)
        (output / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
        result = {"fixture": name, "configuration": mode,
                  "compile_exit": compiled.returncode, "log": str(output / "compile.log")}
        if compiled.returncode == 0:
            executed = subprocess.run([str(exe)], cwd=output, env=env, capture_output=True)
            result["run_exit"] = executed.returncode
            (output / "run.log").write_bytes(executed.stdout + executed.stderr)
        return result

    work = [(name, files, mode) for name, files in fixtures.items() for mode in modes]
    with ThreadPoolExecutor(max_workers=min(8, len(work))) as workers:
        results = list(workers.map(run, work))
    passed = all(row["compile_exit"] == 0 and row.get("run_exit") == 0 for row in results)
    report = {"schema": "xar.ck3_12002.feast_start_fixture_result.v1",
              "local_ck3_contacted": False, "passed": passed, "results": results}
    (build / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
