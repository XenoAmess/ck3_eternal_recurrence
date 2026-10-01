"""MSVC fixture of actual Sway/event production readers; file-only, no game access."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent


def run(build: Path) -> None:
    build.mkdir(parents=True, exist_ok=True)
    temporary = build / "tmp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    sources = ["ck3_12002.cpp", "ck3_12002_events.cpp",
               "ck3_12002_gift_opinion.cpp",
               "ck3_12002_event_window_context.cpp", "ck3_12002_event_window_context_serializer.cpp",
               "ck3_12002_sway_outcome.cpp", "ck3_12002_sway_outcome_test.cpp"]
    suites = []
    for mode, flags in [("Debug", ["/Od", "/MDd"]), ("Release", ["/O2", "/MD"])]:
        output = build / f"sway-outcome-{mode}.exe"
        command = [compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-", "/EHsc",
                   "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", *flags,
                   f'/I{NATIVE / "include"}', *(str(NATIVE / "src" / name) for name in sources),
                   f"/Fe:{output}"]
        compiled = subprocess.run(command, cwd=build, env=environment, capture_output=True, text=True)
        (build / f"compile-{mode}.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
        if compiled.returncode:
            raise RuntimeError(f"compile RED {mode}: {compiled.stdout[-6000:]}{compiled.stderr[-6000:]}")
        executed = subprocess.run([str(output)], cwd=build, env=environment, capture_output=True, text=True)
        (build / f"run-{mode}.log").write_text(executed.stdout + executed.stderr, encoding="utf-8")
        if executed.returncode:
            raise RuntimeError(f"fixture RED {mode}: {executed.stdout}{executed.stderr}")
        for line in executed.stdout.splitlines()[:-1]:
            wire = json.loads(line)
            if wire["instance_terminal_outcome_observed"] or wire["cancel_outcome_observed"]:
                raise RuntimeError("source/opinion observation was mislabeled terminal")
        suites.append({"mode": mode, "status": "GREEN", "output": executed.stdout.splitlines()[-1]})
        mailbox_command = [compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-", "/EHsc",
                           "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", *flags, "/c",
                           f'/I{NATIVE / "include"}', str(NATIVE / "src" / "ck3_12002_sway_outcome_mailbox.cpp"),
                           f'/Fo:{build / ("sway-outcome-mailbox-" + mode + ".obj")}']
        mailbox = subprocess.run(mailbox_command, cwd=build, env=environment, capture_output=True, text=True)
        (build / f"mailbox-compile-{mode}.log").write_text(mailbox.stdout + mailbox.stderr, encoding="utf-8")
        if mailbox.returncode:
            raise RuntimeError(f"mailbox compile RED {mode}: {mailbox.stdout}{mailbox.stderr}")
        suites.append({"mode": mode, "status": "GREEN", "scope": "domain mailbox production object compilation"})
        print(mode, executed.stdout.splitlines()[-1])
    report = {"status": "GREEN", "scope": "actual production readers on synthetic owned memory/callbacks",
              "game_process_started": False, "live_verified": False, "suites": suites}
    (build / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-root", type=Path, required=True)
    run(parser.parse_args().build_root.resolve())
