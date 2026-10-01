"""Build actual Crozier recovery provider/v1 serializer against fixture memory."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

NATIVE = Path(__file__).resolve().parent.parent
SOURCES = [NATIVE / "src" / name for name in (
    "ck3_12002_epidemic_recovery.cpp", "ck3_12002_epidemic_recovery_test.cpp",
    "ck3_12002.cpp", "ck3_12002_phase_definitions.cpp", "player_epidemic_recovery_v1.cpp")]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(temporary)
    os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe unavailable")
    attempts = []
    for mode in ("Od", "O2"):
        cell = output / mode
        cell.mkdir(exist_ok=True)
        executable = cell / "epidemic-recovery-fixture.exe"
        command = [compiler, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8",
                   "/permissive-", "/DNOMINMAX", f"/{mode}", f"/I{NATIVE / 'include'}",
                   *map(str, SOURCES), f"/Fe:{executable}"]
        completed = subprocess.run(command, cwd=cell, env=environment, capture_output=True, text=True)
        (cell / "compile.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        attempt = {"mode": mode, "compile_returncode": completed.returncode, "compile_command": command}
        if completed.returncode == 0:
            wire = cell / "wire"
            completed = subprocess.run([str(executable), str(wire)], cwd=cell, env=environment,
                                       capture_output=True, text=True)
            (cell / "fixture.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
            attempt.update(fixture_returncode=completed.returncode, stdout=completed.stdout,
                           stderr=completed.stderr, executable_sha256=digest(executable))
            attempt["wire"] = [{"name": path.name, "path": str(path), "sha256": digest(path),
                                "status": json.loads(path.read_text(encoding="utf-8"))["status"]}
                               for path in sorted(wire.glob("*.json"))]
        attempts.append(attempt)
    result = {
        "schema": "xar.ck3_12002.epidemic-recovery-fixture.v1",
        "status": "GREEN" if all(row.get("fixture_returncode") == 0 for row in attempts) else "RED",
        "readiness": "static-ready", "game_started": False,
        "real_ck3_process_access": False, "fixture_self_memory_reads": True,
        "wire_origin": "actual production recovery provider and unchanged production v1 serializer; fixture-owned native objects/callbacks",
        "source_sha256": {str(path.relative_to(NATIVE)): digest(path) for path in SOURCES},
        "attempts": attempts,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output.resolve())
    print(json.dumps({"status": report["status"], "result": str(args.output / "result.json"),
                      "sha256": digest(args.output / "result.json"),
                      "attempts": [{key: row.get(key) for key in ("mode", "compile_returncode", "fixture_returncode", "stdout")}
                                   for row in report["attempts"]]}, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "GREEN" else 1)
