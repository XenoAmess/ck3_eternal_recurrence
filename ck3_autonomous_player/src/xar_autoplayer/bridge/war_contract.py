"""Canonical native CK3 war and army state shared by MCP and the planner."""

from __future__ import annotations

from collections.abc import Iterable


MOVE_ARMY_CAPABILITY = "game.command.move-army-N-to-N"
DISBAND_ARMY_CAPABILITY = "game.command.disband-army-N"
ENFORCE_DEMANDS_CAPABILITY = "game.command.enforce-demands-N"
WAR_PRIMARY_OPPONENT_CAPABILITY = "game.state.war-primary-opponent"
RAISE_TROOPS_STEP = "raise-troops-default"


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
        controllable = raw_army.get("controllable")
        if not isinstance(controllable, bool):
            raise ValueError(f"native {name}[{index}].controllable is malformed")
        result.append(
            {
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
        )
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
    """Return stable fallback objectives when no enemy army is observable."""
    province_ids: set[int] = set()
    for war in active_wars:
        province_id = war.get("enemy_primary_default_raise_province_id")
        if isinstance(province_id, int) and not isinstance(province_id, bool):
            province_ids.add(province_id)
    return sorted(province_ids)


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
        or parse_move_army_step(step) is not None
        or parse_disband_army_step(step) is not None
        or parse_enforce_demands_step(step) is not None
    )


def _non_negative_id(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value
