"""Preserve native Select rejection evidence without certifying an action.

Only the fixed admission branch before owner submission can resolve a Select
claim. Missing ACKs, other branches, Confirm and the same revision stay locked.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .ingame_decision_item_action_contract import SELECT_STEP

ERROR = "exact_alive_paused_decision_action_binding_changed"
PREDICATES = {
    "expected_revision_field", "expected_player_character_id_field", "expected_game_pid_field",
    "expected_connection_generation_field", "decision_key_field", "expected_window_kind",
    "expected_outcome", "revision_positive", "revision_matches", "pid_matches",
    "generation_matches", "previous_snapshot_available", "snapshot_read_ok", "snapshot_equal",
    "map_ready", "paused", "has_played_character", "played_character_alive", "actor_positive",
    "actor_matches", "outcome_window_clear", "game_version_matches", "executable_sha256_matches",
}
BINDING_KEYS = {"native_revision", "game_pid", "connection_generation", "played_character_id"}


def _positive(value: object) -> bool:
    return type(value) is int and 0 < value <= 2**64 - 1


def _known_pre_submit(claim: dict[str, object], request: object, frame: object) -> bool:
    if not isinstance(request, dict) or not isinstance(frame, dict):
        return False
    if (set(request) != {"type", "protocol_version", "request_id", "step", "expected_revision",
                         "decision_key", "expected_player_character_id", "expected_game_pid",
                         "expected_connection_generation"}
            or set(frame) != {"type", "protocol_version", "request_id", "ok", "error",
                              "decision_action_pre_dispatch_rejection_v1"}
            or request["type"] != "execute_step" or frame["type"] != "command_result"
            or type(request["protocol_version"]) is not int or request["protocol_version"] != 1
            or type(frame["protocol_version"]) is not int or frame["protocol_version"] != 1
            or request["step"] != SELECT_STEP or frame["ok"] is not False or frame["error"] != ERROR
            or not isinstance(claim.get("request_id"), str)
            or request["request_id"] != claim["request_id"] or frame["request_id"] != claim["request_id"]
            or claim.get("action") != "select" or request["decision_key"] != claim.get("decision_key")):
        return False
    binding = claim.get("binding")
    if not isinstance(binding, dict) or not all(_positive(binding.get(k)) for k in BINDING_KEYS):
        return False
    expected = {k: binding[k] for k in BINDING_KEYS}
    for wire, bound in (("expected_revision", "native_revision"), ("expected_game_pid", "game_pid"),
                        ("expected_connection_generation", "connection_generation"),
                        ("expected_player_character_id", "played_character_id")):
        if not _positive(request[wire]) or request[wire] != expected[bound]:
            return False
    data = frame["decision_action_pre_dispatch_rejection_v1"]
    if (not isinstance(data, dict)
            or set(data) != {"schema", "guard_source_id", "dispatch_stage", "submitted", "dispatch_invoked",
                             "request_id", "step", "decision_key", "failed_predicates", "expected", "actual",
                             "previous_snapshot_available", "snapshot_read_attempted", "snapshot_read_ok",
                             "snapshot_equal", "map_ready", "paused", "has_played_character", "played_character_alive",
                             "current_snapshot", "previous_snapshot", "snapshot_differing_fields"}
            or data["schema"] != "ck3-decision-action-pre-dispatch-rejection-v1"
            or data["guard_source_id"] != "ingame_decision_item_action_admission_v1"
            or data["dispatch_stage"] != "before_main_thread_submit"
            or data["submitted"] is not False or data["dispatch_invoked"] is not False
            or data["request_id"] != claim["request_id"] or data["step"] != SELECT_STEP
            or data["decision_key"] != claim["decision_key"]
            or not isinstance(data["expected"], dict) or set(data["expected"]) != BINDING_KEYS
            or not all(_positive(data["expected"][k]) for k in BINDING_KEYS) or data["expected"] != expected
            or not isinstance(data["failed_predicates"], list) or len(data["failed_predicates"]) != 1
            or not isinstance(data["failed_predicates"][0], str) or data["failed_predicates"][0] not in PREDICATES):
        return False
    actual = data["actual"]
    if (not isinstance(actual, dict) or set(actual) != BINDING_KEYS
            or not all(_positive(actual[k]) for k in ("game_pid", "connection_generation"))
            or type(actual["native_revision"]) is not int or not 0 <= actual["native_revision"] <= 2**64 - 1
            or any(type(data[k]) is not bool for k in ("previous_snapshot_available", "snapshot_read_attempted", "snapshot_read_ok"))
            or (data["snapshot_read_ok"] and not data["snapshot_read_attempted"])):
        return False
    read = data["snapshot_read_ok"]
    for name, present in (("current_snapshot", read), ("previous_snapshot", data["previous_snapshot_available"])):
        snapshot = data[name]
        if ((present and (not isinstance(snapshot, dict) or snapshot.get("type") != "state_snapshot"
                          or type(snapshot.get("protocol_version")) is not int or snapshot["protocol_version"] != 1
                          or snapshot.get("revision") != actual["native_revision"]
                          or not isinstance(snapshot.get("state"), dict)))
                or (not present and snapshot is not None)):
            return False
    if ((read and type(actual["played_character_id"]) is not int)
            or (not read and actual["played_character_id"] is not None)
            or any(type(data[k]) is not bool if read else data[k] is not None
                   for k in ("map_ready", "paused", "has_played_character", "played_character_alive"))
            or (type(data["snapshot_equal"]) is not bool if read and data["previous_snapshot_available"]
                else data["snapshot_equal"] is not None)):
        return False
    failed = data["failed_predicates"][0]
    differences = data["snapshot_differing_fields"]
    if read and data["previous_snapshot_available"]:
        if (not isinstance(differences, list) or not all(isinstance(k, str) and k for k in differences)
                or len(set(differences)) != len(differences)
                or bool(differences) == data["snapshot_equal"]):
            return False
    elif differences is not None:
        return False
    observable = {
        "revision_matches": expected["native_revision"] == actual["native_revision"],
        "pid_matches": expected["game_pid"] == actual["game_pid"],
        "generation_matches": expected["connection_generation"] == actual["connection_generation"],
        "previous_snapshot_available": data["previous_snapshot_available"],
        "snapshot_read_ok": data["snapshot_read_ok"], "snapshot_equal": data["snapshot_equal"],
        "map_ready": data["map_ready"], "paused": data["paused"],
        "has_played_character": data["has_played_character"], "played_character_alive": data["played_character_alive"],
        "actor_positive": actual["played_character_id"] > 0 if read else None,
        "actor_matches": expected["played_character_id"] == actual["played_character_id"] if read else None,
    }
    return failed not in observable or observable[failed] is False


def _put(path: Path, value: dict[str, object]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def preserve_select_error(claim: Path, request: object, frame: object) -> dict[str, object] | None:
    """Store the received parsed ERROR, even if it cannot resolve the claim."""
    if not isinstance(request, dict) or not isinstance(frame, dict):
        return None
    claim_bytes = claim.read_bytes()
    value = json.loads(claim_bytes)
    error_path = claim.with_suffix(".error.json")
    _put(error_path, {"schema": "ck3-ingame-decision-action-native-error-v1",
                     "claim_path": str(claim), "claim_sha256": hashlib.sha256(claim_bytes).hexdigest(),
                     "request": request, "native_command_result": frame})
    ref = {"path": str(error_path), "sha256": hashlib.sha256(error_path.read_bytes()).hexdigest()}
    if _known_pre_submit(value, request, frame):
        _put(claim.with_suffix(".rejected-before-dispatch.json"), {
            "schema": "ck3-ingame-decision-action-rejected-before-dispatch-v1",
            "status": "NATIVE_REJECTED_BEFORE_DISPATCH", "request_id": value["request_id"],
            "claim_path": str(claim), "claim_sha256": hashlib.sha256(claim_bytes).hexdigest(),
            "native_error": ref})
    return ref


def allows_later_select(claim: Path, value: dict[str, object], identity: dict[str, object],
                        current_binding: dict[str, object] | None) -> bool:
    if identity.get("action") != "select" or not isinstance(current_binding, dict):
        return False
    try:
        claim_sha = hashlib.sha256(claim.read_bytes()).hexdigest()
        evidence = json.loads(claim.with_suffix(".rejected-before-dispatch.json").read_bytes())
        error_path = claim.with_suffix(".error.json")
        error_bytes = error_path.read_bytes()
        ref = {"path": str(error_path), "sha256": hashlib.sha256(error_bytes).hexdigest()}
        if (set(evidence) != {"schema", "status", "request_id", "claim_path", "claim_sha256", "native_error"}
                or evidence["schema"] != "ck3-ingame-decision-action-rejected-before-dispatch-v1"
                or evidence["status"] != "NATIVE_REJECTED_BEFORE_DISPATCH"
                or evidence["request_id"] != value["request_id"] or evidence["claim_path"] != str(claim)
                or evidence["claim_sha256"] != claim_sha or evidence["native_error"] != ref):
            return False
        error = json.loads(error_bytes)
        if (set(error) != {"schema", "claim_path", "claim_sha256", "request", "native_command_result"}
                or error["schema"] != "ck3-ingame-decision-action-native-error-v1"
                or error["claim_path"] != str(claim) or error["claim_sha256"] != claim_sha
                or not _known_pre_submit(value, error["request"], error["native_command_result"])):
            return False
        previous = value["action_identity"]
        binding = value["binding"]
        return (all(current_binding[k] == binding[k] for k in
                    ("connection_generation", "game_pid", "played_character_id", "date_raw", "episode_run_id"))
                and _positive(identity.get("public_revision")) and _positive(previous.get("public_revision"))
                and identity["public_revision"] > previous["public_revision"]
                and _positive(current_binding.get("native_revision"))
                and current_binding["native_revision"] > binding["native_revision"])
    except (OSError, ValueError, KeyError, TypeError):
        return False
