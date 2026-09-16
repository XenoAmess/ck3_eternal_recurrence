"""Focus only the R746 stock-cost selection/material contract in both MSVC modes."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

from run_domain_construction_cost_legality_live_observer_v1_tests import (
    _visual_studio_environment,
)


NATIVE = Path(__file__).resolve().parent.parent


def main() -> int:
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("cl.exe missing from Visual Studio environment")
    source = NATIVE / "src"
    with tempfile.TemporaryDirectory(prefix="xar-m4-cost-to-action-") as name:
        build = Path(name)
        for mode, flags in (("normal-Debug", ["/Od", "/MDd", "/Zi"]),
                            ("optimized-Release", ["/O2", "/MD"])):
            output = build / f"m4-cost-to-action-{mode}.exe"
            command = [
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/permissive-",
                "/EHsc", "/UNDEBUG", *flags,
                f"/I{source}", f"/I{NATIVE / 'include'}",
                str(source / "player_world_building_action_candidate_v1.cpp"),
                str(source / "player_world_building_action_candidate_v1_test.cpp"),
                f"/Fe:{output}",
            ]
            subprocess.run(command, cwd=build, env=environment, check=True)
            subprocess.run([str(output)], cwd=build, env=environment, check=True)
            print(f"m4-cost-to-action-{mode}: GREEN_W4WX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
