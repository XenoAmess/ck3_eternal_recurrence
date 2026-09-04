#!/usr/bin/env python3
"""Verify a frozen career-HC/workforce provider candidate without CK3 launch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY = (
    "game.command.query-zhongguo-career-hc-workforce-postcondition-v1"
)
PRIVATE_SWITCH = (
    "XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1"
)
EXPECTED_BASE_COMMIT = "ce458af71a2a44decc085766720082a8b724edb8"
EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _native_source_fingerprint(root: Path) -> str:
    native = root / "ck3_autonomous_player/native_bridge"
    files = [native / "CMakeLists.txt"]
    for tree in (native / "include", native / "src"):
        files.extend(
            path
            for path in tree.rglob("*")
            if path.is_file() and path.suffix in {".cpp", ".hpp", ".h", ".c"}
        )
    lines = []
    for path in sorted(files, key=lambda item: str(item.resolve()).lower()):
        # Match build_fresh.ps1 byte-for-byte on Windows: its source-relative
        # fingerprint uses native backslash separators.
        relative = str(path.relative_to(native))
        lines.append(f"{relative}\0{_sha256(path)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest().upper()


def verify_career_hc_workforce_no_launch_candidate(
    manifest_path: Path,
    *,
    source_root: Path = ROOT,
) -> dict[str, object]:
    """Return a deterministic, read-only report for one frozen candidate."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = _mapping(manifest.get("source"))
    build = _mapping(manifest.get("build"))
    attempt = _mapping(manifest.get("live_attempt"))
    bridge = _mapping(build.get("bridge"))
    injector = _mapping(build.get("injector"))
    frozen_files = _mapping(source.get("frozen_files"))

    native = source_root / "ck3_autonomous_player/native_bridge"
    cmake_path = native / "CMakeLists.txt"
    adapter_path = native / "src/ck3_11906_adapter.cpp"
    abi_path = native / "research/zhongguo_career_hc_workforce_postcondition_v1_abi.json"
    source_contract_path = native / (
        "research/fixtures/"
        "zhongguo_career_hc_workforce_postcondition_v1_source_contract.json"
    )
    route_contract_path = source_root / (
        "tools/zg361_phase2_hc_workforce_route_b_checkpoint_contract.json"
    )

    cmake = cmake_path.read_text(encoding="utf-8")
    adapter = adapter_path.read_text(encoding="utf-8")
    abi = json.loads(abi_path.read_text(encoding="utf-8"))
    source_contract = json.loads(source_contract_path.read_text(encoding="utf-8"))
    route_contract = json.loads(route_contract_path.read_text(encoding="utf-8"))

    cache_path = Path(str(build.get("cmake_cache_path", "")))
    bridge_path = Path(str(bridge.get("path", "")))
    injector_path = Path(str(injector.get("path", "")))
    exe_path = Path(str(manifest.get("ck3_executable_path", "")))
    attempt_path = Path(str(attempt.get("path", "")))
    cache = cache_path.read_text(encoding="utf-8", errors="replace") if (
        cache_path.is_file()
    ) else ""

    option_match = re.search(
        rf"option\(\s*{PRIVATE_SWITCH}\s*.*?\s+OFF\s*\)",
        cmake,
        re.DOTALL,
    )
    guarded_capability = re.search(
        rf"#if defined\({PRIVATE_SWITCH}\).*?"
        r"kZhongguoCareerHcWorkforcePostconditionV1Capability.*?#endif",
        adapter,
        re.DOTALL,
    )
    default_adapter = re.sub(
        rf"#if defined\({PRIVATE_SWITCH}\).*?#endif",
        "",
        adapter,
        flags=re.DOTALL,
    )

    frozen_file_checks: dict[str, bool] = {}
    for relative, expected in frozen_files.items():
        path = source_root / str(relative)
        frozen_file_checks[str(relative)] = (
            path.is_file()
            and isinstance(expected, str)
            and _sha256(path) == expected.upper()
        )

    private_candidate = _mapping(abi.get("private_candidate"))
    route = _mapping(route_contract.get("route"))
    postcondition = _mapping(route_contract.get("postcondition_contract"))
    runner = _mapping(route_contract.get("existing_runner_seam"))
    capability_counts = _mapping(source_contract.get("adapter_capability_counts"))
    checks = {
        "manifest_identity": (
            manifest.get("schema_version") == 1
            and manifest.get("kind")
            == "zg361_career_hc_workforce_no_launch_candidate"
            and manifest.get("readiness") == "static-ready-live-pending"
        ),
        "base_commit_exact": source.get("base_commit") == EXPECTED_BASE_COMMIT,
        "candidate_commit_pinned": bool(
            re.fullmatch(r"[0-9a-f]{40}", str(source.get("candidate_commit", "")))
        ),
        "frozen_source_files_match": bool(frozen_file_checks)
        and all(frozen_file_checks.values()),
        "native_source_fingerprint_matches": (
            _native_source_fingerprint(source_root)
            == str(source.get("native_source_fingerprint_sha256", "")).upper()
        ),
        "private_switch_default_off": option_match is not None,
        "private_capability_guarded": guarded_capability is not None,
        "default_projection_withholds_capability": CAPABILITY not in default_adapter,
        "candidate_cache_opted_in": f"{PRIVATE_SWITCH}:BOOL=ON" in cache,
        "candidate_cache_binds_exact_executable": (
            f"XAR_CK3_EXECUTABLE_PATH:FILEPATH={exe_path.as_posix()}" in cache
            or f"XAR_CK3_EXECUTABLE_PATH:FILEPATH={exe_path}" in cache
        ),
        "candidate_cache_hash_matches": cache_path.is_file()
        and _sha256(cache_path) == str(build.get("cmake_cache_sha256", "")).upper(),
        "paired_bridge_hash_matches": (
            bridge_path.is_file()
            and bridge_path.name == "xar_ck3_bridge.dll"
            and bridge_path.stat().st_size == bridge.get("bytes")
            and _sha256(bridge_path) == str(bridge.get("sha256", "")).upper()
        ),
        "paired_injector_hash_matches": (
            injector_path.is_file()
            and injector_path.name == "xar_ck3_bridge_injector.exe"
            and injector_path.stat().st_size == injector.get("bytes")
            and _sha256(injector_path) == str(injector.get("sha256", "")).upper()
        ),
        "exact_ck3_executable_matches": exe_path.is_file()
        and _sha256(exe_path) == EXPECTED_EXE_SHA256,
        "abi_remains_not_live": (
            abi.get("status") == "static_and_fixture_ready_not_live"
            and private_candidate.get("cmake_switch") == PRIVATE_SWITCH
            and private_candidate.get("default") is False
            and private_candidate.get("production_advertisement_promoted") is False
        ),
        "source_contract_counts_current": (
            source_contract.get("allowlist_count") == 14
            and source_contract.get("mailbox_fixed_slot_index") == 26
            and capability_counts.get("default") == 76
            and capability_counts.get("both_private_candidates") == 78
            and source_contract.get("private_candidate_switch") == PRIVATE_SWITCH
            and source_contract.get("private_candidate_default") is False
        ),
        "b4_route_b_interface_exact": (
            route
            == {
                "event_definition_key": "zg361we.360",
                "route": "B",
                "native_option_index": 1,
                "option_number": 2,
            }
            and postcondition.get("required_fact_count") == 8
            and postcondition.get("provider_seal_scope")
            == "m360_current_cycle_route_b"
            and postcondition.get("m361_charter_required") is False
            and postcondition.get("action_ack_is_business_postcondition") is False
            and postcondition.get("career_hc_capability") == CAPABILITY
            and postcondition.get("same_paused_revision_join_required") is True
            and runner.get("formal_registry_modified") is False
        ),
        "formal_runner_not_modified": manifest.get(
            "formal_runner_registry_modified"
        ) is False and not any(
            "run_zhongguo_acceptance.py" in str(path) for path in frozen_files
        ),
        "future_live_attempt_unique_and_absent": (
            attempt.get("status") == "absent"
            and attempt.get("started") is False
            and attempt.get("consumed") is False
            and isinstance(attempt.get("attempt_id"), str)
            and bool(attempt.get("attempt_id"))
            and bool(str(attempt_path))
            and not attempt_path.exists()
        ),
        "no_live_or_ack_claim": (
            manifest.get("ck3_started") is False
            and manifest.get("live_proof_claimed") is False
            and manifest.get("action_ack_is_business_postcondition") is False
            and manifest.get("production_advertisement_ready") is False
        ),
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_career_hc_workforce_no_launch_candidate_preflight",
        "result": "READY_TO_LIVE" if not failed else "RED",
        "readiness": "static-ready-live-pending" if not failed else "research",
        "checks": checks,
        "frozen_file_checks": frozen_file_checks,
        "failed_checks": failed,
        "bridge_sha256": _sha256(bridge_path) if bridge_path.is_file() else None,
        "injector_sha256": (
            _sha256(injector_path) if injector_path.is_file() else None
        ),
        "attempt_id": attempt.get("attempt_id"),
        "attempt_path": str(attempt_path),
        "ck3_started": False,
        "live_proof_claimed": False,
        "production_advertisement_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = verify_career_hc_workforce_no_launch_candidate(
        args.manifest.resolve(), source_root=args.source_root.resolve()
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.check and report["result"] != "READY_TO_LIVE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
