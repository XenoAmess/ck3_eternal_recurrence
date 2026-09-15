"""Run the focused read-only CK3 cost-gate collector fixture in two MSVC modes."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from run_domain_construction_cost_legality_live_observer_v1_tests import (
    _visual_studio_environment,
)


HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent


def run_mode(mode: str, build: Path, flags: list[str],
             environment: dict[str, str]) -> None:
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("cl.exe was not present in the Visual Studio environment")
    output = build / f"domain-construction-cost-gate-collector-{mode}.exe"
    sources = [
        HERE / "domain_construction_candidate_identity_decoder_v1.cpp",
        HERE / "domain_construction_candidate_cost_legality_decoder_v1.cpp",
        HERE / "domain_construction_cost_legality_collector_source_adapter_v1.cpp",
        NATIVE / "src/domain_construction_cost_gate_collector_v1.cpp",
        NATIVE / "src/domain_construction_cost_gate_collector_v1_test.cpp",
    ]
    command = [
        compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
        "/EHsc", "/UNDEBUG", *flags,
        f"/I{HERE}", f"/I{NATIVE / 'src'}", f"/I{NATIVE / 'include'}",
        *(str(path) for path in sources), f"/Fe:{output}",
    ]
    subprocess.run(command, cwd=build, env=environment, check=True)
    subprocess.run([str(output)], cwd=build, env=environment, check=True)
    print(f"domain-construction-cost-gate-collector-{mode}: GREEN_W4WX")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path)
    arguments = parser.parse_args()
    environment = _visual_studio_environment()
    if arguments.build_root is None:
        with tempfile.TemporaryDirectory(prefix="xar-cost-gate-collector-") as name:
            build = Path(name)
            run_mode("normal", build, ["/Od"], environment)
            run_mode("optimized", build, ["/O2"], environment)
    else:
        build = arguments.build_root.resolve()
        build.mkdir(parents=True, exist_ok=True)
        run_mode("normal", build, ["/Od"], environment)
        run_mode("optimized", build, ["/O2"], environment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
