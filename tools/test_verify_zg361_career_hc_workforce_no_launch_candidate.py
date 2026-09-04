from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from verify_zg361_career_hc_workforce_no_launch_candidate import (  # noqa: E402
    CAPABILITY,
    EXPECTED_BASE_COMMIT,
    PRIVATE_SWITCH,
    _native_source_fingerprint,
    verify_career_hc_workforce_no_launch_candidate,
)


def _write(path: Path, value: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode("utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "source"
    native = root / "ck3_autonomous_player/native_bridge"
    cmake = native / "CMakeLists.txt"
    adapter = native / "src/ck3_11906_adapter.cpp"
    abi = native / "research/zhongguo_career_hc_workforce_postcondition_v1_abi.json"
    source_contract = native / (
        "research/fixtures/"
        "zhongguo_career_hc_workforce_postcondition_v1_source_contract.json"
    )
    route_contract = root / (
        "tools/zg361_phase2_hc_workforce_route_b_checkpoint_contract.json"
    )
    _write(cmake, f"option(\n  {PRIVATE_SWITCH}\n  candidate\n  OFF\n)\n")
    _write(
        adapter,
        f"#if defined({PRIVATE_SWITCH})\n"
        "kZhongguoCareerHcWorkforcePostconditionV1Capability\n#endif\n",
    )
    _write(
        abi,
        json.dumps({
            "status": "static_and_fixture_ready_not_live",
            "private_candidate": {
                "cmake_switch": PRIVATE_SWITCH,
                "default": False,
                "production_advertisement_promoted": False,
            },
        }),
    )
    _write(
        source_contract,
        json.dumps({
            "allowlist_count": 14,
            "mailbox_fixed_slot_index": 26,
            "adapter_capability_counts": {
                "default": 76,
                "both_private_candidates": 78,
            },
            "private_candidate_switch": PRIVATE_SWITCH,
            "private_candidate_default": False,
        }),
    )
    _write(
        route_contract,
        json.dumps({
            "route": {
                "event_definition_key": "zg361we.360",
                "route": "B",
                "native_option_index": 1,
                "option_number": 2,
            },
            "postcondition_contract": {
                "required_fact_count": 8,
                "provider_seal_scope": "m360_current_cycle_route_b",
                "m361_charter_required": False,
                "action_ack_is_business_postcondition": False,
                "career_hc_capability": CAPABILITY,
                "same_paused_revision_join_required": True,
            },
            "existing_runner_seam": {"formal_registry_modified": False},
        }),
    )
    header = native / "include/fixture.hpp"
    _write(header, "#pragma once\n")
    bridge = tmp_path / "build/xar_ck3_bridge.dll"
    injector = tmp_path / "build/xar_ck3_bridge_injector.exe"
    cache = tmp_path / "build/CMakeCache.txt"
    exe = tmp_path / "ck3.exe"
    _write(bridge, b"bridge")
    _write(injector, b"injector")
    _write(
        cache,
        f"{PRIVATE_SWITCH}:BOOL=ON\n"
        f"XAR_CK3_EXECUTABLE_PATH:FILEPATH={exe.as_posix()}\n",
    )
    _write(exe, b"fixture-exe")
    frozen = {
        cmake.relative_to(root).as_posix(): _sha(cmake),
        adapter.relative_to(root).as_posix(): _sha(adapter),
    }
    manifest = tmp_path / "manifest.json"
    _write(
        manifest,
        json.dumps({
            "schema_version": 1,
            "kind": "zg361_career_hc_workforce_no_launch_candidate",
            "readiness": "static-ready-live-pending",
            "source": {
                "base_commit": EXPECTED_BASE_COMMIT,
                "candidate_commit": "1" * 40,
                "native_source_fingerprint_sha256": _native_source_fingerprint(root),
                "frozen_files": frozen,
            },
            "build": {
                "bridge": {
                    "path": str(bridge),
                    "sha256": _sha(bridge),
                    "bytes": bridge.stat().st_size,
                },
                "injector": {
                    "path": str(injector),
                    "sha256": _sha(injector),
                    "bytes": injector.stat().st_size,
                },
                "cmake_cache_path": str(cache),
                "cmake_cache_sha256": _sha(cache),
            },
            "ck3_executable_path": str(exe),
            "live_attempt": {
                "attempt_id": "fixture-absent-attempt",
                "path": str(tmp_path / "absent"),
                "status": "absent",
                "started": False,
                "consumed": False,
            },
            "formal_runner_registry_modified": False,
            "ck3_started": False,
            "live_proof_claimed": False,
            "action_ack_is_business_postcondition": False,
            "production_advertisement_ready": False,
        }),
    )
    return manifest, root


def test_candidate_verifier_is_ready_and_does_not_create_attempt(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest, root = _fixture(tmp_path)
    monkeypatch.setattr(
        "verify_zg361_career_hc_workforce_no_launch_candidate.EXPECTED_EXE_SHA256",
        _sha(tmp_path / "ck3.exe"),
    )
    report = verify_career_hc_workforce_no_launch_candidate(
        manifest, source_root=root
    )
    assert report["result"] == "READY_TO_LIVE"
    assert report["ck3_started"] is False
    assert not (tmp_path / "absent").exists()


def test_candidate_verifier_rejects_hash_drift_and_ack_claim(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest, root = _fixture(tmp_path)
    monkeypatch.setattr(
        "verify_zg361_career_hc_workforce_no_launch_candidate.EXPECTED_EXE_SHA256",
        _sha(tmp_path / "ck3.exe"),
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["action_ack_is_business_postcondition"] = True
    _write(manifest, json.dumps(payload))
    _write(root / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp", "drift")
    report = verify_career_hc_workforce_no_launch_candidate(
        manifest, source_root=root
    )
    assert report["result"] == "RED"
    assert "frozen_source_files_match" in report["failed_checks"]
    assert "native_source_fingerprint_matches" in report["failed_checks"]
    assert "no_live_or_ack_claim" in report["failed_checks"]
