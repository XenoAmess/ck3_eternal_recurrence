"""Retire completed native CI compilation intermediates before Java storage admission."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

from check_native_army_routes_ci import INPUTS as ARMY_INPUTS, TRANSLATION_UNITS as ARMY_UNITS

ARMY_BUILD_NAME = "native-army-route-ci"

BUILD_NAMES = (
    "native-florin-core-ci",
    "native-rite-creation-ci",
    "native-army-route-ci",
    "native-decision-completion-ci",
)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def linked(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()

def cache_path(raw: str, key: str) -> Path:
    rows = [line[len(key) + 1:] for line in raw.splitlines() if line.startswith(key + "=")]
    require(len(rows) == 1 and bool(rows[0]), "unique actual CMake cache path required: " + key)
    return Path(rows[0]).resolve(strict=True)

def stable_digest(path: Path) -> tuple[str, os.stat_result]:
    require(path.is_file() and not linked(path), "direct completed native evidence required: " + str(path))
    before = path.stat(follow_symlinks=False)
    require(stat.S_ISREG(before.st_mode) and before.st_size <= 64 * 1024 * 1024,
            "bounded regular completed native evidence required")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat(follow_symlinks=False)
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            "completed native evidence changed while reading")
    return digest.hexdigest(), after

def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, "duplicate army completion report field")
        result[key] = value
    return result

def command_army_objects(build: Path, native: Path) -> tuple[list[tuple[Path, Path, os.stat_result]], list[tuple[Path, str]]]:
    """The army producer uses cl directly, never CMake or CMakeFiles."""
    report_path = build / "army-reader-ci-result.json"
    digest, _ = stable_digest(report_path)
    require(report_path.stat().st_size <= 1024 * 1024, "bounded army completion report required")
    report = json.loads(report_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require(stable_digest(report_path)[0] == digest, "army completion report changed")
    require(type(report) is dict and report.get("schema") == "xar.native.army-reader-ci.v1"
            and report.get("status") == "passed" and report.get("build_status") == "build_succeeded"
            and report.get("build_dir") == str(build) and report.get("local_ck3_contacted") is False
            and report.get("private_feature_definitions") == [], "actual completed army command role required")
    inputs = report.get("inputs")
    require(type(inputs) is dict and set(inputs) == set(ARMY_INPUTS), "exact army source input inventory required")
    witnesses = [(report_path, digest)]
    for relative in ARMY_INPUTS:
        source = native / relative
        require(source.resolve(strict=True).is_relative_to(native), "army source path escape rejected")
        actual, _ = stable_digest(source)
        require(inputs[relative] == actual, "completed army source differs: " + relative)
        witnesses.append((source, actual))
    steps = report.get("steps")
    require(type(steps) is list and len(steps) == 3 and all(type(step) is dict for step in steps)
            and [step.get("name") for step in steps] == ["msvc-environment", "compile", "army-fixtures"]
            and all(type(step.get("exit_code")) is int and step["exit_code"] == 0 for step in steps),
            "completed army environment, compile and fixture exits required")
    executable = build / "xar_ck3_12002_army_test.exe"
    executable_digest, _ = stable_digest(executable)
    require(report.get("executable_sha256") == executable_digest, "completed army executable differs")
    witnesses.append((executable, executable_digest))
    compiler = steps[1].get("argv")
    require(type(compiler) is list and compiler and type(compiler[0]) is str
            and Path(compiler[0]).is_absolute() and Path(compiler[0]).name.lower() == "cl.exe",
            "actual absolute army compiler required")
    expected_tail = ["/nologo", "/std:c++20", "/O2", "/MD", "/W4", "/permissive-", "/EHsc", "/utf-8",
                     "/UNDEBUG", "/DNOMINMAX", f"/I{native / 'include'}",
                     *(str(native / name) for name in ARMY_UNITS), f"/Fe{executable}"]
    require(compiler[1:] == expected_tail and steps[2].get("argv") == [str(executable)],
            "exact completed army compiler and fixture command required")
    for step in steps[1:]:
        for stream in ("stdout", "stderr"):
            log = build / (step["name"] + "." + stream + ".bin")
            require(step.get(stream) == str(log), "actual army command log path differs")
            log_digest, _ = stable_digest(log)
            witnesses.append((log, log_digest))
    expected_objects = {Path(relative).stem + ".obj" for relative in ARMY_UNITS}
    require(len(expected_objects) == len(ARMY_UNITS), "unique direct army object names required")
    objects = []
    entries = list(build.iterdir())
    require(len(entries) <= 100000, "bounded army command root required")
    for path in entries:
        require(not linked(path), "army command root link rejected")
        if path.suffix.lower() not in (".obj", ".pdb"):
            continue
        # The exact /O2 command has neither /Zi nor a requested PDB output.
        # Do not treat an unexpected root PDB/object as this completed producer's output.
        require(path.name in expected_objects and path.resolve(strict=True).parent == build,
                "unexpected army command intermediate rejected: " + path.name)
        observed = path.stat(follow_symlinks=False)
        require(stat.S_ISREG(observed.st_mode), "regular army object required")
        objects.append((path, build, observed))
    require({path.name for path, _, _ in objects} == expected_objects,
            "complete original army object inventory required")
    return objects, witnesses

def retire(repo_root: Path, runner_temp: Path) -> dict[str, object]:
    repo = repo_root.resolve(strict=True)
    runner = runner_temp.resolve(strict=True)
    require(repo.is_dir() and runner.is_dir(), "existing repository and runner temp required")
    native = (repo / "ck3_autonomous_player" / "native_bridge").resolve(strict=True)
    require(native.is_dir(), "actual repository native source required")
    candidates: list[tuple[Path, Path, os.stat_result]] = []
    command_witnesses: list[tuple[Path, str]] = []
    total_entries = 0
    # Validate the entire closed role set before removing the first intermediate.
    for name in BUILD_NAMES:
        build = runner / name
        require(build.is_dir() and not linked(build) and build.resolve(strict=True) == build,
                "direct owned native build root required: " + name)
        if name == ARMY_BUILD_NAME:
            command_objects, witnesses = command_army_objects(build, native)
            candidates.extend(command_objects)
            command_witnesses.extend(witnesses)
            total_entries += len(command_objects)
            require(total_entries <= 100000, "bounded native intermediate inventory required")
            continue
        cache = build / "CMakeCache.txt"
        require(cache.is_file() and not linked(cache), "original CMake cache required: " + name)
        raw = cache.read_text(encoding="utf-8")
        require(cache_path(raw, "CMAKE_HOME_DIRECTORY:INTERNAL") == native,
                "foreign native CMake source rejected: " + name)
        require(cache_path(raw, "CMAKE_CACHEFILE_DIR:INTERNAL") == build,
                "foreign native CMake binary root rejected: " + name)
        objects = build / "CMakeFiles"
        require(objects.is_dir() and not linked(objects) and objects.resolve(strict=True) == objects,
                "direct owned CMakeFiles root required: " + name)
        for directory, dirs, files in os.walk(objects, followlinks=False):
            parent = Path(directory)
            require(not linked(parent) and parent.resolve(strict=True).is_relative_to(objects),
                    "native intermediate path escape rejected")
            for leaf in dirs:
                require(not linked(parent / leaf), "native intermediate directory link rejected")
            total_entries += len(dirs) + len(files) + 1
            require(total_entries <= 100000, "bounded native intermediate inventory required")
            for leaf in files:
                path = parent / leaf
                if path.suffix.lower() not in (".obj", ".pdb"):
                    continue
                require(not linked(path) and path.resolve(strict=True).is_relative_to(objects),
                        "native intermediate file link rejected")
                observed = path.stat(follow_symlinks=False)
                require(stat.S_ISREG(observed.st_mode), "regular native intermediate required")
                candidates.append((path, objects, observed))
    removed_bytes = 0
    # Every role, including the command-only producer, must remain completed
    # before removing the first object. No missing-cache skip or synthetic cache.
    for path, expected_digest in command_witnesses:
        require(stable_digest(path)[0] == expected_digest, "completed army evidence changed before retirement")
    for path, objects, before in candidates:
        require(not linked(path) and path.resolve(strict=True).is_relative_to(objects),
                "native intermediate changed path before retirement")
        after = path.stat(follow_symlinks=False)
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                "native intermediate changed before retirement")
        path.unlink()
        removed_bytes += before.st_size
    return {
        "schema": "xar.static-ci.completed-native-intermediates/v1",
        "build_roots": [str(runner / name) for name in BUILD_NAMES],
        "removed_files": len(candidates),
        "removed_logical_bytes": removed_bytes,
        "removed_bootstrap_inventory_charge_bytes": removed_bytes + 65536 * len(candidates),
        "retained": "wire, executables, CTest logs, CMake metadata, repository, venv and all other files",
        "quota_or_admission_changed": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--runner-temp", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(retire(args.repo_root, args.runner_temp), sort_keys=True))

if __name__ == "__main__":
    main()
