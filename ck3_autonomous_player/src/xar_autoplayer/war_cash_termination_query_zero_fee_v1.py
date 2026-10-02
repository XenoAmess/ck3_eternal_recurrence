"""Conditional zero fee for one exact, already completed native war query.

The native bridge's war-termination-options branch only reads game state and
returns a query result.  A source plan or command name alone does not prove
that the running DLL and driver used that branch.  Exact runtime and binary
audit receipts must be promoted by SHA before this observer emits zero.
There are deliberately no promoted receipts in this source revision.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import re

from .m5_observed_opportunity_selector import observed_frame


SCHEMA = "xar.ck3.war-termination-query-zero-fee.v1"
EVIDENCE_SCHEMA = "xar.ck3.war-termination-query-zero-fee-evidence.v1"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
# Promote only after reviewing the exact managed run receipt and the DLL's
# read-only dispatch audit.  Empty registries intentionally block all live use.
APPROVED_RUNTIME_RECEIPT_SHA256: frozenset[str] = frozenset()
APPROVED_BINARY_AUDITS: dict[str, str] = {}
ARTIFACT_ROLES = frozenset({
    "game_exe", "save", "driver_state", "native_dll", "injector",
    "official_no_launch_receipt", "managed_session_receipt",
    "binary_audit", "driver_source", "bridge_source", "ck3_source",
})


def _sha256(value: object) -> str | None:
    if type(value) is not str or re.fullmatch(r"[0-9A-Fa-f]{64}", value) is None:
        return None
    return value.upper()


def _blocked(reason: str) -> dict[str, object]:
    return {
        "schema": SCHEMA, "status": "blocked",
        "missing_reasons": [reason],
        "immediate_war_action_cost_raw": None,
        "pending_war_cash_raw": None,
        "future_war_cost_upper_raw": None,
        "future_risk_budget_raw": None,
        "policy_minimum_gold_reserve_raw": None,
        "horizon_days": None,
        "formal_cash_receipt_eligible": False,
    }


def _exact_fields(value: object, expected: Mapping[str, object]) -> bool:
    return (type(value) is dict and set(value) == set(expected)
            and all(type(value[key]) is type(item) and value[key] == item
                    for key, item in expected.items()))


def _treasury_raw(snapshot: Mapping[str, object]) -> int | None:
    gold = snapshot.get("played_character_gold")
    if (type(gold) is not dict or set(gold) != {"raw", "scale"}
            or type(gold.get("raw")) is not int
            or not -(2**63) <= gold["raw"] <= 2**63 - 1
            or type(gold.get("scale")) is not int
            or gold["scale"] != 100_000):
        return None
    return gold["raw"]


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json_object(payload: bytes) -> dict[str, object]:
    value = json.loads(payload, object_pairs_hook=_unique_object)
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _verified_artifact_bytes(
    paths: object, expected: Mapping[str, object],
) -> dict[str, bytes] | None:
    """Stream exact files; retain only three bounded JSON receipts."""
    if not isinstance(paths, Mapping) or set(paths) != ARTIFACT_ROLES:
        return None
    retained: dict[str, bytes] = {}
    small_json = {"official_no_launch_receipt", "managed_session_receipt",
                  "binary_audit"}
    try:
        unique_paths = {str(path.resolve()) for path in paths.values()
                        if isinstance(path, Path)}
    except (OSError, RuntimeError):
        return None
    if len(unique_paths) != len(ARTIFACT_ROLES):
        return None
    for role in sorted(ARTIFACT_ROLES):
        target = paths[role]
        digest = _sha256(expected.get(role))
        if not isinstance(target, Path) or digest is None:
            return None
        try:
            before = target.stat()
            size = before.st_size
            cap = 1024 * 1024 if role in small_json else 1024 * 1024 * 1024
            if not 0 < size <= cap:
                return None
            calculated = hashlib.sha256()
            small_payload = bytearray() if role in small_json else None
            total = 0
            with target.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    total += len(chunk)
                    if total > cap:
                        return None
                    calculated.update(chunk)
                    if small_payload is not None:
                        small_payload.extend(chunk)
            after = target.stat()
            if (total != size or after.st_size != before.st_size
                    or after.st_mtime_ns != before.st_mtime_ns):
                return None
            if calculated.hexdigest().upper() != digest:
                return None
            if small_payload is not None:
                retained[role] = bytes(small_payload)
        except OSError:
            return None
    return retained


def observe_termination_query_zero_fee_v1(
    *, snapshot: Mapping[str, object], planned: Mapping[str, object],
    war_id: int, runtime_evidence_bytes: bytes | None,
    artifact_paths: Mapping[str, Path] | None = None,
) -> dict[str, object]:
    """Price only an exact completed read-only query in one attested frame.

    This is a component observation.  A zero query fee never proves pending
    commitments, future cost/risk, policy reserve, or formal M5 eligibility.
    """
    if not isinstance(snapshot, Mapping):
        return _blocked("native_frame_missing_or_invalid")
    try:
        frame = observed_frame(snapshot)
    except (TypeError, ValueError, KeyError):
        return _blocked("native_frame_missing_or_invalid")
    treasury_raw = _treasury_raw(snapshot)
    if treasury_raw is None:
        return _blocked("current_same_frame_treasury_unavailable")
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        return _blocked("ready_paused_frame_unproven")
    wars = snapshot.get("active_wars")
    if (type(war_id) is not int or war_id <= 0
            or not isinstance(wars, list) or len(wars) != 1
            or not isinstance(wars[0], Mapping)
            or type(wars[0].get("war_id")) is not int
            or wars[0]["war_id"] != war_id):
        return _blocked("unique_selected_war_id_unproven")
    step = f"query-war-termination-options-{war_id}"
    command = {"kind": "read_only_query", "war_id": war_id,
               "query_name": "war_termination_options"}
    if (not isinstance(planned, Mapping)
            or type(planned.get("snapshot_id")) is not str
            or planned["snapshot_id"] != frame["snapshot_id"]
            or type(planned.get("revision")) is not int
            or planned["revision"] != frame["revision"]):
        return _blocked("plan_crossed_native_frame")
    plan = planned.get("plan")
    if (not isinstance(plan, Mapping)
            or plan.get("policy") != "one-life-turn-v1"
            or plan.get("selected_step") != step
            or not _exact_fields(plan.get("priced_command"), command)):
        return _blocked("selected_read_only_query_identity_unproven")
    construction = plan.get("construction_wartime_observation")
    expected_source = {
        "snapshot_id": frame["snapshot_id"],
        "revision": frame["revision"],
        "native_revision": frame["native_revision"],
        "date_raw": frame["date_raw"],
        "episode_run_id": frame["episode_run_id"],
        "actor_character_id": frame["played_character_id"],
    }
    if (not isinstance(construction, Mapping)
            or not _exact_fields(construction.get("source_frame"),
                                 expected_source)):
        return _blocked("construction_source_frame_unproven")
    if type(runtime_evidence_bytes) is not bytes:
        return _blocked("receiver_runtime_receipt_missing")
    if not 0 < len(runtime_evidence_bytes) <= 256 * 1024:
        return _blocked("receiver_runtime_receipt_size_invalid")
    receipt_sha = hashlib.sha256(runtime_evidence_bytes).hexdigest().upper()
    if receipt_sha not in APPROVED_RUNTIME_RECEIPT_SHA256:
        return _blocked("receiver_runtime_receipt_not_promoted")
    try:
        evidence = _json_object(runtime_evidence_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return _blocked("receiver_runtime_receipt_invalid_json")
    if (not isinstance(evidence, dict)
            or evidence.get("schema") != EVIDENCE_SCHEMA
            or evidence.get("status") != "receiver_verified_postquery"
            or not _exact_fields(evidence.get("source_frame_before"), frame)
            or not _exact_fields(evidence.get("source_frame_after"), frame)
            or type(evidence.get("treasury_before_raw")) is not int
            or evidence["treasury_before_raw"] != treasury_raw
            or type(evidence.get("treasury_after_raw")) is not int
            or evidence["treasury_after_raw"] != treasury_raw
            or type(evidence.get("treasury_scale")) is not int
            or evidence["treasury_scale"] != 100_000
            or type(evidence.get("war_id")) is not int
            or evidence["war_id"] != war_id
            or evidence.get("selected_step") != step):
        return _blocked("receiver_runtime_receipt_frame_or_action_mismatch")
    pair = evidence.get("pair")
    run = evidence.get("run")
    query = evidence.get("query_result")
    audit = evidence.get("binary_audit")
    if not all(isinstance(item, dict) for item in (pair, run, query, audit)):
        return _blocked("receiver_pair_run_or_binary_audit_missing")
    dll_sha = _sha256(pair.get("native_dll_sha256"))
    if (pair.get("status") != "receiver_official_no_launch_passed"
            or _sha256(pair.get("game_exe_sha256")) != EXE_SHA256
            or type(pair.get("source_commit")) is not str
            or re.fullmatch(r"[0-9A-Fa-f]{40}", pair["source_commit"]) is None
            or any(_sha256(pair.get(key)) is None for key in (
                "paired_save_sha256", "driver_state_sha256",
                "native_dll_sha256", "injector_sha256",
                "official_no_launch_receipt_sha256",
            ))
            or pair.get("episode_run_id") != frame["episode_run_id"]
            or type(pair.get("actor_character_id")) is not int
            or pair["actor_character_id"] != frame["played_character_id"]
            or type(pair.get("date_raw")) is not int
            or pair["date_raw"] != frame["date_raw"]):
        return _blocked("exact_receiver_pair_unproven")
    if (audit.get("status") != "exact_dll_read_only_no_submit_verified"
            or _sha256(audit.get("native_dll_sha256")) != dll_sha
            or _sha256(audit.get("audit_sha256"))
            != APPROVED_BINARY_AUDITS.get(dll_sha)
            or any(_sha256(audit.get(key)) is None for key in (
                "driver_source_sha256", "bridge_source_sha256",
                "ck3_source_sha256"))):
        return _blocked("exact_dll_driver_read_only_dispatch_unproven")
    if (run.get("status") != "managed_paused_postcheck_passed"
            or _sha256(run.get("session_receipt_sha256")) is None
            or type(run.get("process_pid")) is not int
            or run["process_pid"] <= 0
            or type(run.get("process_created_filetime")) is not int
            or run["process_created_filetime"] <= 0
            or type(run.get("gameplay_submits_before")) is not int
            or run["gameplay_submits_before"] < 0
            or type(run.get("gameplay_submits_after")) is not int
            or run.get("gameplay_submits_after") != run["gameplay_submits_before"]):
        return _blocked("managed_no_submit_postcheck_unproven")
    if (query.get("step") != step or query.get("accepted") is not True
            or query.get("status") != "available"
            or type(query.get("war_id")) is not int
            or query["war_id"] != war_id
            or type(query.get("query_sequence")) is not int
            or query["query_sequence"] <= 0):
        return _blocked("exact_native_query_result_unproven")
    expected_artifacts = {
        "game_exe": pair["game_exe_sha256"],
        "save": pair["paired_save_sha256"],
        "driver_state": pair["driver_state_sha256"],
        "native_dll": pair["native_dll_sha256"],
        "injector": pair["injector_sha256"],
        "official_no_launch_receipt": pair["official_no_launch_receipt_sha256"],
        "managed_session_receipt": run["session_receipt_sha256"],
        "binary_audit": audit["audit_sha256"],
        "driver_source": audit["driver_source_sha256"],
        "bridge_source": audit["bridge_source_sha256"],
        "ck3_source": audit["ck3_source_sha256"],
    }
    receipts = _verified_artifact_bytes(artifact_paths, expected_artifacts)
    if receipts is None:
        return _blocked("exact_runtime_and_source_artifact_bytes_unverified")
    try:
        no_launch = _json_object(receipts["official_no_launch_receipt"])
        managed = _json_object(receipts["managed_session_receipt"])
        binary_audit = _json_object(receipts["binary_audit"])
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return _blocked("external_receipt_or_audit_json_invalid")
    preflight_expected = no_launch.get("expected")
    preflight_profile = no_launch.get("profile")
    preflight_anchor = no_launch.get("resume_anchor")
    checkpoint = (preflight_anchor.get("checkpoint")
                  if isinstance(preflight_anchor, dict) else None)
    driver_anchor = (preflight_anchor.get("driver_state")
                     if isinstance(preflight_anchor, dict) else None)
    if (no_launch.get("kind") != "ck3_native_one_generation_preflight"
            or no_launch.get("status") != "ready"
            or no_launch.get("ok") is not True
            or no_launch.get("ck3_launch_attempted") is not False
            or not isinstance(preflight_expected, dict)
            or not isinstance(preflight_profile, dict)
            or not isinstance(checkpoint, dict)
            or not isinstance(driver_anchor, dict)
            or _sha256(preflight_expected.get("checkpoint_sha256"))
            != _sha256(pair["paired_save_sha256"])
            or _sha256(preflight_expected.get("driver_state_sha256"))
            != _sha256(pair["driver_state_sha256"])
            or _sha256(checkpoint.get("sha256"))
            != _sha256(pair["paired_save_sha256"])
            or _sha256(driver_anchor.get("sha256"))
            != _sha256(pair["driver_state_sha256"])
            or _sha256(preflight_profile.get("ck3_executable_sha256"))
            != EXE_SHA256
            or type(preflight_expected.get("episode_character_id")) is not int
            or preflight_expected["episode_character_id"]
            != frame["played_character_id"]
            or preflight_expected.get("episode_run_id")
            != frame["episode_run_id"]
            or type(driver_anchor.get("episode_character_id")) is not int
            or driver_anchor["episode_character_id"]
            != frame["played_character_id"]
            or driver_anchor.get("episode_run_id")
            != frame["episode_run_id"]
            or type(checkpoint.get("saved_date_raw")) is not int
            or checkpoint["saved_date_raw"] != frame["date_raw"]):
        return _blocked("official_no_launch_pair_receipt_mismatch")
    if (managed.get("schema") != "xar.ck3.war-cash-query-managed-session.v1"
            or managed.get("status") != "same_paused_query_postcheck_passed"
            or not isinstance(managed.get("managed_cleanup"), dict)
            or managed["managed_cleanup"].get("ok") is not True
            or managed.get("runner_status") != "turn_limit"
            or not _exact_fields(managed.get("source_frame_before"), frame)
            or not _exact_fields(managed.get("source_frame_after"), frame)
            or type(managed.get("treasury_before_raw")) is not int
            or managed["treasury_before_raw"] != treasury_raw
            or type(managed.get("treasury_after_raw")) is not int
            or managed["treasury_after_raw"] != treasury_raw
            or type(managed.get("treasury_scale")) is not int
            or managed["treasury_scale"] != 100_000
            or not _exact_fields(managed.get("query_result"), query)
            or managed.get("source_commit") != pair["source_commit"]
            or type(managed.get("process_pid")) is not int
            or managed.get("process_pid") != run["process_pid"]
            or managed.get("managed_session_pid") != run["process_pid"]
            or type(managed.get("process_created_filetime")) is not int
            or managed.get("process_created_filetime")
            != run["process_created_filetime"]
            or type(managed.get("gameplay_submits_before")) is not int
            or managed.get("gameplay_submits_before")
            != run["gameplay_submits_before"]
            or type(managed.get("gameplay_submits_after")) is not int
            or managed.get("gameplay_submits_after")
            != run["gameplay_submits_after"]
            or _sha256(managed.get("loaded_game_exe_sha256")) != EXE_SHA256
            or _sha256(managed.get("loaded_native_dll_sha256")) != dll_sha
            or _sha256(managed.get("launch_injector_sha256"))
            != _sha256(pair["injector_sha256"])
            or _sha256(managed.get("paired_prelaunch_driver_state_sha256"))
            != _sha256(pair["driver_state_sha256"])
            or _sha256(managed.get("bound_driver_state_sha256")) is None
            or _sha256(managed.get("postquery_driver_state_sha256")) is None
            or managed.get("module_hash_scope")
            != "process_mapped_path_disk_bytes_not_memory_pages"
            or any(
                not isinstance(managed.get(key), dict)
                or type(managed[key].get("bridge_pid")) is not int
                or managed[key]["bridge_pid"] != run["process_pid"]
                or type(managed[key].get("episode_character_id")) is not int
                or managed[key]["episode_character_id"]
                != frame["played_character_id"]
                or managed[key].get("episode_run_id")
                != frame["episode_run_id"]
                for key in (
                    "bound_driver_state_binding",
                    "postquery_driver_state_binding",
                )
            )):
        return _blocked("managed_loaded_binary_or_query_postcheck_mismatch")
    request = managed.get("query_request")
    envelope = managed.get("query_response_envelope")
    native_result = (
        envelope.get("result") if isinstance(envelope, dict) else None
    )
    if (not isinstance(request, dict)
            or not isinstance(envelope, dict)
            or not isinstance(native_result, dict)
            or type(request.get("protocol_version")) is not int
            or request["protocol_version"] != 1
            or type(envelope.get("protocol_version")) is not int
            or envelope["protocol_version"] != 1
            or request.get("type") != "execute_step"
            or request.get("step") != step
            or type(request.get("expected_revision")) is not int
            or request["expected_revision"] != frame["native_revision"]
            or type(request.get("request_id")) is not str
            or not request["request_id"]
            or envelope.get("type") != "command_result"
            or envelope.get("request_id") != request["request_id"]
            or envelope.get("ok") is not True
            or native_result.get("step") != step
            or native_result.get("accepted") is not True
            or native_result.get("status") != "available"
            or type(native_result.get("query_sequence")) is not int
            or native_result["query_sequence"] != query["query_sequence"]
            or not isinstance(native_result.get("war_termination_options"), dict)
            or type(native_result["war_termination_options"].get("war_id"))
            is not int
            or native_result["war_termination_options"]["war_id"] != war_id):
        return _blocked("managed_query_protocol_identity_mismatch")
    if (binary_audit.get("schema")
            != "xar.ck3.war-cash-query-binary-audit.v1"
            or binary_audit.get("status")
            != "exact_dll_read_only_no_submit_verified"
            or _sha256(binary_audit.get("native_dll_sha256")) != dll_sha
            or binary_audit.get("source_commit") != pair["source_commit"]
            or _sha256(binary_audit.get("driver_source_sha256"))
            != _sha256(audit["driver_source_sha256"])
            or _sha256(binary_audit.get("bridge_source_sha256"))
            != _sha256(audit["bridge_source_sha256"])
            or _sha256(binary_audit.get("ck3_source_sha256"))
            != _sha256(audit["ck3_source_sha256"])
            or type(binary_audit.get("bridge_query_gameplay_submit_count"))
            is not int
            or binary_audit["bridge_query_gameplay_submit_count"] != 0
            or type(binary_audit.get("native_query_gameplay_submit_count"))
            is not int
            or binary_audit["native_query_gameplay_submit_count"] != 0):
        return _blocked("binary_read_only_dispatch_audit_mismatch")
    return {
        "schema": SCHEMA,
        "status": "selected_read_only_query_zero_fee_proven",
        "source_frame": frame,
        "war_id": war_id,
        "selected_step": step,
        "observed_treasury_raw": treasury_raw,
        "runtime_receipt_sha256": receipt_sha,
        "native_dll_sha256": dll_sha,
        "immediate_war_action_cost_raw": {
            "raw": 0, "scale": 100_000,
            "source": "attested_native_war_termination_options_read_only_v1",
            "source_frame": frame, "war_id": war_id,
        },
        "pending_war_cash_raw": None,
        "future_war_cost_upper_raw": None,
        "future_risk_budget_raw": None,
        "policy_minimum_gold_reserve_raw": None,
        "horizon_days": None,
        "formal_cash_receipt_eligible": False,
    }
