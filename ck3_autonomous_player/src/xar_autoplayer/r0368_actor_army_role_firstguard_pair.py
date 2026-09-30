"""Read the separately frozen native pair that enables the existing queued ROLE wake.

This admission uses explicit manifest byte pins. The original role pair and its
173-case receipt remain historical inputs to the original entry.
"""
from __future__ import annotations

from pathlib import Path
import re

from . import r0368_actor_army_role_operator as original_role
from .errors import AgentError


NATIVE_SOURCE_COMMIT = "aef7ed46f5da8d734be05db9bcca5196e2d02bf2"
BRIDGE_SOURCE_SHA256 = "A6B3BB697C5CB20B49282BEDC7FECB0C5571259610E0D1F908C61E7C9CCB79F0"
NATIVE_SOURCE_FINGERPRINT_SHA256 = "FAA9804DC2CE222F2871FDC846966093BB3E460391274A71F73AE2B37ED465E0"
CK3_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
PAIR_SCHEMA = "xar.war.r0368.release-pair-queued-wake-static.v1"
CANDIDATE_SCHEMA = "xar.war.r0368.release-pair-queued-wake-candidate.v1"
_SHA = re.compile(r"[0-9A-Fa-f]{64}")
_RAW_NAMES = (
    "xar_checkpoint.ck3", "driver-state.json",
    "player-child-matrilineal-formal-v1.json",
)
_PAIR_NAMES = {"xar_ck3_bridge.dll": "dll",
               "xar_ck3_bridge_injector.exe": "injector"}


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise AgentError(f"R0368 {label} SHA-256 is missing or malformed")
    return value.upper()


def _file_row(row: object, *, size_key: str, label: str) -> dict[str, object]:
    if not isinstance(row, dict) or not isinstance(row.get("path"), str):
        raise AgentError(f"R0368 {label} file row is malformed")
    size = row.get(size_key)
    if type(size) is not int or size <= 0:
        raise AgentError(f"R0368 {label} size is malformed")
    path = Path(row["path"])
    digest = _digest(row.get("sha256"), label)
    if path.stat().st_size != size or original_role._sha256(path) != digest:
        raise AgentError(f"R0368 {label} bytes differ from the pinned manifest")
    return {"path": str(path), "bytes": size, "sha256": digest}


def verify_firstguard_source_pair(
    *, candidate_manifest: Path, release_pair_manifest: Path, checkout: Path,
    expected_candidate_sha256: str, expected_release_pair_sha256: str,
) -> dict[str, object]:
    """Rehash new native bytes and the unchanged H3937 source without launch."""
    if original_role.ROLE_ONLY_LIVE_AUTHORIZED:
        raise AgentError("R0368 source admission requires the live query gate closed")
    candidate_sha = original_role._sha256(candidate_manifest)
    pair_sha = original_role._sha256(release_pair_manifest)
    if (candidate_sha != _digest(expected_candidate_sha256, "expected candidate")
            or pair_sha != _digest(expected_release_pair_sha256, "expected pair")):
        raise AgentError("R0368 new candidate or native pair manifest bytes changed")
    candidate = original_role._read_json(candidate_manifest)
    pair = original_role._read_json(release_pair_manifest)
    if (candidate.get("schema") != CANDIDATE_SCHEMA
            or candidate.get("status") != "SOURCE_BYTES_READY_SAME_FRAME_PENDING"
            or candidate.get("candidate_head") != NATIVE_SOURCE_COMMIT
            or _digest(candidate.get("source_fingerprint_sha256"), "candidate source fingerprint")
            != NATIVE_SOURCE_FINGERPRINT_SHA256
            or _digest(candidate.get("source_bridge_cpp_sha256"), "candidate bridge source")
            != BRIDGE_SOURCE_SHA256
            or _digest(candidate.get("pair_manifest_sha256"), "candidate pair") != pair_sha
            or Path(str(candidate.get("pair_manifest_path"))).resolve()
            != release_pair_manifest.resolve()
            or candidate.get("candidate_army_id_is_current_same_frame") is not False
            or candidate.get("native_revision") is not None
            or candidate.get("public_army_row") is not None
            or candidate.get("allied_army_row") is not None
            or candidate.get("operator_enabled") is not False
            or candidate.get("candidate_episode_run_id") != "native-29829-2bc2d599f7f9"
            or candidate.get("candidate_actor_character_id") != 29829
            or candidate.get("candidate_war_id") != 16777231
            or candidate.get("candidate_army_id") != 83886367
            or pair.get("schema") != PAIR_SCHEMA
            or pair.get("status") != "STATIC_GREEN_LIVE_PENDING"
            or pair.get("source_commit") != NATIVE_SOURCE_COMMIT
            or pair.get("configuration") != "Release"
            or pair.get("cmake_option")
            != "XAR_CK3_ENABLE_WAR_ACTOR_ARMY_ROLE_PRIVATE_V1=ON"
            or _digest(pair.get("source_bridge_cpp_sha256"), "bridge source")
            != BRIDGE_SOURCE_SHA256):
        raise AgentError("R0368 new native source pair contract differs")
    if _digest(pair.get("source_fingerprint_sha256"), "native source fingerprint") != NATIVE_SOURCE_FINGERPRINT_SHA256:
        raise AgentError("R0368 queued wake native source fingerprint differs")
    ctest = pair.get("ctest")
    expected_ctest = {
        "junit_tests": 1, "junit_failures": 0, "junit_skipped": 0,
        "focused_total": 1, "focused_passed": 1,
        "focused_test_name": "xar_ck3_actor_army_role_source_gate_v1",
        "exit_code": 0,
    }
    if not isinstance(ctest, dict) or any(
        ctest.get(key) != value for key, value in expected_ctest.items()
    ):
        raise AgentError("R0368 new native pair lacks its focused 1/1 source gate")
    files = candidate.get("files")
    if not isinstance(files, dict) or set(files) != set(_RAW_NAMES) | set(_PAIR_NAMES):
        raise AgentError("R0368 new candidate asset set differs")
    actual: dict[str, dict[str, object]] = {}
    for name in _RAW_NAMES:
        row = _file_row(files[name], size_key="bytes", label=name)
        if row["sha256"] != original_role._ASSET_SHA256[name]:
            raise AgentError(f"R0368 historical source bytes changed: {name}")
        actual[name] = row
    for name, key in _PAIR_NAMES.items():
        release_row = _file_row(pair.get(key), size_key="size_bytes", label=key)
        candidate_row = _file_row(files[name], size_key="bytes", label=name)
        if (release_row["bytes"] != candidate_row["bytes"]
                or release_row["sha256"] != candidate_row["sha256"]):
            raise AgentError(f"R0368 new native pair differs from candidate copy: {name}")
        actual[name] = candidate_row
    exe = pair.get("ck3_executable")
    exe_row = _file_row(exe, size_key="size_bytes", label="CK3 executable")
    if exe.get("launched") is not False or exe_row["sha256"] != CK3_EXE_SHA256:
        raise AgentError("R0368 exact CK3 executable identity differs")
    root = checkout.resolve()
    head = original_role._git(root, "rev-parse", "HEAD")
    if original_role._git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AgentError("R0368 native source checkout is dirty")
    if original_role._git(root, "diff", "--name-only", NATIVE_SOURCE_COMMIT, head,
                          "--", *original_role._NATIVE_PATHS):
        raise AgentError("R0368 native source differs from the new frozen pair")
    bridge_source = root / "ck3_autonomous_player/native_bridge/src/bridge.cpp"
    if original_role._sha256(bridge_source) != BRIDGE_SOURCE_SHA256:
        raise AgentError("R0368 first-guard bridge source bytes differ")
    return {
        "schema": "xar.war.r0368.role-queued-wake-no-launch.v1",
        "status": "SOURCE_BYTES_READY_SAME_FRAME_PENDING",
        "candidate_manifest_sha256": candidate_sha,
        "release_pair_manifest_sha256": pair_sha,
        "checkout_head": head,
        "release_native_source_commit": NATIVE_SOURCE_COMMIT,
        "exact_ck3_exe_sha256": exe_row["sha256"],
        "assets": actual,
        "candidate_episode_run_id": candidate["candidate_episode_run_id"],
        "candidate_actor_character_id": candidate["candidate_actor_character_id"],
        "candidate_war_id": candidate["candidate_war_id"],
        "candidate_army_id": candidate["candidate_army_id"],
        "current_paused_frame": None, "operator_enabled": False,
        "screen_acquired": False, "ck3_started": False, "query_attempts": 0,
        "gameplay_actions": 0, "date_advance_actions": 0,
        "native_source_gate_tests_this_pair": 1,
    }
