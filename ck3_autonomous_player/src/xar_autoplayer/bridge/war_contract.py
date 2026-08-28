"""Canonical native CK3 war and army state shared by MCP and the planner."""

from __future__ import annotations

from collections.abc import Iterable


MOVE_ARMY_CAPABILITY = "game.command.move-army-N-to-N"
PREVIEW_MOVE_ARMY_CAPABILITY = "game.command.preview-move-army-N-to-N"
QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY = (
    "game.command.query-route-contact-horizon-v1-N"
)
ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX = (
    "advance-route-contact-horizon-v1-"
)
DISBAND_ARMY_CAPABILITY = "game.command.disband-army-N"
SPLIT_ARMY_HALF_CAPABILITY = "game.command.split-army-half-N"
MERGE_ARMIES_CAPABILITY = "game.command.merge-armies-N-with-N"
START_ASSAULT_CAPABILITY = "game.command.start-assault-N"
STOP_ASSAULT_CAPABILITY = "game.command.stop-assault-N"
ENFORCE_DEMANDS_CAPABILITY = "game.command.enforce-demands-N"
QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY = (
    "game.command.query-war-termination-options-N"
)
QUERY_WAR_TERMINATION_TERMS_CAPABILITY = (
    "game.command.query-war-termination-terms-v1-N"
)
QUERY_ARMY_STRENGTHS_CAPABILITY = (
    "game.command.query-army-strengths-v1"
)
QUERY_ARMY_STRENGTHS_STEP = "query-army-strengths-v1"
SURRENDER_WAR_CAPABILITY = "game.command.surrender-war-N"
OFFER_WHITE_PEACE_CAPABILITY = "game.command.offer-white-peace-N"
ARMY_ROUTES_CAPABILITY = "game.state.army-routes"
WAR_PRIMARY_OPPONENT_CAPABILITY = "game.state.war-primary-opponent"
WAR_OBJECTIVES_CAPABILITY = "game.state.war-objectives"
WAR_OBJECTIVE_OCCUPATION_CAPABILITY = (
    "game.state.war-objective-occupation"
)
WAR_OBJECTIVE_FORT_LEVEL_CAPABILITY = (
    "game.state.war-objective-fort-level"
)
WAR_OBJECTIVE_GARRISON_CAPABILITY = "game.state.war-objective-garrison"
WAR_OBJECTIVE_SIEGE_PROGRESS_CAPABILITY = (
    "game.state.war-objective-siege-progress"
)
WAR_OBJECTIVE_ASSAULT_CAPABILITY = "game.state.war-objective-assault"
RAISE_TROOPS_STEP = "raise-troops-default"
BATTLE_DECISION_EPOCH_ADVANCE_STEP = "battle-decision-epoch-advance"
BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX = (
    BATTLE_DECISION_EPOCH_ADVANCE_STEP + "-to-"
)
COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP = (
    "committed-route-sentinel-advance"
)
COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX = (
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP + "-army-"
)
BATTLE_TERMINAL_CRUISE_STEP = "battle-terminal-cruise"
BATTLE_SENTINEL_ADVANCE_STEPS = frozenset(
    {
        BATTLE_DECISION_EPOCH_ADVANCE_STEP,
        BATTLE_TERMINAL_CRUISE_STEP,
    }
)

CK3_FIXED_POINT_SCALE = 100_000
MAX_ARMY_STRENGTH_REQUEST_IDS = 64
MAX_ROUTE_CONTACT_HOSTILE_IDS = 64

_TERMINATION_TERMS_GAME_VERSION = "1.19.0.6"
_TERMINATION_TERMS_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
_TERMINATION_TERMS_CLAIM_SCRIPT_SHA256 = (
    "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1"
)
_TERMINATION_TERMS_NATIVE_READER = "CWar+0x270/+0x290;0x28B1AA0"
_TERMINATION_TERMS_CLAIM_LIFECYCLE = (
    "present_only_vtable_slot_0_delete_flags_0"
)
_TERMINATION_TERMS_OUTCOMES = {
    "attacker_victory": {
        "declared_title_disposition": (
            "transfer_to_claimant_via_conquest_claim"
        ),
        "claim_disposition": "resolve_with_add_claim_on_loss",
    },
    "white_peace": {
        "declared_title_disposition": "unchanged",
        "claim_disposition": "retain_and_strengthen_weak",
    },
    "attacker_defeat": {
        "declared_title_disposition": "unchanged",
        "claim_disposition": "remove_declared_target_claims",
    },
}

_ARMY_STRENGTH_ROW_KEYS = {
    "status",
    "army_id",
    "native_carmy_id",
    "scope_role",
    "war_ids",
    "regiment_count",
    "current_soldiers",
    "maximum_soldiers",
    "ai_base_power_raw",
    "ai_base_power_scale",
    "unavailable_reason",
}
_ARMY_STRENGTH_SCOPE_ROLES = {
    "player",
    "active_war_ally",
    "active_war_enemy",
}


def normalize_active_wars(value: object) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("native active_wars must be an array")
    result: list[dict[str, object]] = []
    for index, raw_war in enumerate(value):
        if not isinstance(raw_war, dict):
            raise ValueError(f"native active_wars[{index}] must be an object")
        war_id = _non_negative_id(raw_war.get("war_id"), "war_id")
        player_side = raw_war.get("player_side")
        if player_side not in {"attacker", "defender"}:
            raise ValueError(
                f"native active_wars[{index}].player_side is malformed"
            )
        score = raw_war.get("player_relative_war_score")
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError(
                "native active_wars"
                f"[{index}].player_relative_war_score is malformed"
            )
        primary_opponent_character_id = raw_war.get(
            "primary_opponent_character_id"
        )
        if primary_opponent_character_id is not None:
            primary_opponent_character_id = _non_negative_id(
                primary_opponent_character_id,
                "primary_opponent_character_id",
            )
        player_is_primary_war_leader = raw_war.get(
            "player_is_primary_war_leader"
        )
        if (
            player_is_primary_war_leader is not None
            and not isinstance(player_is_primary_war_leader, bool)
        ):
            raise ValueError(
                "native active_wars"
                f"[{index}].player_is_primary_war_leader is malformed"
            )
        enemy_primary_default_raise_province_id = raw_war.get(
            "enemy_primary_default_raise_province_id"
        )
        if enemy_primary_default_raise_province_id is not None:
            enemy_primary_default_raise_province_id = _non_negative_id(
                enemy_primary_default_raise_province_id,
                "enemy_primary_default_raise_province_id",
            )
        objective_province_ids = _non_negative_id_list(
            raw_war.get("war_objective_province_ids"),
            f"active_wars[{index}].war_objective_province_ids",
        )
        result.append(
            {
                "war_id": war_id,
                "player_side": player_side,
                "primary_opponent_character_id": (
                    primary_opponent_character_id
                ),
                "player_is_primary_war_leader": (
                    player_is_primary_war_leader
                ),
                "enemy_primary_default_raise_province_id": (
                    enemy_primary_default_raise_province_id
                ),
                "targeted_title_ids": _non_negative_id_list(
                    raw_war.get("targeted_title_ids"),
                    f"active_wars[{index}].targeted_title_ids",
                ),
                "war_objective_province_ids": objective_province_ids,
                "objective_province_states": (
                    normalize_objective_province_states(
                        raw_war.get("objective_province_states"),
                        objective_province_ids=objective_province_ids,
                        name=(
                            f"active_wars[{index}]"
                            ".objective_province_states"
                        ),
                    )
                ),
                "player_relative_war_score": score,
                "allied_armies": normalize_armies(
                    raw_war.get("allied_armies"),
                    name=f"active_wars[{index}].allied_armies",
                ),
                "enemy_armies": normalize_armies(
                    raw_war.get("enemy_armies"),
                    name=f"active_wars[{index}].enemy_armies",
                ),
                "source": "native",
            }
        )
    return result


def normalize_objective_province_states(
    value: object,
    *,
    objective_province_ids: list[int],
    name: str = "objective_province_states",
) -> list[dict[str, object]]:
    """Normalize the paused-only rich state for exact war objectives.

    An empty array is a valid unavailable projection: older adapters do not
    publish this additive field, and the native reader atomically suppresses
    a war whose rows exceed its shared snapshot budget.  A non-empty array is
    complete and must exactly follow the objective ID order.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    normalized = [
        _normalize_objective_province_state(
            row,
            name=f"{name}[{index}]",
        )
        for index, row in enumerate(value)
    ]
    if normalized and [
        int(row["province_id"]) for row in normalized
    ] != objective_province_ids:
        raise ValueError(
            f"native {name} must completely match war_objective_province_ids"
        )
    return normalized


def _normalize_objective_province_state(
    value: object, *, name: str
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"native {name} must be an object")
    province_id = _positive_int32_id(
        value.get("province_id"), f"{name}.province_id"
    )
    occupation_observable = _strict_bool(
        value.get("occupation_observable"),
        f"{name}.occupation_observable",
    )
    is_occupied = value.get("is_occupied")
    occupying_character_id = value.get("occupying_character_id")
    if not occupation_observable:
        if is_occupied is not None or occupying_character_id is not None:
            raise ValueError(
                f"native {name} cannot publish an unobservable occupation"
            )
    else:
        is_occupied = _strict_bool(is_occupied, f"{name}.is_occupied")
        if is_occupied:
            occupying_character_id = _positive_int32_id(
                occupying_character_id,
                f"{name}.occupying_character_id",
            )
        elif occupying_character_id is not None:
            raise ValueError(
                f"native {name} cannot publish an occupant when unoccupied"
            )

    fort_level = _optional_non_negative_int32(
        value.get("fort_level"), f"{name}.fort_level"
    )
    garrison_size = _optional_non_negative_int32(
        value.get("garrison_size"), f"{name}.garrison_size"
    )
    besieging_strength = _optional_non_negative_int32(
        value.get("besieging_strength"), f"{name}.besieging_strength"
    )
    siege_observable = _strict_bool(
        value.get("siege_observable"), f"{name}.siege_observable"
    )
    raw_active_siege = value.get("active_siege")
    if not siege_observable:
        if raw_active_siege is not None:
            raise ValueError(
                f"native {name} cannot publish an unobservable active siege"
            )
        active_siege = None
    elif raw_active_siege is None:
        active_siege = None
    else:
        active_siege = _normalize_active_siege(
            raw_active_siege, name=f"{name}.active_siege"
        )
    return {
        "province_id": province_id,
        "occupation_observable": occupation_observable,
        "is_occupied": is_occupied,
        "occupying_character_id": occupying_character_id,
        "fort_level": fort_level,
        "garrison_size": garrison_size,
        "besieging_strength": besieging_strength,
        "siege_observable": siege_observable,
        "active_siege": active_siege,
    }


def _normalize_active_siege(
    value: object, *, name: str
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"native {name} must be an object or null")
    progress = _fixed_point(
        value.get("progress_fraction"),
        f"{name}.progress_fraction",
        fraction=True,
    )
    current = _fixed_point(
        value.get("current_work"), f"{name}.current_work"
    )
    total = _fixed_point(value.get("total_work"), f"{name}.total_work")
    assault_observable = value.get("assault_observable", False)
    if not isinstance(assault_observable, bool):
        raise ValueError(
            f"native {name}.assault_observable must be a boolean"
        )
    assault_fields = (
        "breach_level",
        "assault_in_progress",
        "can_start_assault",
        "can_stop_assault",
        "assault_daily_progress",
        "assault_daily_casualties",
    )
    if not assault_observable:
        if any(value.get(field) is not None for field in assault_fields):
            raise ValueError(
                f"native {name} cannot publish an unobservable assault"
            )
        breach_level = None
        assault_in_progress = None
        can_start_assault = None
        can_stop_assault = None
        assault_daily_progress = None
        assault_daily_casualties = None
    else:
        breach_level = _optional_non_negative_int32(
            value.get("breach_level"), f"{name}.breach_level"
        )
        if breach_level is None or breach_level > 2:
            raise ValueError(
                f"native {name}.breach_level must be in range 0..2"
            )
        assault_in_progress = _strict_bool(
            value.get("assault_in_progress"),
            f"{name}.assault_in_progress",
        )
        can_start_assault = _strict_bool(
            value.get("can_start_assault"), f"{name}.can_start_assault"
        )
        can_stop_assault = _strict_bool(
            value.get("can_stop_assault"), f"{name}.can_stop_assault"
        )
        assault_daily_progress = _fixed_point(
            value.get("assault_daily_progress"),
            f"{name}.assault_daily_progress",
        )
        assault_daily_casualties = _optional_non_negative_int32(
            value.get("assault_daily_casualties"),
            f"{name}.assault_daily_casualties",
        )
        if assault_daily_casualties is None:
            raise ValueError(
                f"native {name}.assault_daily_casualties is required"
            )
    return {
        "siege_id": _positive_int32_id(
            value.get("siege_id"), f"{name}.siege_id"
        ),
        "besieging_army_id": _optional_positive_int32_id(
            value.get("besieging_army_id"),
            f"{name}.besieging_army_id",
        ),
        "player_army_besieging": _strict_bool(
            value.get("player_army_besieging"),
            f"{name}.player_army_besieging",
        ),
        "progress_fraction": progress,
        "current_work": current,
        "total_work": total,
        "remaining_work": {
            "raw": max(int(total["raw"]) - int(current["raw"]), 0),
            "scale": CK3_FIXED_POINT_SCALE,
        },
        "days_left": _optional_non_negative_int32(
            value.get("days_left"), f"{name}.days_left"
        ),
        "assault_observable": assault_observable,
        "breach_level": breach_level,
        "walls_breached": (
            breach_level > 0 if breach_level is not None else None
        ),
        "assault_in_progress": assault_in_progress,
        "can_start_assault": can_start_assault,
        "can_stop_assault": can_stop_assault,
        "assault_daily_progress": assault_daily_progress,
        "assault_daily_casualties": assault_daily_casualties,
    }


def _fixed_point(
    value: object, name: str, *, fraction: bool = False
) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError(f"native {name} must contain raw and scale")
    raw = value.get("raw")
    scale = value.get("scale")
    if (
        isinstance(raw, bool)
        or not isinstance(raw, int)
        or raw < 0
        or raw > 2**63 - 1
        or scale != CK3_FIXED_POINT_SCALE
    ):
        raise ValueError(f"native {name} fixed value is malformed")
    if fraction and raw > CK3_FIXED_POINT_SCALE:
        raise ValueError(f"native {name} fraction is out of range")
    return {"raw": raw, "scale": CK3_FIXED_POINT_SCALE}


def normalize_armies(
    value: object, *, name: str = "player_armies"
) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    result: list[dict[str, object]] = []
    for index, raw_army in enumerate(value):
        if not isinstance(raw_army, dict):
            raise ValueError(f"native {name}[{index}] must be an object")
        soldiers = raw_army.get("soldiers")
        # One early reverse-engineering fixture used this spelling.  Accept it
        # on input, but never expose it through the canonical MCP snapshot.
        if soldiers is None:
            soldiers = raw_army.get("soldier_count")
        if (
            soldiers is not None
            and (
                isinstance(soldiers, bool)
                or not isinstance(soldiers, int)
                or soldiers < 0
            )
        ):
            raise ValueError(f"native {name}[{index}].soldiers is malformed")
        current_province_id = raw_army.get("current_province_id")
        if current_province_id is not None:
            current_province_id = _non_negative_id(
                current_province_id, "current_province_id"
            )
        move_target = raw_army.get("move_target_province_id")
        explicit_observable = raw_army.get("move_target_observable")
        if explicit_observable is not None and not isinstance(
            explicit_observable, bool
        ):
            raise ValueError(
                f"native {name}[{index}].move_target_observable is malformed"
            )
        move_target_observable = (
            explicit_observable
            if isinstance(explicit_observable, bool)
            else "move_target_province_id" in raw_army
        )
        if move_target is not None:
            move_target = _non_negative_id(
                move_target, "move_target_province_id"
            )
        route_province_ids = raw_army.get("route_province_ids")
        if "route_province_ids" in raw_army and not isinstance(
            route_province_ids, list
        ):
            raise ValueError(
                f"native {name}[{index}].route_province_ids must be an array"
            )
        controllable = raw_army.get("controllable")
        if not isinstance(controllable, bool):
            raise ValueError(f"native {name}[{index}].controllable is malformed")
        normalized: dict[str, object] = {
                "army_id": _non_negative_id(raw_army.get("army_id"), "army_id"),
                "owner_character_id": _non_negative_id(
                    raw_army.get("owner_character_id"), "owner_character_id"
                ),
                "soldiers": soldiers,
                "current_province_id": current_province_id,
                "move_target_province_id": move_target,
                "move_target_observable": move_target_observable,
                "controllable": controllable,
                "source": "native",
            }
        if "route_province_ids" in raw_army:
            normalized["route_province_ids"] = [
                _positive_int32_id(
                    province_id,
                    f"{name}[{index}].route_province_ids",
                )
                for province_id in (
                    route_province_ids
                    if isinstance(route_province_ids, list)
                    else []
                )
            ]
        for optional_flag in ("in_combat", "retreating"):
            flag = raw_army.get(optional_flag)
            if flag is not None and not isinstance(flag, bool):
                raise ValueError(
                    f"native {name}[{index}].{optional_flag} is malformed"
                )
            if isinstance(flag, bool):
                normalized[optional_flag] = flag
        army_state = raw_army.get("army_state")
        if army_state is not None and (
            not isinstance(army_state, str) or not army_state
        ):
            raise ValueError(f"native {name}[{index}].army_state is malformed")
        if isinstance(army_state, str):
            normalized["army_state"] = army_state
        army_state_code = raw_army.get("army_state_code")
        if army_state_code is not None:
            normalized["army_state_code"] = _non_negative_id(
                army_state_code, "army_state_code"
            )
        result.append(normalized)
    return result


_ROUTE_CONTACT_HORIZON_KEYS = {
    "status",
    "date_raw",
    "snapshot_revision",
    "subject_army_id",
    "target_province_id",
    "hostile_army_ids",
    "subject_route",
    "hostile_routes",
    "horizon_start_date_raw",
    "horizon_end_date_raw",
    "one_day_contact_free",
    "conflicts",
}
_TIMED_ROUTE_KEYS = {
    "timeline_observable",
    "army_id",
    "current_province_id",
    "effective_origin_province_id",
    "route_province_ids",
    "arrival_date_raws",
}
_SAME_PROVINCE_CONFLICT_KEYS = {
    "kind",
    "hostile_army_id",
    "province_id",
    "overlap_start_date_raw",
    "overlap_end_date_raw",
}
_OPPOSING_EDGE_CONFLICT_KEYS = {
    "kind",
    "hostile_army_id",
    "subject_from_province_id",
    "subject_to_province_id",
    "hostile_from_province_id",
    "hostile_to_province_id",
    "overlap_start_date_raw",
    "overlap_end_date_raw",
}


def normalize_route_contact_horizon(
    value: object,
    *,
    expected_subject_army_id: int,
    expected_target_province_id: int,
    expected_hostile_army_ids: Iterable[int],
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Validate the atomic one-day native route/contact proof."""
    if not isinstance(value, dict) or set(value) != _ROUTE_CONTACT_HORIZON_KEYS:
        raise ValueError("native route_contact_horizon has a malformed schema")
    if value.get("status") != "available":
        raise ValueError("native route_contact_horizon is not available")
    subject = _positive_int32_id(
        value.get("subject_army_id"), "route_contact_horizon.subject_army_id"
    )
    target = _positive_int32_id(
        value.get("target_province_id"),
        "route_contact_horizon.target_province_id",
    )
    date_raw = _signed_int32(
        value.get("date_raw"), "route_contact_horizon.date_raw"
    )
    revision = value.get("snapshot_revision")
    if (
        isinstance(revision, bool)
        or not isinstance(revision, int)
        or not 1 <= revision <= 2**64 - 1
    ):
        raise ValueError(
            "route_contact_horizon.snapshot_revision must be positive uint64"
        )
    expected_hostiles = sorted(
        {
            _positive_int32_id(army_id, "expected_hostile_army_ids")
            for army_id in expected_hostile_army_ids
        }
    )
    hostile_ids = [
        _positive_int32_id(
            army_id, "route_contact_horizon.hostile_army_ids"
        )
        for army_id in _required_list(
            value.get("hostile_army_ids"),
            "route_contact_horizon.hostile_army_ids",
        )
    ]
    if (
        subject != expected_subject_army_id
        or target != expected_target_province_id
        or date_raw != expected_date_raw
        or revision != expected_snapshot_revision
        or hostile_ids != expected_hostiles
        or not hostile_ids
        or subject in hostile_ids
    ):
        raise ValueError("native route_contact_horizon scope binding disagrees")

    subject_route = _normalize_timed_route(
        value.get("subject_route"),
        expected_army_id=subject,
        date_raw=date_raw,
        name="route_contact_horizon.subject_route",
    )
    if not (
        subject_route["route_province_ids"]
        and subject_route["route_province_ids"][-1] == target
        or not subject_route["route_province_ids"]
        and subject_route["current_province_id"] == target
    ):
        raise ValueError("native route_contact_horizon subject route misses target")
    raw_hostile_routes = _required_list(
        value.get("hostile_routes"),
        "route_contact_horizon.hostile_routes",
    )
    hostile_routes = [
        _normalize_timed_route(
            route,
            expected_army_id=hostile_ids[index],
            date_raw=date_raw,
            name=f"route_contact_horizon.hostile_routes[{index}]",
        )
        for index, route in enumerate(raw_hostile_routes)
    ] if len(raw_hostile_routes) == len(hostile_ids) else []
    if len(hostile_routes) != len(hostile_ids):
        raise ValueError("native route_contact_horizon hostile scope is incomplete")

    horizon_start = _signed_int32(
        value.get("horizon_start_date_raw"),
        "route_contact_horizon.horizon_start_date_raw",
    )
    horizon_end = _signed_int32(
        value.get("horizon_end_date_raw"),
        "route_contact_horizon.horizon_end_date_raw",
    )
    contact_free = _strict_bool(
        value.get("one_day_contact_free"),
        "route_contact_horizon.one_day_contact_free",
    )
    if horizon_start != date_raw or horizon_end != date_raw + 24:
        raise ValueError("native route_contact_horizon is not a one-day window")
    raw_conflicts = _required_list(
        value.get("conflicts"), "route_contact_horizon.conflicts"
    )
    conflicts: list[dict[str, object]] = []
    for index, conflict in enumerate(raw_conflicts):
        if not isinstance(conflict, dict):
            raise ValueError(
                f"native route_contact_horizon.conflicts[{index}] is malformed"
            )
        kind = conflict.get("kind")
        expected_keys = (
            _SAME_PROVINCE_CONFLICT_KEYS
            if kind == "same_province"
            else _OPPOSING_EDGE_CONFLICT_KEYS
            if kind == "opposing_edge"
            else None
        )
        if expected_keys is None or set(conflict) != expected_keys:
            raise ValueError(
                f"native route_contact_horizon.conflicts[{index}] has an unknown shape"
            )
        hostile_id = _positive_int32_id(
            conflict.get("hostile_army_id"),
            f"route_contact_horizon.conflicts[{index}].hostile_army_id",
        )
        if hostile_id not in hostile_ids:
            raise ValueError(
                f"native route_contact_horizon.conflicts[{index}] lacks scope"
            )
        normalized_conflict: dict[str, object] = {
            "kind": kind,
            "hostile_army_id": hostile_id,
        }
        id_fields = (
            ("province_id",)
            if kind == "same_province"
            else (
                "subject_from_province_id",
                "subject_to_province_id",
                "hostile_from_province_id",
                "hostile_to_province_id",
            )
        )
        for field in id_fields:
            normalized_conflict[field] = _positive_int32_id(
                conflict.get(field),
                f"route_contact_horizon.conflicts[{index}].{field}",
            )
        overlap_start = _signed_int32(
            conflict.get("overlap_start_date_raw"),
            f"route_contact_horizon.conflicts[{index}].overlap_start_date_raw",
        )
        overlap_end = _signed_int32(
            conflict.get("overlap_end_date_raw"),
            f"route_contact_horizon.conflicts[{index}].overlap_end_date_raw",
        )
        if not (
            horizon_start <= overlap_start <= overlap_end <= horizon_end
        ):
            raise ValueError(
                f"native route_contact_horizon.conflicts[{index}] is outside the horizon"
            )
        normalized_conflict["overlap_start_date_raw"] = overlap_start
        normalized_conflict["overlap_end_date_raw"] = overlap_end
        conflicts.append(normalized_conflict)
    if contact_free == bool(conflicts):
        raise ValueError("native route_contact_horizon predicate disagrees")
    return {
        "status": "available",
        "date_raw": date_raw,
        "snapshot_revision": revision,
        "subject_army_id": subject,
        "target_province_id": target,
        "hostile_army_ids": hostile_ids,
        "subject_route": subject_route,
        "hostile_routes": hostile_routes,
        "horizon_start_date_raw": horizon_start,
        "horizon_end_date_raw": horizon_end,
        "one_day_contact_free": contact_free,
        "conflicts": conflicts,
    }


def _normalize_timed_route(
    value: object,
    *,
    expected_army_id: int,
    date_raw: int,
    name: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _TIMED_ROUTE_KEYS:
        raise ValueError(f"native {name} has a malformed schema")
    if value.get("timeline_observable") is not True:
        raise ValueError(f"native {name} timeline is not observable")
    army_id = _positive_int32_id(value.get("army_id"), f"{name}.army_id")
    current = _positive_int32_id(
        value.get("current_province_id"), f"{name}.current_province_id"
    )
    effective_origin = _positive_int32_id(
        value.get("effective_origin_province_id"),
        f"{name}.effective_origin_province_id",
    )
    route = [
        _positive_int32_id(province_id, f"{name}.route_province_ids")
        for province_id in _required_list(
            value.get("route_province_ids"), f"{name}.route_province_ids"
        )
    ]
    arrivals = [
        _signed_int32(arrival, f"{name}.arrival_date_raws")
        for arrival in _required_list(
            value.get("arrival_date_raws"), f"{name}.arrival_date_raws"
        )
    ]
    if (
        army_id != expected_army_id
        or len(route) != len(arrivals)
        or not route
        and effective_origin != current
        or route
        and effective_origin not in {current, route[0]}
        or any(arrival < date_raw for arrival in arrivals)
        or any(left > right for left, right in zip(arrivals, arrivals[1:]))
    ):
        raise ValueError(f"native {name} timeline is malformed")
    return {
        "timeline_observable": True,
        "army_id": army_id,
        "current_province_id": current,
        "effective_origin_province_id": effective_origin,
        "route_province_ids": route,
        "arrival_date_raws": arrivals,
    }


def stationary_province_contact_free_in_horizon(
    value: object,
    province_id: int,
) -> bool:
    """Project one stationary Province against a validated hostile timeline.

    The route-contact query is subject-bound, but its hostile route array is
    complete for the exact paused frame.  A stationary friendly army can
    therefore reuse that array: contact exists when a hostile already occupies
    its Province at the closed-window start, or arrives there on/before the
    closed-window end.
    """
    province = _positive_int32_id(
        province_id, "stationary route-contact province_id"
    )
    if not isinstance(value, dict):
        raise ValueError("stationary route-contact horizon must be an object")
    subject = _positive_int32_id(
        value.get("subject_army_id"),
        "stationary route-contact subject_army_id",
    )
    target = _positive_int32_id(
        value.get("target_province_id"),
        "stationary route-contact target_province_id",
    )
    date_raw = _signed_int32(
        value.get("date_raw"), "stationary route-contact date_raw"
    )
    revision = value.get("snapshot_revision")
    hostile_ids = _required_list(
        value.get("hostile_army_ids"),
        "stationary route-contact hostile_army_ids",
    )
    normalized = normalize_route_contact_horizon(
        value,
        expected_subject_army_id=subject,
        expected_target_province_id=target,
        expected_hostile_army_ids=hostile_ids,
        expected_date_raw=date_raw,
        expected_snapshot_revision=revision,
    )
    horizon_start = int(normalized["horizon_start_date_raw"])
    horizon_end = int(normalized["horizon_end_date_raw"])
    routes = normalized["hostile_routes"]
    if not isinstance(routes, list):
        raise ValueError("stationary route-contact hostile routes are malformed")
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError("stationary route-contact hostile route is malformed")
        if route.get("current_province_id") == province:
            return False
        provinces = route.get("route_province_ids")
        arrivals = route.get("arrival_date_raws")
        if not isinstance(provinces, list) or not isinstance(arrivals, list):
            raise ValueError("stationary route-contact timeline is malformed")
        for route_province, arrival in zip(provinces, arrivals, strict=True):
            if (
                route_province == province
                and horizon_start <= arrival <= horizon_end
            ):
                return False
    return True


def unavoidable_current_province_contact_in_horizon(
    value: object,
) -> bool:
    """Recognize the narrow one-day contact transition that rerouting cannot beat.

    This is deliberately stricter than ``one_day_contact_free is False``.  It
    only accepts a moving subject whose first timed arrival is after the closed
    one-day window and whose complete conflict set consists of same-Province
    overlaps at the subject's current Province.  In that shape a new target
    cannot move the army off its already committed edge before contact.
    """
    if not isinstance(value, dict):
        return False
    if (
        value.get("status") != "available"
        or value.get("one_day_contact_free") is not False
    ):
        return False
    subject_route = value.get("subject_route")
    conflicts = value.get("conflicts")
    horizon_end = value.get("horizon_end_date_raw")
    if (
        not isinstance(subject_route, dict)
        or not isinstance(conflicts, list)
        or not conflicts
        or isinstance(horizon_end, bool)
        or not isinstance(horizon_end, int)
    ):
        return False
    current_province_id = subject_route.get("current_province_id")
    route = subject_route.get("route_province_ids")
    arrivals = subject_route.get("arrival_date_raws")
    if (
        isinstance(current_province_id, bool)
        or not isinstance(current_province_id, int)
        or current_province_id <= 0
        or not isinstance(route, list)
        or not route
        or not isinstance(arrivals, list)
        or len(arrivals) != len(route)
        or isinstance(arrivals[0], bool)
        or not isinstance(arrivals[0], int)
        or arrivals[0] <= horizon_end
    ):
        return False
    return all(
        isinstance(conflict, dict)
        and conflict.get("kind") == "same_province"
        and conflict.get("province_id") == current_province_id
        and isinstance(conflict.get("overlap_start_date_raw"), int)
        and not isinstance(conflict.get("overlap_start_date_raw"), bool)
        and conflict["overlap_start_date_raw"] <= horizon_end
        for conflict in conflicts
    )


def player_armies_from_state(
    active_wars: Iterable[dict[str, object]],
    explicit_player_armies: object,
) -> list[dict[str, object]]:
    """Merge the postwar top-level list with armies embedded in active wars."""
    explicit = (
        normalize_armies(explicit_player_armies)
        if explicit_player_armies is not None
        else []
    )
    allied: list[dict[str, object]] = []
    for war in active_wars:
        rows = war.get("allied_armies")
        if isinstance(rows, list):
            allied.extend(
                row
                for row in rows
                if isinstance(row, dict) and row.get("controllable") is True
            )
    return deduplicate_armies([*explicit, *allied])


def enemy_armies_from_wars(
    active_wars: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    enemies: list[dict[str, object]] = []
    for war in active_wars:
        rows = war.get("enemy_armies")
        if isinstance(rows, list):
            enemies.extend(row for row in rows if isinstance(row, dict))
    return deduplicate_armies(enemies)


def enemy_primary_default_raise_province_ids(
    active_wars: Iterable[dict[str, object]],
) -> list[int]:
    """Return stable fallback objectives published for active wars."""
    province_ids: list[int] = []
    seen: set[int] = set()
    for war in active_wars:
        province_id = war.get("enemy_primary_default_raise_province_id")
        if (
            isinstance(province_id, int)
            and not isinstance(province_id, bool)
            and province_id not in seen
        ):
            seen.add(province_id)
            province_ids.append(province_id)
    return province_ids


def war_objective_province_ids(
    active_wars: Iterable[dict[str, object]],
) -> list[int]:
    """Return exact objectives in the adapter's stable traversal order."""
    province_ids: list[int] = []
    seen: set[int] = set()
    for war in active_wars:
        raw = war.get("war_objective_province_ids")
        if isinstance(raw, list):
            for province_id in raw:
                if (
                    isinstance(province_id, int)
                    and not isinstance(province_id, bool)
                    and province_id not in seen
                ):
                    seen.add(province_id)
                    province_ids.append(province_id)
    return province_ids


def controllable_armies(
    armies: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    return [army for army in armies if army.get("controllable") is True]


def deduplicate_armies(
    armies: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    by_id: dict[int, dict[str, object]] = {}
    for army in armies:
        army_id = army.get("army_id")
        if isinstance(army_id, bool) or not isinstance(army_id, int):
            continue
        by_id.setdefault(army_id, dict(army))
    return list(by_id.values())


def army_strength_scope(
    snapshot: dict[str, object],
) -> list[dict[str, object]]:
    """Derive the exact public-CUnit scope of one paused strength query.

    Membership, ordering, and roles come only from the already published
    snapshot.  Character ownership is deliberately irrelevant: it cannot
    safely reconstruct a war relation lane.
    """
    raw_player_armies = snapshot.get("player_armies")
    raw_active_wars = snapshot.get("active_wars")
    if not isinstance(raw_player_armies, list):
        raise ValueError("army-strength scope requires player_armies")
    if not isinstance(raw_active_wars, list):
        raise ValueError("army-strength scope requires active_wars")

    rows: list[dict[str, object]] = []
    by_id: dict[int, dict[str, object]] = {}

    def admit(raw_army: object, role: str) -> None:
        if not isinstance(raw_army, dict):
            raise ValueError("army-strength scope contains a malformed army")
        army_id = _positive_int32_id(
            raw_army.get("army_id"), "army-strength scope army_id"
        )
        current = by_id.get(army_id)
        if current is None:
            current = {
                "army_id": army_id,
                "scope_role": role,
                "war_ids": [],
            }
            by_id[army_id] = current
            rows.append(current)
            return
        precedence = {
            "active_war_enemy": 0,
            "active_war_ally": 1,
            "player": 2,
        }
        if precedence[role] > precedence[str(current["scope_role"])]:
            current["scope_role"] = role

    for raw_army in raw_player_armies:
        admit(raw_army, "player")

    wars: list[tuple[int, list[object], list[object]]] = []
    for raw_war in raw_active_wars:
        if not isinstance(raw_war, dict):
            raise ValueError("army-strength scope contains a malformed war")
        war_id = _positive_int32_id(
            raw_war.get("war_id"), "army-strength scope war_id"
        )
        allied = raw_war.get("allied_armies")
        enemy = raw_war.get("enemy_armies")
        if not isinstance(allied, list) or not isinstance(enemy, list):
            raise ValueError(
                "army-strength scope requires allied and enemy army arrays"
            )
        wars.append((war_id, allied, enemy))
        for raw_army in allied:
            admit(raw_army, "active_war_ally")
        for raw_army in enemy:
            admit(raw_army, "active_war_enemy")

    for war_id, allied, enemy in wars:
        members: set[int] = set()
        for raw_army in [*allied, *enemy]:
            if not isinstance(raw_army, dict):
                raise ValueError(
                    "army-strength scope contains a malformed war army"
                )
            members.add(
                _positive_int32_id(
                    raw_army.get("army_id"),
                    "army-strength scope war army_id",
                )
            )
        for army_id in members:
            row = by_id[army_id]
            war_ids = row["war_ids"]
            if isinstance(war_ids, list) and war_id not in war_ids:
                war_ids.append(war_id)
    return rows


def normalize_army_strength_request_ids(value: object) -> list[int]:
    """Validate the explicit MCP subset without silently deduplicating it."""
    if not isinstance(value, list):
        raise ValueError("army_ids must be an array")
    if not 1 <= len(value) <= MAX_ARMY_STRENGTH_REQUEST_IDS:
        raise ValueError(
            "army_ids must contain between 1 and "
            f"{MAX_ARMY_STRENGTH_REQUEST_IDS} IDs"
        )
    result: list[int] = []
    seen: set[int] = set()
    for index, raw_army_id in enumerate(value):
        army_id = _positive_int32_id(
            raw_army_id, f"army_ids[{index}]"
        )
        if army_id in seen:
            raise ValueError("army_ids must not contain duplicates")
        seen.add(army_id)
        result.append(army_id)
    return result


def normalize_army_strengths(
    value: object,
    *,
    expected_scope: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    """Normalize one exact-build, row-atomic army strength result."""
    if not isinstance(value, list):
        raise ValueError("native army_strengths must be an array")
    rows = [
        _normalize_army_strength_row(
            raw_row, name=f"army_strengths[{index}]"
        )
        for index, raw_row in enumerate(value)
    ]
    ids = [int(row["army_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("native army_strengths contains duplicate ArmyIDs")
    if expected_scope is not None:
        expected_identity = [
            {
                "army_id": _positive_int32_id(
                    row.get("army_id"), "expected army-strength scope army_id"
                ),
                "scope_role": row.get("scope_role"),
                "war_ids": row.get("war_ids"),
            }
            for row in expected_scope
        ]
        actual_identity = [
            {
                "army_id": row["army_id"],
                "scope_role": row["scope_role"],
                "war_ids": row["war_ids"],
            }
            for row in rows
        ]
        if actual_identity != expected_identity:
            raise ValueError(
                "native army_strengths does not match the paused snapshot scope"
            )
    return rows


def army_strength_query_status(
    rows: Iterable[dict[str, object]],
) -> str:
    return (
        "available"
        if all(row.get("status") == "available" for row in rows)
        else "partial"
    )


def _normalize_army_strength_row(
    value: object, *, name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _ARMY_STRENGTH_ROW_KEYS:
        raise ValueError(f"native {name} schema is malformed")
    status = value.get("status")
    if status not in {"available", "unavailable"}:
        raise ValueError(f"native {name}.status is malformed")
    scope_role = value.get("scope_role")
    if scope_role not in _ARMY_STRENGTH_SCOPE_ROLES:
        raise ValueError(f"native {name}.scope_role is malformed")
    war_ids = _strict_positive_int32_id_list(
        value.get("war_ids"), f"{name}.war_ids"
    )
    native_carmy_id = _optional_positive_int32_id(
        value.get("native_carmy_id"), f"{name}.native_carmy_id"
    )
    regiment_count = _optional_non_negative_int32(
        value.get("regiment_count"), f"{name}.regiment_count"
    )
    current_soldiers = _optional_non_negative_int32(
        value.get("current_soldiers"), f"{name}.current_soldiers"
    )
    maximum_soldiers = _optional_non_negative_int32(
        value.get("maximum_soldiers"), f"{name}.maximum_soldiers"
    )
    ai_base_power_raw = value.get("ai_base_power_raw")
    if ai_base_power_raw is not None and (
        isinstance(ai_base_power_raw, bool)
        or not isinstance(ai_base_power_raw, int)
        or ai_base_power_raw < -(2**63)
        or ai_base_power_raw > 2**63 - 1
    ):
        raise ValueError(
            f"native {name}.ai_base_power_raw must be signed int64 or null"
        )
    if value.get("ai_base_power_scale") != CK3_FIXED_POINT_SCALE:
        raise ValueError(
            f"native {name}.ai_base_power_scale must be "
            f"{CK3_FIXED_POINT_SCALE}"
        )
    unavailable_reason = value.get("unavailable_reason")
    aggregates = (
        regiment_count,
        current_soldiers,
        maximum_soldiers,
        ai_base_power_raw,
    )
    if status == "available":
        if native_carmy_id is None or any(item is None for item in aggregates):
            raise ValueError(f"native available {name} is incomplete")
        if unavailable_reason is not None:
            raise ValueError(
                f"native available {name} cannot have unavailable_reason"
            )
    else:
        if any(item is not None for item in aggregates):
            raise ValueError(
                f"native unavailable {name} must null every aggregate"
            )
        if not isinstance(unavailable_reason, str) or not unavailable_reason:
            raise ValueError(
                f"native unavailable {name} requires a reason"
            )
    return {
        "status": status,
        "army_id": _positive_int32_id(value.get("army_id"), f"{name}.army_id"),
        "native_carmy_id": native_carmy_id,
        "scope_role": scope_role,
        "war_ids": war_ids,
        "regiment_count": regiment_count,
        "current_soldiers": current_soldiers,
        "maximum_soldiers": maximum_soldiers,
        "ai_base_power_raw": ai_base_power_raw,
        "ai_base_power_scale": CK3_FIXED_POINT_SCALE,
        "unavailable_reason": unavailable_reason,
    }


def move_army_step(army_id: int, province_id: int) -> str:
    return (
        f"move-army-{_non_negative_id(army_id, 'army_id')}"
        f"-to-{_non_negative_id(province_id, 'province_id')}"
    )


def preview_move_army_step(army_id: int, province_id: int) -> str:
    return (
        f"preview-move-army-{_positive_int32_id(army_id, 'army_id')}"
        f"-to-{_positive_int32_id(province_id, 'province_id')}"
    )


def query_route_contact_horizon_step(
    subject_army_id: int,
    target_province_id: int,
    hostile_army_ids: Iterable[int],
) -> str:
    """Build the canonical exact-build route/contact query literal."""
    subject = _positive_int32_id(subject_army_id, "subject_army_id")
    target = _positive_int32_id(target_province_id, "target_province_id")
    hostiles = sorted(
        {
            _positive_int32_id(army_id, "hostile_army_ids")
            for army_id in hostile_army_ids
        }
    )
    if not hostiles or len(hostiles) > MAX_ROUTE_CONTACT_HOSTILE_IDS:
        raise ValueError(
            "hostile_army_ids must contain 1..64 unique positive int32 IDs"
        )
    if subject in hostiles:
        raise ValueError("subject army cannot also be hostile")
    suffix = "-".join(str(army_id) for army_id in hostiles)
    return (
        f"query-route-contact-horizon-v1-{subject}-to-{target}"
        f"-h-{len(hostiles)}-{suffix}"
    )


def advance_route_contact_horizon_step(
    subject_army_id: int,
    target_province_id: int,
    hostile_army_ids: Iterable[int],
) -> str:
    """Build the proof-bound one-day composite step literal."""
    query = query_route_contact_horizon_step(
        subject_army_id, target_province_id, hostile_army_ids
    )
    return ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX + query.removeprefix(
        "query-route-contact-horizon-v1-"
    )


def disband_army_step(army_id: int) -> str:
    return f"disband-army-{_non_negative_id(army_id, 'army_id')}"


def split_army_half_step(army_id: int) -> str:
    return f"split-army-half-{_positive_int32_id(army_id, 'army_id')}"


def merge_armies_step(
    destination_army_id: int, source_army_id: int
) -> str:
    destination = _positive_int32_id(
        destination_army_id, "destination_army_id"
    )
    source = _positive_int32_id(source_army_id, "source_army_id")
    if destination == source:
        raise ValueError("merge army IDs must be distinct")
    return f"merge-armies-{destination}-with-{source}"


def start_assault_step(siege_id: int) -> str:
    return f"start-assault-{_positive_int32_id(siege_id, 'siege_id')}"


def stop_assault_step(siege_id: int) -> str:
    return f"stop-assault-{_positive_int32_id(siege_id, 'siege_id')}"


def enforce_demands_step(war_id: int) -> str:
    return f"enforce-demands-{_non_negative_id(war_id, 'war_id')}"


def query_war_termination_options_step(war_id: int) -> str:
    return (
        "query-war-termination-options-"
        f"{_positive_int32_id(war_id, 'war_id')}"
    )


def query_war_termination_terms_step(war_id: int) -> str:
    return (
        "query-war-termination-terms-v1-"
        f"{_positive_int32_id(war_id, 'war_id')}"
    )


def surrender_war_step(war_id: int) -> str:
    return f"surrender-war-{_positive_int32_id(war_id, 'war_id')}"


def offer_white_peace_step(war_id: int) -> str:
    return f"offer-white-peace-{_positive_int32_id(war_id, 'war_id')}"


def parse_move_army_step(step: object) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith("move-army-"):
        return None
    payload = step.removeprefix("move-army-")
    army_text, separator, province_text = payload.partition("-to-")
    if (
        not separator
        or not army_text.isdigit()
        or not province_text.isdigit()
    ):
        return None
    return int(army_text), int(province_text)


def parse_preview_move_army_step(step: object) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith("preview-move-army-"):
        return None
    payload = step.removeprefix("preview-move-army-")
    army_text, separator, province_text = payload.partition("-to-")
    if (
        not separator
        or not army_text.isdigit()
        or not province_text.isdigit()
    ):
        return None
    army_id = int(army_text)
    province_id = int(province_text)
    if not (0 < army_id <= 2**31 - 1 and 0 < province_id <= 2**31 - 1):
        return None
    return army_id, province_id


def parse_query_route_contact_horizon_step(
    step: object,
) -> tuple[int, int, tuple[int, ...]] | None:
    prefix = "query-route-contact-horizon-v1-"
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    payload = step.removeprefix(prefix)
    subject_text, to_separator, tail = payload.partition("-to-")
    target_text, hostile_separator, hostile_tail = tail.partition("-h-")
    if (
        not to_separator
        or not hostile_separator
        or not subject_text.isdigit()
        or not target_text.isdigit()
    ):
        return None
    count_text, count_separator, ids_text = hostile_tail.partition("-")
    if not count_separator or not count_text.isdigit() or not ids_text:
        return None
    subject = int(subject_text)
    target = int(target_text)
    count = int(count_text)
    id_tokens = ids_text.split("-")
    if (
        not 0 < subject <= 2**31 - 1
        or not 0 < target <= 2**31 - 1
        or not 0 < count <= MAX_ROUTE_CONTACT_HOSTILE_IDS
        or len(id_tokens) != count
        or any(not token.isdigit() for token in id_tokens)
    ):
        return None
    hostiles = tuple(int(token) for token in id_tokens)
    if (
        any(not 0 < army_id <= 2**31 - 1 for army_id in hostiles)
        or tuple(sorted(set(hostiles))) != hostiles
        or subject in hostiles
    ):
        return None
    return subject, target, hostiles


def parse_advance_route_contact_horizon_step(
    step: object,
) -> tuple[int, int, tuple[int, ...]] | None:
    if not isinstance(step, str) or not step.startswith(
        ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX
    ):
        return None
    query = "query-route-contact-horizon-v1-" + step.removeprefix(
        ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX
    )
    return parse_query_route_contact_horizon_step(query)


def battle_decision_epoch_advance_step(target_date_raw: int) -> str:
    if (
        isinstance(target_date_raw, bool)
        or not isinstance(target_date_raw, int)
        or not 0 < target_date_raw <= 2**63 - 1
    ):
        raise ValueError("target_date_raw must be a positive signed int64")
    return f"{BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX}{target_date_raw}"


def parse_battle_decision_epoch_advance_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX
    ):
        return None
    target_text = step.removeprefix(
        BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX
    )
    if (
        not target_text.isascii()
        or not target_text.isdigit()
        or target_text.startswith("0")
    ):
        return None
    target_date_raw = int(target_text)
    return target_date_raw if 0 < target_date_raw <= 2**63 - 1 else None


def committed_route_sentinel_advance_step(
    subject_army_id: int,
    target_province_id: int,
    target_date_raw: int,
) -> str:
    for name, value, maximum in (
        ("subject_army_id", subject_army_id, 2**31 - 1),
        ("target_province_id", target_province_id, 2**31 - 1),
        ("target_date_raw", target_date_raw, 2**63 - 1),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 < value <= maximum
        ):
            raise ValueError(f"{name} must be a positive signed integer")
    return (
        f"{COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX}"
        f"{subject_army_id}-to-{target_province_id}-until-{target_date_raw}"
    )


def parse_committed_route_sentinel_advance_step(
    step: object,
) -> tuple[int, int, int] | None:
    if not isinstance(step, str) or not step.startswith(
        COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX
    ):
        return None
    payload = step.removeprefix(
        COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX
    )
    subject_text, to_separator, remainder = payload.partition("-to-")
    target_text, until_separator, date_text = remainder.partition("-until-")
    if (
        not to_separator
        or not until_separator
        or not subject_text.isascii()
        or not subject_text.isdigit()
        or subject_text.startswith("0")
        or not target_text.isascii()
        or not target_text.isdigit()
        or target_text.startswith("0")
        or not date_text.isascii()
        or not date_text.isdigit()
        or date_text.startswith("0")
    ):
        return None
    subject_army_id = int(subject_text)
    target_province_id = int(target_text)
    target_date_raw = int(date_text)
    if (
        not 0 < subject_army_id <= 2**31 - 1
        or not 0 < target_province_id <= 2**31 - 1
        or not 0 < target_date_raw <= 2**63 - 1
    ):
        return None
    return subject_army_id, target_province_id, target_date_raw


def is_life_advance_step(step: object) -> bool:
    return bool(
        step == "life-advance"
        or (
            isinstance(step, str)
            and step in BATTLE_SENTINEL_ADVANCE_STEPS
        )
        or parse_battle_decision_epoch_advance_step(step) is not None
        or parse_committed_route_sentinel_advance_step(step) is not None
        or parse_advance_route_contact_horizon_step(step) is not None
    )


def parse_disband_army_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("disband-army-"):
        return None
    army_text = step.removeprefix("disband-army-")
    return int(army_text) if army_text.isdigit() else None


def parse_split_army_half_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("split-army-half-"):
        return None
    army_text = step.removeprefix("split-army-half-")
    if not army_text.isascii() or not army_text.isdigit():
        return None
    army_id = int(army_text)
    return army_id if 0 < army_id <= 2**31 - 1 else None


def parse_merge_armies_step(step: object) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith("merge-armies-"):
        return None
    payload = step.removeprefix("merge-armies-")
    destination_text, separator, source_text = payload.partition("-with-")
    if (
        not separator
        or not destination_text.isascii()
        or not destination_text.isdigit()
        or not source_text.isascii()
        or not source_text.isdigit()
    ):
        return None
    destination = int(destination_text)
    source = int(source_text)
    if not (
        0 < destination <= 2**31 - 1
        and 0 < source <= 2**31 - 1
        and destination != source
    ):
        return None
    return destination, source


def parse_start_assault_step(step: object) -> int | None:
    return _parse_assault_step(step, prefix="start-assault-")


def parse_stop_assault_step(step: object) -> int | None:
    return _parse_assault_step(step, prefix="stop-assault-")


def _parse_assault_step(step: object, *, prefix: str) -> int | None:
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    siege_text = step.removeprefix(prefix)
    if not siege_text.isascii() or not siege_text.isdecimal():
        return None
    siege_id = int(siege_text)
    return siege_id if 0 < siege_id <= 2**31 - 1 else None


def parse_enforce_demands_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("enforce-demands-"):
        return None
    war_text = step.removeprefix("enforce-demands-")
    return int(war_text) if war_text.isdigit() else None


def parse_query_war_termination_options_step(step: object) -> int | None:
    return _parse_generation_war_step(
        step, prefix="query-war-termination-options-"
    )


def parse_query_war_termination_terms_step(step: object) -> int | None:
    return _parse_generation_war_step(
        step, prefix="query-war-termination-terms-v1-"
    )


def parse_surrender_war_step(step: object) -> int | None:
    return _parse_generation_war_step(step, prefix="surrender-war-")


def parse_offer_white_peace_step(step: object) -> int | None:
    return _parse_generation_war_step(step, prefix="offer-white-peace-")


def _parse_generation_war_step(step: object, *, prefix: str) -> int | None:
    """Parse only the canonical spelling of a full-generation WarID step."""
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    war_text = step.removeprefix(prefix)
    if (
        not war_text
        or not war_text.isascii()
        or not war_text.isdecimal()
        or war_text.startswith("0")
    ):
        return None
    war_id = int(war_text)
    return war_id if 0 < war_id <= 2**31 - 1 else None


def normalize_war_termination_terms(
    value: object,
    *,
    expected_war_id: int | None = None,
) -> dict[str, object]:
    """Normalize the complete, narrow claim-CB disposition slice."""
    if not isinstance(value, dict):
        raise ValueError("native war_termination_terms must be an object")
    status = value.get("status")
    common_keys = {
        "schema_version",
        "status",
        "war_id",
        "casus_belli",
        "supported_slice",
        "readiness",
        "provenance",
    }
    if status == "available":
        expected_keys = common_keys | {
            "claimant_character_id",
            "target_title_ids",
            "claims",
            "outcomes",
        }
    elif status == "unsupported":
        expected_keys = common_keys | {"reason"}
    else:
        raise ValueError("native war_termination_terms.status is malformed")
    if set(value) != expected_keys or value.get("schema_version") != 1:
        raise ValueError(
            "native war_termination_terms top-level schema is malformed"
        )

    war_id = _positive_int32_id(
        value.get("war_id"), "war_termination_terms.war_id"
    )
    if expected_war_id is not None and war_id != _positive_int32_id(
        expected_war_id, "expected_war_id"
    ):
        raise ValueError("native war_termination_terms WarID mismatch")
    casus_belli = value.get("casus_belli")
    if not isinstance(casus_belli, dict) or set(casus_belli) != {
        "database_index",
        "canonical_key",
    }:
        raise ValueError("native war_termination_terms.casus_belli malformed")
    database_index = _optional_non_negative_int32(
        casus_belli.get("database_index"),
        "war_termination_terms.casus_belli.database_index",
    )
    if database_index is None:
        raise ValueError(
            "native war_termination_terms CB database index is required"
        )
    canonical_key = casus_belli.get("canonical_key")
    if not isinstance(canonical_key, str) or not canonical_key:
        raise ValueError(
            "native war_termination_terms CB canonical key is malformed"
        )
    if value.get("supported_slice") != "claim_cb_claim_disposition":
        raise ValueError(
            "native war_termination_terms supported slice drifted"
        )
    provenance = _normalize_war_termination_terms_provenance(
        value.get("provenance")
    )

    if status == "unsupported":
        if canonical_key == "claim_cb" or value.get("reason") != (
            "casus_belli_not_claim_cb"
        ):
            raise ValueError(
                "native war_termination_terms unsupported branch malformed"
            )
        readiness = value.get("readiness")
        if not isinstance(readiness, dict) or readiness != {"ready": False}:
            raise ValueError(
                "native war_termination_terms unsupported readiness malformed"
            )
        return {
            "schema_version": 1,
            "status": "unsupported",
            "war_id": war_id,
            "casus_belli": {
                "database_index": database_index,
                "canonical_key": canonical_key,
            },
            "supported_slice": "claim_cb_claim_disposition",
            "reason": "casus_belli_not_claim_cb",
            "readiness": {"ready": False},
            "provenance": provenance,
        }

    if canonical_key != "claim_cb":
        raise ValueError(
            "native war_termination_terms available branch is not claim_cb"
        )
    claimant_character_id = _positive_int32_id(
        value.get("claimant_character_id"),
        "war_termination_terms.claimant_character_id",
    )
    target_title_ids = _strict_positive_int32_id_list(
        value.get("target_title_ids"),
        "war_termination_terms.target_title_ids",
    )
    if not target_title_ids:
        raise ValueError(
            "native war_termination_terms target titles must be nonempty"
        )
    raw_claims = value.get("claims")
    if not isinstance(raw_claims, list) or len(raw_claims) != len(
        target_title_ids
    ):
        raise ValueError(
            "native war_termination_terms claims must match target titles"
        )
    claims: list[dict[str, object]] = []
    for index, (raw_claim, title_id) in enumerate(
        zip(raw_claims, target_title_ids, strict=True)
    ):
        name = f"war_termination_terms.claims[{index}]"
        if not isinstance(raw_claim, dict):
            raise ValueError(f"native {name} must be an object")
        present = _strict_bool(raw_claim.get("present"), f"{name}.present")
        expected_claim_keys = (
            {"title_id", "present", "strong", "implicit", "state"}
            if present
            else {"title_id", "present", "state"}
        )
        if set(raw_claim) != expected_claim_keys or _positive_int32_id(
            raw_claim.get("title_id"), f"{name}.title_id"
        ) != title_id:
            raise ValueError(f"native {name} schema/title order is malformed")
        if not present:
            if raw_claim.get("state") != "absent":
                raise ValueError(f"native {name} absent state is malformed")
            claims.append(
                {"title_id": title_id, "present": False, "state": "absent"}
            )
            continue
        strong = _strict_bool(raw_claim.get("strong"), f"{name}.strong")
        implicit = _strict_bool(
            raw_claim.get("implicit"), f"{name}.implicit"
        )
        expected_state = (
            ("strong_" if strong else "weak_")
            + ("implicit" if implicit else "explicit")
        )
        if raw_claim.get("state") != expected_state:
            raise ValueError(f"native {name} claim state is inconsistent")
        claims.append(
            {
                "title_id": title_id,
                "present": True,
                "strong": strong,
                "implicit": implicit,
                "state": expected_state,
            }
        )

    outcomes = value.get("outcomes")
    if not isinstance(outcomes, dict) or set(outcomes) != set(
        _TERMINATION_TERMS_OUTCOMES
    ):
        raise ValueError("native war_termination_terms outcomes malformed")
    normalized_outcomes: dict[str, dict[str, str]] = {}
    for outcome, expected_disposition in _TERMINATION_TERMS_OUTCOMES.items():
        disposition = outcomes.get(outcome)
        if not isinstance(disposition, dict) or disposition != (
            expected_disposition
        ):
            raise ValueError(
                f"native war_termination_terms outcome {outcome} drifted"
            )
        normalized_outcomes[outcome] = dict(expected_disposition)
    readiness = value.get("readiness")
    expected_readiness = {
        "identity_ready": True,
        "targets_ready": True,
        "claim_rows_ready": True,
        "claim_disposition_ready": True,
        "ready": True,
    }
    if not isinstance(readiness, dict) or readiness != expected_readiness:
        raise ValueError(
            "native war_termination_terms available readiness malformed"
        )
    return {
        "schema_version": 1,
        "status": "available",
        "war_id": war_id,
        "casus_belli": {
            "database_index": database_index,
            "canonical_key": "claim_cb",
        },
        "supported_slice": "claim_cb_claim_disposition",
        "claimant_character_id": claimant_character_id,
        "target_title_ids": target_title_ids,
        "claims": claims,
        "outcomes": normalized_outcomes,
        "readiness": expected_readiness,
        "provenance": provenance,
    }


def _normalize_war_termination_terms_provenance(
    value: object,
) -> dict[str, str]:
    expected = {
        "game_version": _TERMINATION_TERMS_GAME_VERSION,
        "executable_sha256": _TERMINATION_TERMS_EXECUTABLE_SHA256,
        "native_reader": _TERMINATION_TERMS_NATIVE_READER,
        "present_claim_lifecycle": _TERMINATION_TERMS_CLAIM_LIFECYCLE,
        "claim_script_sha256": _TERMINATION_TERMS_CLAIM_SCRIPT_SHA256,
    }
    if not isinstance(value, dict) or value != expected:
        raise ValueError(
            "native war_termination_terms provenance is malformed"
        )
    return dict(expected)


def normalize_war_termination_options(
    value: object,
    *,
    expected_war_id: int | None = None,
) -> dict[str, object]:
    """Normalize one atomic native war-termination query.

    The exact-build reader publishes each context, native validator, opponent
    answer score, and auto-accept result atomically.  CB-specific terms remain
    explicit unavailable data and may not be inferred from those values.
    """
    if not isinstance(value, dict):
        raise ValueError("native war_termination_options must be an object")
    expected_keys = {
        "war_id",
        "player_side",
        "player_is_primary_war_leader",
        "player_relative_war_score",
        "war_duration_days",
        "absolute_war_scores_observable",
        "attacker_war_score",
        "defender_war_score",
        "war_score_breakdown",
        "active_casus_belli_present",
        "active_casus_belli_identity",
        "cb_allows_white_peace",
        "options",
    }
    if set(value) != expected_keys:
        raise ValueError(
            "native war_termination_options top-level schema is malformed"
        )
    war_id = _positive_int32_id(value.get("war_id"), "war_id")
    if expected_war_id is not None and war_id != _positive_int32_id(
        expected_war_id, "expected_war_id"
    ):
        raise ValueError("native war_termination_options WarID mismatch")
    player_side = value.get("player_side")
    if player_side not in {"attacker", "defender"}:
        raise ValueError(
            "native war_termination_options.player_side is malformed"
        )
    is_primary = _strict_bool(
        value.get("player_is_primary_war_leader"),
        "war_termination_options.player_is_primary_war_leader",
    )
    score = value.get("player_relative_war_score")
    if (
        isinstance(score, bool)
        or not isinstance(score, int)
        or score < -(2**31)
        or score > 2**31 - 1
    ):
        raise ValueError(
            "native war_termination_options.player_relative_war_score "
            "must be a signed int32"
        )
    war_duration_days = _optional_non_negative_int32(
        value.get("war_duration_days"),
        "war_termination_options.war_duration_days",
    )
    active_cb = _optional_strict_bool(
        value.get("active_casus_belli_present"),
        "war_termination_options.active_casus_belli_present",
    )
    white_peace_allowed = _optional_strict_bool(
        value.get("cb_allows_white_peace"),
        "war_termination_options.cb_allows_white_peace",
    )
    if white_peace_allowed is not None and active_cb is not True:
        raise ValueError(
            "native war_termination_options cannot publish white-peace "
            "permission without an active casus belli"
        )
    active_cb_identity = _normalize_active_casus_belli_identity(
        value.get("active_casus_belli_identity"),
        active_casus_belli_present=active_cb,
    )
    absolute_scores_observable = _strict_bool(
        value.get("absolute_war_scores_observable"),
        "war_termination_options.absolute_war_scores_observable",
    )
    attacker_score = _optional_signed_int32(
        value.get("attacker_war_score"),
        "war_termination_options.attacker_war_score",
    )
    defender_score = _optional_signed_int32(
        value.get("defender_war_score"),
        "war_termination_options.defender_war_score",
    )
    if absolute_scores_observable:
        if attacker_score is None or defender_score is None:
            raise ValueError(
                "native observable absolute war scores must both be present"
            )
        if defender_score != -attacker_score:
            raise ValueError(
                "native defender_war_score must negate attacker_war_score"
            )
        expected_player_score = (
            attacker_score if player_side == "attacker" else defender_score
        )
        if score != expected_player_score:
            raise ValueError(
                "native absolute war scores disagree with player-relative score"
            )
    elif attacker_score is not None or defender_score is not None:
        raise ValueError(
            "native unobservable absolute war scores must both be null"
        )
    war_score_breakdown = _normalize_war_score_breakdown(
        value.get("war_score_breakdown")
    )
    raw_options = value.get("options")
    if not isinstance(raw_options, dict) or set(raw_options) != {
        "surrender",
        "white_peace",
        "victory",
    }:
        raise ValueError(
            "native war_termination_options.options must contain exactly "
            "surrender, white_peace, and victory"
        )
    surrender_outcome = (
        "attacker_defeat" if player_side == "attacker" else "attacker_victory"
    )
    victory_outcome = (
        "attacker_victory" if player_side == "attacker" else "attacker_defeat"
    )
    options = {
        "surrender": _normalize_war_termination_option(
            raw_options.get("surrender"),
            name="surrender",
            expected_outcome=surrender_outcome,
        ),
        "white_peace": _normalize_war_termination_option(
            raw_options.get("white_peace"),
            name="white_peace",
            expected_outcome="white_peace",
        ),
        "victory": _normalize_war_termination_option(
            raw_options.get("victory"),
            name="victory",
            expected_outcome=victory_outcome,
        ),
    }
    if not is_primary and any(
        option["context_constructed"] for option in options.values()
    ):
        raise ValueError(
            "native war_termination_options constructed a context for a "
            "non-primary participant"
        )
    if (
        white_peace_allowed is not True
        and options["white_peace"]["context_constructed"]
    ):
        raise ValueError(
            "native war_termination_options constructed white peace for a "
            "casus belli that forbids it"
        )
    return {
        "war_id": war_id,
        "player_side": player_side,
        "player_is_primary_war_leader": is_primary,
        "player_relative_war_score": score,
        "war_duration_days": war_duration_days,
        "active_casus_belli_present": active_cb,
        "active_casus_belli_identity": active_cb_identity,
        "cb_allows_white_peace": white_peace_allowed,
        "absolute_war_scores_observable": absolute_scores_observable,
        "attacker_war_score": attacker_score,
        "defender_war_score": defender_score,
        "war_score_breakdown": war_score_breakdown,
        "options": options,
        "source": "native",
    }


def _normalize_active_casus_belli_identity(
    value: object,
    *,
    active_casus_belli_present: bool | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    if active_casus_belli_present is not True or not isinstance(value, dict) or set(
        value
    ) != {"database_index", "canonical_key"}:
        raise ValueError(
            "native active_casus_belli_identity is malformed"
        )
    database_index = _optional_non_negative_int32(
        value.get("database_index"),
        "war_termination_options.active_casus_belli_identity.database_index",
    )
    canonical_key = value.get("canonical_key")
    if database_index is None or not isinstance(canonical_key, str) or not (
        canonical_key
    ):
        raise ValueError(
            "native active_casus_belli_identity is incomplete"
        )
    return {
        "database_index": database_index,
        "canonical_key": canonical_key,
    }


def _normalize_war_score_breakdown(
    value: object,
) -> dict[str, int] | None:
    if value is None:
        return None
    fields = {"imprisonment", "battles", "occupation", "ticking"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(
            "native war_score_breakdown must be null or contain all four fields"
        )
    return {
        field: _signed_int32(
            value.get(field),
            f"war_termination_options.war_score_breakdown.{field}",
        )
        for field in sorted(fields)
    }


def _normalize_war_termination_option(
    value: object,
    *,
    name: str,
    expected_outcome: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "outcome",
        "hostage_variant",
        "context_constructed",
        "native_validator_passed",
        "available",
        "terms_observable",
        "terms",
        "ai_acceptance_observable",
        "ai_acceptance",
        "auto_accept_observable",
        "auto_accept",
        "recipient_response",
    }:
        raise ValueError(
            f"native war_termination_options.options.{name} is malformed"
        )
    if value.get("outcome") != expected_outcome:
        raise ValueError(
            f"native war_termination_options.options.{name}.outcome is "
            "inconsistent with player_side"
        )
    if value.get("hostage_variant") != "none":
        raise ValueError(
            "native war_termination_options only supports the no-hostage "
            f"variant for {name}"
        )
    context_constructed = _strict_bool(
        value.get("context_constructed"),
        f"war_termination_options.options.{name}.context_constructed",
    )
    validator = value.get("native_validator_passed")
    if validator is not None and not isinstance(validator, bool):
        raise ValueError(
            "native war_termination_options.options."
            f"{name}.native_validator_passed must be boolean or null"
        )
    if not context_constructed and validator is not None:
        raise ValueError(
            "native war_termination_options.options."
            f"{name} cannot publish a validator result without a context"
        )
    available = _strict_bool(
        value.get("available"),
        f"war_termination_options.options.{name}.available",
    )
    if available is not (context_constructed and validator is True):
        raise ValueError(
            "native war_termination_options.options."
            f"{name}.available is inconsistent with context and validator"
        )
    terms_observable = _strict_bool(
        value.get("terms_observable"),
        f"war_termination_options.options.{name}.terms_observable",
    )
    terms = value.get("terms")
    if terms_observable or terms != {
        "status": "unavailable",
        "reason": "cb_specific_terms_not_observable",
    }:
        raise ValueError(
            "native war_termination_options option terms must remain "
            "explicitly unavailable"
        )
    acceptance_observable = _strict_bool(
        value.get("ai_acceptance_observable"),
        f"war_termination_options.options.{name}.ai_acceptance_observable",
    )
    acceptance = (
        _signed_fixed_point(
            value.get("ai_acceptance"),
            f"war_termination_options.options.{name}.ai_acceptance",
        )
        if acceptance_observable
        else None
    )
    if not acceptance_observable and value.get("ai_acceptance") is not None:
        raise ValueError(
            "native war_termination_options cannot publish an unobservable "
            f"AI acceptance score for {name}"
        )
    auto_accept_observable = _strict_bool(
        value.get("auto_accept_observable"),
        f"war_termination_options.options.{name}.auto_accept_observable",
    )
    auto_accept = value.get("auto_accept")
    if auto_accept_observable:
        auto_accept = _strict_bool(
            auto_accept,
            f"war_termination_options.options.{name}.auto_accept",
        )
    elif auto_accept is not None:
        raise ValueError(
            "native war_termination_options cannot publish an unobservable "
            f"auto-accept result for {name}"
        )
    if not context_constructed and (
        acceptance_observable or auto_accept_observable
    ):
        raise ValueError(
            "native war_termination_options cannot evaluate acceptance "
            f"without a constructed {name} context"
        )
    recipient_response = _normalize_war_termination_recipient_response(
        value.get("recipient_response"),
        name=name,
        context_constructed=context_constructed,
        validator=validator,
    )
    return {
        "outcome": expected_outcome,
        "hostage_variant": "none",
        "context_constructed": context_constructed,
        # Null is an observed unknown and must never be coerced to false.
        "native_validator_passed": validator,
        "available": available,
        "terms_observable": False,
        "terms": terms,
        "ai_acceptance_observable": acceptance_observable,
        "ai_acceptance": acceptance,
        "auto_accept_observable": auto_accept_observable,
        "auto_accept": auto_accept,
        "recipient_response": recipient_response,
    }


def _normalize_war_termination_recipient_response(
    value: object,
    *,
    name: str,
    context_constructed: bool,
    validator: bool | None,
) -> dict[str, object]:
    path = f"war_termination_options.options.{name}.recipient_response"
    if not isinstance(value, dict) or set(value) != {
        "status",
        "decision_status_raw",
        "would_accept_now",
    }:
        raise ValueError(f"native {path} is malformed")
    status = value.get("status")
    decision_status_raw = value.get("decision_status_raw")
    would_accept_now = value.get("would_accept_now")
    if status == "unavailable":
        if decision_status_raw is not None or would_accept_now is not None:
            raise ValueError(
                f"native {path} unavailable branch must contain null values"
            )
        return {
            "status": "unavailable",
            "decision_status_raw": None,
            "would_accept_now": None,
        }
    if status != "available":
        raise ValueError(f"native {path}.status is malformed")
    if not context_constructed or validator is not True:
        raise ValueError(
            f"native {path} cannot be available without a valid context"
        )
    if (
        isinstance(decision_status_raw, bool)
        or not isinstance(decision_status_raw, int)
        or decision_status_raw not in {0, 1, 2}
    ):
        raise ValueError(
            f"native {path}.decision_status_raw must be one of 0, 1, 2"
        )
    would_accept = _strict_bool(
        would_accept_now, f"{path}.would_accept_now"
    )
    if would_accept is not (decision_status_raw != 2):
        raise ValueError(
            f"native {path}.would_accept_now disagrees with final status"
        )
    return {
        "status": "available",
        "decision_status_raw": decision_status_raw,
        "would_accept_now": would_accept,
    }


def is_native_war_step(step: object) -> bool:
    return (
        step == RAISE_TROOPS_STEP
        or step == QUERY_ARMY_STRENGTHS_STEP
        or parse_preview_move_army_step(step) is not None
        or parse_query_route_contact_horizon_step(step) is not None
        or parse_move_army_step(step) is not None
        or parse_disband_army_step(step) is not None
        or parse_split_army_half_step(step) is not None
        or parse_merge_armies_step(step) is not None
        or parse_start_assault_step(step) is not None
        or parse_stop_assault_step(step) is not None
        or parse_enforce_demands_step(step) is not None
        or parse_query_war_termination_options_step(step) is not None
        or parse_query_war_termination_terms_step(step) is not None
        or parse_surrender_war_step(step) is not None
        or parse_offer_white_peace_step(step) is not None
    )


def _non_negative_id(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _positive_int32_id(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
        or value > 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _optional_positive_int32_id(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _positive_int32_id(value, name)


def _optional_non_negative_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > 2**31 - 1
    ):
        raise ValueError(f"{name} must be a non-negative int32 or null")
    return value


def _signed_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < -(2**31)
        or value > 2**31 - 1
    ):
        raise ValueError(f"{name} must be a signed int32")
    return value


def _optional_signed_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _signed_int32(value, name)


def _signed_fixed_point(value: object, name: str) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError(f"native {name} must contain raw and scale")
    raw = value.get("raw")
    scale = value.get("scale")
    if (
        isinstance(raw, bool)
        or not isinstance(raw, int)
        or raw < -(2**63)
        or raw > 2**63 - 1
        or scale != CK3_FIXED_POINT_SCALE
    ):
        raise ValueError(f"native {name} fixed value is malformed")
    return {"raw": raw, "scale": CK3_FIXED_POINT_SCALE}


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _required_list(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    return value


def _optional_strict_bool(value: object, name: str) -> bool | None:
    if value is None:
        return None
    return _strict_bool(value, name)


def _non_negative_id_list(value: object, name: str) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    result: list[int] = []
    seen: set[int] = set()
    for item in value:
        normalized = _non_negative_id(item, name)
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _strict_positive_int32_id_list(value: object, name: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    result: list[int] = []
    seen: set[int] = set()
    for index, item in enumerate(value):
        normalized = _positive_int32_id(item, f"{name}[{index}]")
        if normalized in seen:
            raise ValueError(f"native {name} must not contain duplicates")
        seen.add(normalized)
        result.append(normalized)
    return result
