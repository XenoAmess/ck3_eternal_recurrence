"""Canonical native CK3 war and army state shared by MCP and the planner."""

from __future__ import annotations

from collections.abc import Iterable


MOVE_ARMY_CAPABILITY = "game.command.move-army-N-to-N"
PREVIEW_MOVE_ARMY_CAPABILITY = "game.command.preview-move-army-N-to-N"
DISBAND_ARMY_CAPABILITY = "game.command.disband-army-N"
ENFORCE_DEMANDS_CAPABILITY = "game.command.enforce-demands-N"
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
RAISE_TROOPS_STEP = "raise-troops-default"

CK3_FIXED_POINT_SCALE = 100_000


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


def disband_army_step(army_id: int) -> str:
    return f"disband-army-{_non_negative_id(army_id, 'army_id')}"


def enforce_demands_step(war_id: int) -> str:
    return f"enforce-demands-{_non_negative_id(war_id, 'war_id')}"


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


def parse_disband_army_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("disband-army-"):
        return None
    army_text = step.removeprefix("disband-army-")
    return int(army_text) if army_text.isdigit() else None


def parse_enforce_demands_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("enforce-demands-"):
        return None
    war_text = step.removeprefix("enforce-demands-")
    return int(war_text) if war_text.isdigit() else None


def is_native_war_step(step: object) -> bool:
    return (
        step == RAISE_TROOPS_STEP
        or parse_preview_move_army_step(step) is not None
        or parse_move_army_step(step) is not None
        or parse_disband_army_step(step) is not None
        or parse_enforce_demands_step(step) is not None
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


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


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
