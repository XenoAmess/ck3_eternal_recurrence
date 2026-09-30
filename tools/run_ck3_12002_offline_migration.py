#!/usr/bin/env python3
"""Build and test the CK3 1.20.0.2 migration without starting any game process."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "ck3_autonomous_player" / "native_bridge"
ARTIFACT = ROOT / "artifacts/migrations/2026-09-30/post-update-1.20.0.2"
SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def native_tools() -> tuple[Path, Path, Path, Path]:
    installer = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer"
    result = subprocess.run(
        [str(installer / "vswhere.exe"), "-latest", "-products", "*", "-property", "installationPath"],
        capture_output=True, text=True, check=True,
    )
    installation = Path(result.stdout.strip())
    extensions = installation / "Common7/IDE/CommonExtensions/Microsoft/CMake"
    return (installation / "Common7/Tools/VsDevCmd.bat",
            extensions / "CMake/bin/cmake.exe",
            extensions / "CMake/bin/ctest.exe",
            extensions / "Ninja/ninja.exe")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ARTIFACT / "installation/binaries/ck3.exe")
    parser.add_argument("--legacy-exe", type=Path, default=Path(
        r"Z:\Crusader Kings III\Crusader Kings III_1.19.0.6_20260604\binaries\ck3.exe"),
        help="disk-only old EXE used by the existing mailbox regression fixture")
    parser.add_argument("--build-dir", type=Path, default=ARTIFACT / "build-migration-msvc")
    parser.add_argument("--output", type=Path, default=ARTIFACT / "offline-migration-result.json")
    parser.add_argument("--source-data-root", type=Path, default=ROOT,
                        help="root holding the frozen script paths used by the phase AST")
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--clean-first", action="store_true",
                        help="rebuild objects after the observed old MSVC dependency-prefix failure")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    executable_hash = hashlib.file_digest(args.exe.open("rb"), "sha256").hexdigest().upper()
    if executable_hash != SHA256:
        parser.error("the supplied disk EXE is not the frozen CK3 1.20.0.2 build")
    args.build_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    log_dir = args.output.parent / (args.output.stem + "-logs")
    log_dir.mkdir(exist_ok=True)
    devcmd, cmake, ctest, ninja = native_tools()
    result: dict[str, object] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "executable_sha256": executable_hash,
        "game_version": "1.20.0.2",
        "live": False,
        "build_dir": str(args.build_dir.resolve()),
        "source_root": str(ROOT),
        "source_data_root": str(args.source_data_root.resolve()),
        "legacy_executable": str(args.legacy_exe.resolve()),
        "steps": [],
    }

    def record(name: str, command: list[str], *, msvc: bool = False) -> str:
        log = log_dir / f"{name}.log"
        if msvc:
            installer = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer"
            script = (f'set "PATH={installer};%PATH%" && call "{devcmd}" '
                      '-arch=x64 -host_arch=x64 >nul && '
                      + subprocess.list2cmdline(command))
            # Pass CMD's command language directly; Python's list2cmdline on
            # the whole /c argument escapes nested quotes as literal \".
            command = f'"{os.environ.get("COMSPEC", "cmd.exe")}" /d /s /c "{script}"'
        print(f"{name}: running", flush=True)
        with log.open("wb") as stream:
            environment = os.environ.copy()
            environment["XAR_CK3_12002_FROZEN_SOURCE_ROOT"] = str(args.source_data_root.resolve())
            completed = subprocess.run(command, cwd=ROOT, env=environment,
                                       stdout=stream, stderr=subprocess.STDOUT)
        result["steps"].append({"name": name, "returncode": completed.returncode, "log": str(log)})
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if completed.returncode:
            print(f"{name}: RED (see {log})", flush=True)
            raise subprocess.CalledProcessError(completed.returncode, command)
        print(f"{name}: GREEN", flush=True)
        return log.read_text(encoding="utf-8", errors="replace")

    try:
        # These checked-in scripts inspect the supplied disk image, never a PID.
        research = NATIVE / "research"
        aggregate = research / "verify_ck3_12002_migration.py"
        verifiers = ([aggregate] if aggregate.is_file() else
                     sorted(set(research.glob("verify_ck3_12002*.py")) |
                            set(research.glob("ck3_1_20_0_2_*_verify.py"))))
        for verifier in verifiers:
            command = [sys.executable, str(verifier), "--exe", str(args.exe.resolve())]
            if verifier == aggregate:
                abi_output = args.output.with_name(args.output.stem + "-abi.json")
                command += ["--output", str(abi_output)]
                result["abi_result"] = str(abi_output)
            record(verifier.stem, command)
        phase_builder = research / "build_ck3_12002_phase_ast.py"
        if phase_builder.is_file():
            record("phase-ast-reproducibility", [sys.executable, str(phase_builder), "--check"])
            record("phase-ast-tests", [sys.executable, str(research / "test_ck3_12002_phase_ast.py")])
        record("configure", [str(cmake), "-S", str(NATIVE), "-B", str(args.build_dir),
                             "-G", "Ninja", "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                             "-DBUILD_TESTING=ON", "-DCMAKE_CXX_COMPILER=cl",
                             f"-DXAR_CK3_12002_FROZEN_EXE={args.exe.resolve()}",
                             f"-DXAR_CK3_11906_REFERENCE_EXE={args.legacy_exe.resolve()}",
                             f"-DCMAKE_MAKE_PROGRAM={ninja}"], msvc=True)
        help_text = record("targets", [str(cmake), "--build", str(args.build_dir), "--target", "help"], msvc=True)
        targets = sorted(set(re.findall(r"^(xar_ck3_12002_[A-Za-z0-9_]+):", help_text, re.MULTILINE)))
        targets += ["xar_ck3_bridge", "xar_ck3_bridge_host", "xar_ck3_bridge_attach_host",
                    "xar_ck3_bridge_injector", "xar_ck3_adapter_registry_test",
                    "xar_ck3_main_thread_query_mailbox_v1_test"]
        result["targets"] = targets
        build_command = [str(cmake), "--build", str(args.build_dir), "--target", *targets,
                         "-j", str(args.jobs)]
        if args.clean_first:
            build_command.append("--clean-first")
        record("build", build_command, msvc=True)
        # No suspended-injection, running-attach, host or gameplay acceptance tests.
        test_pattern = (r"^(xar_ck3_12002_.*|xar_ck3_native_bridge_adapter_registry|"
                        r"xar_ck3_native_bridge_main_thread_query_mailbox_v1)$")
        record("ctest", [str(ctest), "--test-dir", str(args.build_dir), "-R", test_pattern,
                         "--output-on-failure"])
        result["status"] = "GREEN"
    except subprocess.CalledProcessError:
        result["status"] = "RED"
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{result['status']}: {args.output}", flush=True)
    return 0 if result["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
