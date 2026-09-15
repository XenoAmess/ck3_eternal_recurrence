"""Run the G2-M4 private world-definition source in normal and optimized MSVC.

This compiles only the two read-only source units and a fake closed county-view
fixture. No CK3 instance, loaded DLL, or shared save is touched.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

from run_domain_construction_cost_legality_live_observer_v1_tests import (
    _visual_studio_environment,
)


HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent


def main() -> int:
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("cl.exe missing from Visual Studio environment")
    with tempfile.TemporaryDirectory(prefix="xar-player-world-buildings-") as name:
        build = Path(name)
        for mode, flags in (("normal-Debug", ["/Od", "/MDd", "/Zi"]),
                            ("optimized-Release", ["/O2", "/MD"])):
            output = build / f"player-world-buildings-{mode}.exe"
            command = [
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                "/permissive-", "/EHsc", "/UNDEBUG", *flags,
                f"/I{NATIVE / 'src'}", f"/I{NATIVE / 'include'}",
                str(NATIVE / "src/player_held_construction_model_enumerator_v1.cpp"),
                str(NATIVE / "src/player_world_building_definition_source_v1.cpp"),
                str(NATIVE / "src/player_world_building_definition_source_v1_test.cpp"),
                f"/Fe:{output}",
            ]
            subprocess.run(command, cwd=build, env=environment, check=True)
            subprocess.run([str(output)], cwd=build, env=environment, check=True)
            process_output = build / f"player-world-buildings-process-{mode}.exe"
            process_command = [
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                "/permissive-", "/EHsc", "/UNDEBUG", *flags,
                f"/I{NATIVE / 'src'}", f"/I{NATIVE / 'include'}",
                str(NATIVE / "src/player_world_building_definition_source_v1_process.cpp"),
                str(NATIVE / "src/player_world_building_definition_source_v1_process_test.cpp"),
                f"/Fe:{process_output}",
            ]
            subprocess.run(process_command, cwd=build, env=environment,
                           check=True)
            subprocess.run([str(process_output)], cwd=build, env=environment,
                           check=True)
            print(f"player-world-buildings-{mode}: GREEN_W4WX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
