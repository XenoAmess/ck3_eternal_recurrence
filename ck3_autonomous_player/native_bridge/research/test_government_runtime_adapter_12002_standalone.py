#!/usr/bin/env python3
"""Build the new profile and existing government fixtures without CK3 access."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from test_government_runtime_adapter_bridge_binder_v1_standalone import (
    visual_studio_developer_shell,
)


COMMON_SOURCES = (
    "government_runtime_adapter_observer_v1.cpp",
    "government_runtime_adapter_source_adapter_v1.cpp",
    "government_runtime_adapter_bridge_binder_v1.cpp",
    "campaign_root_context_v1.cpp",
    "loaded_feature_manifest_v1.cpp",
    "ck3_12002_campaign.cpp",
    "ck3_12002_features.cpp",
    "ck3_12002_nonwar_metrics.cpp",
    "ck3_12002_nonwar_council.cpp",
    "ck3_12002_nonwar_realm.cpp",
)
FIXTURE_SOURCES = (
    "government_runtime_adapter_observer_v1_test.cpp",
    "government_runtime_adapter_source_adapter_v1_test.cpp",
    "government_runtime_adapter_bridge_binder_v1_test.cpp",
    "government_runtime_adapter_12002_test.cpp",
)


def run_batch(*, command: list[str], shell: Path, output: Path, tag: str) -> None:
    batch = output / f"build-{tag}.cmd"
    batch.write_text(
        "@echo off\n"
        f'call "{shell}" -no_logo -arch=amd64 >nul\n'
        "if errorlevel 1 exit /b %errorlevel%\n"
        f"{subprocess.list2cmdline(command)}\n"
        "exit /b %errorlevel%\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", str(batch)],
        cwd=output,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (output / f"build-{tag}.log").write_text(
        completed.stdout + completed.stderr, encoding="utf-8"
    )
    if completed.returncode:
        raise RuntimeError(f"{tag} build failed; see {output / f'build-{tag}.log'}")


def build_mode(
    *, root: Path, shell: Path, output: Path, optimized: bool,
    fixture_scope: str,
) -> dict:
    native = root / "ck3_autonomous_player/native_bridge"
    mode = "O2" if optimized else "Od"
    output = output / mode
    output.mkdir(parents=True, exist_ok=True)
    compiler = [
        "cl.exe", "/nologo", "/std:c++20", "/EHsc", "/permissive-",
        "/Zc:__cplusplus", "/W4", "/WX", "/utf-8", "/DNOMINMAX",
        "/DWIN32_LEAN_AND_MEAN", "/DUNICODE", "/D_UNICODE", f"/{mode}",
        f"/I{native / 'include'}",
    ]
    run_batch(
        command=compiler + ["/c", "/MP64"] + [
            str(native / "src" / source) for source in COMMON_SOURCES
        ],
        shell=shell,
        output=output,
        tag="common",
    )
    objects = [str(output / Path(source).with_suffix(".obj")) for source in COMMON_SOURCES]
    results = []
    fixtures = FIXTURE_SOURCES if fixture_scope == "all" else FIXTURE_SOURCES[-1:]
    for source in fixtures:
        tag = Path(source).stem
        executable = output / f"{tag}.exe"
        run_batch(
            command=compiler + [str(native / "src" / source)] + objects + [
                f"/Fe:{executable}"
            ],
            shell=shell,
            output=output,
            tag=tag,
        )
        arguments = [str(executable)]
        if source == "government_runtime_adapter_12002_test.cpp":
            arguments += ["--wire-json-dir", str(output / "wire")]
        completed = subprocess.run(
            arguments, cwd=output, capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
        (output / f"{tag}.log").write_text(
            completed.stdout + completed.stderr, encoding="utf-8"
        )
        if completed.returncode:
            raise RuntimeError(f"{mode} {tag} failed: {completed.stdout}{completed.stderr}")
        if source == "government_runtime_adapter_12002_test.cpp":
            available = json.loads((output / "wire/available.json").read_text(encoding="utf-8"))
            unavailable = json.loads((output / "wire/unavailable.json").read_text(encoding="utf-8"))
            if (
                available["status"] != "available"
                or available["adapter"]["status"] != "core_supported"
                or available["effective_feature_flags"]["items"][43]["key"] != "by_god_alone"
                or unavailable["status"] != "unavailable"
                or unavailable["snapshot_revision"] != 701
            ):
                raise RuntimeError(f"{mode} actual serialized government payload failed")
        results.append({
            "fixture": source,
            "result": completed.stdout.strip(),
            "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        })
    return {"mode": mode, "compile": "GREEN_W4_WX", "fixtures": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--fixture", choices=("all", "current"), default="all")
    args = parser.parse_args()
    output = args.artifacts.resolve()
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[3]
    shell = visual_studio_developer_shell()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(
            build_mode, root=root, shell=shell, output=output, optimized=optimized,
            fixture_scope=args.fixture,
        ) for optimized in (False, True)]
        results = [future.result() for future in futures]
    receipt = {
        "status": "GREEN",
        "contract": "government-runtime-adapter-12002",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixture_scope": args.fixture,
        "results": results,
        "source_sha256": {
            source: hashlib.sha256(
                (root / "ck3_autonomous_player/native_bridge/src" / source).read_bytes()
            ).hexdigest() for source in COMMON_SOURCES + FIXTURE_SOURCES
        },
        "ck3_launched": False,
        "ck3_process_queried": False,
        "ck3_pipe_opened": False,
        "live_status": "not_run",
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
