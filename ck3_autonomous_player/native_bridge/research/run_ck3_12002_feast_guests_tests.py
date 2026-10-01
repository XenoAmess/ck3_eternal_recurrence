"""Exercise exact-build feast guest production readers with fixture-owned data."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

NATIVE = Path(__file__).resolve().parent.parent


def run(build: Path, selected: list[str] | None = None) -> None:
    build.mkdir(parents=True, exist_ok=True)
    temporary = build / "tmp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(temporary)
    os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment
    env = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=env.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    suites = []
    common = ["activity_planner_diag_v1.cpp", "activity_cost_slot12_passive_v1.cpp",
              "activity_stage5_gold_cost_v1.cpp", "activity_stage5_feast_guest_join_v1.cpp",
              "activity_feast_guest_candidate_v1.cpp",
              "activity_feast_guest_rule_provenance_v1.cpp"]
    available = ("ck3_12002_feast_guests_test", "activity_stage5_feast_guest_join_v1_test",
                     "activity_feast_guest_candidate_v1_test",
                     "activity_feast_guest_rule_provenance_v1_test")
    if selected is not None and any(test not in available for test in selected):
        raise ValueError("unknown feast guest fixture")
    for mode, flags in (("Debug", ["/Od", "/MDd"]), ("Release", ["/O2", "/MD"])):
        for test in selected or available:
            output = build / f"{test}-{mode}.exe"
            command = [compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
                       "/EHsc", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", *flags,
                       f"/I{NATIVE / 'include'}", f"/I{NATIVE / 'src'}",
                       *(str(NATIVE / "src" / name) for name in common),
                       str(NATIVE / "src" / f"{test}.cpp"), f"/Fe:{output}"]
            compiled = subprocess.run(command, cwd=build, env=env, capture_output=True, text=True)
            (build / f"{test}-{mode}-compile.log").write_text(
                compiled.stdout + compiled.stderr, encoding="utf-8")
            if compiled.returncode:
                raise RuntimeError(f"compile RED {test} {mode}: {compiled.stdout[-5000:]}{compiled.stderr[-5000:]}")
            tested = subprocess.run([str(output)], cwd=build, env=env, capture_output=True, text=True)
            (build / f"{test}-{mode}-run.log").write_text(tested.stdout + tested.stderr, encoding="utf-8")
            if tested.returncode:
                raise RuntimeError(f"fixture RED {test} {mode}: {tested.returncode} {tested.stdout}{tested.stderr}")
            suites.append({"test": test, "mode": mode, "status": "GREEN",
                           "output": tested.stdout.strip()})
            print(test, mode, "GREEN")
    (build / "result.json").write_text(json.dumps({
        "status": "GREEN", "readiness": "static-ready",
        "evidence_scope": "production native readers with fixture-owned memory and final-native callbacks",
        "game_process_started": False, "running_process_access": False,
        "suites": suites}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--suite", nargs="+", choices=(
        "ck3_12002_feast_guests_test", "activity_stage5_feast_guest_join_v1_test",
        "activity_feast_guest_candidate_v1_test", "activity_feast_guest_rule_provenance_v1_test"))
    args = parser.parse_args()
    run(args.build_root.resolve(), args.suite)
