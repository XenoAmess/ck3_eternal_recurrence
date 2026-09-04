#!/usr/bin/env python3
"""Verify the refreshed promotion-source capture freeze without weakening v1."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import tempfile
from typing import Iterable

from verify_zg361_promotion_source_capture_no_launch_candidate import (
    EXPECTED_BASE_COMMIT,
    ROOT,
    _mapping,
    _sha256,
    verify_promotion_source_capture_no_launch_candidate,
)


CURRENT_CANDIDATE_COMMIT = "a01f8cb684d39e2ea8e95fbf0f20f170b6f1a396"
CURRENT_MANIFEST_KIND = (
    "zg361_promotion_source_capture_refreshed_no_launch_candidate"
)
SUPERSEDED_CANDIDATE_COMMIT = "366f30f0e899650582a7f76c8f0043ecc37e4887"
SUPERSEDED_MANIFEST_RELATIVE = (
    "ck3_autonomous_player/native_bridge/research/fixtures/"
    "zhongguo_promotion_source_capture_no_launch_candidate_366f30f_20260904.json"
)
SUPERSEDED_MANIFEST_SHA256 = (
    "4268B6D147D234536A03A98EC1F7A5E08DAAA7246DFF340B51FD42E2E94A8F98"
)
SUPERSEDED_DRIFTED_FILES = (
    "ck3_autonomous_player/native_bridge/CMakeLists.txt",
    "ck3_autonomous_player/native_bridge/src/bridge.cpp",
    "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp",
    "ck3_autonomous_player/native_bridge/src/game_adapter.cpp",
    "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
)
EXPECTED_SUPERSEDED_FAILURES = (
    "frozen_source_files_match",
    "native_source_fingerprint_matches",
)


def _deep_merge(base: dict[str, object], overlay: dict[str, object]) -> None:
    for key, value in overlay.items():
        current = base.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            _deep_merge(current, value)
        else:
            base[key] = copy.deepcopy(value)


def _hydrate_manifest(
    manifest: dict[str, object], source_root: Path
) -> dict[str, object]:
    """Apply the small refreshed overlay to the hash-pinned v1 manifest."""

    extends = _mapping(manifest.get("extends"))
    old_path = source_root / SUPERSEDED_MANIFEST_RELATIVE
    if not old_path.is_file() or _sha256(old_path) != SUPERSEDED_MANIFEST_SHA256:
        return copy.deepcopy(manifest)
    hydrated = json.loads(old_path.read_text(encoding="utf-8"))
    _deep_merge(
        hydrated,
        {
            key: value
            for key, value in manifest.items()
            if key not in {"extends", "supersession"}
        },
    )
    hydrated["supersession"] = copy.deepcopy(manifest.get("supersession"))
    return hydrated


def _write_v1_projection(manifest: dict[str, object], path: Path) -> None:
    """Project only v1's historical commit/test constants for strict reuse."""

    projected = copy.deepcopy(manifest)
    source = _mapping(projected.get("source"))
    tests = _mapping(projected.get("tests"))
    full_native = _mapping(tests.get("full_native"))
    source["candidate_commit"] = SUPERSEDED_CANDIDATE_COMMIT
    full_native["passed"] = 93
    projected["schema_version"] = 1
    projected["kind"] = "zg361_promotion_source_capture_no_launch_candidate"
    path.write_text(
        json.dumps(projected, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _frozen_file_drift(
    manifest: dict[str, object], source_root: Path
) -> list[str]:
    source = _mapping(manifest.get("source"))
    frozen_files = _mapping(source.get("frozen_files"))
    drifted: list[str] = []
    for relative, expected in frozen_files.items():
        path = source_root / str(relative)
        if not path.is_file() or _sha256(path) != str(expected).upper():
            drifted.append(str(relative))
    return sorted(drifted)


def verify_refreshed_promotion_source_capture_no_launch_candidate(
    manifest_path: Path,
    *,
    source_root: Path = ROOT,
    running_process_names: Iterable[str] | None = None,
) -> dict[str, object]:
    """Verify current bytes plus explicit fail-closed supersession evidence."""

    overlay = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = _hydrate_manifest(overlay, source_root)
    source = _mapping(manifest.get("source"))
    tests = _mapping(manifest.get("tests"))
    supersession = _mapping(manifest.get("supersession"))

    with tempfile.TemporaryDirectory() as temporary:
        projected_path = Path(temporary) / "v1-projection.json"
        _write_v1_projection(manifest, projected_path)
        report = verify_promotion_source_capture_no_launch_candidate(
            projected_path,
            source_root=source_root,
            running_process_names=running_process_names,
        )

    superseded_manifest_path = source_root / SUPERSEDED_MANIFEST_RELATIVE
    superseded_manifest = json.loads(
        superseded_manifest_path.read_text(encoding="utf-8")
    )
    superseded_report = verify_promotion_source_capture_no_launch_candidate(
        superseded_manifest_path,
        source_root=source_root,
        running_process_names=[],
    )
    superseded_drifted_files = _frozen_file_drift(
        superseded_manifest, source_root
    )

    checks = dict(_mapping(report.get("checks")))
    checks["refreshed_manifest_identity"] = (
        overlay.get("schema_version") == 2
        and overlay.get("kind") == CURRENT_MANIFEST_KIND
        and overlay.get("readiness") == "static-ready-live-pending"
        and _mapping(overlay.get("extends")).get("path")
        == SUPERSEDED_MANIFEST_RELATIVE
        and _mapping(overlay.get("extends")).get("sha256")
        == SUPERSEDED_MANIFEST_SHA256
    )
    checks["integrated_b7_base_and_latest_candidate"] = (
        source.get("base_commit") == EXPECTED_BASE_COMMIT
        and source.get("candidate_commit") == CURRENT_CANDIDATE_COMMIT
    )
    checks["fresh_native_tests_green"] = tests.get("full_native") == {
        "result": "GREEN",
        "passed": 94,
        "failed": 0,
    }
    cache_path = Path(str(_mapping(manifest.get("build")).get("cmake_cache_path", "")))
    cache = (
        cache_path.read_text(encoding="utf-8", errors="replace")
        if cache_path.is_file()
        else ""
    )
    checks["g2_actual_expiry_candidate_default_off_in_fresh_cache"] = (
        "XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1:BOOL=OFF"
        in cache
    )
    checks["supersession_is_explicit_and_fail_closed"] = (
        supersession.get("candidate_commit") == SUPERSEDED_CANDIDATE_COMMIT
        and supersession.get("manifest_path") == SUPERSEDED_MANIFEST_RELATIVE
        and supersession.get("manifest_sha256")
        == SUPERSEDED_MANIFEST_SHA256
        and _sha256(superseded_manifest_path) == SUPERSEDED_MANIFEST_SHA256
        and supersession.get("reason")
        == "canonical native and managed bridge sources advanced after the old freeze"
        and supersession.get("old_candidate_result_on_current_source") == "RED"
        and supersession.get("old_failed_checks")
        == list(EXPECTED_SUPERSEDED_FAILURES)
        and superseded_report.get("result") == "RED"
        and superseded_report.get("failed_checks")
        == list(EXPECTED_SUPERSEDED_FAILURES)
        and superseded_drifted_files == sorted(SUPERSEDED_DRIFTED_FILES)
    )

    failed = [name for name, passed in checks.items() if passed is not True]
    report["checks"] = checks
    report["failed_checks"] = failed
    report["result"] = "READY_TO_SERIAL_LIVE" if not failed else "RED"
    report["readiness"] = (
        "static-ready-live-pending" if not failed else "research"
    )
    report["kind"] = (
        "zg361_promotion_source_capture_refreshed_no_launch_candidate_preflight"
    )
    report["candidate_commit"] = CURRENT_CANDIDATE_COMMIT
    report["superseded_candidate_commit"] = SUPERSEDED_CANDIDATE_COMMIT
    report["superseded_drifted_files"] = superseded_drifted_files
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = verify_refreshed_promotion_source_capture_no_launch_candidate(
        args.manifest.resolve(), source_root=args.source_root.resolve()
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return (
        1
        if args.check and report["result"] != "READY_TO_SERIAL_LIVE"
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
