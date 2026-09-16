"""Focused M4 exact source and private action glue in /Od and /O2.

Only the five affected bridge objects are compiled with the private action
option ON; this is a static/no-launch gate, not live construction evidence.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import tempfile

from run_domain_construction_application_main_runtime_v1_tests import (
    _visual_studio_environment,
)


HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
OBJECTS = [
    "CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/player_construction_view_probe_v1_mailbox.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/player_world_building_definition_source_v1.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/player_world_building_action_candidate_v1.cpp.obj",
    "CMakeFiles/xar_ck3_bridge.dir/src/domain_construction_application_main_runtime_v1.cpp.obj",
]


def _run(command: list[str], environment: dict[str, str]) -> None:
    result = subprocess.run(command, cwd=NATIVE, env=environment,
                            capture_output=True, text=True, errors="replace")
    if result.returncode:
        raise RuntimeError(
            f"focused command failed {result.returncode}: {command}\n"
            f"{result.stdout[-6000:]}\n{result.stderr[-6000:]}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    executable = args.exe.resolve()
    if not executable.is_file():
        parser.error(f"missing frozen CK3 EXE: {executable}")
    environment = _visual_studio_environment()
    cmake = environment["XAR_DEV21_CMAKE"]
    ninja = environment["XAR_DEV21_NINJA"]
    python = environment.get("PYTHON", "") or __import__("sys").executable
    _run([python, str(HERE / "verify_player_world_building_action_private_v1.py"),
          "--exe", str(executable)], environment)
    _run([python, "-m", "py_compile",
          str(HERE / "run_g2m4_paused_world_building_action.py")], environment)
    for mode, cmake_type in (("normal-Debug", "Debug"),
                             ("optimized-Release", "Release")):
        with tempfile.TemporaryDirectory(
            prefix=f"xar-m4-action-{cmake_type.lower()}-", dir=NATIVE.parent
        ) as temporary:
            build = Path(temporary)
            _run([
                cmake, "-S", str(NATIVE), "-B", str(build), "-G", "Ninja",
                f"-DCMAKE_MAKE_PROGRAM={ninja}",
                f"-DCMAKE_BUILD_TYPE={cmake_type}", "-DBUILD_TESTING=OFF",
                f"-DXAR_CK3_EXECUTABLE_PATH={executable}",
                "-DXAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1=ON",
                "-DXAR_CK3_ENABLE_G2_PLAYER_WORLD_BUILDING_ACTION_PRIVATE_V1=ON",
            ], environment)
            _run([ninja, "-C", str(build), "-j", "1", *OBJECTS], environment)
            print(f"m4-private-world-building-{mode}: GREEN_FOCUSED_OBJECTS_NO_LAUNCH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
