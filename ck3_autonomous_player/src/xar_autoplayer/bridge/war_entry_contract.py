"""Strict request contract for exact-build native war-entry assessments.

The query accepts only explicit full-generation CharacterIDs.  Result fields
are intentionally added only after their exact CK3 1.19.0.6 ABIs are frozen;
this module must never synthesize strategic power from snapshot soldier totals.
"""

from __future__ import annotations


QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY = (
    "game.command.query-war-entry-assessments-v1-N"
)
QUERY_WAR_ENTRY_ASSESSMENTS_STEP_PREFIX = (
    "query-war-entry-assessments-v1-"
)
# The first production reader, parser, bridge and MCP rollout all permit
# exactly one target per request.
MAX_WAR_ENTRY_TARGETS = 1
FIXED_POINT_SCALE = 100_000
GAME_VERSION = "1.19.0.6"
EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
# ``ai_context_ready`` is the frozen schema-v1 key.  It now means the exact
# 0x18784D0 native State16 builder, its dependency, and both byte-identical
# samples are ready; it does not assert that a human manager AIContext exists.
_READINESS = {
    "actor_identity_ready": True,
    "targets_declarable_ready": True,
    "effective_targets_ready": True,
    "ai_context_ready": True,
    "native_output_ready": True,
    "network_decomposition_ready": True,
    "same_frame_ready": True,
    "ready": True,
}
_PROVENANCE = {
    "game_version": GAME_VERSION,
    "executable_sha256": EXECUTABLE_SHA256,
    "assessment_rva": "0x1878A00",
    "network_collector_rva": "0x1879850",
    # Legacy schema-v1 spelling for the target/network decomposition leaf.
    # Actor base power is authoritative State16+0x00 from 0x18784D0.
    "power_leaf": "CCharacter+0x1B8->+0x308",
    "fixed_point_scale": FIXED_POINT_SCALE,
}
_ASSESSMENT_KEYS = {
    "target_character_id",
    "effective_target_character_id",
    "distance_raw",
    "actor_power_base_raw",
    "actor_network_contribution_raw",
    "actor_power_total_raw",
    "target_power_base_raw",
    "target_network_contribution_raw",
    "target_pre_adjustment_total_raw",
    "target_adjustment_delta_raw",
    "target_power_total_raw",
    "actual_power_ratio_raw",
    "target_ai_context_actor_entry_raw",
    "actor_ai_context_target_entry_raw",
    "native_flags_raw",
}


def normalize_war_entry_target_ids(value: object) -> list[int]:
    """Return the one production positive signed-int32 CharacterID."""
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_WAR_ENTRY_TARGETS:
        raise ValueError(
            "target_character_ids must contain exactly 1 CharacterID"
        )
    result: list[int] = []
    seen: set[int] = set()
    for index, raw in enumerate(value):
        if (
            isinstance(raw, bool)
            or not isinstance(raw, int)
            or not 1 <= raw <= 2**31 - 1
        ):
            raise ValueError(
                f"target_character_ids[{index}] must be a positive "
                "full-generation signed-int32 CharacterID"
            )
        if raw in seen:
            raise ValueError("target_character_ids must be distinct")
        seen.add(raw)
        result.append(raw)
    return result


def query_war_entry_assessments_step(target_character_ids: list[int]) -> str:
    """Encode the canonical one-target production native literal."""
    targets = normalize_war_entry_target_ids(target_character_ids)
    return (
        QUERY_WAR_ENTRY_ASSESSMENTS_STEP_PREFIX
        + str(len(targets))
        + "-"
        + "-".join(str(target) for target in targets)
    )


def parse_query_war_entry_assessments_step(step: object) -> list[int] | None:
    """Parse a canonical literal, rejecting alternate numeric spellings."""
    if not isinstance(step, str) or not step.startswith(
        QUERY_WAR_ENTRY_ASSESSMENTS_STEP_PREFIX
    ):
        return None
    raw = step[len(QUERY_WAR_ENTRY_ASSESSMENTS_STEP_PREFIX) :]
    parts = raw.split("-")
    if len(parts) < 2 or any(not _canonical_decimal(part) for part in parts):
        return None
    count = int(parts[0])
    if count != len(parts) - 1:
        return None
    try:
        targets = normalize_war_entry_target_ids(
            [int(part) for part in parts[1:]]
        )
    except ValueError:
        return None
    return targets if query_war_entry_assessments_step(targets) == step else None


def require_declarable_war_targets(
    snapshot: object, target_character_ids: list[int]
) -> list[int]:
    """Require every requested target to occur in the current discovery rows."""
    targets = normalize_war_entry_target_ids(target_character_ids)
    if not isinstance(snapshot, dict):
        raise ValueError("war-entry assessment requires a snapshot object")
    declarations = snapshot.get("declarable_wars")
    if not isinstance(declarations, list):
        raise ValueError("snapshot declarable_wars must be an array")
    available: set[int] = set()
    for index, row in enumerate(declarations):
        if not isinstance(row, dict):
            raise ValueError(f"snapshot declarable_wars[{index}] is malformed")
        target = row.get("target_character_id")
        if (
            isinstance(target, bool)
            or not isinstance(target, int)
            or not 1 <= target <= 2**31 - 1
        ):
            raise ValueError(
                f"snapshot declarable_wars[{index}].target_character_id "
                "is not a positive full-generation CharacterID"
            )
        available.add(target)
    outside = [target for target in targets if target not in available]
    if outside:
        raise ValueError(
            "target_character_ids are outside current declarable_wars: "
            f"{outside}"
        )
    return targets


def normalize_war_entry_assessments(
    value: object,
    *,
    expected_target_character_ids: list[int] | None = None,
    expected_actor_character_id: int | None = None,
    expected_snapshot_revision: int | None = None,
) -> dict[str, object]:
    """Validate one atomic, complete exact-build native assessment payload."""
    expected_keys = {
        "schema_version",
        "status",
        "snapshot_revision",
        "date_raw",
        "actor_character_id",
        "requested_target_character_ids",
        "assessments",
        "readiness",
        "provenance",
    }
    if (
        not isinstance(value, dict)
        or set(value) != expected_keys
        or value.get("schema_version") != 1
        or value.get("status") != "available"
    ):
        raise ValueError("native war_entry_assessments schema is malformed")

    snapshot_revision = _non_negative_int64(
        value.get("snapshot_revision"), "snapshot_revision"
    )
    if (
        expected_snapshot_revision is not None
        and snapshot_revision
        != _non_negative_int64(
            expected_snapshot_revision, "expected_snapshot_revision"
        )
    ):
        raise ValueError("native war-entry snapshot revision mismatch")
    date_raw = _signed_int32(value.get("date_raw"), "date_raw")
    actor_id = _positive_int32(
        value.get("actor_character_id"), "actor_character_id"
    )
    if expected_actor_character_id is not None and actor_id != _positive_int32(
        expected_actor_character_id, "expected_actor_character_id"
    ):
        raise ValueError("native war-entry actor CharacterID mismatch")
    requested = normalize_war_entry_target_ids(
        value.get("requested_target_character_ids")
    )
    if expected_target_character_ids is not None and requested != (
        normalize_war_entry_target_ids(expected_target_character_ids)
    ):
        raise ValueError("native war-entry requested target order mismatch")

    raw_rows = value.get("assessments")
    if not isinstance(raw_rows, list) or len(raw_rows) != len(requested):
        raise ValueError("native war-entry assessment rows do not match request")
    rows = [
        _normalize_assessment(row, requested[index], index)
        for index, row in enumerate(raw_rows)
    ]
    if value.get("readiness") != _READINESS:
        raise ValueError("native war-entry assessment readiness is incomplete")
    if value.get("provenance") != _PROVENANCE:
        raise ValueError("native war-entry assessment provenance drifted")
    return {
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": snapshot_revision,
        "date_raw": date_raw,
        "actor_character_id": actor_id,
        "requested_target_character_ids": requested,
        "assessments": rows,
        "readiness": dict(_READINESS),
        "provenance": dict(_PROVENANCE),
    }


def _normalize_assessment(
    value: object, requested_target: int, index: int
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _ASSESSMENT_KEYS:
        raise ValueError(f"native war-entry assessments[{index}] is malformed")
    target = _positive_int32(
        value.get("target_character_id"),
        f"assessments[{index}].target_character_id",
    )
    if target != requested_target:
        raise ValueError("native war-entry assessment target order mismatch")
    effective_target = _positive_int32(
        value.get("effective_target_character_id"),
        f"assessments[{index}].effective_target_character_id",
    )
    raw_names = (
        "distance_raw",
        "actor_power_base_raw",
        "actor_network_contribution_raw",
        "actor_power_total_raw",
        "target_power_base_raw",
        "target_network_contribution_raw",
        "target_pre_adjustment_total_raw",
        "target_adjustment_delta_raw",
        "target_power_total_raw",
        "actual_power_ratio_raw",
    )
    raw = {
        name: _signed_int64(value.get(name), f"assessments[{index}].{name}")
        for name in raw_names
    }
    for name in (
        "distance_raw",
        "actor_power_base_raw",
        "actor_power_total_raw",
        "target_power_base_raw",
        "target_pre_adjustment_total_raw",
        "target_power_total_raw",
        "actual_power_ratio_raw",
    ):
        if raw[name] < 0:
            raise ValueError(f"native war-entry {name} cannot be negative")
    if _checked_add_int64(
        raw["actor_power_base_raw"], raw["actor_network_contribution_raw"]
    ) != raw["actor_power_total_raw"]:
        raise ValueError("native war-entry actor power decomposition drifted")
    target_pre = _checked_add_int64(
        raw["target_power_base_raw"], raw["target_network_contribution_raw"]
    )
    if target_pre != raw["target_pre_adjustment_total_raw"]:
        raise ValueError("native war-entry target pre-adjustment decomposition drifted")
    if _checked_add_int64(
        target_pre, raw["target_adjustment_delta_raw"]
    ) != raw["target_power_total_raw"]:
        raise ValueError("native war-entry target adjustment decomposition drifted")
    return {
        "target_character_id": target,
        "effective_target_character_id": effective_target,
        **raw,
        "target_ai_context_actor_entry_raw": _signed_int32(
            value.get("target_ai_context_actor_entry_raw"),
            f"assessments[{index}].target_ai_context_actor_entry_raw",
        ),
        "actor_ai_context_target_entry_raw": _signed_int32(
            value.get("actor_ai_context_target_entry_raw"),
            f"assessments[{index}].actor_ai_context_target_entry_raw",
        ),
        "native_flags_raw": _uint8(
            value.get("native_flags_raw"),
            f"assessments[{index}].native_flags_raw",
        ),
    }


def _canonical_decimal(value: str) -> bool:
    return bool(
        value
        and value.isascii()
        and value.isdecimal()
        and not (len(value) > 1 and value.startswith("0"))
    )


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive signed-int32 integer")
    return value


def _signed_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a signed-int32 integer")
    return value


def _signed_int64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**63) <= value <= 2**63 - 1
    ):
        raise ValueError(f"{name} must be a signed-int64 integer")
    return value


def _non_negative_int64(value: object, name: str) -> int:
    result = _signed_int64(value, name)
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _uint8(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 255
    ):
        raise ValueError(f"{name} must be a uint8 integer")
    return value


def _checked_add_int64(left: int, right: int) -> int:
    result = left + right
    if not -(2**63) <= result <= 2**63 - 1:
        raise ValueError("native war-entry power decomposition overflowed int64")
    return result
