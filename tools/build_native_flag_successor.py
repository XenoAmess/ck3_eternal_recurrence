#!/usr/bin/env python3
"""Enable existing native flags while retaining a frozen MSVC/Ninja baseline.

Only production units whose local include closure mentions an enabled flag,
and explicitly declared newly enabled sources, are compiled. Unchanged object
files are borrowed read-only for a new archive/DLL. No CMake reconfiguration,
game process, baseline mutation or live qualification is performed.
"""
from __future__ import annotations

import argparse
import ctypes
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from run_native_msvc import child_environment, initialize_msvc, visual_studio_installation


def windows_args(command: str) -> list[str]:
    count = ctypes.c_int()
    parse = ctypes.windll.shell32.CommandLineToArgvW
    parse.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
    parse.restype = ctypes.POINTER(ctypes.c_wchar_p)
    parsed = parse(command, ctypes.byref(count))
    if not parsed:
        raise ValueError("Cannot decode the original MSVC command")
    try:
        return [parsed[index] for index in range(count.value)]
    finally:
        ctypes.windll.kernel32.LocalFree(parsed)


def pin(path: Path) -> dict:
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def run(config: dict) -> dict:
    baseline = Path(config["baseline_build_dir"]).resolve()
    source = Path(config["source_dir"]).resolve()
    output = Path(config["output_dir"]).resolve()
    if output == baseline or baseline in output.parents or output in baseline.parents:
        raise ValueError("Successor output must be separate from the frozen baseline")
    output.mkdir(parents=True, exist_ok=False)
    flags = tuple(config["enable_definitions"])
    if not flags or any(not re.fullmatch(r"[A-Z][A-Z0-9_]+", flag) for flag in flags):
        raise ValueError("Explicit existing Boolean native definitions are required")
    cache = (baseline / "CMakeCache.txt").read_text(encoding="utf-8-sig")
    for flag in flags:
        if f"{flag}:BOOL=OFF" not in cache:
            raise ValueError(f"Baseline does not declare the requested disabled flag: {flag}")
    environment = child_environment(output)
    environment, tools = initialize_msvc(
        visual_studio_installation(None, environment), output, environment)
    query = subprocess.run([tools["ninja"], "-C", str(baseline), "-t", "compdb"],
                           check=True, capture_output=True, text=True, encoding="utf-8")
    database = json.loads(query.stdout)
    runtime_target, bridge_target = config["runtime_target"], config["bridge_target"]
    groups = {}
    for target in (runtime_target, bridge_target):
        prefix = f"CMakeFiles/{target}.dir/"
        groups[target] = [row for row in database if row.get("output", "").startswith(prefix)
                          and row["output"].endswith(".obj")]
        if not groups[target] or any(not (baseline / row["output"]).is_file()
                                     for row in groups[target]):
            raise ValueError(f"Baseline lacks the complete production objects: {target}")
    includes = re.compile(r'^\s*#\s*include\s*"([^"\n]+)"', re.MULTILINE)
    memo: dict[Path, set[Path]] = {}
    texts: dict[Path, str] = {}

    def source_text(path: Path) -> str:
        if path not in texts:
            texts[path] = path.read_text(encoding="utf-8-sig", errors="replace")
        return texts[path]

    def closure(path: Path, active: frozenset = frozenset()) -> set[Path]:
        path = path.resolve()
        if path in memo:
            return memo[path]
        if path in active:
            return set()
        result = {path}
        text = source_text(path)
        for name in includes.findall(text):
            candidates = (path.parent / name, source / "include" / name,
                          source / "src" / name, source / "research" / name)
            child = next((item for item in candidates if item.is_file()), None)
            if child is not None:
                result.update(closure(child, active | {path}))
        memo[path] = result
        return result

    changed = []
    for target, rows in groups.items():
        for row in rows:
            dependencies = closure(Path(row["file"]))
            if any(any(flag in source_text(dependency)
                       for flag in flags) for dependency in dependencies):
                changed.append((target, row))
    template = next(row for row in groups[runtime_target]
                    if Path(row["file"]).name == config["runtime_template_source"])
    for relative in config.get("additional_sources", []):
        path = (source / relative).resolve()
        if not path.is_file() or source not in path.parents:
            raise ValueError(f"Newly enabled source is unavailable: {relative}")
        if any(Path(row["file"]).resolve() == path for row in groups[runtime_target]):
            raise ValueError(f"Additional source was already present: {relative}")
        row = dict(template, file=str(path),
                   output=f"CMakeFiles/{runtime_target}.dir/{relative}.obj")
        row["template_file"] = template["file"]
        changed.append((runtime_target, row))
    report = {"schema": "ck3-native-flag-successor-v1", "baseline_build_dir": str(baseline),
              "source_dir": str(source), "output_dir": str(output), "flags": list(flags),
              "baseline_dll": pin(baseline / f"{bridge_target}.dll"),
              "baseline_archive": pin(baseline / f"{runtime_target}.lib"),
              "compiled": [], "fixtures": [], "local_ck3_contacted": False,
              "live_qualified": False, "status": "building"}
    report_path = output / "RESULT.actual.json"

    def save():
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def command(argv, label):
        log = output / (label + ".log")
        started = time.monotonic()
        with log.open("wb") as stream:
            completed = subprocess.run(argv, cwd=output, env=environment,
                                       stdout=stream, stderr=subprocess.STDOUT)
        record = {"argv": argv, "exit_code": completed.returncode,
                  "elapsed_seconds": round(time.monotonic() - started, 3), "log": pin(log)}
        if completed.returncode:
            raise RuntimeError(json.dumps(record))
        return record

    def compile_row(pair):
        target, row = pair
        argv = windows_args(row["command"])
        original = row.get("template_file", row["file"])
        destination = output / row["output"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        for index, value in enumerate(argv):
            if value.startswith("/Fo"):
                argv[index] = "/Fo" + str(destination)
            elif value.startswith("/Fd"):
                argv[index] = "/Fd" + str(destination.parent) + "\\"
            elif value.replace("\\", "/").lower() == original.replace("\\", "/").lower():
                argv[index] = row["file"]
        argv.extend("-D" + flag + "=1" for flag in flags)
        record = command(argv, target + "-" + Path(row["file"]).stem)
        return {"target": target, "source": pin(Path(row["file"])),
                "object": pin(destination), "original_output": row["output"], **record}

    save()
    try:
        with ThreadPoolExecutor(max_workers=config.get("jobs", 4)) as executor:
            for record in executor.map(compile_row, changed):
                report["compiled"].append(record)
                save()
        replaced = {record["original_output"]: Path(record["object"]["path"])
                    for record in report["compiled"]}
        objects = {}
        for target, rows in groups.items():
            objects[target] = [replaced.get(row["output"], baseline / row["output"]) for row in rows]
        for target, row in changed:
            if not any(existing["output"] == row["output"] for existing in groups[target]):
                objects[target].append(replaced[row["output"]])
        runtime = output / f"{runtime_target}.lib"
        response = output / "runtime-objects.rsp"
        response.write_text(subprocess.list2cmdline([str(path) for path in objects[runtime_target]]), encoding="utf-8")
        compiler_dir = Path(tools["cl"]).parent
        report["archive"] = command([str(compiler_dir / "lib.exe"), "/nologo", "/machine:x64",
                                      "/OUT:" + str(runtime), "@" + str(response)], "archive")
        libraries = [baseline / "xar_bridge_protocol.lib", runtime, "bcrypt.lib", "kernel32.lib", "user32.lib",
                     "gdi32.lib", "winspool.lib", "shell32.lib", "ole32.lib", "oleaut32.lib", "uuid.lib",
                     "comdlg32.lib", "advapi32.lib"]
        response = output / "bridge-objects.rsp"
        response.write_text(subprocess.list2cmdline([str(path) for path in objects[bridge_target]]
                                                   + [str(path) for path in libraries]), encoding="utf-8")
        report["link"] = command([str(compiler_dir / "link.exe"), "/nologo", "@" + str(response),
                                   "/OUT:" + str(output / f"{bridge_target}.dll"),
                                   "/IMPLIB:" + str(output / f"{bridge_target}.lib"),
                                   "/DLL", "/VERSION:0.0", "/MACHINE:X64", "/INCREMENTAL:NO"], "link")
        report.update(dll=pin(output / f"{bridge_target}.dll"), runtime=pin(runtime))
        save()
        for relative in config.get("fixture_sources", []):
            row = dict(template, file=str(source / relative), template_file=template["file"],
                       output="fixtures/" + Path(relative).name + ".obj")
            record = compile_row(("fixture", row))
            executable = output / "fixtures" / (Path(relative).stem + ".exe")
            fixture_response = executable.with_suffix(".rsp")
            fixture_response.write_text(subprocess.list2cmdline([
                record["object"]["path"],
                *(str(path) for path in objects[bridge_target] if config.get("fixture_whole_bridge") is True),
                *(str(baseline / path) for path in config.get("fixture_link_objects", [])),
                *map(str, libraries)]), encoding="utf-8")
            record["link"] = command([str(compiler_dir / "link.exe"), "/nologo", "/MACHINE:X64", "/OPT:REF",
                "/OUT:" + str(executable), "@" + str(fixture_response)], Path(relative).stem + "-link")
            record["run"] = command([str(executable), str(output / "wire")], Path(relative).stem + "-run")
            report["fixtures"].append(record)
            save()
        report.update(status="built", dll=pin(output / f"{bridge_target}.dll"),
                      runtime=pin(runtime), reused_objects=sum(len(rows) for rows in groups.values())
                      - sum(1 for _, row in changed if "template_file" not in row))
    except Exception as error:
        report.update(status="failed", error=str(error))
        raise
    finally:
        save()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(json.loads(args.config.read_text(encoding="utf-8")))
        print(json.dumps({key: report[key] for key in ("status", "dll", "runtime", "reused_objects")}, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
