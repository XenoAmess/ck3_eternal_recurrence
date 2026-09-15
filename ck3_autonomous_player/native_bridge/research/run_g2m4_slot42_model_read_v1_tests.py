"""Focused normal/optimized native compile for the additive private slot42 model read."""

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
    with tempfile.TemporaryDirectory(prefix="xar-g2m4-slot42-model-") as name:
        build = Path(name)
        for mode, flags in (("normal", ["/Od"]), ("optimized", ["/O2"])):
            for unit in (
                "player_held_construction_model_enumerator_v1.cpp",
                "player_construction_view_probe_v1_mailbox.cpp",
            ):
                output = build / f"{Path(unit).stem}-{mode}.obj"
                subprocess.run([
                    compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                    "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/permissive-",
                    "/EHsc", "/UNDEBUG", *flags,
                    f"/I{HERE}", f"/I{NATIVE / 'src'}",
                    f"/I{NATIVE / 'include'}",
                    "/c", str(NATIVE / "src" / unit), f"/Fo:{output}",
                ], cwd=build, env=environment, check=True)
            print(f"g2m4-slot42-player-model-{mode}: GREEN_W4WX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
