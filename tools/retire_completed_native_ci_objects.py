"""Retire completed native CI compilation intermediates before Java storage admission."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import stat

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

def retire(repo_root: Path, runner_temp: Path) -> dict[str, object]:
    repo = repo_root.resolve(strict=True)
    runner = runner_temp.resolve(strict=True)
    require(repo.is_dir() and runner.is_dir(), "existing repository and runner temp required")
    native = (repo / "ck3_autonomous_player" / "native_bridge").resolve(strict=True)
    require(native.is_dir(), "actual repository native source required")
    candidates: list[tuple[Path, Path, os.stat_result]] = []
    total_entries = 0
    # Validate the entire closed role set before removing the first intermediate.
    for name in BUILD_NAMES:
        build = runner / name
        require(build.is_dir() and not linked(build) and build.resolve(strict=True) == build,
                "direct owned native build root required: " + name)
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
