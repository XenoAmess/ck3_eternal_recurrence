"""Compile the private player-view cache probe in normal and optimized MSVC."""

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
    with tempfile.TemporaryDirectory(prefix="xar-player-construction-view-") as name:
        build = Path(name)
        for mode, flags in (("normal", ["/Od"]), ("optimized", ["/O2"])):
            output = build / f"player-construction-view-probe-{mode}.exe"
            command = [
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                "/permissive-", "/EHsc", "/UNDEBUG", *flags,
                f"/I{HERE}", f"/I{NATIVE / 'src'}",
                f"/I{NATIVE / 'include'}",
                str(NATIVE / "src/player_construction_view_probe_v1.cpp"),
                str(NATIVE / "src/player_construction_view_probe_v1_test.cpp"),
                f"/Fe:{output}",
            ]
            subprocess.run(command, cwd=build, env=environment, check=True)
            subprocess.run([str(output)], cwd=build, env=environment, check=True)
            process_object = build / f"player-construction-view-probe-process-{mode}.obj"
            subprocess.run([
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/permissive-",
                "/EHsc", *flags, f"/I{HERE}", f"/I{NATIVE / 'src'}",
                f"/I{NATIVE / 'include'}", "/c",
                str(NATIVE / "src/player_construction_view_probe_v1_process.cpp"),
                f"/Fo:{process_object}",
            ], cwd=build, env=environment, check=True)
            mailbox_object = build / f"player-construction-view-probe-mailbox-{mode}.obj"
            subprocess.run([
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/permissive-",
                "/EHsc", *flags, f"/I{HERE}", f"/I{NATIVE / 'src'}",
                f"/I{NATIVE / 'include'}", "/c",
                str(NATIVE / "src/player_construction_view_probe_v1_mailbox.cpp"),
                f"/Fo:{mailbox_object}",
            ], cwd=build, env=environment, check=True)
            subprocess.run([
                compiler, "/nologo", "/std:c++20", "/W4",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                "/DXAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1=1",
                '/DXAR_BRIDGE_VERSION="0.1.0"',
                "/permissive-", "/EHsc", *flags,
                f"/I{HERE}", f"/I{NATIVE / 'src'}",
                f"/I{NATIVE / 'include'}", "/Zs",
                str(NATIVE / "src/bridge.cpp"),
            ], cwd=build, env=environment, check=True)
            print(f"player-construction-view-probe-{mode}: GREEN_W4WX_NATIVE_AND_BRIDGE_SYNTAX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
