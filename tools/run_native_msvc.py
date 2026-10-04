#!/usr/bin/env python3
"""Configure or incrementally build native targets with the installed x64 MSVC tools.

The wrapper initializes vcvars64 in a child cmd process and keeps compiler
temporary files, logs and Python caches below the requested build directory.
It does not start CK3 or prepare a game profile.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from register_project_exe_exclusions import (
    after_successful_build, has_codemodel_reply, opted_in, request_codemodel, validate_source,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "ck3_autonomous_player/native_bridge"
DEFAULT_VS = Path(r"C:\Program Files\Microsoft Visual Studio\18\Community")
CONFIGURATIONS = ("Debug", "Release", "RelWithDebInfo", "MinSizeRel")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    result.add_argument("--build-dir", type=Path, required=True)
    result.add_argument("--vs-install", type=Path)
    result.add_argument("--configuration", choices=CONFIGURATIONS, default="Release")
    result.add_argument("--jobs", type=int, default=64)
    result.add_argument("--target", action="extend", nargs="+")
    result.add_argument("--defender-external-candidate", help="Explicit caller label for this external project candidate source")
    result.add_argument("--cmake-define", action="append", default=[], metavar="NAME=VALUE")
    result.add_argument("--configure", action="store_true", help="Run CMake configure")
    result.add_argument("--build", action="store_true", help="Run the selected build targets")
    result.add_argument("--probe", action="store_true", help="Report tool versions without configuring or building")
    return result


def child_environment(build_dir: Path) -> dict[str, str]:
    environment = {key.upper(): value for key, value in os.environ.items()}
    temporary = build_dir / ".msvc-temp"
    temporary.mkdir(parents=True, exist_ok=True)
    environment.update({
        "TEMP": str(temporary),
        "TMP": str(temporary),
        "PYTHONPYCACHEPREFIX": str(build_dir / ".python-cache"),
        "XDG_CACHE_HOME": str(build_dir / ".cache"),
        "CCACHE_DIR": str(build_dir / ".cache/ccache"),
        "SCCACHE_DIR": str(build_dir / ".cache/sccache"),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "VSLANG": "1033",
    })
    return environment


def visual_studio_installation(requested: Path | None, environment: dict[str, str]) -> Path:
    if requested is not None:
        installation = requested.resolve()
    elif (DEFAULT_VS / "VC/Auxiliary/Build/vcvars64.bat").is_file():
        installation = DEFAULT_VS
    else:
        vswhere = Path(environment.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / (
            "Microsoft Visual Studio/Installer/vswhere.exe"
        )
        query = subprocess.run(
            [str(vswhere), "-latest", "-products", "*", "-requires",
             "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=environment, check=True,
        )
        if not query.stdout.strip():
            raise RuntimeError("vswhere did not find an x64 MSVC installation")
        installation = Path(query.stdout.strip())
    if not (installation / "VC/Auxiliary/Build/vcvars64.bat").is_file():
        raise RuntimeError(f"vcvars64.bat is missing in {installation}")
    return installation


def initialize_msvc(
    installation: Path, build_dir: Path, environment: dict[str, str]
) -> tuple[dict[str, str], dict[str, str]]:
    vcvars = installation / "VC/Auxiliary/Build/vcvars64.bat"
    capture_script = build_dir / ".msvc-temp/capture-environment.cmd"
    capture_script.write_text(
        f'@echo off\ncall "{vcvars}" >nul\nif errorlevel 1 exit /b %errorlevel%\nset\n',
        encoding="utf-8", newline="\r\n",
    )
    captured = subprocess.run(
        [environment.get("COMSPEC", "cmd.exe"), "/d", "/u", "/c", str(capture_script)],
        cwd=build_dir, env=environment, capture_output=True, check=True,
    )
    result = environment.copy()
    for line in captured.stdout.decode("utf-16-le", errors="replace").splitlines():
        if "=" in line and not line.startswith("="):
            key, value = line.split("=", 1)
            result[key.upper()] = value
    # Retain the explicit output locations even if an installed vcvars script
    # changes a temporary variable while discovering the Windows SDK.
    for key in ("TEMP", "TMP", "PYTHONPYCACHEPREFIX", "XDG_CACHE_HOME", "CCACHE_DIR",
                "SCCACHE_DIR", "PYTHONUTF8", "PYTHONIOENCODING", "VSLANG"):
        result[key] = environment[key]
    cmake_root = installation / "Common7/IDE/CommonExtensions/Microsoft/CMake"
    cmake = cmake_root / "CMake/bin/cmake.exe"
    ninja = cmake_root / "Ninja/ninja.exe"
    for tool in (cmake, ninja):
        if not tool.is_file():
            raise RuntimeError(f"Visual Studio build tool is missing: {tool}")
    compiler = shutil.which("cl.exe", path=result.get("PATH"))
    if compiler is None:
        raise RuntimeError("vcvars64 did not publish cl.exe")
    compiler_path = Path(compiler)
    result["PATH"] = os.pathsep.join(
        [str(compiler_path.parent), str(cmake.parent), str(ninja.parent), result.get("PATH", "")]
    )
    return result, {"vcvars64": str(vcvars), "cmake": str(cmake), "ninja": str(ninja), "cl": compiler}


def configure_command(args: argparse.Namespace, tools: dict[str, str]) -> list[str]:
    command = [tools["cmake"], "-S", str(args.source_dir), "-B", str(args.build_dir),
               "-G", "Ninja", f"-DCMAKE_BUILD_TYPE={args.configuration}",
               f"-DCMAKE_MAKE_PROGRAM={tools['ninja']}", f"-DCMAKE_CXX_COMPILER={tools['cl']}",
               f"-DCMAKE_C_COMPILER={tools['cl']}"]
    command.extend(f"-D{value}" for value in args.cmake_define)
    return command


def build_command(args: argparse.Namespace, tools: dict[str, str]) -> list[str]:
    targets = args.target or ["xar_ck3_bridge", "xar_ck3_bridge_injector"]
    return [tools["cmake"], "--build", str(args.build_dir), "--parallel", str(args.jobs),
            "--target", *targets]


def run_logged(command: list[str], log: Path, environment: dict[str, str], cwd: Path) -> None:
    print(json.dumps({"command": command, "log": str(log)}, ensure_ascii=False), flush=True)
    with log.open("wb") as output:
        process = subprocess.Popen(command, cwd=cwd, env=environment,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process.stdout is None:
            raise RuntimeError("build output pipe was not created")
        for line in process.stdout:
            output.write(line)
            output.flush()
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        returncode = process.wait()
    if returncode:
        raise subprocess.CalledProcessError(returncode, command)


def repair_dependency_prefix(build_dir: Path, compiler: str) -> str:
    # Reuse the project's byte-preserving fix for a Chinese-only cl.exe.
    helper = DEFAULT_SOURCE / "tools/build_fresh.py"
    spec = importlib.util.spec_from_file_location("xar_native_build_fresh", helper)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import existing dependency-prefix helper: {helper}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.repair_ninja_msvc_dependency_prefix(build_dir, Path(compiler))


def probe_tools(tools: dict[str, str], environment: dict[str, str], build_dir: Path) -> dict:
    versions = {}
    for name, arguments in (("cl", ["/Bv"]), ("cmake", ["--version"]), ("ninja", ["--version"])):
        result = subprocess.run([tools[name], *arguments], cwd=build_dir, env=environment,
                                capture_output=True, check=False)
        log = build_dir / f"msvc-probe-{name}.log"
        log.write_bytes(result.stdout + result.stderr)
        # cl /Bv without an input prints its version and D8003, then exits 2.
        if result.returncode not in ({0, 2} if name == "cl" else {0}):
            raise subprocess.CalledProcessError(result.returncode, [tools[name], *arguments])
        versions[name] = {"returncode": result.returncode, "log": str(log),
                          "version_lines": (result.stdout + result.stderr).decode(
                              "mbcs" if os.name == "nt" else "utf-8", errors="replace"
                          ).splitlines()[:3]}
    return versions


def run(args: argparse.Namespace) -> dict:
    if args.jobs < 1:
        raise ValueError("--jobs must be positive")
    args.source_dir = args.source_dir.resolve()
    args.build_dir = args.build_dir.resolve()
    defender_enabled = opted_in(ROOT)
    external_candidate = getattr(args, "defender_external_candidate", None)
    if defender_enabled and not args.probe:
        validate_source(ROOT, args.source_dir, external_candidate)
    if not args.probe and not (args.source_dir / "CMakeLists.txt").is_file():
        raise RuntimeError(f"CMakeLists.txt is missing: {args.source_dir}")
    args.build_dir.mkdir(parents=True, exist_ok=True)
    sys.pycache_prefix = str(args.build_dir / ".python-cache")
    environment = child_environment(args.build_dir)
    installation = visual_studio_installation(args.vs_install, environment)
    environment, tools = initialize_msvc(installation, args.build_dir, environment)
    report = {"schema": "xar.native.msvc-build.v1", "source_dir": str(args.source_dir),
              "build_dir": str(args.build_dir), "configuration": args.configuration,
              "jobs": args.jobs, "targets": args.target or ["xar_ck3_bridge", "xar_ck3_bridge_injector"],
              "tools": tools, "local_ck3_contacted": False,
              "temporary_dir": environment["TEMP"], "python_cache": environment["PYTHONPYCACHEPREFIX"]}
    report_path = args.build_dir / "native-msvc-result.json"
    try:
        if args.probe:
            report["versions"] = probe_tools(tools, environment, args.build_dir)
            report["status"] = "probe_ready"
        else:
            configure = args.configure or not args.build
            build = args.build or not args.configure
            if defender_enabled:
                request_codemodel(args.build_dir)
                # The existing build-only tree may predate this small query.
                # A normal configure creates typed target artifact provenance.
                if build and not configure and not has_codemodel_reply(args.build_dir):
                    configure = True
            report["configured"] = configure
            report["built"] = build
            if configure:
                run_logged(configure_command(args, tools), args.build_dir / "msvc-configure.log", environment, args.build_dir)
                report["dependency_prefix_mode"] = repair_dependency_prefix(args.build_dir, tools["cl"])
            if build:
                run_logged(build_command(args, tools), args.build_dir / "msvc-build.log", environment, args.build_dir)
            report["status"] = "built" if build else "configured"
            if build:
                report["build_succeeded"] = True
                report["defender_exclusions"] = after_successful_build(
                    ROOT, args.source_dir, args.build_dir, args.configuration,
                    report["targets"], external_candidate)
                if report["defender_exclusions"]["status"] == "settings_failed":
                    report["status"] = "built_defender_registration_failed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        report = run(parser().parse_args())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "built_defender_registration_failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
