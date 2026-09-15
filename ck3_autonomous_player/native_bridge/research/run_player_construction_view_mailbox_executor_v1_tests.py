"""Exercise the private M4 mailbox executor identity in normal and optimized MSVC."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from run_domain_construction_cost_legality_live_observer_v1_tests import (
    _visual_studio_environment,
)


NATIVE = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ck3-executable", required=True, type=Path)
    args = parser.parse_args()
    executable = args.ck3_executable.resolve()
    if not executable.is_file():
        parser.error(f"CK3 exact-build executable missing: {executable}")

    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("cl.exe missing from Visual Studio environment")
    source = NATIVE / "src"
    research = NATIVE / "research"
    root = NATIVE.parent.parent
    contract = (
        source / "main_thread_query_mailbox_v1.cpp",
        research / "main_thread_query_mailbox_v1_abi.json",
        research / "fixtures/main_thread_query_mailbox_v1_source_contract.json",
        root / "docs/ck3-native-ai/main-thread-query-mailbox.md",
        executable,
        source / "bridge.cpp",
    )
    with tempfile.TemporaryDirectory(prefix="xar-m4-mailbox-executor-") as name:
        build = Path(name)
        for mode, optimization in (("normal", "/Od"), ("optimized", "/O2")):
            output = build / f"m4-mailbox-executor-{mode}.exe"
            command = [
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/permissive-", "/EHsc", "/UNDEBUG", optimization,
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/DUNICODE",
                "/D_UNICODE", f"/I{NATIVE / 'include'}",
                str(contract[0]), str(source / "main_thread_query_mailbox_v1_test.cpp"),
                "bcrypt.lib", "user32.lib", f"/Fe:{output}",
            ]
            subprocess.run(command, cwd=build, env=environment, check=True)
            subprocess.run(
                [str(output), *(str(path) for path in contract)],
                cwd=build, env=environment, check=True,
            )
            print(f"m4-mailbox-executor-{mode}: GREEN_REGISTERED_PAUSED_EXECUTOR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
