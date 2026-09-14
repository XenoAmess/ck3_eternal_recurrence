#!/usr/bin/env python3
"""Compile and run the private observer core in normal and optimized modes."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


VSWHERE = Path(
    r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
)


def visual_studio_developer_shell() -> Path:
    if not VSWHERE.is_file():
        raise RuntimeError("vswhere.exe is unavailable")
    completed = subprocess.run(
        [
            str(VSWHERE),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    installation = completed.stdout.strip()
    if not installation:
        raise RuntimeError("an x64 MSVC installation is unavailable")
    shell = Path(installation) / "Common7/Tools/VsDevCmd.bat"
    if not shell.is_file():
        raise RuntimeError(f"VsDevCmd.bat is unavailable: {shell}")
    return shell


def compile_and_run(
    *, root: Path, shell: Path, output_root: Path, optimized: bool
) -> dict[str, object]:
    native = root / "ck3_autonomous_player/native_bridge"
    source = native / "src/government_runtime_adapter_observer_v1.cpp"
    test = native / "src/government_runtime_adapter_observer_v1_test.cpp"
    mode = "optimized" if optimized else "normal"
    executable = output_root / f"government_runtime_adapter_observer_v1_{mode}.exe"
    compiler = [
        "cl.exe",
        "/nologo",
        "/std:c++20",
        "/EHsc",
        "/permissive-",
        "/Zc:__cplusplus",
        "/W4",
        "/WX",
        "/O2" if optimized else "/Od",
        f"/I{native / 'include'}",
        str(source),
        str(test),
        f"/Fe:{executable}",
    ]
    batch = output_root / f"build-{mode}.cmd"
    batch.write_text(
        "@echo off\n"
        f'call "{shell}" -no_logo -arch=amd64 >nul\n'
        "if errorlevel 1 exit /b %errorlevel%\n"
        f"{subprocess.list2cmdline(compiler)}\n"
        "exit /b %errorlevel%\n",
        encoding="utf-8",
    )
    built = subprocess.run(
        ["cmd.exe", "/d", "/c", str(batch)],
        cwd=output_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if built.returncode != 0 or not executable.is_file():
        raise RuntimeError(
            f"{mode} /W4 /WX build failed ({built.returncode}):\n"
            f"{built.stdout}\n{built.stderr}"
        )
    ran = subprocess.run(
        [str(executable)],
        cwd=output_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if ran.returncode != 0:
        raise RuntimeError(
            f"{mode} observer test failed ({ran.returncode}):\n"
            f"{ran.stdout}\n{ran.stderr}"
        )
    return {
        "mode": mode,
        "compile": "GREEN_W4_WX",
        "test": ran.stdout.strip(),
        "ck3_launched": False,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    shell = visual_studio_developer_shell()
    with tempfile.TemporaryDirectory(prefix="xar-gov-observer-") as temporary:
        output_root = Path(temporary)
        results = [
            compile_and_run(
                root=root, shell=shell, output_root=output_root, optimized=False
            ),
            compile_and_run(
                root=root, shell=shell, output_root=output_root, optimized=True
            ),
        ]
    print(
        json.dumps(
            {
                "status": "GREEN",
                "contract": "government_runtime_adapter_observer_v1",
                "results": results,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
