#!/usr/bin/env python3
"""Build and run the SCHEME10 private binder fixture."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def repository_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root was not found")


def vcvars64() -> Path | None:
    if shutil.which("cl.exe"):
        return None
    candidates: list[Path] = []
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(variable)
        if base:
            candidates.extend(
                (Path(base) / "Microsoft Visual Studio").glob(
                    "*/*/VC/Auxiliary/Build/vcvars64.bat"
                )
            )
    if not candidates:
        raise RuntimeError("MSVC cl.exe/vcvars64.bat was not found")
    return sorted(candidates, reverse=True)[0]


def quoted(path: Path) -> str:
    return f'"{path}"'


def main() -> int:
    root = repository_root()
    bridge = root / "ck3_autonomous_player" / "native_bridge"
    sources = [
        "active_scheme_state_v1_private_observer.cpp",
        "active_scheme_state_v1_private_source_adapter.cpp",
        "active_scheme_semantic_action_v1_private.cpp",
        "active_scheme_semantic_action_v1_private_native_command_adapter.cpp",
        "active_scheme_interaction_definition_resolver_v1_private.cpp",
        "active_scheme_paused_live_native_glue_v1_private.cpp",
        "active_scheme_precondition_command_binders_v1_private.cpp",
        "active_scheme_precondition_command_binders_v1_private_test.cpp",
    ]
    optimization = "/O2 /DNDEBUG" if sys.flags.optimize else "/Od"
    label = "optimized-python" if sys.flags.optimize else "normal-python"
    with tempfile.TemporaryDirectory(prefix="scheme10-binders-") as raw_temp:
        temporary = Path(raw_temp)
        executable = temporary / "scheme10_binders_test.exe"
        command = " ".join(
            [
                "cl.exe",
                "/nologo /std:c++20 /permissive- /EHsc /W4 /WX",
                optimization,
                "/I",
                quoted(bridge / "include"),
                "/I",
                quoted(bridge / "src"),
                *(quoted(bridge / "src" / source) for source in sources),
                f'/Fo{quoted(temporary)}\\',
                f'/Fe:{quoted(executable)}',
            ]
        )
        batch = temporary / "build-and-run.cmd"
        lines = ["@echo off"]
        environment = vcvars64()
        if environment is not None:
            lines.extend(
                [f"call {quoted(environment)} >nul", "if errorlevel 1 exit /b 97"]
            )
        lines.extend(
            [command, "if errorlevel 1 exit /b 98", quoted(executable),
             "if errorlevel 1 exit /b 99"]
        )
        batch.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
        completed = subprocess.run(
            [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(batch)],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if completed.returncode != 0:
            print(completed.stdout, file=sys.stderr)
            return completed.returncode
    print(f"GREEN: active-scheme SCHEME10 {label} /W4 /WX fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
