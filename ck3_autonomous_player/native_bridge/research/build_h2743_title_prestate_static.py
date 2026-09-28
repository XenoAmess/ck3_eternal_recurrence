"""Build the H2743 title-holder prestate candidate in a fresh workdir.

This is a static compiler check. It never starts CK3 or attaches to a process.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


BRIDGE = Path(__file__).resolve().parents[1]
VSWHERE = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    args = parser.parse_args()
    build = args.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=False)
    if not VSWHERE.is_file():
        raise RuntimeError("Visual Studio locator unavailable")
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
    captured = subprocess.run(
        ["cmd.exe", "/d", "/c", str(environment_script)],
        check=True, capture_output=True, text=True, errors="replace",
    )
    import os
    environment = os.environ.copy()
    for line in captured.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            environment[key.upper()] = value
    configure = [str(cmake), "-S", str(BRIDGE), "-B", str(build),
                 "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
                 f"-DCMAKE_MAKE_PROGRAM={ninja}"]
    compile_ = [str(cmake), "--build", str(build), "--target", "xar_ck3_bridge",
                "--parallel", "2"]
    for name, argv in (("configure", configure), ("build", compile_)):
        result = subprocess.run(argv, env=environment, capture_output=True,
                                text=True, errors="replace")
        (build / f"{name}-stdout.txt").write_text(result.stdout, encoding="utf-8")
        (build / f"{name}-stderr.txt").write_text(result.stderr, encoding="utf-8")
        (build / f"{name}-argv.json").write_text(json.dumps(argv, indent=2), encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{name} failed ({result.returncode}); see preserved logs")
    print(build / "xar_ck3_bridge.dll")


if __name__ == "__main__":
    main()
