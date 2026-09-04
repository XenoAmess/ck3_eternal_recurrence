#!/usr/bin/env python3
"""Verify the product-wide B7 default and B3 compensation-ON freezes."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Iterable, Mapping

from verify_zg361_promotion_source_capture_no_launch_candidate import (
    ROOT,
    _mapping,
    _native_source_fingerprint,
    _sha256,
)
from verify_zg361_promotion_source_capture_no_launch_candidate_final import (
    _hydrate_manifest as hydrate_previous_manifest,
    verify_final_promotion_source_capture_no_launch_candidate,
)
from verify_zg361_promotion_source_capture_no_launch_candidate_refresh import (
    _deep_merge,
)


CURRENT_CANDIDATE_COMMIT = "1c696588dfdb02f9be051220db06cf303f3f9f99"
NATIVE_BUILD_SOURCE_COMMIT = "cac1e85b616827a9ae11d755dd71f119325e6f3f"
CURRENT_MANIFEST_KIND = (
    "zg361_promotion_source_product_native_no_launch_candidate"
)
PREVIOUS_CANDIDATE_COMMIT = "7d50c2d3b739221e216c5158a04b6d18bf6b3587"
PREVIOUS_MANIFEST_RELATIVE = (
    "ck3_autonomous_player/native_bridge/research/fixtures/"
    "zhongguo_promotion_source_capture_no_launch_candidate_7d50c2d_20260904.json"
)
PREVIOUS_MANIFEST_SHA256 = (
    "E778470FF5733E0E5A737F192B82B1B29F52DF2CBBAB5BA7D0BE46C40B13AE5A"
)
EXPECTED_PREVIOUS_FAILURES = (
    "frozen_source_files_match",
    "native_source_fingerprint_matches",
    "supersession_is_explicit_and_fail_closed",
    "a01_candidate_superseded_fail_closed",
)
COMPENSATION_FLAG = (
    "XAR_CK3_ENABLE_ZHONGGUO_PROMOTION_COMPENSATION_CANDIDATE_V1"
)
PRIVATE_FLAGS = (
    "XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1",
    "XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1",
    "XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2",
    "XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1",
    "XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1",
    "XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1",
    "XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1",
    "XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1",
    "XAR_CK3_ENABLE_PHASE2_COMPLETION_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_POST_CALL_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_V1",
    "XAR_CK3_ENABLE_PHASE2_WRAPPER_ENTRY_OBSERVER_V1",
    "XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1",
    "XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1",
    "XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1",
    "XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1",
    "XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1",
    "XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1",
    COMPENSATION_FLAG,
    "XAR_CK3_ENABLE_ZHONGGUO_SCOREBOARD_PRODUCTION_V1",
)


def _hydrate_manifest(
    manifest: dict[str, object], source_root: Path
) -> dict[str, object]:
    previous_path = source_root / PREVIOUS_MANIFEST_RELATIVE
    if (
        not previous_path.is_file()
        or _sha256(previous_path) != PREVIOUS_MANIFEST_SHA256
    ):
        return copy.deepcopy(manifest)
    previous_overlay = json.loads(previous_path.read_text(encoding="utf-8"))
    hydrated = hydrate_previous_manifest(previous_overlay, source_root)
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


def _replace_flag_value(argv: list[str], flag: str, value: str) -> None:
    index = argv.index(flag)
    argv[index + 1] = value


def _write_previous_projection(
    manifest: dict[str, object], path: Path, source_root: Path
) -> None:
    projected = copy.deepcopy(manifest)
    previous = json.loads(
        (source_root / PREVIOUS_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    )
    source = _mapping(projected.get("source"))
    source["candidate_commit"] = PREVIOUS_CANDIDATE_COMMIT
    projected["schema_version"] = 3
    projected["kind"] = (
        "zg361_promotion_source_capture_final_no_launch_candidate"
    )
    projected["extends"] = copy.deepcopy(previous.get("extends"))
    projected["supersession"] = copy.deepcopy(previous.get("supersession"))

    default_build = _mapping(projected.get("build"))
    bridge = _mapping(default_build.get("bridge"))
    injector = _mapping(default_build.get("injector"))
    command = _mapping(projected.get("live_command"))
    argv = [str(value) for value in command.get("argv", [])]
    _replace_flag_value(argv, "--bridge-dll", str(bridge.get("path")))
    _replace_flag_value(
        argv, "--bridge-injector", str(injector.get("path"))
    )
    command["argv"] = argv
    path.write_text(
        json.dumps(projected, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _product_source_fingerprint(root: Path) -> tuple[str, int, int]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "mod_zhongguo_style"],
        check=True,
        capture_output=True,
    )
    relative_paths = sorted(
        value.decode("utf-8")
        for value in completed.stdout.split(b"\0")
        if value
    )
    digest = hashlib.sha256()
    total_bytes = 0
    for relative in relative_paths:
        data = (root / relative).read_bytes()
        total_bytes += len(data)
        file_sha256 = hashlib.sha256(data).hexdigest().upper()
        digest.update(
            f"{relative}\0{len(data)}\0{file_sha256}\n".encode("utf-8")
        )
    return digest.hexdigest().upper(), len(relative_paths), total_bytes


def _cache_flags(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    flags: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.fullmatch(r"(XAR_CK3_ENABLE_[A-Z0-9_]+):BOOL=(ON|OFF)", line)
        if match:
            flags[match.group(1)] = match.group(2)
    return dict(sorted(flags.items()))


def _artifact_matches(item: Mapping[str, object]) -> bool:
    path = Path(str(item.get("path", "")))
    return (
        path.is_file()
        and path.stat().st_size == item.get("bytes")
        and _sha256(path) == str(item.get("sha256", "")).upper()
    )


def _build_matches(build: Mapping[str, object]) -> bool:
    cache_path = Path(str(build.get("cmake_cache_path", "")))
    ctest = _mapping(build.get("ctest_log"))
    ctest_path = Path(str(ctest.get("path", "")))
    ctest_text = (
        ctest_path.read_text(encoding="utf-8", errors="replace")
        if ctest_path.is_file()
        else ""
    )
    return (
        cache_path.is_file()
        and cache_path.stat().st_size == build.get("cmake_cache_bytes")
        and _sha256(cache_path)
        == str(build.get("cmake_cache_sha256", "")).upper()
        and _artifact_matches(_mapping(build.get("bridge")))
        and _artifact_matches(_mapping(build.get("injector")))
        and _artifact_matches(ctest)
        and "100% tests passed, 0 tests failed out of 94" in ctest_text
    )


def _expected_live_argv(
    manifest: Mapping[str, object], candidate: Mapping[str, object]
) -> list[str]:
    attempt = _mapping(manifest.get("live_attempt"))
    command = _mapping(manifest.get("live_command"))
    root = Path(str(command.get("execution_source_root", "")))
    bridge = _mapping(candidate.get("bridge"))
    injector = _mapping(candidate.get("injector"))
    argv = [str(value) for value in command.get("argv", [])]
    pipe = argv[argv.index("--bridge-pipe") + 1] if "--bridge-pipe" in argv else ""
    return [
        str(root / "tools/.venv/Scripts/python.exe"),
        str(root / "tools/run_zhongguo_acceptance.py"),
        "--artifacts-dir",
        str(attempt.get("path")),
        "--phase2-promotion-source-checkpoint-live",
        "--phase2-promotion-source-checkpoint-timeout-seconds",
        "600",
        "--bridge-dll",
        str(bridge.get("path")),
        "--bridge-injector",
        str(injector.get("path")),
        "--bridge-pipe",
        pipe,
        "--phase2-seed-contract",
        str(command.get("seed_contract_path")),
    ]


def verify_product_native_no_launch_candidate(
    manifest_path: Path,
    *,
    source_root: Path = ROOT,
    running_process_names: Iterable[str] | None = None,
) -> dict[str, object]:
    overlay = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = _hydrate_manifest(overlay, source_root)
    source = _mapping(manifest.get("source"))
    default_build = _mapping(manifest.get("build"))
    candidate_build = _mapping(manifest.get("live_candidate_build"))
    supersession = _mapping(manifest.get("supersession"))
    boundary = _mapping(manifest.get("build_boundary"))

    with tempfile.TemporaryDirectory() as temporary:
        projection = Path(temporary) / "previous-projection.json"
        _write_previous_projection(manifest, projection, source_root)
        report = verify_final_promotion_source_capture_no_launch_candidate(
            projection,
            source_root=source_root,
            running_process_names=running_process_names,
        )

    previous_path = source_root / PREVIOUS_MANIFEST_RELATIVE
    previous_report = verify_final_promotion_source_capture_no_launch_candidate(
        previous_path, source_root=source_root, running_process_names=[]
    )
    product_fingerprint, product_count, product_bytes = (
        _product_source_fingerprint(source_root)
    )
    native_fingerprint, native_count = _native_source_fingerprint(source_root)
    expected_default_flags = {name: "OFF" for name in PRIVATE_FLAGS}
    expected_candidate_flags = dict(expected_default_flags)
    expected_candidate_flags[COMPENSATION_FLAG] = "ON"
    actual_default_flags = _cache_flags(
        Path(str(default_build.get("cmake_cache_path", "")))
    )
    actual_candidate_flags = _cache_flags(
        Path(str(candidate_build.get("cmake_cache_path", "")))
    )
    frozen_product_files = _mapping(source.get("frozen_product_files"))
    frozen_product_checks = {
        str(relative): (
            (source_root / str(relative)).is_file()
            and _sha256(source_root / str(relative)) == str(expected).upper()
        )
        for relative, expected in frozen_product_files.items()
    }
    command = _mapping(manifest.get("live_command"))
    argv = [str(value) for value in command.get("argv", [])]
    attempt = _mapping(manifest.get("live_attempt"))
    attempt_path = Path(str(attempt.get("path", "")))
    pipe = argv[argv.index("--bridge-pipe") + 1] if "--bridge-pipe" in argv else ""

    checks = dict(_mapping(report.get("checks")))
    # The two historical exact-drift-list checks predate the later runner-only
    # change. The immediate predecessor is still checked below by exact hash,
    # exact RED set, and the current full source fingerprints.
    checks.pop("supersession_is_explicit_and_fail_closed", None)
    checks.pop("a01_candidate_superseded_fail_closed", None)
    checks.update(
        {
            "product_native_manifest_identity": (
                overlay.get("schema_version") == 4
                and overlay.get("kind") == CURRENT_MANIFEST_KIND
                and overlay.get("readiness") == "static-ready-live-pending"
                and _mapping(overlay.get("extends")).get("path")
                == PREVIOUS_MANIFEST_RELATIVE
                and _mapping(overlay.get("extends")).get("sha256")
                == PREVIOUS_MANIFEST_SHA256
            ),
            "current_candidate_and_native_source_exact": (
                source.get("candidate_commit") == CURRENT_CANDIDATE_COMMIT
                and source.get("native_build_source_commit")
                == NATIVE_BUILD_SOURCE_COMMIT
                and source.get("native_source_equivalent_to_candidate") is True
                and native_fingerprint
                == str(source.get("native_source_fingerprint_sha256", "")).upper()
                and native_count == source.get("native_source_file_count")
            ),
            "tracked_product_source_exact": (
                product_fingerprint
                == str(source.get("product_source_fingerprint_sha256", "")).upper()
                and product_count == source.get("product_source_file_count")
                and product_bytes == source.get("product_source_bytes")
                and bool(frozen_product_checks)
                and all(frozen_product_checks.values())
            ),
            "fresh_default_build_and_ctest_exact": _build_matches(default_build),
            "fresh_compensation_on_build_and_ctest_exact": _build_matches(
                candidate_build
            ),
            "default_cache_all_private_flags_off": (
                _mapping(default_build.get("capability_flags"))
                == expected_default_flags
                and actual_default_flags == expected_default_flags
            ),
            "live_cache_only_compensation_candidate_on": (
                _mapping(candidate_build.get("capability_flags"))
                == expected_candidate_flags
                and actual_candidate_flags == expected_candidate_flags
            ),
            "default_and_candidate_semantics_not_conflated": (
                boundary.get("default_build_production_advertised") is False
                and boundary.get("default_build_provider_advertised") is False
                and boundary.get("live_build_candidate_only") is True
                and boundary.get("live_build_production_advertised") is False
                and boundary.get("live_build_provider_advertised") is True
                and boundary.get("candidate_flag") == COMPENSATION_FLAG
                and boundary.get("candidate_flag_is_default") is False
            ),
            "descriptor_candidate_gate_is_source_bound": (
                COMPENSATION_FLAG
                in (source_root / "ck3_autonomous_player/native_bridge/CMakeLists.txt").read_text(
                    encoding="utf-8-sig"
                )
                and "#if defined(" + COMPENSATION_FLAG + ")"
                in (source_root / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp").read_text(
                    encoding="utf-8-sig"
                )
                and "kZhongguoPromotionCompensationPostconditionV1Capability"
                in (source_root / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp").read_text(
                    encoding="utf-8-sig"
                )
            ),
            "previous_candidate_superseded_fail_closed": (
                supersession.get("candidate_commit") == PREVIOUS_CANDIDATE_COMMIT
                and supersession.get("manifest_path") == PREVIOUS_MANIFEST_RELATIVE
                and supersession.get("manifest_sha256") == PREVIOUS_MANIFEST_SHA256
                and _sha256(previous_path) == PREVIOUS_MANIFEST_SHA256
                and supersession.get("old_candidate_result_on_current_source") == "RED"
                and supersession.get("old_failed_checks")
                == list(EXPECTED_PREVIOUS_FAILURES)
                and previous_report.get("result") == "RED"
                and previous_report.get("failed_checks")
                == list(EXPECTED_PREVIOUS_FAILURES)
            ),
            "product_generators_and_static_validation_green": (
                _mapping(manifest.get("product_validation"))
                == {
                    "validate_local": "GREEN",
                    "feedback_promotion_pip_generator_check": "GREEN",
                    "compensation_generator_check": "GREEN",
                    "phase2_central_runtime_generator_check": "GREEN",
                }
            ),
            "single_future_command_uses_candidate_only_build": (
                command.get("authorized_command_count") == 1
                and command.get("runner_owns_ck3_lifecycle") is True
                and argv == _expected_live_argv(manifest, candidate_build)
                and (
                    Path(str(command.get("execution_source_root", "")))
                    / "tools/run_zhongguo_acceptance.py"
                ).is_file()
                and _sha256(
                    Path(str(command.get("execution_source_root", "")))
                    / "tools/run_zhongguo_acceptance.py"
                )
                == str(
                    _mapping(source.get("frozen_files")).get(
                        "tools/run_zhongguo_acceptance.py", ""
                    )
                ).upper()
                and re.fullmatch(
                    r"\\\\\.\\pipe\\xar_ck3_bridge_zg361_[0-9a-f]{32}", pipe
                )
                is not None
                and attempt.get("status") == "absent"
                and attempt.get("started") is False
                and attempt.get("consumed") is False
                and not attempt_path.exists()
            ),
        }
    )
    failed = [name for name, passed in checks.items() if passed is not True]
    report.update(
        {
            "schema_version": 4,
            "kind": "zg361_promotion_source_product_native_no_launch_preflight",
            "candidate_commit": CURRENT_CANDIDATE_COMMIT,
            "result": "READY_TO_SERIAL_LIVE" if not failed else "RED",
            "readiness": "static-ready-live-pending" if not failed else "research",
            "checks": checks,
            "failed_checks": failed,
            "product_source_fingerprint_sha256": product_fingerprint,
            "product_source_file_count": product_count,
            "product_source_bytes": product_bytes,
            "native_source_fingerprint_sha256": native_fingerprint,
            "native_source_file_count": native_count,
            "default_capability_flags": actual_default_flags,
            "live_candidate_capability_flags": actual_candidate_flags,
            "frozen_product_file_checks": frozen_product_checks,
            "authorized_live_argv": argv,
            "attempt_id": attempt.get("attempt_id"),
            "attempt_path": str(attempt_path),
            "superseded_candidate_commit": PREVIOUS_CANDIDATE_COMMIT,
            "superseded_failed_checks": previous_report.get("failed_checks"),
            "ck3_started": False,
            "live_proof_claimed": False,
            "production_advertisement_ready": False,
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = verify_product_native_no_launch_candidate(
        args.manifest.resolve(), source_root=args.source_root.resolve()
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.check and report["result"] != "READY_TO_SERIAL_LIVE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
