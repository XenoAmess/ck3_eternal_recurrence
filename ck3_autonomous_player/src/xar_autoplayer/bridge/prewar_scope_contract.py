"""Fail-closed contract for the declaration-bound prewar primary scope.

This v1 slice intentionally stops before calling itself a participant or
arrival forecast.  It binds a current declarable-war choice to the exact
primary actor/effective target and to every currently raised CUnit owned by
those two Characters, including current Province and the complete paused
remaining route.  Native join callability, declaration objective Provinces,
contact geometry, route time and combat-v3 prewar admission remain separate
false gates.
"""

from __future__ import annotations

import re


PREWAR_SCOPE_V1_CAPABILITY_CANDIDATE = "game.command.query-prewar-scope-v1-N"
PREWAR_SCOPE_V1_STEP_PREFIX = "query-prewar-scope-v1-"
# Kept explicit so a contract import can never be confused with advertising
# a usable production command.
PREWAR_SCOPE_V1_ADVERTISED = False
GAME_VERSION = "1.19.0.6"
EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
MAX_ROUTE_PROVINCES = 4_096

_DECLARATION_ID = re.compile(
    r"(?P<target>[1-9]\d*)-(?P<casus_belli>0|[1-9]\d*)-"
    r"(?P<configuration>-1|0|[1-9]\d*)"
)
_READINESS = {
    "exact_build_ready": True,
    "primary_participants_ready": True,
    "primary_raised_armies_ready": True,
    "native_join_bounds_ready": False,
    "declaration_objective_provinces_ready": False,
    "contact_geometry_ready": False,
    "native_arrival_timeline_ready": False,
    "combat_v3_prewar_scope_ready": False,
    "war_entry_forecast_inputs_ready": False,
}
_PROVENANCE = {
    "game_version": GAME_VERSION,
    "executable_sha256": EXECUTABLE_SHA256,
    "unit_storage_slot_rva": "0x570CC80",
    "unit_identity": "CUnit+0x10_full_generation",
    "unit_owner": "CUnit+0x174_full_character_id",
    "current_province": "CUnit+0x20->CProvince+0x10",
    "paused_route": "CUnit+0x38/+0x40/+0x44_pointer_rows:+0x00_ProvinceID",
    "sample_policy": "two_complete_primary_scope_samples_must_match",
    "unresolved_native_abis": [
        "join_callability_and_acceptance",
        "declaration_title_to_objective_provinces",
        "conditional_contact_entry_selection",
        "route_cost_and_movement_speed_to_arrival_date",
        "same_day_contact_insertion_order",
        "combat_v3_declaration_bound_prewar_admission",
    ],
}


def query_prewar_scope_v1_step(declaration_id: object) -> str:
    """Encode the bounded one-declaration research/production candidate."""
    return PREWAR_SCOPE_V1_STEP_PREFIX + normalize_prewar_declaration_id(
        declaration_id
    )


def parse_query_prewar_scope_v1_step(step: object) -> str | None:
    if not isinstance(step, str) or not step.startswith(
        PREWAR_SCOPE_V1_STEP_PREFIX
    ):
        return None
    declaration_id = step.removeprefix(PREWAR_SCOPE_V1_STEP_PREFIX)
    try:
        normalized = normalize_prewar_declaration_id(declaration_id)
    except ValueError:
        return None
    return normalized if step == query_prewar_scope_v1_step(normalized) else None


def normalize_prewar_declaration_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("prewar declaration_id must be a string")
    match = _DECLARATION_ID.fullmatch(value)
    if match is None:
        raise ValueError("prewar declaration_id is malformed")
    target = _positive_int32(int(match.group("target")), "declaration target")
    cb_index = _non_negative_int32(
        int(match.group("casus_belli")), "declaration casus_belli"
    )
    config = int(match.group("configuration"))
    if config < -1 or config > 2**31 - 1:
        raise ValueError("declaration configuration is out of range")
    canonical = f"{target}-{cb_index}-{config}"
    if canonical != value:
        raise ValueError("prewar declaration_id is not canonical")
    return canonical


def require_current_declarable_war(
    snapshot: object, declaration_id: object
) -> dict[str, object]:
    """Return the exact current declaration row or reject stale scope."""
    expected = normalize_prewar_declaration_id(declaration_id)
    if not isinstance(snapshot, dict):
        raise ValueError("prewar scope requires a snapshot object")
    rows = snapshot.get("declarable_wars")
    if not isinstance(rows, list):
        raise ValueError("snapshot declarable_wars must be an array")
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("declaration_id") == expected
    ]
    if len(matches) != 1:
        raise ValueError("prewar declaration is absent or ambiguous in snapshot")
    row = matches[0]
    if row.get("target_character_id") != int(expected.split("-", 1)[0]):
        raise ValueError("prewar declaration target identity drifted")
    return dict(row)


def normalize_prewar_primary_scope(
    value: object,
    *,
    expected_declaration_id: object,
    expected_actor_character_id: object,
    expected_snapshot_revision: object | None = None,
) -> dict[str, object]:
    """Validate the exact partial scope without upgrading unresolved gates."""
    root = _exact_object(
        value,
        {
            "schema_version",
            "contract_stage",
            "status",
            "snapshot_revision",
            "date_raw",
            "declaration_id",
            "actor_character_id",
            "effective_target_character_id",
            "primary_participants",
            "primary_raised_armies",
            "readiness",
            "provenance",
        },
        "prewar_primary_scope",
    )
    if root.get("schema_version") != 1:
        raise ValueError("prewar primary scope schema_version is malformed")
    if root.get("contract_stage") != "declaration_bound_primary_scope_v1":
        raise ValueError("prewar primary scope contract_stage is malformed")
    if root.get("status") != "available_primary_scope":
        raise ValueError("prewar primary scope is not atomically available")
    revision = _non_negative_int64(
        root.get("snapshot_revision"), "snapshot_revision"
    )
    if expected_snapshot_revision is not None and revision != _non_negative_int64(
        expected_snapshot_revision, "expected_snapshot_revision"
    ):
        raise ValueError("prewar primary scope revision mismatch")
    date_raw = _signed_int32(root.get("date_raw"), "date_raw")
    declaration_id = normalize_prewar_declaration_id(root.get("declaration_id"))
    if declaration_id != normalize_prewar_declaration_id(expected_declaration_id):
        raise ValueError("prewar primary scope declaration mismatch")
    actor = _positive_int32(root.get("actor_character_id"), "actor_character_id")
    if actor != _positive_int32(
        expected_actor_character_id, "expected_actor_character_id"
    ):
        raise ValueError("prewar primary scope actor mismatch")
    effective_target = _positive_int32(
        root.get("effective_target_character_id"),
        "effective_target_character_id",
    )
    if effective_target == actor:
        raise ValueError("prewar primary scope sides collapse to one Character")

    participants = _normalize_primary_participants(
        root.get("primary_participants"), actor, effective_target
    )
    armies = _normalize_primary_armies(
        root.get("primary_raised_armies"), actor, effective_target
    )
    if root.get("readiness") != _READINESS:
        raise ValueError("prewar primary scope readiness overclaims or drifted")
    if root.get("provenance") != _PROVENANCE:
        raise ValueError("prewar primary scope provenance drifted")
    return {
        "schema_version": 1,
        "contract_stage": "declaration_bound_primary_scope_v1",
        "status": "available_primary_scope",
        "snapshot_revision": revision,
        "date_raw": date_raw,
        "declaration_id": declaration_id,
        "actor_character_id": actor,
        "effective_target_character_id": effective_target,
        "primary_participants": participants,
        "primary_raised_armies": armies,
        "readiness": dict(_READINESS),
        "provenance": {
            **_PROVENANCE,
            "unresolved_native_abis": list(_PROVENANCE["unresolved_native_abis"]),
        },
    }


def _normalize_primary_participants(
    value: object, actor: int, effective_target: int
) -> list[dict[str, object]]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("prewar primary_participants must contain two rows")
    expected = [
        (actor, "attacker", "declaration_primary_actor"),
        (effective_target, "defender", "declaration_effective_target"),
    ]
    result: list[dict[str, object]] = []
    for index, (raw, expected_row) in enumerate(zip(value, expected, strict=True)):
        row = _exact_object(
            raw,
            {"character_id", "side", "source", "join_certainty"},
            f"primary_participants[{index}]",
        )
        actual = (
            _positive_int32(
                row.get("character_id"),
                f"primary_participants[{index}].character_id",
            ),
            row.get("side"),
            row.get("source"),
        )
        if actual != expected_row or row.get("join_certainty") != "primary_required":
            raise ValueError("prewar primary participant identity/order drifted")
        result.append(dict(row))
    return result


def _normalize_primary_armies(
    value: object, actor: int, effective_target: int
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("prewar primary_raised_armies must be an array")
    result: list[dict[str, object]] = []
    seen: set[int] = set()
    previous_key: tuple[int, int] | None = None
    owner_side = {actor: "attacker", effective_target: "defender"}
    for index, raw in enumerate(value):
        row = _exact_object(
            raw,
            {
                "army_id",
                "owner_character_id",
                "side",
                "current_province_id",
                "route_province_ids",
            },
            f"primary_raised_armies[{index}]",
        )
        army_id = _positive_int32(
            row.get("army_id"), f"primary_raised_armies[{index}].army_id"
        )
        if army_id in seen:
            raise ValueError("prewar primary scope repeats a CUnitID")
        seen.add(army_id)
        owner = _positive_int32(
            row.get("owner_character_id"),
            f"primary_raised_armies[{index}].owner_character_id",
        )
        side = row.get("side")
        if owner_side.get(owner) != side:
            raise ValueError("prewar primary army owner/side drifted")
        current_raw = row.get("current_province_id")
        current = (
            None
            if current_raw is None
            else _positive_int32(
                current_raw,
                f"primary_raised_armies[{index}].current_province_id",
            )
        )
        raw_route = row.get("route_province_ids")
        if not isinstance(raw_route, list) or len(raw_route) > MAX_ROUTE_PROVINCES:
            raise ValueError("prewar primary army route is malformed")
        route = [
            _positive_int32(
                province_id,
                f"primary_raised_armies[{index}].route_province_ids[{route_index}]",
            )
            for route_index, province_id in enumerate(raw_route)
        ]
        sort_key = (0 if side == "attacker" else 1, army_id)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("prewar primary armies are not in canonical order")
        previous_key = sort_key
        result.append(
            {
                "army_id": army_id,
                "owner_character_id": owner,
                "side": side,
                "current_province_id": current,
                "route_province_ids": route,
            }
        )
    return result


def _exact_object(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} schema is malformed")
    return value


def _signed_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a signed int32")
    return value


def _positive_int32(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be a positive full-generation ID")
    return result


def _non_negative_int32(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _non_negative_int64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 2**63 - 1
    ):
        raise ValueError(f"{name} must be a non-negative int64")
    return value
