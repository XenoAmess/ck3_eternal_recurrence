#!/usr/bin/env python3
"""Build the bounded particle2 factory debug-capture helper with MSVC."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


VSWHERE = Path(
    r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-path", type=Path)
    parser.add_argument("--debug-build", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    return parser


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _resolve_plan(args: argparse.Namespace) -> dict[str, object]:
    research_root = Path(__file__).resolve().parent
    source = research_root / "particle2_factory_debug_capture.cpp"
    if not source.is_file():
        raise RuntimeError(f"Missing source: {source}")
    output = (
        args.output_path.resolve()
        if args.output_path is not None
        else (
            research_root
            / "build-particle2-factory-debug-capture"
            / "particle2_factory_debug_capture.exe"
        ).resolve()
    )
    return {
        "source": str(source),
        "output": str(output),
        "debug_build": bool(args.debug_build),
        "compiler_flags": ["/Od", "/Zi"] if args.debug_build else ["/O2"],
        "vswhere": str(VSWHERE),
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    plan = _resolve_plan(args)
    if args.plan_only:
        return {"status": "planned", **plan}
    if not VSWHERE.is_file():
        raise RuntimeError("vswhere.exe is unavailable")
    installation = subprocess.run(
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
    ).stdout.strip()
    if not installation:
        raise RuntimeError("No x64 MSVC installation found")
    developer_shell = Path(installation) / "Common7" / "Tools" / "VsDevCmd.bat"
    if not developer_shell.is_file():
        raise RuntimeError(f"VsDevCmd.bat is unavailable: {developer_shell}")

    output = Path(str(plan["output"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    compiler_arguments = [
        "cl.exe",
        "/nologo",
        "/std:c++20",
        "/EHsc",
        "/W4",
        "/WX",
        *[str(value) for value in plan["compiler_flags"]],
        "/DUNICODE",
        "/D_UNICODE",
        str(plan["source"]),
        f"/Fe:{output}",
        "bcrypt.lib",
    ]
    command = (
        f"call {subprocess.list2cmdline([str(developer_shell)])} "
        "-no_logo -arch=amd64 >nul && "
        + subprocess.list2cmdline(compiler_arguments)
    )
    completed = subprocess.run(
        ["cmd.exe", "/d", "/s", "/c", command], check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"MSVC build failed with exit code {completed.returncode}"
        )
    if not output.is_file():
        raise RuntimeError(f"MSVC build did not produce {output}")
    return {
        "status": "ready",
        "output": str(output),
        "bytes": output.stat().st_size,
        "sha256": _sha256(output),
        "debug_build": bool(args.debug_build),
    }


def main() -> int:
    try:
        result = run(_parser().parse_args())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
