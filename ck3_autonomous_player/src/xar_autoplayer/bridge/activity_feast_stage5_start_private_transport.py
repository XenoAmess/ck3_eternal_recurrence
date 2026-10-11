"""Default-off paused native reads for feast Start and its independent poststate."""

from __future__ import annotations

import uuid
import re
from collections.abc import Mapping
from typing import cast

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


INPUT_STEP = "query-activity-feast-stage5-start-inputs-v1-private"
POST_STEP = "query-activity-feast-hosted-post-v1-private"
START_STEP = "start-activity-feast-stage5-v1-private"
INPUT_SCHEMA = "activity-feast-stage5-start-inputs-private-v1"
POST_SCHEMA = "activity-feast-hosted-post-private-read-v1"
RESOURCE_KEYS = ("gold", "treasury", "piety", "barter_goods")
_MAX_I64 = 2**63 - 1
_MIN_I64 = -(2**63)


def _positive(value: object, maximum: int = 2**64 - 1) -> bool:
    return type(value) is int and 0 < value <= maximum


def _signed(value: object) -> bool:
    return type(value) is int and _MIN_I64 <= value <= _MAX_I64


def _source_snapshot(driver: object) -> dict[str, object]:
    snapshot = driver.take_snapshot()
    actor = snapshot.get("played_character")
    if (
        type(snapshot.get("revision")) is not int
        or not _positive(snapshot["revision"])
        or not _positive(snapshot.get("native_revision"))
        or type(snapshot.get("date_raw")) is not int
        or snapshot["date_raw"] < 0
        or snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or not isinstance(snapshot.get("snapshot_id"), str)
        or not snapshot["snapshot_id"]
        or not isinstance(actor, Mapping)
        or actor.get("alive") is not True
        or not _positive(actor.get("character_id"), 2**32 - 1)
    ):
        raise BridgeUnavailableError("private feast Start read needs a living paused actor")
    return snapshot


def _same_frame(before: Mapping[str, object], after: Mapping[str, object]) -> bool:
    return bool(
        all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and after.get("paused") is True
        and after.get("map_ready") is True
        and after.get("played_character") == before.get("played_character")
    )


def _balances(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict) or set(value) != set(RESOURCE_KEYS):
        raise BridgeUnavailableError("private feast balances malformed")
    copied: dict[str, dict[str, object]] = {}
    for key in RESOURCE_KEYS:
        row = value[key]
        if (
            not isinstance(row, dict)
            or set(row) != {"available", "raw"}
            or type(row["available"]) is not bool
            or (row["available"] is True and not _signed(row["raw"]))
            or (row["available"] is False and row["raw"] is not None)
        ):
            raise BridgeUnavailableError("private feast balance row malformed")
        copied[key] = dict(row)
    return copied


def _hosted(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list) or len(value) > 64:
        raise BridgeUnavailableError("private feast hosted identities malformed")
    copied: list[dict[str, object]] = []
    seen: set[int] = set()
    identity_fields = {"activity_id", "host_character_id", "activity_type_key"}
    terminal_fields = {
        "terminal_flags_observed", "native_completed", "native_invalidated",
    }
    stamp_fields = {"native_completion_stamp_observed", "native_completion_stamp_raw"}
    for row in value:
        if (
            not isinstance(row, dict)
            or set(row) not in (
                identity_fields, identity_fields | terminal_fields,
                identity_fields | stamp_fields, identity_fields | terminal_fields | stamp_fields,
            )
            or not _positive(row["activity_id"], 2**32 - 1)
            or not _positive(row["host_character_id"], 2**32 - 1)
            or not isinstance(row["activity_type_key"], str)
            or not row["activity_type_key"]
            or len(row["activity_type_key"]) > 63
            or row["activity_id"] in seen
        ):
            raise BridgeUnavailableError("private feast hosted identity malformed")
        if terminal_fields <= set(row) and (
            row["terminal_flags_observed"] is not True
            or type(row["native_completed"]) is not bool
            or type(row["native_invalidated"]) is not bool
        ):
            raise BridgeUnavailableError("private feast hosted terminal flags malformed")
        if stamp_fields <= set(row):
            observed = row["native_completion_stamp_observed"]
            raw = row["native_completion_stamp_raw"]
            if (type(observed) is not bool
                    or observed and (type(raw) is not int or not 0 <= raw < 2**64)
                    or not observed and raw is not None):
                raise BridgeUnavailableError("private feast native completion stamp malformed")
        seen.add(row["activity_id"])
        copied.append(dict(row))
    return copied



def _native_terminal_observations(value: object, *, actor_id: int) -> dict[str, object] | None:
    """Qualify only the optional journal; unavailable data cannot gate the post."""
    if value is None:
        return None
    def require(condition: bool) -> None:
        if not condition:
            raise ValueError("private feast native terminal journal malformed")
    def integer(raw: object, low: int, high: int) -> bool:
        return type(raw) is int and low <= raw <= high
    try:
        family_keys = {
            "schema", "available", "unavailable_reason", "observer_attached", "process_lifetime",
            "read_only", "query_thread_id_u32", "query_actor_full_id_u32", "record_capacity",
            "earliest_retained_sequence_u64", "latest_capture_sequence_u64",
            "overflow_dropped_count_u64", "record_count", "records",
        }
        row_keys = {
            "capture_sequence_u64", "capture_thread_id_u32", "source_cut_rva_u64",
            "manager_identity_u64", "activity_identity_u64", "type_identity_u64",
            "activity_full_id_u32", "activity_instance_generation_u8", "host_character_id_i32",
            "type_key", "completed_observed", "completed_raw_u8", "invalidated_observed",
            "invalidated_raw_u8", "native_completion_stamp_observed",
            "native_completion_stamp_raw_u64", "capture_frame",
        }
        frame_keys = {"date_raw_i64", "actor_character_id_i32", "owner_thread_id_u32",
                      "paused", "map_ready", "has_played_character", "played_character_alive"}
        require(isinstance(value, dict) and set(value) == family_keys
                and value["schema"] == "activity_terminal_observations_12004_v1")
        require(all(type(value[key]) is bool for key in
                    ("available", "observer_attached", "process_lifetime", "read_only"))
                and value["process_lifetime"] is True and value["read_only"] is True)
        require(integer(value["query_thread_id_u32"], 0, 0xFFFFFFFF)
                and integer(value["query_actor_full_id_u32"], 0, 0xFFFFFFFF)
                and type(value["record_capacity"]) is int and value["record_capacity"] == 64
                and integer(value["record_count"], 0, 64)
                and isinstance(value["records"], list) and len(value["records"]) == value["record_count"])
        require(all(integer(value[key], 0, 2**64 - 1) for key in
                    ("earliest_retained_sequence_u64", "latest_capture_sequence_u64", "overflow_dropped_count_u64")))
        earliest, latest = value["earliest_retained_sequence_u64"], value["latest_capture_sequence_u64"]
        require((earliest == 0) == (latest == 0) and earliest <= latest)
        if value["available"]:
            require(value["unavailable_reason"] is None and value["observer_attached"] is True
                    and value["query_thread_id_u32"] != 0 and value["query_actor_full_id_u32"] == actor_id)
        else:
            require(isinstance(value["unavailable_reason"], str) and bool(value["unavailable_reason"])
                    and not value["records"])
        rows = []
        previous = 0
        for row in value["records"]:
            require(isinstance(row, dict) and set(row) == row_keys)
            require(integer(row["capture_sequence_u64"], 1, 2**64 - 1)
                    and earliest <= row["capture_sequence_u64"] <= latest
                    and previous < row["capture_sequence_u64"]
                    and integer(row["capture_thread_id_u32"], 1, 0xFFFFFFFF))
            require(all(integer(row[key], 0, 2**64 - 1) for key in
                        ("source_cut_rva_u64", "manager_identity_u64", "activity_identity_u64", "type_identity_u64"))
                    and row["source_cut_rva_u64"] == 0x29BF68C)
            require(integer(row["activity_full_id_u32"], 0, 0xFFFFFFFE)
                    and integer(row["activity_instance_generation_u8"], 0, 255)
                    and row["activity_instance_generation_u8"] == row["activity_full_id_u32"] >> 24
                    and integer(row["host_character_id_i32"], -(2**31), 2**31 - 1)
                    and (row["host_character_id_i32"] & 0xFFFFFFFF) == value["query_actor_full_id_u32"]
                    and row["type_key"] == "activity_feast")
            for flag, raw_key, maximum in (
                ("completed_observed", "completed_raw_u8", 255),
                ("invalidated_observed", "invalidated_raw_u8", 255),
                ("native_completion_stamp_observed", "native_completion_stamp_raw_u64", 2**64 - 1),
            ):
                require(type(row[flag]) is bool)
                require(integer(row[raw_key], 0, maximum) if row[flag] else row[raw_key] is None)
            frame = row["capture_frame"]
            require(isinstance(frame, dict) and set(frame) == frame_keys
                    and integer(frame["date_raw_i64"], -(2**63), 2**63 - 1)
                    and integer(frame["actor_character_id_i32"], -(2**31), 2**31 - 1)
                    and frame["actor_character_id_i32"] == row["host_character_id_i32"]
                    and integer(frame["owner_thread_id_u32"], 1, 0xFFFFFFFF)
                    and frame["owner_thread_id_u32"] == row["capture_thread_id_u32"]
                    and all(type(frame[key]) is bool for key in
                            ("paused", "map_ready", "has_played_character", "played_character_alive"))
                    and frame["map_ready"] is True and frame["has_played_character"] is True
                    and frame["played_character_alive"] is True)
            rows.append({**row, "capture_frame": dict(frame)})
            previous = row["capture_sequence_u64"]
        return {**value, "records": rows}
    except ValueError:
        return None


def _native_completion_effect_counter_observations(
    value: object, *, actor_id: int,
) -> dict[str, object] | None:
    """Qualify only the optional original-call source, preserving unknown faces."""
    if value is None:
        return None
    def require(condition: bool) -> None:
        if not condition:
            raise ValueError("private feast original-call counter journal malformed")
    def integer(raw: object, low: int, high: int) -> bool:
        return type(raw) is int and low <= raw <= high
    family_keys = {
        "schema", "available", "unavailable_reason", "observer_attached", "read_only",
        "process_lifetime", "query_thread_id_u32", "query_actor_full_id_u32", "record_capacity",
        "earliest_retained_sequence_u64", "latest_capture_sequence_u64",
        "overflow_dropped_count_u64", "pairing_dropped_count_u64", "record_count", "records",
    }
    row_keys = {
        "capture_sequence_u64", "observer_invocation_sequence_u64", "capture_thread_id_u32",
        "source_call_rva_u64", "source_callee_rva_u64", "source_return_rva_u64",
        "activity_identity_u64", "participant_identity_u64", "effect_identity_u64",
        "native_context_identity_u64", "original_parent_rsp_u64", "original_call_return_observed",
        "before", "after", "same_activity_full_id_observed", "same_activity_full_id",
        "same_participant_full_id_observed", "same_participant_full_id",
    }
    face_keys = {
        "frame_observed", "frame", "activity_full_id_observed", "activity_full_id_u32",
        "activity_instance_generation_u8", "host_observed", "host_character_id_i32",
        "type_observed", "type_identity_u64", "type_key_observed", "type_key",
        "participant_full_id_observed", "participant_full_id_u32",
        "participant_instance_generation_u8", "resource_extension_observed",
        "resource_extension_identity_u64", "prestige_observed", "prestige_raw_i64",
        "stress_observed", "stress_raw_i32", "reveler_xp_observed", "reveler_xp_raw_i64",
        "reveler_xp_unavailable_reason",
    }
    frame_keys = {
        "date_raw_i64", "actor_character_id_i32", "owner_thread_id_u32", "paused",
        "map_ready", "has_played_character", "played_character_alive",
    }
    try:
        require(isinstance(value, dict) and set(value) == family_keys
                and value["schema"] == "activity_completion_effect_counter_observations_12004_v1")
        require(all(type(value[key]) is bool for key in
                    ("available", "observer_attached", "read_only", "process_lifetime"))
                and value["read_only"] is True and value["process_lifetime"] is True)
        require(integer(value["query_thread_id_u32"], 0, 0xFFFFFFFF)
                and integer(value["query_actor_full_id_u32"], 0, 0xFFFFFFFF)
                and type(value["record_capacity"]) is int and value["record_capacity"] == 64
                and integer(value["record_count"], 0, 64)
                and isinstance(value["records"], list)
                and len(value["records"]) == value["record_count"])
        require(all(integer(value[key], 0, 2**64 - 1) for key in
                    ("earliest_retained_sequence_u64", "latest_capture_sequence_u64",
                     "overflow_dropped_count_u64", "pairing_dropped_count_u64")))
        earliest, latest = value["earliest_retained_sequence_u64"], value["latest_capture_sequence_u64"]
        require((earliest == 0) == (latest == 0) and earliest <= latest)
        if value["available"]:
            require(value["unavailable_reason"] is None and value["observer_attached"] is True
                    and value["query_thread_id_u32"] != 0 and value["query_actor_full_id_u32"] == actor_id)
        else:
            require(isinstance(value["unavailable_reason"], str)
                    and bool(value["unavailable_reason"]) and not value["records"])
        rows = []
        previous = 0
        for row in value["records"]:
            require(isinstance(row, dict) and set(row) == row_keys)
            require(integer(row["capture_sequence_u64"], 1, 2**64 - 1)
                    and earliest <= row["capture_sequence_u64"] <= latest
                    and previous < row["capture_sequence_u64"]
                    and integer(row["observer_invocation_sequence_u64"], 1, 2**64 - 1)
                    and integer(row["capture_thread_id_u32"], 1, 0xFFFFFFFF)
                    and type(row["original_call_return_observed"]) is bool)
            for key, expected in (("source_call_rva_u64", 0x23F6B82),
                                  ("source_callee_rva_u64", 0x3765760),
                                  ("source_return_rva_u64", 0x23F6B87)):
                require(integer(row[key], 0, 2**64 - 1) and row[key] == expected)
            require(all(integer(row[key], 0, 2**64 - 1) for key in
                        ("activity_identity_u64", "participant_identity_u64", "effect_identity_u64",
                         "native_context_identity_u64", "original_parent_rsp_u64")))
            faces = {}
            for side in ("before", "after"):
                face = row[side]
                require(isinstance(face, dict) and set(face) == face_keys)
                for flag, raw_key, low, high in (
                    ("activity_full_id_observed", "activity_full_id_u32", 0, 0xFFFFFFFF),
                    ("host_observed", "host_character_id_i32", -(2**31), 2**31 - 1),
                    ("type_observed", "type_identity_u64", 0, 2**64 - 1),
                    ("participant_full_id_observed", "participant_full_id_u32", 0, 0xFFFFFFFF),
                    ("resource_extension_observed", "resource_extension_identity_u64", 0, 2**64 - 1),
                    ("prestige_observed", "prestige_raw_i64", -(2**63), 2**63 - 1),
                    ("stress_observed", "stress_raw_i32", -(2**31), 2**31 - 1),
                ):
                    require(type(face[flag]) is bool)
                    require(integer(face[raw_key], low, high) if face[flag] else face[raw_key] is None)
                for field in ("activity", "participant"):
                    generation = face[field + "_instance_generation_u8"]
                    if face[field + "_full_id_observed"]:
                        require(integer(generation, 0, 255)
                                and generation == face[field + "_full_id_u32"] >> 24)
                    else:
                        require(generation is None)
                require(type(face["type_key_observed"]) is bool)
                require(isinstance(face["type_key"], str) and 0 < len(face["type_key"]) <= 64
                        if face["type_key_observed"] else face["type_key"] is None)
                require(face["reveler_xp_observed"] is False and face["reveler_xp_raw_i64"] is None
                        and face["reveler_xp_unavailable_reason"] == "no_raw_only_reveler_xp_reader")
                require(type(face["frame_observed"]) is bool)
                frame = face["frame"]
                if face["frame_observed"]:
                    require(isinstance(frame, dict) and set(frame) == frame_keys
                            and integer(frame["date_raw_i64"], -(2**63), 2**63 - 1)
                            and integer(frame["actor_character_id_i32"], -(2**31), 2**31 - 1)
                            and integer(frame["owner_thread_id_u32"], 1, 0xFFFFFFFF)
                            and frame["owner_thread_id_u32"] == row["capture_thread_id_u32"]
                            and all(type(frame[key]) is bool for key in
                                    ("paused", "map_ready", "has_played_character", "played_character_alive")))
                else:
                    require(frame is None)
                for counter in ("prestige", "stress"):
                    if face[counter + "_observed"]:
                        require(face["resource_extension_observed"] is True)
                        if face["resource_extension_identity_u64"] == 0:
                            raw_key = "prestige_raw_i64" if counter == "prestige" else "stress_raw_i32"
                            require(face[raw_key] == 0)
                faces[side] = {**face, "frame": dict(frame) if frame is not None else None}
            before = faces["before"]
            require(all(before[key] is True for key in
                        ("frame_observed", "activity_full_id_observed", "host_observed",
                         "type_observed", "type_key_observed", "participant_full_id_observed"))
                    and before["type_key"] == "activity_feast"
                    and before["participant_full_id_u32"] == actor_id
                    and (before["frame"]["actor_character_id_i32"] & 0xFFFFFFFF) == actor_id)
            for field in ("activity", "participant"):
                flag = row["same_" + field + "_full_id_observed"]
                equal = row["same_" + field + "_full_id"]
                require(type(flag) is bool)
                if flag:
                    require(type(equal) is bool
                            and all(faces[side][field + "_full_id_observed"] is True
                                    for side in ("before", "after"))
                            and equal == (faces["before"][field + "_full_id_u32"]
                                          == faces["after"][field + "_full_id_u32"]))
                else:
                    require(equal is None)
            rows.append({**row, **faces})
            previous = row["capture_sequence_u64"]
        return {**value, "records": rows}
    except ValueError:
        return None


def _outcome_values(value: object) -> dict[str, object]:
    """Copy native actor counters; absent reads remain None, not zero."""
    fields = {"prestige_raw", "stress_points", "reveler_present", "reveler_xp_raw"}
    if not isinstance(value, dict) or set(value) != fields:
        raise BridgeUnavailableError("private feast outcome counters malformed")
    for key in ("prestige_raw", "reveler_xp_raw"):
        if value[key] is not None and not _signed(value[key]):
            raise BridgeUnavailableError("private feast fixed-point outcome counter malformed")
    stress = value["stress_points"]
    if stress is not None and (type(stress) is not int or not -(2**31) <= stress < 2**31):
        raise BridgeUnavailableError("private feast integer stress counter malformed")
    present = value["reveler_present"]
    if present is not None and type(present) is not bool:
        raise BridgeUnavailableError("private feast reveler presence malformed")
    return dict(value)


def _ordinary_guest_route(
    value: object, *, native_revision: int, date_raw: int, actor_id: int,
    normal_refresh_sequence: int,
) -> dict[str, object]:
    fields = {
        "status", "authored_rule_key", "candidate_status", "rule_status",
        "provenance_status", "rule_active", "native_key_hash", "provenance_key_hash",
        "provenance_refresh_sequence", "raw_rule_character_count",
        "filtered_rule_character_count", "candidate_membership", "candidate", "qualified",
    }
    if (not isinstance(value, dict) or set(value) != fields
            or value["status"] not in {"observed", "unavailable"}
            or value["authored_rule_key"] != "activity_invite_rule_close_family"
            or value["candidate_status"] not in {
                "observed", "no_qualified_candidate", "target_not_filtered",
                "exact_build_rejected", "frame_changed", "planner_unavailable",
                "no_normal_refresh", "candidate_source_unavailable",
                "native_evaluation_failed", "arrival_unavailable", "configuration_changed"}
            or value["rule_status"] not in {
                "observed_active", "observed_inactive", "exact_build_rejected",
                "frame_changed", "planner_unavailable", "window_unbound",
                "rule_unavailable", "ambiguous_rule", "native_read_failed",
                "native_action_failed", "postcondition_failed"}
            or value["provenance_status"] not in {
                "observed", "exact_build_rejected", "no_normal_refresh", "frame_changed",
                "planner_unavailable", "rule_unavailable", "ambiguous_rule",
                "capture_overflow", "native_read_failed"}
            or type(value["qualified"]) is not bool):
        raise BridgeUnavailableError("private feast ordinary guest source malformed")
    rule_observed = value["rule_status"] in {"observed_active", "observed_inactive"}
    if rule_observed:
        if (value["rule_active"] is not (value["rule_status"] == "observed_active")
                or type(value["native_key_hash"]) is not int
                or not 0 <= value["native_key_hash"] <= 0xFFFFFFFF):
            raise BridgeUnavailableError("private feast ordinary rule data malformed")
    elif value["rule_active"] is not None or value["native_key_hash"] is not None:
        raise BridgeUnavailableError("private feast ordinary rule unavailable data malformed")
    provenance_fields = ("provenance_key_hash", "provenance_refresh_sequence",
                         "raw_rule_character_count", "filtered_rule_character_count",
                         "candidate_membership")
    if value["provenance_status"] == "observed":
        if (type(value["candidate_membership"]) is not bool
                or type(value["provenance_key_hash"]) is not int
                or not 0 <= value["provenance_key_hash"] <= 0xFFFFFFFF
                or not _positive(value["provenance_refresh_sequence"], 2**64 - 1)
                or type(value["raw_rule_character_count"]) is not int
                or type(value["filtered_rule_character_count"]) is not int
                or not 0 <= value["filtered_rule_character_count"] <= value["raw_rule_character_count"] <= 4096
                or (value["candidate_membership"] and value["filtered_rule_character_count"] == 0)):
            raise BridgeUnavailableError("private feast ordinary provenance malformed")
    elif any(value[key] is not None for key in provenance_fields):
        raise BridgeUnavailableError("private feast ordinary provenance unavailable data malformed")
    candidate = value["candidate"]
    if value["candidate_status"] == "observed":
        if (not isinstance(candidate, dict) or set(candidate) != {
                "character_id", "planner_join_raw", "travel_days", "arrival_raw",
                "planned_start_raw", "snapshot_revision", "date_raw", "actor_character_id",
                "normal_refresh_sequence", "source_fingerprint", "native_filtered"}
                or not _positive(candidate["character_id"], 0xFFFFFFFF)
                or candidate["character_id"] == actor_id
                or any(type(candidate[key]) is not int for key in (
                    "planner_join_raw", "travel_days", "arrival_raw", "planned_start_raw",
                    "snapshot_revision", "date_raw", "actor_character_id"))
                or not -(2**63) <= candidate["planner_join_raw"] < 2**63
                or any(not -(2**31) <= candidate[key] < 2**31 for key in (
                    "travel_days", "arrival_raw", "planned_start_raw"))
                or candidate["snapshot_revision"] != native_revision
                or candidate["date_raw"] != date_raw or candidate["actor_character_id"] != actor_id
                or not _positive(candidate["normal_refresh_sequence"], 2**64 - 1)
                or not isinstance(candidate["source_fingerprint"], str)
                or re.fullmatch(r"0x[0-9a-f]{16}", candidate["source_fingerprint"]) is None
                or type(candidate["native_filtered"]) is not bool):
            raise BridgeUnavailableError("private feast ordinary candidate malformed")
    elif candidate is not None:
        raise BridgeUnavailableError("private feast ordinary candidate unavailable data malformed")
    observed = bool(
        candidate is not None and candidate["native_filtered"]
        and candidate["normal_refresh_sequence"] == normal_refresh_sequence
        and value["rule_status"] == "observed_active" and value["rule_active"] is True
        and value["provenance_status"] == "observed"
        and value["native_key_hash"] == value["provenance_key_hash"])
    qualified = bool(
        observed and value["candidate_membership"] is True
        and value["filtered_rule_character_count"] > 0
        and candidate["planner_join_raw"] > 0 and candidate["travel_days"] >= 0
        and candidate["arrival_raw"] <= candidate["planned_start_raw"])
    if (value["status"] != ("observed" if observed else "unavailable")
            or value["qualified"] is not qualified):
        raise BridgeUnavailableError("private feast ordinary qualification disagreed")
    return {**value, "candidate": dict(candidate) if candidate is not None else None}


def _parse_payload(
    value: object, *, step: str, native_revision: int,
    date_raw: int, actor_id: int,
) -> dict[str, object]:
    common = {
        "schema", "snapshot_revision", "date_raw", "actor_character_id",
        "balances", "hosted_activities", "read_only", "advertised",
    }
    input_fields = {
        "activity_key", "selected_option_key", "planning_stage", "scale",
        "normal_refresh_sequence", "final_can_start", "resources",
        "native_guest_route_qualified", "guest_join_status",
        "selected_nonhost_count", "positive_join_count",
        "timely_positive_join_count", "arrival_time_observed",
    }
    fields = common | (input_fields if step == INPUT_STEP else set())
    if (not isinstance(value, dict)
            or not fields <= set(value)
            or not set(value) <= fields | {"outcome_values"} | (
                {"ordinary_guest_route"} if step == INPUT_STEP else {
                    "native_terminal_observations", "native_completion_effect_counter_observations"})
            or value["schema"] != (INPUT_SCHEMA if step == INPUT_STEP else POST_SCHEMA)
            or type(value["snapshot_revision"]) is not int
            or value["snapshot_revision"] != native_revision
            or type(value["date_raw"]) is not int
            or value["date_raw"] != date_raw
            or type(value["actor_character_id"]) is not int
            or value["actor_character_id"] != actor_id
            or value["read_only"] is not True
            or value["advertised"] is not False):
        raise BridgeUnavailableError("private feast Start payload malformed")
    balances = _balances(value["balances"])
    hosted = _hosted(value["hosted_activities"])
    result = {**value, "balances": balances, "hosted_activities": hosted}
    if "outcome_values" in value:
        result["outcome_values"] = _outcome_values(value["outcome_values"])
    if step == POST_STEP and "native_terminal_observations" in value:
        result["native_terminal_observations"] = _native_terminal_observations(
            value["native_terminal_observations"], actor_id=actor_id,
        )
    if step == POST_STEP and "native_completion_effect_counter_observations" in value:
        result["native_completion_effect_counter_observations"] = (
            _native_completion_effect_counter_observations(
                value["native_completion_effect_counter_observations"], actor_id=actor_id,
            )
        )
    if step == INPUT_STEP:
        resources = value["resources"]
        if not isinstance(resources, dict) or set(resources) != set(RESOURCE_KEYS):
            raise BridgeUnavailableError("private feast Start costs malformed")
        copied_resources: dict[str, dict[str, object]] = {}
        for key in RESOURCE_KEYS:
            row = resources[key]
            if (
                not isinstance(row, dict)
                or set(row) != {"resource_index", "configured_cost_raw"}
                or type(row["resource_index"]) is not int
                or not 0 <= row["resource_index"] < 10
                or not _signed(row["configured_cost_raw"])
            ):
                raise BridgeUnavailableError("private feast Start cost row malformed")
            copied_resources[key] = dict(row)
        if (
            value["activity_key"] != "activity_feast"
            or value["selected_option_key"] != "feast_type_generic"
            or type(value["planning_stage"]) is not int
            or value["planning_stage"] != 5
            or type(value["scale"]) is not int
            or value["scale"] != 100000
            or not _positive(value["normal_refresh_sequence"])
            or type(value["final_can_start"]) is not bool
            or type(value["native_guest_route_qualified"]) is not bool
            or not isinstance(value["guest_join_status"], str)
            or value["guest_join_status"] not in {
                "observed", "exact_build_rejected", "frame_changed",
                "planner_unavailable", "planner_diagnostic_unavailable",
                "planner_absent", "not_stage_five", "widget_detached",
                "widget_hidden", "host_view_type_mismatch",
                "no_normal_refresh",
                "configuration_changed", "guest_source_unavailable",
                "native_evaluation_failed", "cache_disagreed",
                "arrival_source_unavailable", "arrival_evaluation_failed",
            }
            or type(value["arrival_time_observed"]) is not bool
        ):
            raise BridgeUnavailableError("private feast Start inputs malformed")
        counts = [value[key] for key in (
            "selected_nonhost_count", "positive_join_count",
            "timely_positive_join_count",
        )]
        if value["guest_join_status"] == "observed":
            if (any(type(count) is not int or not 0 <= count <= 128
                    for count in counts)
                    or not counts[2] <= counts[1] <= counts[0]
                    or value["arrival_time_observed"] is not True):
                raise BridgeUnavailableError("private feast guest counts malformed")
        elif (any(count is not None for count in counts)
              or value["arrival_time_observed"] is not False):
            raise BridgeUnavailableError("private feast unavailable guest must remain unknown")
        result["resources"] = copied_resources
    if step == INPUT_STEP and "ordinary_guest_route" in value:
        result["ordinary_guest_route"] = _ordinary_guest_route(
            value["ordinary_guest_route"], native_revision=native_revision,
            date_raw=date_raw, actor_id=actor_id,
            normal_refresh_sequence=value["normal_refresh_sequence"])
        selected_qualified = bool(
            value["guest_join_status"] == "observed" and value["arrival_time_observed"]
            and value["selected_nonhost_count"] > 0 and value["timely_positive_join_count"] > 0)
        if value["native_guest_route_qualified"] is not (
                selected_qualified or result["ordinary_guest_route"]["qualified"]):
            raise BridgeUnavailableError("private feast guest routes disagreed")
    return result


def _query(driver: object, *, step: str, expected_revision: int,
           timeout_seconds: float) -> dict[str, object]:
    if getattr(driver, "allow_private_activity_feast_stage5_start_query", False) is not True:
        raise UnsupportedStepError("private feast Start query is disabled")
    if not _positive(expected_revision):
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _source_snapshot(driver)
    provenance = private_native_provenance(before)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("private feast Start query revision changed")
    actor_id = cast(int, before["played_character"]["character_id"])
    request_id = "activity-feast-start-read-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
    }
    if step == INPUT_STEP:
        request.update({
            "expected_activity_key": "activity_feast",
            "expected_option_key": "feast_type_generic",
            "expected_planning_stage": 5,
        })
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast Start command_result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private feast Start native RED: "
                                     + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    key = ("activity_feast_stage5_start_inputs" if step == INPUT_STEP
           else "activity_feast_hosted_post")
    if (not isinstance(envelope, dict) or set(envelope) != {
        "step", "accepted", "status", "private_build", "read_only",
        "advertised", key, "backend_id",
    } or envelope["step"] != step or envelope["accepted"] is not True
            or envelope["status"] != "available"
            or envelope["private_build"] is not True
            or envelope["read_only"] is not True
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast Start envelope malformed")
    payload = _parse_payload(
        envelope[key], step=step,
        native_revision=cast(int, before["native_revision"]),
        date_raw=cast(int, before["date_raw"]), actor_id=actor_id,
    )
    after = driver.take_snapshot()
    if not _same_frame(before, after):
        raise BridgeUnavailableError("private feast Start query crossed paused frame")
    return {
        **payload, **provenance, "queried_snapshot_id": before["snapshot_id"],
        "queried_revision": before["revision"],
        "queried_native_revision": before["native_revision"],
        "post_snapshot_id": after["snapshot_id"],
    }


def query_activity_feast_stage5_start_inputs_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    return _query(driver, step=INPUT_STEP, expected_revision=expected_revision,
                  timeout_seconds=timeout_seconds)


def query_activity_feast_hosted_post_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    return _query(driver, step=POST_STEP, expected_revision=expected_revision,
                  timeout_seconds=timeout_seconds)


def submit_activity_feast_stage5_start_private_v1(
    driver: object, *, inputs: Mapping[str, object],
    reserve_raw: Mapping[str, int], timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Submit once after a separately persisted intent; pending is not success."""
    if getattr(driver, "allow_private_activity_feast_stage5_start_action", False) is not True:
        raise UnsupportedStepError("private feast Start action is disabled")
    if (inputs.get("schema") != INPUT_SCHEMA
            or inputs.get("native_guest_route_qualified") is not True
            or inputs.get("final_can_start") is not True
            or not isinstance(reserve_raw, Mapping)
            or set(reserve_raw) != set(RESOURCE_KEYS)
            or any(type(reserve_raw[key]) is not int or not 0 <= reserve_raw[key] <= _MAX_I64
                   for key in RESOURCE_KEYS)):
        raise BridgeUnavailableError("private feast Start lacks qualified inputs")
    before = _source_snapshot(driver)
    provenance = private_native_provenance(before)
    actor_id = cast(int, before["played_character"]["character_id"])
    if any((inputs.get(key) != expected) for key, expected in (
        ("queried_snapshot_id", before["snapshot_id"]),
        ("queried_revision", before["revision"]),
        ("snapshot_revision", before["native_revision"]),
        ("date_raw", before["date_raw"]),
        ("actor_character_id", actor_id),
    )):
        raise BridgeUnavailableError("private feast Start inputs crossed paused frame")
    request_id = "activity-feast-start-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": START_STEP,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": actor_id,
        "expected_activity_key": "activity_feast",
        "expected_option_key": "feast_type_generic",
        "expected_planning_stage": 5,
        "policy_positive": True,
        "previous_submit_pending": False,
        **{f"reserve_{key}_raw": reserve_raw[key] for key in RESOURCE_KEYS},
    }
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private feast Start command_result unavailable")
    envelope = frame.get("result")
    if frame.get("ok") is not True:
        reason = (envelope.get("activity_feast_stage5_start", {}).get("failure")
                  if isinstance(envelope, dict) else frame.get("error"))
        raise BridgeUnavailableError("private feast Start native RED: " + str(reason))
    if (not isinstance(envelope, dict)
            or set(envelope) != {
                "step", "accepted", "status", "private_build", "read_only",
                "advertised", "activity_feast_stage5_start", "backend_id",
            }
            or envelope["step"] != START_STEP
            or envelope["accepted"] is not True
            or envelope["status"] != "pending"
            or envelope["private_build"] is not True
            or envelope["read_only"] is not False
            or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("private feast Start pending envelope malformed")
    action = envelope["activity_feast_stage5_start"]
    if (not isinstance(action, dict)
            or action.get("schema") != "activity-feast-stage5-start-private-action-v1"
            or action.get("submitted") is not True
            or action.get("native_status") != "submitted_pending"
            or not isinstance(action.get("precondition"), dict)):
        raise BridgeUnavailableError("private feast Start ACK lacks native pending")
    # A changed snapshot is expected only after the native action.  The caller
    # performs an independent hosted/resource post read before any success.
    return {**provenance, "request_id": request_id, "native_status": "submitted_pending",
            "ack": dict(action), "source_snapshot_id": before["snapshot_id"]}
