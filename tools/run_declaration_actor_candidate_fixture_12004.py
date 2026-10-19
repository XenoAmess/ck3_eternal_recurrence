"""Compile one bounded offline declaration fixture DLL, never a bridge or EXE."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"
sys.path.insert(0, str(ROOT / "tools"))
import run_native_msvc as msvc

MAXIMUM = 64 * 1024 * 1024
SOURCE_NAMES = ("ck3_12002.cpp", "ck3_12002_commands.cpp", "ck3_12002_declarations.cpp",
                "ck3_12002_declarations_test.cpp")


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def freeze(destination: Path) -> dict:
    sources, headers = [], []
    source_root, include_root = destination / "source", destination / "source/include"
    source_root.mkdir(); include_root.mkdir()
    pending = []
    for name in SOURCE_NAMES:
        source = NATIVE / "src" / name
        output = source_root / name
        output.write_bytes(source.read_bytes())
        sources.append({"original": pin(source), "frozen": pin(output)})
        pending.extend(re.findall(r'^#include "([^"]+)"', source.read_text(encoding="utf-8-sig"), re.M))
    seen = set()
    while pending:
        relative = pending.pop()
        if relative in seen:
            continue
        seen.add(relative)
        if not relative.startswith("xar_bridge/") or ".." in Path(relative).parts:
            raise ValueError("unexpected project include: " + relative)
        source, output = NATIVE / "include" / relative, include_root / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(source.read_bytes())
        headers.append({"original": pin(source), "frozen": pin(output)})
        pending.extend(re.findall(r'^#include "([^"]+)"', source.read_text(encoding="utf-8-sig"), re.M))
        if len(seen) > 1024 or sum(x["frozen"]["bytes"] for x in headers) > 16 * 1024 * 1024:
            raise ValueError("unexpected header closure expansion")
    original_test = source_root / SOURCE_NAMES[-1]
    text = original_test.read_text(encoding="utf-8-sig")
    original_entry = "int main(int argc, char **argv) {"
    if text.count(original_entry) != 1:
        raise ValueError("fixture main source changed")
    text = text.replace(original_entry, "int RunDeclarationsMain(int argc, char **argv) {", 1)
    close = text.rindex("\n}")
    text = text[:close] + "\n  return 0;" + text[close:]
    text += '\nextern "C" __declspec(dllexport) int RunNativeDeclarationFixture() {\n'
    text += '  char name[] = "offline-declaration-actor-fixture"; char *argv[] = {name, nullptr};\n'
    text += '  try { return RunDeclarationsMain(1, argv); }\n'
    text += '  catch (const std::exception &error) { std::cerr << error.what() << "\\n"; return 81; }\n}\n'
    generated = source_root / "offline-fixture.cpp"
    generated.write_text(text, encoding="utf-8", newline="\n")
    return {"production_sources": sources, "project_headers": headers, "generated_fixture": pin(generated),
            "test_transform": "Rename original main only, add explicit return0 and exported exception-catching entry; all fixture bodies retained"}


def main() -> int:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--storage-child", required=True, type=Path)
    args = parser.parse_args()
    child = json.loads(args.storage_child.read_text(encoding="utf-8-sig"))
    if str(args.output_root.resolve()).lower().replace("\\", "/") not in json.dumps(child).lower().replace("\\\\", "/"):
        raise ValueError("storage child does not name the requested exact root")
    if args.output_root.exists():
        raise ValueError("output root must be fresh/create-only")
    args.output_root.mkdir()
    started = datetime.now(timezone.utc).isoformat()
    report = {"schema": "xar.declaration-actor-candidate-offline-fixture/v1", "started_at_utc": started,
              "machine_id": subprocess.check_output(
                  [sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True).strip(),
              "producer": pin(Path(__file__)), "storage_child": pin(args.storage_child),
              "output_root": str(args.output_root.resolve()), "maximum_bytes": MAXIMUM,
              "new_EXEs": 0, "Game_native_desktop_or_system_setting_calls": 0,
              "scope": "actual declarations.cpp/core/commands and existing full fixtures plus actor candidate fixtures; offline callback equivalence only"}
    result_path = args.output_root / "RESULT.json"
    try:
        report["source_freeze"] = freeze(args.output_root)
        write(args.output_root / "SOURCE-FREEZE.json", report["source_freeze"])
        build = args.output_root / "build"
        build.mkdir()
        environment = msvc.child_environment(build)
        installation = msvc.visual_studio_installation(None, environment)
        environment, tools = msvc.initialize_msvc(installation, build, environment)
        report["environment_producer"] = pin(ROOT / "tools/run_native_msvc.py")
        report["compiler"] = pin(Path(tools["cl"]))
        report["vcvars64"] = pin(Path(tools["vcvars64"]))
        report["toolchain"] = {key: environment.get(key) for key in ("VCTOOLSVERSION", "WINDOWSSDKVERSION", "INCLUDE", "LIB")}
        source = args.output_root / "source"
        dll = build / "declaration-actor-fixture.dll"
        command = [tools["cl"], "/nologo", "/LD", "/std:c++20", "/MD", "/EHsc", "/W4", "/WX",
                   "/permissive-", "/utf-8", "/UNDEBUG", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                   "/showIncludes", "/I" + str(source / "include"),
                   *[str(source / name) for name in SOURCE_NAMES[:-1]], str(source / "offline-fixture.cpp"),
                   "/Fo" + str(build) + "\\", "/link", "/OUT:" + str(dll),
                   "/IMPLIB:" + str(build / "declaration-actor-fixture.lib")]
        log = build / "compile-link.log"
        tick = time.perf_counter()
        with log.open("wb") as stream:
            completed = subprocess.run(command, cwd=build, env=environment, stdout=stream,
                                       stderr=subprocess.STDOUT, timeout=120,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        report["compile"] = {"argv": command, "exit_code": completed.returncode,
                             "elapsed_seconds": time.perf_counter() - tick, "log": pin(log)}
        # MSVC /showIncludes uses the installed UI language despite VSLANG.
        # Parse the native byte log's absolute path, without assuming an English
        # prefix or decoding a CP936 diagnostic as UTF-8.
        includes = set(re.findall(rb"(?m)^[^\r\n]*?:\s+([A-Za-z]:[\\/][^\r\n]+)\r?$", log.read_bytes()))
        if not includes:
            raise ValueError("/showIncludes yielded no actual header paths")
        actual_headers = [pin(Path(name.strip().decode("mbcs"))) for name in sorted(includes)]
        write(args.output_root / "ACTUAL-HEADER-PINS.json", actual_headers)
        report["actual_header_pins"] = pin(args.output_root / "ACTUAL-HEADER-PINS.json")
        if completed.returncode:
            report["status"] = "COMPILE_RED"
            return 1
        report["DLL"] = pin(dll)
        # A separate ordinary interpreter loads only this offline fixture DLL.
        # There is no Game process open/injection/bridge export or EXE target.
        script = build / "run-ctypes.py"
        script.write_text('import ctypes,sys\n'
                          'module=ctypes.WinDLL(sys.argv[1])\n'
                          'entry=module.RunNativeDeclarationFixture\n'
                          'entry.argtypes=[];entry.restype=ctypes.c_int\n'
                          'raise SystemExit(entry())\n', encoding="utf-8")
        with (build / "fixture.log").open("wb") as stream:
            tick = time.perf_counter()
            executed = subprocess.run([sys.executable, str(script), str(dll)], cwd=build,
                                      env=environment, stdout=stream, stderr=subprocess.STDOUT,
                                      timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        report["execute"] = {"route": "independent ordinary Python ctypes DLL", "exit_code": executed.returncode,
                             "elapsed_seconds": time.perf_counter() - tick, "runner": pin(script),
                             "log": pin(build / "fixture.log")}
        report["status"] = "PASS" if executed.returncode == 0 else "FIXTURE_RED"
        return 0 if executed.returncode == 0 else 1
    finally:
        report["ended_at_utc"] = datetime.now(timezone.utc).isoformat()
        write(result_path, report)
        files = [pin(path) for path in sorted(args.output_root.rglob("*")) if path.is_file()]
        total = sum(row["bytes"] for row in files)
        write(args.output_root / "FILES.json", {"machine_id": report["machine_id"], "files": files,
                                               "logical_bytes_before_manifest": total,
                                               "future_writes_reserved_bytes": 0})
        total += (args.output_root / "FILES.json").stat().st_size
        if total > MAXIMUM:
            raise RuntimeError("storage child hard limit exceeded")
        print(json.dumps({"status": report.get("status", "ERROR"), "result": pin(result_path),
                          "file_count": len(files) + 1, "logical_bytes": total,
                          "future_writes_reserved_bytes": 0}))


if __name__ == "__main__":
    raise SystemExit(main())
