"""Root-only standalone FIRST using an already qualified incremental runtime.

Compile only the owned fixture main, link the qualified production Bridge
object/runtime/Protocol closure, run the native producer once and the single
registered MCP compound once. No configure, runtime rebuild or old test replay.
Authored source lane does not execute this helper.
"""

from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def referenced_path(value, relative_to: Path) -> Path:
    path = Path(value["path"] if isinstance(value, dict) else value)
    return path if path.is_absolute() else relative_to / path


def windows_arguments(command: str) -> list[str]:
    # Decode the qualified Windows command without guessing quote boundaries.
    shell32 = ctypes.windll.shell32
    shell32.CommandLineToArgvW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
    count = ctypes.c_int()
    pointer = shell32.CommandLineToArgvW(command, ctypes.byref(count))
    if not pointer:
        raise OSError("CommandLineToArgvW could not decode qualified compile command")
    try:
        return [pointer[index] for index in range(count.value)]
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(ctypes.cast(pointer, ctypes.c_void_p))


def fixture_compile_arguments(row: dict, source: Path, obj: Path, output: Path) -> list[str]:
    arguments = windows_arguments(row["command"])
    original_source = os.path.normcase(os.path.normpath(row["file"]))
    result = [arguments[0]]
    skip_next = False
    replaced_source = False
    for argument in arguments[1:]:
        if skip_next:
            skip_next = False
            continue
        if argument.lower().startswith(("/fo", "/fd")):
            skip_next = len(argument) == 3
            continue
        if os.path.normcase(os.path.normpath(argument)) == original_source:
            replaced_source = True
            continue
        result.append(argument)
    if not replaced_source:
        raise ValueError("qualified compile row did not contain its declared source")
    native = source.parents[1]
    # Current complete source headers precede the qualified inherited overlays;
    # the remaining options/feature definitions keep their real compile shape.
    result[1:1] = ["/I" + str(native / name) for name in ("include", "src", "research")]
    result.extend(["/UNDEBUG", "/Fo" + str(obj), "/Fd" + str(output / "fixture.pdb"), str(source)])
    return result


def compiler_environment(vcvars: Path, output: Path, additions: dict) -> dict[str, str]:
    environment = {key.upper(): value for key, value in os.environ.items()}
    temporary = output / "compiler-temp"
    temporary.mkdir(parents=True, exist_ok=True)
    environment.update({"TEMP": str(temporary), "TMP": str(temporary), "VSLANG": "1033",
                        "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
                        "PYTHONPYCACHEPREFIX": str(output / "python-cache")})
    capture = output / "capture-msvc.cmd"
    capture.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\n'
        'if errorlevel 1 exit /b %errorlevel%\nset\n', encoding="utf-8", newline="\r\n")
    completed = subprocess.run([environment.get("COMSPEC", "cmd.exe"), "/d", "/u", "/c", str(capture)],
        cwd=output, env=environment, capture_output=True, check=True)
    for line in completed.stdout.decode("utf-16-le", errors="replace").splitlines():
        if "=" in line and not line.startswith("="):
            key, value = line.split("=", 1)
            environment[key.upper()] = value
    environment.update({key.upper(): str(value) for key, value in additions.items()})
    return environment


def execute(stage: str, command: list[str], cwd: Path, environment: dict,
            output: Path, report: dict) -> None:
    log = output / (stage + ".log")
    with log.open("wb") as stream:
        result = subprocess.run(command, cwd=cwd, env=environment,
            stdout=stream, stderr=subprocess.STDOUT, check=False)
    report["stages"].append({"stage": stage, "argv": command, "cwd": str(cwd),
                             "exit_code": result.returncode, "log": str(log)})
    if result.returncode != 0:
        raise RuntimeError(stage + " failed; retain " + str(log))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-receipt", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"schema": "ck3.actual4.prisoner-release-material-standalone-first.v1",
        "status": "NOTRUN", "runtime_receipt": str(args.runtime_receipt.resolve()),
        "source_root": str(args.source_root.resolve()), "output_dir": str(output), "stages": [],
        "configured": False, "runtime_rebuilt": False, "old_tests_replayed": False,
        "replacement_provider_defined": False, "game_or_pipe_contacted": False,
        "production_live": False, "action_submitted": False}
    try:
        receipt_path = args.runtime_receipt.resolve()
        receipt = read_json(receipt_path)
        if receipt.get("dll_build_status") != "GREEN":
            raise ValueError("FIRST needs the completed qualified runtime receipt")
        manifest_path = referenced_path(receipt["manifest"], receipt_path.parent)
        manifest = read_json(manifest_path)
        plan_path = referenced_path(manifest["new_compile_and_link_plan"], manifest_path.parent)
        plan = read_json(plan_path)
        compile_path = referenced_path(manifest["actual_compile_commands"], manifest_path.parent)
        compile_rows = read_json(compile_path)
        preferred = "ck3_12004_prisoner_collection_result.cpp"
        row = next((item for item in compile_rows if Path(item["file"]).name == preferred), compile_rows[0])
        native = args.source_root.resolve() / "ck3_autonomous_player" / "native_bridge"
        source = native / "tests" / "ck3_12004_prisoner_release_material_whole_first.cpp"
        obj = output / "prisoner-release-material-first.obj"
        executable = output / "prisoner-release-material-first.exe"
        arguments = fixture_compile_arguments(row, source, obj, output)
        toolchain = manifest["toolchain"]
        environment = compiler_environment(
            referenced_path(toolchain["vcvars64"], manifest_path.parent), output,
            plan.get("compiler_environment_added", {}))
        report.update({"runtime_source_head": receipt.get("source_head"),
            "manifest": str(manifest_path), "qualified_build_plan": str(plan_path),
            "qualified_compile_commands": str(compile_path), "fixture_compiled_translation_units": 1})
        execute("fixture-compile", arguments, Path(row["directory"]), environment, output, report)
        qualified_rsp = referenced_path(plan["response_file"], plan_path.parent)
        rsp = output / "fixture-link.rsp"
        # These are actual qualified production objects/libraries, including
        # the current substituted runtime archive and Protocol dependency.
        rsp.write_text(subprocess.list2cmdline([str(obj)]) + "\n" +
            qualified_rsp.read_text(encoding="utf-8-sig"), encoding="utf-8", newline="\n")
        report["qualified_bridge_runtime_protocol_response_file"] = str(qualified_rsp)
        execute("fixture-link", [str(referenced_path(toolchain["link"], manifest_path.parent)),
            "/nologo", "@" + str(rsp), "/out:" + str(executable), "/machine:x64", "/INCREMENTAL:NO"],
            Path(plan["link_cwd"]), environment, output, report)
        wires = output / "native"
        consumed = output / "registered"
        execute("native-first", [str(executable), str(wires)], output, environment, output, report)
        consumer = native / "research" / "fixtures" / "run_prisoner_release_material_12004_registered_first.py"
        execute("registered-first", [str(args.python.resolve()), str(consumer),
            "--source-root", str(args.source_root.resolve()), "--native-wire-dir", str(wires),
            "--output-dir", str(consumed)], output, environment, output, report)
        native_receipt = read_json(wires / "NATIVE-FIRST.json")
        public_receipt = read_json(consumed / "CONSUMER-FIRST.json")
        if (native_receipt.get("whole_wire_cases") != 4 or public_receipt.get("status") != "GREEN"
                or public_receipt.get("compound_methods") != 1 or len(public_receipt.get("rows", [])) != 5):
            raise ValueError("FIRST did not complete the one native/public compound with all five cases")
        report.update({"status": "GREEN", "native_receipt": str(wires / "NATIVE-FIRST.json"),
            "public_receipt": str(consumed / "CONSUMER-FIRST.json"), "compound_methods": 1,
            "native_whole_cases": 4, "public_cases": 5})
    except Exception as error:
        report.update({"status": "RED", "error": str(error)})
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    path = output / "ROOT-STANDALONE-FIRST.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": str(path)}))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
