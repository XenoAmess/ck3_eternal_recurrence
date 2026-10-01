"""Compile and execute copied-memory hosted Feast fixtures without CK3 access."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
ROOT = HERE.parents[2]


def run(build: Path) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location(
        "xar_native_msvc", ROOT / "tools/run_native_msvc.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    environment = module.child_environment(build)
    installation = module.visual_studio_installation(None, environment)
    environment, tools = module.initialize_msvc(installation, build, environment)

    def suite(configuration: str, legacy: bool) -> dict:
        directory = build / (configuration + ("-legacy" if legacy else "-12002"))
        directory.mkdir(exist_ok=True)
        target = directory / "hosted-fixture.exe"
        fixture = "activity_hosted_identity_v1_test.cpp" if legacy else "ck3_12002_activity_hosted_identity_test.cpp"
        source_names = ["activity_hosted_identity_v1.cpp", fixture]
        if not legacy:
            source_names.append("activity_feast_resource_balance_v1.cpp")
        flags = ["/Od", "/MDd"] if configuration == "Debug" else ["/O2", "/MD"]
        command = [tools["cl"], "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-", "/EHsc",
                   *flags, f'/I{NATIVE / "include"}',
                   *(str(NATIVE / "src" / name) for name in source_names), f"/Fe:{target}"]
        compile_result = subprocess.run(command, cwd=directory, env=environment, capture_output=True)
        (directory / "compile.log").write_bytes(compile_result.stdout + compile_result.stderr)
        if compile_result.returncode:
            raise RuntimeError(f"Compile RED: {directory}; {(compile_result.stdout + compile_result.stderr).decode('utf-8', errors='replace')}")
        execution = subprocess.run([str(target)], cwd=directory, env=environment, capture_output=True)
        (directory / "run.log").write_bytes(execution.stdout + execution.stderr)
        if execution.returncode:
            raise RuntimeError(f"Fixture RED: {directory}; exit {execution.returncode}")
        return {"configuration": configuration, "profile": "1.19.0.6" if legacy else "1.20.0.2",
                "cases": 5 if legacy else 8, "status": "GREEN", "executable": str(target),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}

    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(suite, configuration, legacy)
                for configuration in ("Debug", "Release") for legacy in (False, True)]
        suites = [job.result() for job in jobs]
    report = {"status": "GREEN", "evidence_scope": "synthetic memory with production reader",
              "game_process_started": False, "local_ck3_contacted": False, "suites": suites}
    (build / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().build_root.resolve()), indent=2))
