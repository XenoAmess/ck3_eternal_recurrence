#!/usr/bin/env python3
"""Verify the final cleanup-dispatch-aware B7 capture freeze without CK3."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import tempfile
from typing import Iterable

from verify_zg361_promotion_source_capture_no_launch_candidate import (
    ROOT,
    _mapping,
    _sha256,
)
from verify_zg361_promotion_source_capture_no_launch_candidate_refresh import (
    CURRENT_MANIFEST_KIND as A01_MANIFEST_KIND,
    _deep_merge,
    _frozen_file_drift,
    _hydrate_manifest as hydrate_a01_manifest,
    verify_refreshed_promotion_source_capture_no_launch_candidate,
)


CURRENT_CANDIDATE_COMMIT = "7d50c2d3b739221e216c5158a04b6d18bf6b3587"
CURRENT_MANIFEST_KIND = (
    "zg361_promotion_source_capture_final_no_launch_candidate"
)
SUPERSEDED_CANDIDATE_COMMIT = "a01f8cb684d39e2ea8e95fbf0f20f170b6f1a396"
SUPERSEDED_MANIFEST_RELATIVE = (
    "ck3_autonomous_player/native_bridge/research/fixtures/"
    "zhongguo_promotion_source_capture_no_launch_candidate_a01f8cb_20260904.json"
)
SUPERSEDED_MANIFEST_SHA256 = (
    "CE33DAB589FF02EBABCE7928233935B41E6D0EEE8C68E27BF4F6AC8697DA6A30"
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


def _hydrate_manifest(
    manifest: dict[str, object], source_root: Path
) -> dict[str, object]:
    previous_path = source_root / SUPERSEDED_MANIFEST_RELATIVE
    if (
        not previous_path.is_file()
        or _sha256(previous_path) != SUPERSEDED_MANIFEST_SHA256
    ):
        return copy.deepcopy(manifest)
    previous_overlay = json.loads(previous_path.read_text(encoding="utf-8"))
    hydrated = hydrate_a01_manifest(previous_overlay, source_root)
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


def _write_a01_projection(
    manifest: dict[str, object], path: Path, source_root: Path
) -> None:
    projected = copy.deepcopy(manifest)
    previous_overlay = json.loads(
        (source_root / SUPERSEDED_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    )
    source = _mapping(projected.get("source"))
    tests = _mapping(projected.get("tests"))
    full_native = _mapping(tests.get("full_native"))
    source["candidate_commit"] = SUPERSEDED_CANDIDATE_COMMIT
    full_native["passed"] = 94
    projected["schema_version"] = 2
    projected["kind"] = A01_MANIFEST_KIND
    projected["extends"] = copy.deepcopy(previous_overlay.get("extends"))
    projected["supersession"] = copy.deepcopy(
        previous_overlay.get("supersession")
    )
    path.write_text(
        json.dumps(projected, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def verify_final_promotion_source_capture_no_launch_candidate(
    manifest_path: Path,
    *,
    source_root: Path = ROOT,
    running_process_names: Iterable[str] | None = None,
) -> dict[str, object]:
    overlay = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = _hydrate_manifest(overlay, source_root)
    source = _mapping(manifest.get("source"))
    build = _mapping(manifest.get("build"))
    tests = _mapping(manifest.get("tests"))
    supersession = _mapping(manifest.get("supersession"))

    with tempfile.TemporaryDirectory() as temporary:
        projected_path = Path(temporary) / "a01-projection.json"
        _write_a01_projection(manifest, projected_path, source_root)
        report = verify_refreshed_promotion_source_capture_no_launch_candidate(
            projected_path,
            source_root=source_root,
            running_process_names=running_process_names,
        )

    previous_path = source_root / SUPERSEDED_MANIFEST_RELATIVE
    previous_overlay = json.loads(previous_path.read_text(encoding="utf-8"))
    previous_report = (
        verify_refreshed_promotion_source_capture_no_launch_candidate(
            previous_path,
            source_root=source_root,
            running_process_names=[],
        )
    )
    previous_hydrated = hydrate_a01_manifest(previous_overlay, source_root)
    drifted_files = _frozen_file_drift(previous_hydrated, source_root)

    checks = dict(_mapping(report.get("checks")))
    checks["final_manifest_identity"] = (
        overlay.get("schema_version") == 3
        and overlay.get("kind") == CURRENT_MANIFEST_KIND
        and overlay.get("readiness") == "static-ready-live-pending"
        and _mapping(overlay.get("extends")).get("path")
        == SUPERSEDED_MANIFEST_RELATIVE
        and _mapping(overlay.get("extends")).get("sha256")
        == SUPERSEDED_MANIFEST_SHA256
    )
    checks["cleanup_dispatch_base_and_latest_candidate"] = (
        source.get("base_commit")
        == "d53befaa4872662562f5db5d31757ca731e799e0"
        and source.get("cleanup_dispatch_base_commit")
        == "ff89dcdbefb9d8fc86ce4722df847946e96d0e81"
        and source.get("candidate_commit") == CURRENT_CANDIDATE_COMMIT
    )
    checks["fresh_native_tests_green"] = tests.get("full_native") == {
        "result": "GREEN",
        "passed": 94,
        "failed": 0,
    }
    cache_path = Path(str(build.get("cmake_cache_path", "")))
    cache = (
        cache_path.read_text(encoding="utf-8", errors="replace")
        if cache_path.is_file()
        else ""
    )
    checks["all_adjacent_private_candidates_default_off"] = all(
        token in cache
        for token in (
            "XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1:BOOL=OFF",
            "XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1:BOOL=OFF",
            "XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1:BOOL=OFF",
            "XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1:BOOL=OFF",
        )
    )
    ctest = _mapping(build.get("ctest_log"))
    ctest_path = Path(str(ctest.get("path", "")))
    ctest_text = (
        ctest_path.read_text(encoding="utf-8", errors="replace")
        if ctest_path.is_file()
        else ""
    )
    checks["frozen_ctest_log_is_94_of_94_green"] = (
        ctest_path.is_file()
        and ctest_path.stat().st_size == ctest.get("bytes")
        and _sha256(ctest_path) == str(ctest.get("sha256", "")).upper()
        and "100% tests passed, 0 tests failed out of 94" in ctest_text
    )
    checks["a01_candidate_superseded_fail_closed"] = (
        supersession.get("candidate_commit") == SUPERSEDED_CANDIDATE_COMMIT
        and supersession.get("manifest_path") == SUPERSEDED_MANIFEST_RELATIVE
        and supersession.get("manifest_sha256") == SUPERSEDED_MANIFEST_SHA256
        and _sha256(previous_path) == SUPERSEDED_MANIFEST_SHA256
        and supersession.get("reason")
        == "private G2 cleanup dispatch advanced canonical native and managed bridge sources"
        and supersession.get("old_candidate_result_on_current_source") == "RED"
        and supersession.get("old_failed_checks")
        == list(EXPECTED_SUPERSEDED_FAILURES)
        and previous_report.get("result") == "RED"
        and previous_report.get("failed_checks")
        == list(EXPECTED_SUPERSEDED_FAILURES)
        and drifted_files == sorted(SUPERSEDED_DRIFTED_FILES)
    )

    failed = [name for name, passed in checks.items() if passed is not True]
    report["checks"] = checks
    report["failed_checks"] = failed
    report["result"] = "READY_TO_SERIAL_LIVE" if not failed else "RED"
    report["readiness"] = (
        "static-ready-live-pending" if not failed else "research"
    )
    report["kind"] = (
        "zg361_promotion_source_capture_final_no_launch_candidate_preflight"
    )
    report["candidate_commit"] = CURRENT_CANDIDATE_COMMIT
    report["superseded_candidate_commit"] = SUPERSEDED_CANDIDATE_COMMIT
    report["superseded_drifted_files"] = drifted_files
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = verify_final_promotion_source_capture_no_launch_candidate(
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
    return 1 if args.check and report["result"] != "READY_TO_SERIAL_LIVE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
