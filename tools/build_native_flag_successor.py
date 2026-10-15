#!/usr/bin/env python3
"""Build pinned flag/source successors from a frozen MSVC/Ninja baseline.

Production units affected by new flags or exact source overlays are compiled.
Header overlays use actual Ninja compiler dependencies plus the new local
include closure across both production targets. Unchanged object
files are borrowed read-only for a new archive/DLL. No CMake reconfiguration,
game process, baseline mutation or live qualification is performed.

Optional source_overlay declares output_dir and files with relative_path plus
an exact source {path, bytes, sha256} pin. Its new source tree is a separate copy;
enable_definitions may be empty for this explicit source-only successor. The
original source_dir remains the predecessor lineage identity. Actual Ninja
dependencies and each affected production output are preserved in the report.
"""
from __future__ import annotations

import argparse
import ctypes
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from run_native_msvc import child_environment, initialize_msvc, visual_studio_installation
from register_project_exe_exclusions import collect_command_manifest, opted_in, register_manifest


ROOT = Path(__file__).resolve().parents[1]


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


def parse_ninja_dependencies(text: str, baseline: Path) -> dict[str, set[Path]]:
    """Read Ninja's actual MSVC dependency records, including indirect headers."""
    result, current = {}, None
    for line in text.splitlines():
        match = re.match(r'^(.*): #deps \d+, deps mtime .* \((VALID|STALE)\)$', line)
        if match:
            current = match[1].replace('\\', '/')
            if match[2] != 'VALID':
                current = None
            else:
                result[current] = set()
        elif current is not None and line.startswith('    '):
            path = Path(line.strip())
            result[current].add((path if path.is_absolute() else baseline / path).resolve())
    return result


def materialize_source_overlay(config: dict, source: Path, inherited: dict) -> tuple[Path, dict | None]:
    declaration = config.get('source_overlay')
    previous = inherited.get('effective_source_dir', source)
    if declaration is None:
        return previous, None
    if not isinstance(declaration, dict) or set(declaration) != {'output_dir', 'files'}:
        raise ValueError('Source overlay requires explicit output_dir and pinned files')
    destination = Path(declaration['output_dir']).resolve()
    if any(destination == root or destination in root.parents or root in destination.parents
           for root in (source, previous, Path(config['baseline_build_dir']).resolve())):
        raise ValueError('Overlay source must be separate from original source/baseline')
    files = declaration['files']
    if not isinstance(files, list) or not files:
        raise ValueError('Source overlay requires nonempty exact file pins')
    prepared, seen = [], set()
    for row in files:
        relative = Path(row['relative_path'])
        if relative.anchor or '..' in relative.parts or not relative.parts:
            raise ValueError('Overlay relative_path escapes source')
        name = relative.as_posix()
        if name in seen:
            raise ValueError('Duplicate overlay source: ' + name)
        seen.add(name)
        reference = row['source']
        path = Path(reference['path']).resolve()
        actual = pin(path)
        if actual['bytes'] != reference.get('bytes') or actual['sha256'] != reference.get('sha256'):
            raise ValueError('Pinned overlay input changed: ' + name)
        prepared.append((relative, actual, path.read_bytes()))
    shutil.copytree(previous, destination)
    records = []
    for relative, actual, raw in prepared:
        path = destination / relative
        before = pin(path) if path.is_file() else None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        records.append({'relative_path': relative.as_posix(), 'source': actual,
                        'before': before, 'materialized': pin(path)})
    return destination, {'base_dir': str(previous), 'output_dir': str(destination), 'files': records}


def local_include_closure(path: Path, source: Path, memo=None, active=frozenset()) -> set[Path]:
    """Conservative new-source closure supplements actual pre-overlay compiler deps."""
    memo = {} if memo is None else memo
    path = path.resolve()
    if path in memo:
        return memo[path]
    if path in active:
        return set()
    result = {path}
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    for name in re.findall(r'^\s*#\s*include\s*["<]([^">\n]+)[">]', text, re.MULTILINE):
        candidates = (path.parent / name, source / 'include' / name,
                      source / 'src' / name, source / 'research' / name)
        child = next((item for item in candidates if item.is_file()), None)
        if child is not None:
            result.update(local_include_closure(child, source, memo, active | {path}))
    memo[path] = result
    return result


def select_changed_objects(groups, source, effective_source, flags, overlay_names, actual_dependencies):
    changed, selections, memo = [], [], {}
    for target, rows in groups.items():
        for row in rows:
            relative = Path(row['file']).resolve().relative_to(source)
            row['file'] = str(effective_source / relative)
            dependencies = local_include_closure(Path(row['file']), effective_source, memo)
            original_deps = actual_dependencies.get(row['output'], set())
            old_names = {path.relative_to(source).as_posix() for path in original_deps if path.is_relative_to(source)}
            new_names = {path.relative_to(effective_source).as_posix() for path in dependencies}
            affected = sorted(overlay_names & (old_names | new_names))
            enabled = [flag for flag in flags if any(flag in path.read_text(encoding='utf-8-sig', errors='replace')
                                                     for path in dependencies)]
            if affected or enabled:
                changed.append((target, row))
                selections.append({'target': target, 'original_output': row['output'],
                    'source_overlay_dependencies': affected, 'new_flag_dependencies': enabled,
                    'actual_original_dependencies': [str(path) for path in sorted(original_deps)]})
    return changed, selections


def remap_source_arguments(argv, roots, effective_source):
    for root in roots:
        pattern = re.escape(root.as_posix()) + r'(?=/|$)'
        argv = [re.sub(pattern, lambda match: effective_source.as_posix(), value.replace('\\', '/'),
                       flags=re.IGNORECASE) for value in argv]
    return argv


def inherit_successor(config: dict, baseline: Path, source: Path, groups: dict, _seen=None) -> dict:
    """Borrow a linked predecessor's exact objects without changing its evidence.

    A fixture failure does not invalidate an independently successful archive and
    DLL link. Its original status is retained; this is never live qualification.
    """
    location = config.get("baseline_successor_report")
    if location is None:
        return {"flags": [], "objects": {}, "report": None}
    report_path = Path(location).resolve()
    seen = set() if _seen is None else _seen
    if report_path in seen:
        raise ValueError('Cyclic predecessor report chain')
    seen.add(report_path)
    prior = json.loads(report_path.read_text(encoding="utf-8"))
    if (prior.get("schema") != "ck3-native-flag-successor-v1"
            or Path(prior["baseline_build_dir"]).resolve() != baseline
            or Path(prior["source_dir"]).resolve() != source
            or prior.get("archive", {}).get("exit_code") != 0
            or prior.get("link", {}).get("exit_code") != 0):
        raise ValueError("Predecessor must use the same baseline/source and have a successful archive/DLL link")
    flags = prior.get("flags", [])
    if not flags or any(not re.fullmatch(r"[A-Z][A-Z0-9_]+", flag) for flag in flags):
        raise ValueError("Predecessor has no explicit Boolean native definitions")
    for key in ("baseline_dll", "baseline_archive"):
        expected = prior[key]
        if pin(Path(expected["path"])) != expected:
            raise ValueError("Predecessor baseline input changed: " + key)
    ancestor = prior.get('predecessor')
    if ancestor:
        actual = pin(Path(ancestor['path']))
        if any(actual[key] != ancestor.get(key) for key in ('bytes', 'sha256')):
            raise ValueError('Predecessor report chain pin changed')
    inherited = inherit_successor({'baseline_successor_report': ancestor['path']}, baseline, source, groups, seen) if ancestor else {'objects': {}}
    objects = dict(inherited['objects'])
    own = set()
    effective_source = Path(prior.get('effective_source_dir', source)).resolve()
    for record in prior.get("compiled", []):
        target, name = record["target"], record["original_output"]
        if target not in groups or record.get("exit_code") != 0:
            raise ValueError("Predecessor contains an unsuccessful/unknown production object")
        for key in ("source", "object"):
            expected = record[key]
            if pin(Path(expected["path"])) != expected:
                raise ValueError("Predecessor pinned input changed: " + key)
        if name in own:
            raise ValueError("Duplicate predecessor object: " + name)
        own.add(name)
        objects[name] = Path(record["object"]["path"])
        row = next((row for row in groups[target] if row["output"] == name), None)
        if row is None:
            original = source / Path(record['source']['path']).resolve().relative_to(effective_source)
            row = {"file": str(original), "output": name}
            groups[target].append(row)
        elif Path(row["file"]).resolve().relative_to(source) != Path(record["source"]["path"]).resolve().relative_to(effective_source):
            raise ValueError("Predecessor object/source identity crossed")
        row["inherited_argv"] = record["argv"]
        row['argv_source_root'] = str(effective_source)
    if not objects:
        raise ValueError("Predecessor has no reusable production objects")
    return {"flags": flags, "objects": objects, 'effective_source_dir': effective_source,
            "report": {**pin(report_path), "original_status": prior.get("status"),
                       "archive_exit_code": 0, "link_exit_code": 0}}


def run(config: dict) -> dict:
    baseline = Path(config["baseline_build_dir"]).resolve()
    source = Path(config["source_dir"]).resolve()
    output = Path(config["output_dir"]).resolve()
    if output == baseline or baseline in output.parents or output in baseline.parents:
        raise ValueError("Successor output must be separate from the frozen baseline")
    output.mkdir(parents=True, exist_ok=False)
    flags = tuple(config["enable_definitions"])
    if (not flags and not config.get('source_overlay')) or any(not re.fullmatch(r"[A-Z][A-Z0-9_]+", flag) for flag in flags):
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
    inherited = inherit_successor(config, baseline, source, groups)
    if set(flags).intersection(inherited["flags"]):
        raise ValueError("Requested flags are already enabled in the predecessor")
    all_flags = tuple(dict.fromkeys([*inherited["flags"], *flags]))
    effective_source, overlay = materialize_source_overlay(config, source, inherited)
    actual_dependencies, dependency_record = {}, None
    if overlay:
        query = subprocess.run([tools['ninja'], '-C', str(baseline), '-t', 'deps'],
                               check=True, capture_output=True, text=True, encoding='utf-8')
        path = output / 'baseline-ninja-dependencies.txt'
        path.write_text(query.stdout, encoding='utf-8')
        dependency_record = pin(path)
        actual_dependencies = parse_ninja_dependencies(query.stdout, baseline)
        baseline_outputs = {row['output'] for row in database}
        for rows in groups.values():
            for row in rows:
                if row['output'] in baseline_outputs and row['output'] not in actual_dependencies:
                    raise ValueError('Original compiler dependencies unavailable: ' + row['output'])
    overlay_names = {row['relative_path'] for row in overlay['files']} if overlay else set()
    previous_source = inherited.get('effective_source_dir', source)
    changed, selections = select_changed_objects(groups, source, effective_source, flags,
                                                  overlay_names, actual_dependencies)
    template = next(row for row in groups[runtime_target]
                    if Path(row["file"]).name == config["runtime_template_source"])
    for relative in config.get("additional_sources", []):
        path = (effective_source / relative).resolve()
        if not path.is_file() or effective_source not in path.parents:
            raise ValueError(f"Newly enabled source is unavailable: {relative}")
        if any(Path(row["file"]).resolve() == path for row in groups[runtime_target]):
            raise ValueError(f"Additional source was already present: {relative}")
        row = dict(template, file=str(path),
                   output=f"CMakeFiles/{runtime_target}.dir/{relative}.obj")
        row["template_file"] = template["file"]
        changed.append((runtime_target, row))
    report = {"schema": "ck3-native-flag-successor-v1", "baseline_build_dir": str(baseline),
              "source_dir": str(source), "output_dir": str(output), "flags": list(all_flags),
              'effective_source_dir': str(effective_source), 'source_overlay': overlay,
              'original_compiler_dependencies': dependency_record, 'dependency_selection': selections,
              "new_flags": list(flags), "predecessor": inherited["report"],
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
        argv = list(row["inherited_argv"]) if "inherited_argv" in row else windows_args(row["command"])
        if effective_source != source:
            argv = remap_source_arguments(argv, {source, previous_source, Path(row.get('argv_source_root', source))}, effective_source)
        # Both are MSVC equivalents; the exact-EXE provenance contract uses /c.
        argv = ["/c" if value == "-c" else value for value in argv]
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
        argv.extend("-D" + flag + "=1" for flag in all_flags
                    if not any(value in ("-D" + flag + "=1", "/D" + flag + "=1") for value in argv))
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
            objects[target] = [replaced.get(row["output"], inherited["objects"].get(
                row["output"], baseline / row["output"])) for row in rows]
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
            row = dict(template, file=str(effective_source / relative), template_file=template["file"],
                       output="fixtures/" + Path(relative).name + ".obj")
            record = compile_row(("fixture", row))
            executable = output / "fixtures" / (Path(relative).stem + ".exe")
            fixture_response = executable.with_suffix(".rsp")
            fixture_response.write_text(subprocess.list2cmdline([
                *(str(path) for path in objects[bridge_target] if config.get("fixture_whole_bridge") is True),
                *(str(replaced.get(path, inherited['objects'].get(path, baseline / path)))
                  for path in config.get("fixture_link_objects", [])),
                *map(str, libraries)]), encoding="utf-8")
            record["link"] = command([str(compiler_dir / "link.exe"), "/nologo", "/MACHINE:X64", "/OPT:REF",
                "/OUT:" + str(executable), record["object"]["path"],
                "@" + str(fixture_response)], Path(relative).stem + "-link")
            if opted_in(ROOT):
                exclusion_manifest = collect_command_manifest(
                    ROOT, effective_source, output, record["link"]["argv"], [executable],
                    config.get("defender_external_candidate"), source_commands=[
                        {"argv": record["argv"], "return_code": record["exit_code"]}])
                manifest_path = executable.with_suffix(".defender-manifest.json")
                manifest_path.write_text(json.dumps(exclusion_manifest, indent=2) + "\n", encoding="utf-8")
                receipt_path = executable.with_suffix(".defender-receipt.json")
                exclusions = register_manifest(exclusion_manifest, receipt_path,
                                               manifest_bytes=manifest_path.read_bytes())
                record["defender_exclusions"] = {"status": exclusions["status"], "receipt": pin(receipt_path)}
                if exclusions["status"] == "settings_failed":
                    raise RuntimeError("Fixture built; exact EXE Defender registration failed: " + str(receipt_path))
            else:
                record["defender_exclusions"] = {"status": "disabled", "reason": "Local Git opt-in absent/false or CI environment"}
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
