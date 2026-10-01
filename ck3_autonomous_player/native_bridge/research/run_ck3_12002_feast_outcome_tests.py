"""Compile and execute independent Feast outcome counter fixtures without CK3 access."""
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


def run(build: Path, serializer_source: Path, wire_fixture: Path | None = None) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location(
        "xar_native_msvc", ROOT / "tools/run_native_msvc.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    environment = module.child_environment(build)
    installation = module.visual_studio_installation(None, environment)
    environment, tools = module.initialize_msvc(installation, build, environment)

    def suite(configuration: str) -> dict:
        directory = build / configuration
        directory.mkdir(exist_ok=True)
        target = directory / "outcome-fixture.exe"
        source_names = ["ck3_12002_feast_outcome_values.cpp",
                        "ck3_12002_phase_character.cpp",
                        "activity_hosted_identity_v1.cpp",
                        "activity_feast_resource_balance_v1.cpp",
                        "ck3_12002_feast_outcome_values_test.cpp"]
        flags = ["/Od", "/MDd"] if configuration == "Debug" else ["/O2", "/MD"]
        command = [tools["cl"], "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-", "/EHsc",
                   *flags, f'/I{NATIVE / "include"}', f'/I{NATIVE / "src"}',
                   *(str(NATIVE / "src" / name) for name in source_names),
                   str(serializer_source), f"/Fe:{target}"]
        compile_result = subprocess.run(command, cwd=directory, env=environment, capture_output=True)
        (directory / "compile.log").write_bytes(compile_result.stdout + compile_result.stderr)
        if compile_result.returncode:
            raise RuntimeError(f"Compile RED: {directory}; {(compile_result.stdout + compile_result.stderr).decode('utf-8', errors='replace')}")
        wire = directory / "wire"
        execution = subprocess.run([str(target), str(wire)], cwd=directory,
                                   env=environment, capture_output=True)
        (directory / "run.log").write_bytes(execution.stdout + execution.stderr)
        if execution.returncode:
            raise RuntimeError(f"Fixture RED: {directory}; exit {execution.returncode}")
        return {"configuration": configuration, "profile": "1.20.0.2",
                "cases": 8, "status": "GREEN", "executable": str(target),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "post_wire": str(wire / "post-wire.json"),
                "baseline_wire": str(wire / "before-start.json"),
                "post_wire_sha256": hashlib.sha256((wire / "post-wire.json").read_bytes()).hexdigest(),
                "baseline_wire_sha256": hashlib.sha256((wire / "before-start.json").read_bytes()).hexdigest()}

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(suite, configuration)
                for configuration in ("Debug", "Release")]
        suites = [job.result() for job in jobs]
    report = {"status": "GREEN", "evidence_scope": "synthetic memory with production reader",
              "game_process_started": False, "local_ck3_contacted": False,
              "serializer_source": str(serializer_source),
              "serializer_source_sha256": hashlib.sha256(serializer_source.read_bytes()).hexdigest(),
              "wire_labels": ["ongoing_before", "completed_after", "nonreveler_ongoing", "released"],
              "baseline_fixture_supplied_fields": ["four_costs_observed", "resources",
                                                   "normal_refresh_sequence", "final_can_start",
                                                   "guest_join_status"],
              "suites": suites}
    if suites[0]["post_wire_sha256"] != suites[1]["post_wire_sha256"]:
        raise RuntimeError("Debug/Release production wire differs")
    if wire_fixture is not None:
        wire_fixture.parent.mkdir(parents=True, exist_ok=True)
        wire_fixture.write_bytes(Path(suites[1]["post_wire"]).read_bytes())
        wire_fixture.with_name(wire_fixture.stem + "_baseline.json").write_bytes(
            Path(suites[1]["baseline_wire"]).read_bytes())
        report["tracked_wire_fixture"] = str(wire_fixture)
    (build / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--serializer-source", type=Path, required=True,
                        help="Exact serializer extraction emitted by the parent wire test")
    parser.add_argument("--wire-fixture", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.build_root.resolve(), args.serializer_source.resolve(),
                         args.wire_fixture.resolve() if args.wire_fixture else None), indent=2))
