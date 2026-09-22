#!/usr/bin/env python3
"""Build the native bridge in a never-before-used Ninja directory."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import locale
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import uuid


CONFIGURATIONS = ("Debug", "Release", "RelWithDebInfo", "MinSizeRel")
DEPENDENCY_OBJECTS = (
    "CMakeFiles/xar_ck3_bridge.dir/src/ck3_11906.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/ck3_11906_adapter.cpp.obj",
)
EXPECTED_2052_PREFIX = base64.b64decode(
    "5rOo5oSPOiDljIXlkKvmlofku7Y6"
).decode("utf-8")


class FreshBuildError(RuntimeError):
    pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--ck3-executable-path", type=Path)
    parser.add_argument(
        "--configuration", choices=CONFIGURATIONS, default="Release"
    )
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument(
        "--build-jobs", type=int,
        help="Bound native compiler jobs when CK3 or another build owns resources",
    )
    parser.add_argument(
        "--feudal-1066-selected-bookmark-private",
        action="store_true",
        help="Build the private controlled selected-bookmark StartGame candidate",
    )
    parser.add_argument(
        "--feudal-1066-target-robert",
        action="store_true",
        help="Bind that private 1066 candidate to Robert's exact stock bookmark key",
    )
    parser.add_argument(
        "--focused-feudal-start", action="store_true",
        help="Build only bridge, injector, and exact adapter registry test",
    )
    parser.add_argument("--plan-only", action="store_true")
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def native_bridge_source_fingerprint(root: Path) -> str:
    root = root.resolve()
    paths = [root / "CMakeLists.txt"]
    for tree_name in ("include", "src"):
        tree = root / tree_name
        paths.extend(
            path
            for path in tree.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".cpp", ".hpp", ".h", ".c"}
        )
    lines = []
    root_text = str(root)
    for path in sorted(paths, key=lambda value: str(value.resolve()).lower()):
        relative = str(path.resolve())[len(root_text) :].lstrip("\\/")
        lines.append(f"{relative}\0{_sha256(path)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest().upper()


def _recover_2052_prefix(generated: str) -> str | None:
    encodings = [locale.getpreferredencoding(False), "mbcs", "cp936"]
    for encoding in dict.fromkeys(encodings):
        try:
            repaired = generated.encode(encoding).decode("utf-8")
        except (LookupError, UnicodeError):
            continue
        if (
            repaired.startswith(EXPECTED_2052_PREFIX)
            and not repaired[len(EXPECTED_2052_PREFIX) :].strip()
        ):
            return repaired
    return None


def repair_ninja_msvc_dependency_prefix(
    build_root: Path, compiler_path: Path
) -> str:
    compiler_directory = compiler_path.resolve().parent
    locale_ids = {
        child.name
        for child in compiler_directory.iterdir()
        if child.is_dir()
        and child.name.isdigit()
        and (child / "clui.dll").is_file()
    }
    if "1033" in locale_ids:
        return "vslang-1033"
    if "2052" not in locale_ids:
        return "cmake-detected"

    rules_path = build_root.resolve() / "CMakeFiles" / "rules.ninja"
    if not rules_path.is_file():
        raise FreshBuildError(
            f"Ninja rules file is missing after configure: {rules_path}"
        )
    rules = rules_path.read_text(encoding="utf-8")
    matches = list(
        re.finditer(r"(?m)^msvc_deps_prefix = (?P<value>[^\r\n]*)\r?$", rules)
    )
    if len(matches) != 1:
        raise FreshBuildError(
            f"expected exactly one msvc_deps_prefix in {rules_path}"
        )
    match = matches[0]
    generated = match.group("value")
    if (
        generated.startswith(EXPECTED_2052_PREFIX)
        and not generated[len(EXPECTED_2052_PREFIX) :].strip()
    ):
        return "direct-2052-utf8"
    repaired = _recover_2052_prefix(generated)
    if repaired is None:
        raise FreshBuildError(
            f"could not recover the 2052 MSVC /showIncludes prefix in {rules_path}"
        )
    if repaired != generated:
        start, end = match.span("value")
        rules_path.write_text(rules[:start] + repaired + rules[end:], encoding="utf-8")
    return "repaired-2052-utf8"


def _required_command(name: str) -> str:
    command = shutil.which(name)
    if command is None:
        raise FreshBuildError(
            f"{name} is required; run this helper from an x64 Visual Studio developer shell"
        )
    return command


def _run_checked(argv: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        argv,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
    )
    if result.returncode != 0:
        details = f"\n{result.stderr}" if capture and result.stderr else ""
        raise FreshBuildError(
            f"command failed with exit code {result.returncode}: {' '.join(argv)}{details}"
        )
    return result.stdout if capture else ""


def _resolve_build_dir(source_dir: Path, value: Path | None) -> Path:
    if value is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        value = source_dir / f"build-fresh-{stamp}-{uuid.uuid4().hex[:8]}"
    return value.resolve()


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.build_jobs is not None and args.build_jobs < 1:
        raise FreshBuildError("--build-jobs must be positive")
    if (
        args.focused_feudal_start
        and not args.feudal_1066_selected_bookmark_private
    ):
        raise FreshBuildError(
            "--focused-feudal-start requires the private candidate build"
        )
    if (
        args.feudal_1066_target_robert
        and not args.feudal_1066_selected_bookmark_private
    ):
        raise FreshBuildError(
            "--feudal-1066-target-robert requires the private candidate build"
        )
    source_dir = Path(__file__).resolve().parents[1]
    build_dir = _resolve_build_dir(source_dir, args.build_dir)
    ck3_executable = (
        args.ck3_executable_path.resolve()
        if args.ck3_executable_path is not None
        else None
    )
    if ck3_executable is not None and not ck3_executable.is_file():
        raise FreshBuildError(
            f"CK3 source-contract executable is missing: {ck3_executable}"
        )
    if build_dir.exists():
        raise FreshBuildError(
            f"fresh native bridge build directory already exists: {build_dir}"
        )

    plan: dict[str, object] = {
        "source_dir": str(source_dir),
        "build_dir": str(build_dir),
        "generator": "Ninja",
        "configuration": args.configuration,
        "msvc_output_language": "1033",
        "msvc_dependency_prefix_strategy": "vslang-1033-with-2052-utf8-repair",
        "fresh_directory_required": True,
        "source_fingerprint_required": True,
        "dependency_header": "ck3_11906.hpp",
        "dependency_objects": list(DEPENDENCY_OBJECTS),
        "tests_enabled": not args.skip_tests,
        "feudal_1066_selected_bookmark_private":
            args.feudal_1066_selected_bookmark_private,
        "feudal_1066_target_robert": args.feudal_1066_target_robert,
        "build_jobs": args.build_jobs,
        "focused_feudal_start": args.focused_feudal_start,
        "ck3_executable_path": (
            str(ck3_executable) if ck3_executable is not None else None
        ),
    }
    if args.plan_only:
        return plan

    cmake = _required_command("cmake")
    ninja = _required_command("ninja")
    compiler = Path(_required_command("cl"))
    ctest = _required_command("ctest")
    fingerprint_before = native_bridge_source_fingerprint(source_dir)
    build_dir.mkdir(parents=False, exist_ok=False)

    prior_vslang = os.environ.get("VSLANG")
    try:
        os.environ["VSLANG"] = "1033"
        configure = [
            cmake,
            "-S",
            str(source_dir),
            "-B",
            str(build_dir),
            "-G",
            "Ninja",
            f"-DCMAKE_BUILD_TYPE={args.configuration}",
        ]
        if ck3_executable is not None:
            configure.append(f"-DXAR_CK3_EXECUTABLE_PATH={ck3_executable}")
        if args.feudal_1066_selected_bookmark_private:
            configure.append(
                "-DXAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1=ON"
            )
            configure.append(
                "-DXAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1=ON"
            )
        if args.feudal_1066_target_robert:
            configure.append("-DXAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1=ON")
        _run_checked(configure)
        prefix_mode = repair_ninja_msvc_dependency_prefix(build_dir, compiler)
        build = [cmake, "--build", str(build_dir), "--parallel"]
        if args.build_jobs is not None:
            build.append(str(args.build_jobs))
        if args.focused_feudal_start:
            build.extend([
                "--target",
                "xar_ck3_bridge",
                "xar_ck3_bridge_injector",
                "xar_ck3_adapter_registry_test",
                "xar_ck3_frontend_bookmark_model_probe_v1_test",
            ])
        _run_checked(build)
        for dependency_object in DEPENDENCY_OBJECTS:
            dependency_text = _run_checked(
                [ninja, "-C", str(build_dir), "-t", "deps", dependency_object],
                capture=True,
            )
            if not re.search(r"#deps\s+[1-9][0-9]*", dependency_text) or not re.search(
                r"ck3_11906\.hpp", dependency_text
            ):
                raise FreshBuildError(
                    "Ninja did not record ck3_11906.hpp for "
                    f"{dependency_object}; refusing this native bridge build"
                )
        if not args.skip_tests:
            test = [ctest, "--test-dir", str(build_dir),
                    "--output-on-failure"]
            if args.focused_feudal_start:
                test.extend([
                    "-R", "^xar_ck3_native_bridge_(adapter_registry|frontend_bookmark_model_probe_v1)$"
                ])
            _run_checked(test)
    finally:
        if prior_vslang is None:
            os.environ.pop("VSLANG", None)
        else:
            os.environ["VSLANG"] = prior_vslang

    fingerprint_after = native_bridge_source_fingerprint(source_dir)
    if fingerprint_after != fingerprint_before:
        raise FreshBuildError(
            "native bridge sources changed during the fresh build; refusing its artifacts"
        )
    dll = build_dir / "xar_ck3_bridge.dll"
    injector = build_dir / "xar_ck3_bridge_injector.exe"
    for artifact in (dll, injector):
        if not artifact.is_file():
            raise FreshBuildError(f"fresh native bridge artifact is missing: {artifact}")
    return {
        "status": "ready",
        "build_dir": str(build_dir),
        "source_fingerprint_sha256": fingerprint_after,
        "dll_path": str(dll),
        "dll_sha256": _sha256(dll),
        "injector_path": str(injector),
        "injector_sha256": _sha256(injector),
        "tests_ran": not args.skip_tests,
        "test_scope": (
            "feudal-start-adapter-and-bookmark-model"
            if args.focused_feudal_start
            else "all-native-offline"
        ),
        "dependency_gate": "ck3_11906.hpp-recorded",
        "msvc_dependency_prefix_mode": prefix_mode,
    }


def main() -> int:
    try:
        result = run(_parser().parse_args())
    except (FreshBuildError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
