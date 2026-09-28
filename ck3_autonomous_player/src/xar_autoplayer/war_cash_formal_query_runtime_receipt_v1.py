"""Fail-closed managed receipt for a formally selected war-options query.

The receipt records an executed read-only query and exact runtime bindings.
It is not a cash quote or a binary read-only audit.  No recipient may promote
it to a zero-fee observation without separate pair and DLL review.
"""

from __future__ import annotations

from collections.abc import Mapping
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re

from .m5_observed_opportunity_selector import observed_frame
from .war_cash_termination_query_zero_fee_v1 import EXE_SHA256


SCHEMA = "xar.ck3.war-cash-query-managed-session.v1"
STEP = "query-war-termination-options-16777231"
WAR_ID = 16777231


def _blocked(reason: str) -> dict[str, object]:
    return {
        "schema": SCHEMA, "status": "blocked", "missing_reasons": [reason],
        "formal_cash_receipt_eligible": False,
        "immediate_war_action_cost_raw": None,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _treasury_raw(snapshot: Mapping[str, object]) -> int | None:
    gold = snapshot.get("played_character_gold")
    if (type(gold) is not dict or set(gold) != {"raw", "scale"}
            or type(gold.get("raw")) is not int
            or not -(2**63) <= gold["raw"] <= 2**63 - 1
            or type(gold.get("scale")) is not int
            or gold["scale"] != 100_000):
        return None
    return gold["raw"]


def _driver_state_bytes_and_binding(path: Path) -> tuple[str, dict[str, object]]:
    """Hash and parse the same bounded, opened driver-state bytes."""
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if before.st_size < 1 or before.st_size > 128 * 1024 * 1024:
            raise ValueError("driver state outside bounded receipt size")
        payload = stream.read(128 * 1024 * 1024 + 1)
        after = os.fstat(stream.fileno())
    current = path.stat()
    if (len(payload) != before.st_size
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or current.st_size != after.st_size
            or current.st_mtime_ns != after.st_mtime_ns
            or (current.st_dev, current.st_ino)
            != (after.st_dev, after.st_ino)
            or len(payload) > 128 * 1024 * 1024):
        raise ValueError("driver state changed during receipt read")

    def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("driver state has duplicate JSON key")
            result[key] = value
        return result

    state = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_pairs)
    if not isinstance(state, dict):
        raise ValueError("driver state is not a JSON object")
    return hashlib.sha256(payload).hexdigest().upper(), {
        "bridge_pid": state.get("bridge_pid"),
        "episode_character_id": state.get("episode_character_id"),
        "episode_run_id": state.get("episode_run_id"),
    }


def _created_filetime(pid: int) -> int:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [
        ctypes.POINTER(wintypes.FILETIME)
    ] * 4
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), "OpenProcess failed")
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel32.GetProcessTimes(
            handle, *(ctypes.byref(value) for value in times)
        ):
            raise OSError(ctypes.get_last_error(), "GetProcessTimes failed")
        value = times[0]
        return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)
    finally:
        kernel32.CloseHandle(handle)


def capture_query_process_binding(
    *, pid: int, game_exe: Path, native_dll: Path,
    injector: Path, driver_state: Path,
) -> dict[str, object]:
    """Read one live CK3 process and files; never attach a write handle."""
    if os.name != "nt" or type(pid) is not int or pid <= 0:
        return _blocked("windows_live_process_identity_unavailable")
    try:
        import psutil

        process = psutil.Process(pid)
        created = _created_filetime(pid)
        if created <= 0 or not process.is_running():
            return _blocked("process_creation_or_liveness_unproven")
        actual_exe = Path(process.exe()).resolve(strict=True)
        expected_exe = game_exe.resolve(strict=True)
        expected_dll = native_dll.resolve(strict=True)
        if (os.path.normcase(str(actual_exe)) != os.path.normcase(str(expected_exe))
                or actual_exe.name.casefold() != "ck3.exe"):
            return _blocked("running_exe_path_mismatch")
        loaded_dlls = {
            os.path.normcase(str(Path(mapping.path).resolve(strict=True)))
            for mapping in process.memory_maps(grouped=False)
            if Path(mapping.path).name.casefold() == expected_dll.name.casefold()
        }
        if loaded_dlls != {os.path.normcase(str(expected_dll))}:
            return _blocked("loaded_native_dll_path_not_unique_or_mismatch")
        driver_state_path = driver_state.resolve(strict=True)
        driver_sha, driver_binding = _driver_state_bytes_and_binding(
            driver_state_path
        )
        hashes = {
            "game_exe_sha256": _sha256_file(actual_exe),
            "native_dll_sha256": _sha256_file(expected_dll),
            "launch_injector_sha256": _sha256_file(injector.resolve(strict=True)),
            "driver_state_sha256": driver_sha,
        }
        if hashes["game_exe_sha256"] != EXE_SHA256:
            return _blocked("exact_game_exe_sha256_mismatch")
        if _created_filetime(pid) != created or not process.is_running():
            return _blocked("process_changed_during_binary_read")
        return {
            "schema": "xar.ck3.war-cash-query-process-binding.v1",
            "status": "read_only_process_and_files_sampled",
            "process_pid": pid, "process_created_filetime": created,
            "game_exe_path": str(actual_exe),
            "native_dll_path": str(expected_dll),
            "injector_path": str(injector.resolve(strict=True)),
            "driver_state_path": str(driver_state_path),
            "driver_state_binding": driver_binding,
            **hashes,
        }
    except Exception as error:
        return _blocked(f"process_module_or_file_read_failed:{type(error).__name__}")


def build_formal_query_session_receipt(
    *, before: Mapping[str, object], after: Mapping[str, object],
    outcome: Mapping[str, object], wire: object,
    process_before: Mapping[str, object], process_after: Mapping[str, object],
    gameplay_submits_before: int, gameplay_submits_after: int,
    source_commit: str, paired_prelaunch_driver_state_sha256: str,
) -> dict[str, object]:
    """Bind only a real auto_turn selected query to the same paused frame."""
    try:
        frame_before = observed_frame(before)
        frame_after = observed_frame(after)
    except (TypeError, ValueError, KeyError):
        return _blocked("six_field_native_frame_invalid")
    if (frame_before != frame_after
            or before.get("paused") is not True
            or after.get("paused") is not True
            or before.get("map_ready") is not True
            or after.get("map_ready") is not True):
        return _blocked("same_ready_paused_frame_unproven")
    treasury_before_raw = _treasury_raw(before)
    treasury_after_raw = _treasury_raw(after)
    if (treasury_before_raw is None
            or treasury_after_raw != treasury_before_raw):
        return _blocked("same_paused_treasury_unproven")
    for snapshot in (before, after):
        wars = snapshot.get("active_wars")
        if (not isinstance(wars, list) or len(wars) != 1
                or not isinstance(wars[0], Mapping)
                or type(wars[0].get("war_id")) is not int
                or wars[0]["war_id"] != WAR_ID):
            return _blocked("unique_active_war_unproven")
    plan = outcome.get("plan")
    expected_command = {
        "kind": "read_only_query", "war_id": WAR_ID,
        "query_name": "war_termination_options",
    }
    if (outcome.get("status") != "executed"
            or outcome.get("selected_step") != STEP
            or outcome.get("snapshot_id") != frame_before["snapshot_id"]
            or type(outcome.get("revision")) is not int
            or outcome["revision"] != frame_before["revision"]
            or not isinstance(plan, Mapping)
            or plan.get("policy") != "one-life-turn-v1"
            or plan.get("selected_step") != STEP
            or plan.get("priced_command") != expected_command
            or type(plan.get("priced_command")) is not dict):
        return _blocked("actual_auto_turn_selected_typed_query_unproven")
    if (not isinstance(wire, Mapping)
            or not isinstance(wire.get("request"), Mapping)
            or not isinstance(wire.get("response_envelope"), Mapping)
            or not isinstance(wire.get("before"), Mapping)
            or not isinstance(wire.get("after"), Mapping)):
        return _blocked("exact_query_protocol_objects_missing")
    request = wire["request"]
    envelope = wire["response_envelope"]
    for name in ("before", "after"):
        projected = wire[name]
        if (any(projected.get(key) != frame_before[key] for key in frame_before)
                or projected.get("paused") is not True
                or projected.get("map_ready") is not True
                or projected.get("active_war_ids") != [WAR_ID]
                or projected.get("played_character_gold") != {
                    "raw": treasury_before_raw, "scale": 100_000,
                }):
            return _blocked(f"driver_inner_{name}_frame_mismatch")
    if (type(request.get("protocol_version")) is not int
            or request["protocol_version"] != 1
            or type(envelope.get("protocol_version")) is not int
            or envelope["protocol_version"] != 1
            or request.get("type") != "execute_step"
            or request.get("step") != STEP
            or type(request.get("expected_revision")) is not int
            or request["expected_revision"] != frame_before["native_revision"]
            or type(request.get("request_id")) is not str
            or not request["request_id"]
            or envelope.get("type") != "command_result"
            or envelope.get("request_id") != request["request_id"]
            or envelope.get("ok") is not True):
        return _blocked("query_request_or_native_envelope_mismatch")
    native_result = envelope.get("result")
    result = outcome.get("result")
    if (not isinstance(native_result, Mapping)
            or not isinstance(result, Mapping)
            or native_result.get("step") != STEP
            or native_result.get("accepted") is not True
            or native_result.get("status") != "available"
            or type(native_result.get("query_sequence")) is not int
            or native_result["query_sequence"] <= 0
            or result.get("step") != STEP
            or result.get("backend_id") != "native-headless"
            or result.get("accepted") is not True
            or result.get("status") != "available"
            or result.get("query_sequence") != native_result["query_sequence"]
            or not isinstance(result.get("war_termination_options"), Mapping)
            or result["war_termination_options"].get("war_id") != WAR_ID
            or not isinstance(native_result.get("war_termination_options"), Mapping)
            or native_result["war_termination_options"].get("war_id") != WAR_ID):
        return _blocked("query_result_or_war_id_mismatch")
    if (type(gameplay_submits_before) is not int
            or type(gameplay_submits_after) is not int
            or gameplay_submits_before < 0
            or gameplay_submits_after != gameplay_submits_before):
        return _blocked("runner_gameplay_submit_count_changed_or_unknown")
    if (type(source_commit) is not str
            or re.fullmatch(r"[0-9a-fA-F]{40}", source_commit) is None):
        return _blocked("source_commit_identity_invalid")
    if (type(paired_prelaunch_driver_state_sha256) is not str
            or re.fullmatch(r"[0-9A-Fa-f]{64}",
                            paired_prelaunch_driver_state_sha256) is None):
        return _blocked("prelaunch_pair_driver_state_identity_invalid")
    if (not isinstance(process_before, Mapping)
            or not isinstance(process_after, Mapping)):
        return _blocked("process_module_samples_unavailable")
    if (process_before.get("status") != "read_only_process_and_files_sampled"
            or process_after.get("status") != "read_only_process_and_files_sampled"):
        return _blocked("process_module_samples_unavailable")
    for key in (
        "process_pid", "process_created_filetime", "game_exe_path",
        "native_dll_path", "injector_path", "game_exe_sha256",
        "native_dll_sha256", "launch_injector_sha256",
    ):
        if process_before.get(key) != process_after.get(key):
            return _blocked(f"process_or_module_changed:{key}")
    if (type(process_before.get("process_pid")) is not int
            or process_before["process_pid"] <= 0
            or type(process_before.get("process_created_filetime")) is not int
            or process_before["process_created_filetime"] <= 0
            or process_before.get("game_exe_sha256") != EXE_SHA256):
        return _blocked("exact_live_process_identity_unproven")
    for binding in (
        process_before.get("driver_state_binding"),
        process_after.get("driver_state_binding"),
    ):
        if (not isinstance(binding, Mapping)
                or type(binding.get("bridge_pid")) is not int
                or binding["bridge_pid"] != process_before["process_pid"]
                or type(binding.get("episode_character_id")) is not int
                or binding["episode_character_id"]
                != frame_before["played_character_id"]
                or binding.get("episode_run_id")
                != frame_before["episode_run_id"]):
            return _blocked("postrestore_driver_state_actor_or_pid_mismatch")
    return {
        "schema": SCHEMA, "status": "same_paused_query_postcheck_passed",
        "source_frame_before": frame_before,
        "source_frame_after": frame_after,
        "treasury_before_raw": treasury_before_raw,
        "treasury_after_raw": treasury_after_raw,
        "treasury_scale": 100_000,
        "selected_step": STEP, "priced_command": expected_command,
        "query_result": {
            "step": STEP, "accepted": True, "status": "available",
            "war_id": WAR_ID,
            "query_sequence": native_result["query_sequence"],
        },
        "query_request": dict(request),
        "query_response_envelope": dict(envelope),
        "source_commit": source_commit,
        "process_pid": process_before["process_pid"],
        "process_created_filetime": process_before["process_created_filetime"],
        # These hashes are of mapped paths' on-disk bytes, not live code pages.
        "loaded_game_exe_sha256": process_before["game_exe_sha256"],
        "loaded_native_dll_sha256": process_before["native_dll_sha256"],
        "module_hash_scope": "process_mapped_path_disk_bytes_not_memory_pages",
        "launch_injector_sha256": process_before["launch_injector_sha256"],
        "paired_prelaunch_driver_state_sha256": (
            paired_prelaunch_driver_state_sha256.upper()
        ),
        "bound_driver_state_sha256": process_before["driver_state_sha256"],
        "postquery_driver_state_sha256": process_after["driver_state_sha256"],
        "bound_driver_state_binding": dict(
            process_before["driver_state_binding"]
        ),
        "postquery_driver_state_binding": dict(
            process_after["driver_state_binding"]
        ),
        "gameplay_submits_before": gameplay_submits_before,
        "gameplay_submits_after": gameplay_submits_after,
        "submit_count_scope": "runner_gameplay_actions_plus_exact_binary_audit_required",
        "formal_cash_receipt_eligible": False,
        "immediate_war_action_cost_raw": None,
    }
