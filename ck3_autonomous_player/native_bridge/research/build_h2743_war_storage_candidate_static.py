"""Build and CTest a new H2743 read-only WarManager candidate without CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


BRIDGE = Path(__file__).resolve().parents[1]
VSWHERE = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
TEST_NAME = "xar_ck3_h2743_war_storage_candidate_v1"


def _run(build: Path, name: str, argv: list[str], env: dict[str, str]) -> None:
    result = subprocess.run(argv, env=env, capture_output=True, text=True,
                            errors="replace")
    (build / f"{name}-argv.json").write_text(json.dumps(argv, indent=2), encoding="utf-8")
    (build / f"{name}-stdout.txt").write_text(result.stdout, encoding="utf-8")
    (build / f"{name}-stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{name} failed ({result.returncode}); preserved logs in {build}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    args = parser.parse_args()
    build = args.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=False)
    installation = Path(subprocess.run(
        [str(VSWHERE), "-latest", "-products", "*", "-requires",
         "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property",
         "installationPath"], check=True, capture_output=True, text=True,
    ).stdout.strip())
    vcvars = installation / "VC/Auxiliary/Build/vcvars64.bat"
    cmake = installation / "Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
    ninja = installation / "Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe"
    if not all(path.is_file() for path in (vcvars, cmake, ninja)):
        raise RuntimeError("MSVC, CMake or Ninja unavailable")
    environment_script = build / "capture-msvc-environment.cmd"
    environment_script.write_text(f'@call "{vcvars}" >nul\n@set\n', encoding="utf-8")
    captured = subprocess.run(["cmd.exe", "/d", "/c", str(environment_script)],
                              check=True, capture_output=True, text=True,
                              errors="replace")
    env = os.environ.copy()
    for line in captured.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            env[key.upper()] = value
    _run(build, "configure", [str(cmake), "-S", str(BRIDGE), "-B", str(build),
                             "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                             f"-DCMAKE_MAKE_PROGRAM={ninja}"], env)
    _run(build, "build", [str(cmake), "--build", str(build), "--target",
                         "xar_ck3_bridge", f"{TEST_NAME}_test", "--parallel", "2"], env)
    _run(build, "ctest", [str(cmake.parent / "ctest.exe"), "--test-dir", str(build),
                         "-R", f"^{TEST_NAME}$", "--output-on-failure"], env)
    dll = build / "xar_ck3_bridge.dll"
    receipt = {"status": "static_build_and_ctest_green", "dll_path": str(dll),
               "dll_sha256": hashlib.sha256(dll.read_bytes()).hexdigest().upper(),
               "ctest": TEST_NAME, "ck3_launched": False}
    (build / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                        encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
