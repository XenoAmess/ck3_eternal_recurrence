"""Private same-frame transport for one legal war's current resource slice."""

from __future__ import annotations

import copy
import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError


STEP_PREFIX = "query-m5-war-primary-current-v1-"


def _integer(value: object, label: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if positive and value <= 0:
        raise ValueError(f"{label} must be positive")
    if not -(2**63) <= value <= 2**63 - 1:
        raise ValueError(f"{label} is outside int64")
    return value


def _binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    return (
        snapshot.get("snapshot_id"),
        snapshot.get("revision"),
        snapshot.get("native_revision"),
        snapshot.get("date_raw"),
        snapshot.get("paused"),
        snapshot.get("map_ready"),
        copy.deepcopy(snapshot.get("played_character")),
        copy.deepcopy(snapshot.get("played_character_gold")),
        copy.deepcopy(snapshot.get("declarable_wars")),
        copy.deepcopy(snapshot.get("active_wars")),
        copy.deepcopy(snapshot.get("player_armies")),
    )


def _positive_ids(value: object, label: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    result = [_integer(item, f"{label}[]", positive=True) for item in value]
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must contain distinct IDs")
    return result


def _expected_declaration(
    snapshot: Mapping[str, object], target_character_id: int
) -> dict[str, object]:
    rows = snapshot.get("declarable_wars")
    if not isinstance(rows, list):
        raise ValueError("declarable_wars must be an array")
    selected = next(
        (
            row
            for row in rows
            if isinstance(row, Mapping)
            and row.get("target_character_id") == target_character_id
        ),
        None,
    )
    if selected is None:
        raise ValueError("requested target is absent from declarable_wars")
    key = selected.get("casus_belli_key")
    titles = selected.get("target_title_ids")
    if not isinstance(key, str) or not key or not isinstance(titles, list):
        raise ValueError("declarable war identity is malformed")
    normalized_titles = [
        _integer(item, "declarable_wars.target_title_ids[]", positive=True)
        for item in titles
    ]
    return {
        "target_character_id": _integer(
            selected.get("target_character_id"),
            "declarable_wars.target_character_id",
            positive=True,
        ),
        "casus_belli_index": _integer(
            selected.get("casus_belli_index"), "declarable_wars.casus_belli_index"
        ),
        "casus_belli_key": key,
        "configuration_index": _integer(
            selected.get("configuration_index"),
            "declarable_wars.configuration_index",
        ),
        "claimant_character_id": _integer(
            selected.get("claimant_character_id"),
            "declarable_wars.claimant_character_id",
        ),
        "target_title_ids": normalized_titles,
    }


def _normalize_declaration(value: object) -> dict[str, object]:
    expected_keys = {
        "target_character_id",
        "casus_belli_index",
        "casus_belli_key",
        "configuration_index",
        "claimant_character_id",
        "target_title_ids",
    }
    if not isinstance(value, Mapping) or set(value) != expected_keys:
        raise ValueError("M5 war declaration shape changed")
    key = value.get("casus_belli_key")
    titles = value.get("target_title_ids")
    if not isinstance(key, str) or not key or not isinstance(titles, list):
        raise ValueError("M5 war declaration identity is malformed")
    return {
        "target_character_id": _integer(
            value.get("target_character_id"),
            "declaration.target_character_id",
            positive=True,
        ),
        "casus_belli_index": _integer(
            value.get("casus_belli_index"), "declaration.casus_belli_index"
        ),
        "casus_belli_key": key,
        "configuration_index": _integer(
            value.get("configuration_index"), "declaration.configuration_index"
        ),
        "claimant_character_id": _integer(
            value.get("claimant_character_id"), "declaration.claimant_character_id"
        ),
        "target_title_ids": [
            _integer(item, "declaration.target_title_ids[]", positive=True)
            for item in titles
        ],
    }


def _expected_active_war_ids(snapshot: Mapping[str, object]) -> list[int]:
    rows = snapshot.get("active_wars")
    if not isinstance(rows, list):
        raise ValueError("active_wars must be an array")
    result: list[int] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"active_wars[{index}] must be an object")
        result.append(
            _integer(row.get("war_id"), f"active_wars[{index}].war_id", positive=True)
        )
    if len(set(result)) != len(result):
        raise ValueError("active_wars contains duplicate WarIDs")
    return result


def _expected_actor_armies(
    snapshot: Mapping[str, object], actor_character_id: int
) -> list[dict[str, object]]:
    rows = snapshot.get("player_armies")
    if not isinstance(rows, list):
        raise ValueError("player_armies must be an array")
    result: list[dict[str, object]] = []
    seen: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"player_armies[{index}] must be an object")
        if row.get("owner_character_id") != actor_character_id:
            continue
        army_id = _integer(
            row.get("army_id"), f"player_armies[{index}].army_id", positive=True
        )
        if army_id in seen:
            raise ValueError("player_armies contains a duplicate actor army")
        seen.add(army_id)
        current = row.get("current_province_id")
        move_target = row.get("move_target_province_id")
        move_observable = row.get("move_target_observable")
        route = row.get("route_province_ids")
        if current is not None:
            current = _integer(
                current, f"player_armies[{index}].current_province_id", positive=True
            )
        if move_target is not None:
            move_target = _integer(
                move_target,
                f"player_armies[{index}].move_target_province_id",
                positive=True,
            )
        if not isinstance(move_observable, bool) or not isinstance(route, list):
            raise ValueError("player army route observation is malformed")
        normalized_route = [
            _integer(
                item,
                f"player_armies[{index}].route_province_ids[]",
                positive=True,
            )
            for item in route
        ]
        result.append(
            {
                "army_id": army_id,
                "owner_character_id": actor_character_id,
                "has_current_province": current is not None,
                "current_province_id": current if current is not None else -1,
                "move_target_observable": move_observable,
                "move_target_province_id": (
                    move_target if move_target is not None else -1
                ),
                "route_province_ids": normalized_route,
            }
        )
    return result


def _normalize(
    value: object,
    *,
    snapshot: Mapping[str, object],
    expected_native_revision: int,
    expected_date_raw: int,
    expected_target_id: int,
    expected_actor_id: int,
) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("M5 war current slice must be an object")
    expected_keys = {
        "status",
        "native_revision",
        "date_raw",
        "actor_character_id",
        "declaration",
        "effective_target_character_id",
        "native_power_ratio_raw",
        "native_power_ratio_scale",
        "current_treasury",
        "active_war_ids",
        "actor_current_raised_armies",
        "actor_current_raised_supply",
    }
    if (
        set(value) != expected_keys
        or value.get("status") != "available_current_primary_slice"
    ):
        raise ValueError("M5 war current slice shape changed")
    if (
        _integer(value.get("native_revision"), "native_revision", positive=True)
        != expected_native_revision
        or _integer(value.get("date_raw"), "date_raw") != expected_date_raw
        or _integer(
            value.get("actor_character_id"), "actor_character_id", positive=True
        )
        != expected_actor_id
    ):
        raise ValueError("M5 war current slice frame identity changed")

    declaration = _normalize_declaration(value.get("declaration"))
    expected_declaration = _expected_declaration(snapshot, expected_target_id)
    if declaration != expected_declaration:
        raise ValueError("M5 war declaration differs from the first legal target row")
    _integer(
        value.get("effective_target_character_id"),
        "effective_target_character_id",
        positive=True,
    )
    ratio = _integer(value.get("native_power_ratio_raw"), "native_power_ratio_raw")
    if ratio < 0 or value.get("native_power_ratio_scale") != 100_000:
        raise ValueError("native power ratio is malformed")

    treasury = value.get("current_treasury")
    expected_treasury = snapshot.get("played_character_gold")
    if (
        not isinstance(expected_treasury, Mapping)
        or set(expected_treasury) != {"raw", "scale"}
        or expected_treasury.get("scale") != 100_000
    ):
        raise ValueError("public snapshot current treasury is malformed")
    expected_treasury_raw = _integer(
        expected_treasury.get("raw"), "played_character_gold.raw"
    )
    if (
        not isinstance(treasury, Mapping)
        or set(treasury) != {"raw", "scale"}
        or treasury.get("scale") != 100_000
        or _integer(treasury.get("raw"), "current_treasury.raw")
        != expected_treasury_raw
    ):
        raise ValueError("current treasury differs from the public snapshot")

    active_war_ids = _positive_ids(value.get("active_war_ids"), "active_war_ids")
    if active_war_ids != _expected_active_war_ids(snapshot):
        raise ValueError("active WarIDs differ from the public snapshot")

    expected_armies = _expected_actor_armies(snapshot, expected_actor_id)
    raised = value.get("actor_current_raised_armies")
    if not isinstance(raised, list):
        raise ValueError("current raised armies must be an array")
    normalized_raised: list[dict[str, object]] = []
    for index, row in enumerate(raised):
        if not isinstance(row, Mapping) or set(row) != {
            "army_id",
            "owner_character_id",
            "has_current_province",
            "current_province_id",
            "move_target_observable",
            "move_target_province_id",
            "route_province_ids",
        }:
            raise ValueError(f"actor_current_raised_armies[{index}] shape changed")
        has_current = row.get("has_current_province")
        move_observable = row.get("move_target_observable")
        route = row.get("route_province_ids")
        if (
            not isinstance(has_current, bool)
            or not isinstance(move_observable, bool)
            or not isinstance(route, list)
        ):
            raise ValueError("current raised army route observation is malformed")
        normalized_raised.append(
            {
                "army_id": _integer(
                    row.get("army_id"),
                    f"actor_current_raised_armies[{index}].army_id",
                    positive=True,
                ),
                "owner_character_id": _integer(
                    row.get("owner_character_id"),
                    f"actor_current_raised_armies[{index}].owner_character_id",
                    positive=True,
                ),
                "has_current_province": has_current,
                "current_province_id": _integer(
                    row.get("current_province_id"),
                    f"actor_current_raised_armies[{index}].current_province_id",
                ),
                "move_target_observable": move_observable,
                "move_target_province_id": _integer(
                    row.get("move_target_province_id"),
                    f"actor_current_raised_armies[{index}].move_target_province_id",
                ),
                "route_province_ids": [
                    _integer(
                        item,
                        f"actor_current_raised_armies[{index}].route_province_ids[]",
                        positive=True,
                    )
                    for item in route
                ],
            }
        )
    if normalized_raised != expected_armies:
        raise ValueError("current raised armies differ from the public snapshot")

    supply = value.get("actor_current_raised_supply")
    if not isinstance(supply, list):
        raise ValueError("current raised supply must be an array")
    normalized_supply: list[dict[str, int]] = []
    supply_ids: list[int] = []
    for index, row in enumerate(supply):
        if not isinstance(row, Mapping) or set(row) != {
            "army_id",
            "native_carmy_id",
            "owner_character_id",
            "current_supply_raw",
            "current_supply_scale",
        }:
            raise ValueError(f"actor_current_raised_supply[{index}] shape changed")
        army_id = _integer(
            row.get("army_id"),
            f"actor_current_raised_supply[{index}].army_id",
            positive=True,
        )
        owner = _integer(
            row.get("owner_character_id"),
            f"actor_current_raised_supply[{index}].owner_character_id",
            positive=True,
        )
        supply_raw = _integer(
            row.get("current_supply_raw"),
            f"actor_current_raised_supply[{index}].current_supply_raw",
        )
        if (
            owner != expected_actor_id
            or supply_raw < 0
            or row.get("current_supply_scale") != 100_000
        ):
            raise ValueError("current raised supply identity/value is malformed")
        normalized_supply.append(
            {
                "army_id": army_id,
                "native_carmy_id": _integer(
                    row.get("native_carmy_id"),
                    f"actor_current_raised_supply[{index}].native_carmy_id",
                    positive=True,
                ),
                "owner_character_id": owner,
                "current_supply_raw": supply_raw,
                "current_supply_scale": 100_000,
            }
        )
        supply_ids.append(army_id)
    raised_ids = [int(row["army_id"]) for row in expected_armies]
    if len(set(supply_ids)) != len(supply_ids) or set(supply_ids) != set(raised_ids):
        raise ValueError("current raised supply does not cover the actor armies")
    return {
        **dict(value),
        "declaration": expected_declaration,
        "current_treasury": dict(treasury),
        "active_war_ids": active_war_ids,
        "actor_current_raised_armies": normalized_raised,
        "actor_current_raised_supply": normalized_supply,
    }


def query_m5_war_primary_current_private_v1(
    driver: object,
    *,
    target_character_id: int,
    expected_revision: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Read current war resources; future costs and reserve remain unknown."""
    if getattr(driver, "allow_private_m5_war_primary_current_query", False) is not True:
        raise UnsupportedStepError("private M5 war current query is disabled")
    _integer(target_character_id, "target_character_id", positive=True)
    if (
        isinstance(expected_revision, bool)
        or not isinstance(expected_revision, int)
        or expected_revision < 0
    ):
        raise ValueError("expected_revision must be a non-negative integer")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or timeout_seconds <= 0
    ):
        raise ValueError("timeout_seconds must be positive")

    before = driver.take_snapshot()
    player = before.get("played_character")
    native_revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    if (
        before.get("revision") != expected_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(player, Mapping)
        or player.get("alive") is not True
        or isinstance(player.get("character_id"), bool)
        or not isinstance(player.get("character_id"), int)
        or player["character_id"] <= 0
        or isinstance(native_revision, bool)
        or not isinstance(native_revision, int)
        or native_revision <= 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
    ):
        raise BridgeUnavailableError(
            "M5 war current query requires a current paused map frame"
        )
    try:
        _expected_declaration(before, target_character_id)
        _expected_active_war_ids(before)
        _expected_actor_armies(before, player["character_id"])
    except ValueError as error:
        raise BridgeUnavailableError(
            f"M5 war current public frame is malformed: {error}"
        ) from error

    request_id = "m5-war-primary-current-" + uuid.uuid4().hex
    step = STEP_PREFIX + str(target_character_id)
    driver.endpoint.send(
        {
            "type": "execute_step",
            "protocol_version": 1,
            "request_id": request_id,
            "step": step,
            "expected_revision": native_revision,
        }
    )
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("M5 war current command_result timed out")
    if (
        frame.get("type") != "command_result"
        or frame.get("protocol_version") != 1
        or frame.get("request_id") != request_id
        or frame.get("ok") is not True
    ):
        raise BridgeUnavailableError(
            "M5 war current query returned RED: "
            + str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    if (
        not isinstance(result, Mapping)
        or set(result) != {
            "step",
            "accepted",
            "status",
            "m5_war_primary_current",
        }
        or result.get("step") != step
        or result.get("accepted") is not True
        or result.get("status") != "available"
    ):
        raise BridgeUnavailableError("M5 war current private envelope changed")
    try:
        normalized = _normalize(
            result.get("m5_war_primary_current"),
            snapshot=before,
            expected_native_revision=native_revision,
            expected_date_raw=date_raw,
            expected_target_id=target_character_id,
            expected_actor_id=player["character_id"],
        )
    except ValueError as error:
        raise BridgeUnavailableError(
            f"M5 war current result is malformed: {error}"
        ) from error
    after = driver.take_snapshot()
    if _binding(after) != _binding(before):
        raise BridgeUnavailableError("M5 war current query crossed its paused frame")
    return {
        "status": "available",
        "private_build": True,
        "read_only": True,
        "advertised": False,
        "backend_id": "native-headless",
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "date_raw": date_raw,
        "m5_war_primary_current": normalized,
        "readiness": {
            "current_treasury_ready": True,
            "current_raised_armies_ready": True,
            "current_raised_supply_ready": True,
            "future_supply_ready": False,
            "campaign_cost_ready": False,
            "minimum_gold_reserve_ready": False,
            "war_proposal_ready": False,
        },
    }
