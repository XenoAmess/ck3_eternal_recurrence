"""Private same-frame transport for minor-religious-war faith defenders."""

from __future__ import annotations

import copy
import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError


STEP_PREFIX = "query-minor-religious-war-defenders-v1-"


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
        copy.deepcopy(snapshot.get("declarable_wars")),
        copy.deepcopy(snapshot.get("active_wars")),
    )


def _normalize(value: object, *, expected_native_revision: int,
               expected_date_raw: int, expected_target_id: int,
               expected_actor_id: int) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("minor religious war defenders must be an object")
    expected_keys = {
        "status", "native_revision", "date_raw", "declaration",
        "actor_character_id", "primary_defender_character_id",
        "actor_power_base_raw", "actor_power_total_raw",
        "primary_defender_power_base_raw",
        "primary_defender_power_total_raw",
        "prospective_joiner_base_power_raw",
        "primary_plus_joiner_base_power_raw",
        "primary_total_plus_joiner_base_power_raw", "power_scale",
        "prospective_joiners",
    }
    if set(value) != expected_keys or value.get("status") != "available":
        raise ValueError("minor religious war defenders shape changed")
    revision = _integer(value.get("native_revision"), "native_revision", positive=True)
    date_raw = _integer(value.get("date_raw"), "date_raw")
    actor_id = _integer(value.get("actor_character_id"), "actor_character_id", positive=True)
    defender_id = _integer(
        value.get("primary_defender_character_id"),
        "primary_defender_character_id", positive=True,
    )
    if revision != expected_native_revision or date_raw != expected_date_raw:
        raise ValueError("minor religious war defenders frame changed")
    if actor_id != expected_actor_id or actor_id == defender_id:
        raise ValueError("minor religious war actor/defender identity changed")

    declaration = value.get("declaration")
    declaration_keys = {
        "target_character_id", "casus_belli_index", "casus_belli_key",
        "configuration_index", "claimant_character_id", "target_title_ids",
        "defender_faith_can_join_source",
    }
    if not isinstance(declaration, Mapping) or set(declaration) != declaration_keys:
        raise ValueError("minor religious war declaration shape changed")
    if (
        _integer(declaration.get("target_character_id"),
                 "declaration.target_character_id", positive=True)
        != expected_target_id
        or declaration.get("casus_belli_key") != "minor_religious_war"
        or declaration.get("defender_faith_can_join_source") is not True
    ):
        raise ValueError("declaration is not the requested minor religious war")
    for name in ("casus_belli_index", "configuration_index",
                 "claimant_character_id"):
        _integer(declaration.get(name), f"declaration.{name}")
    title_ids = declaration.get("target_title_ids")
    if not isinstance(title_ids, list) or any(
        _integer(item, "declaration.target_title_ids[]", positive=True) <= 0
        for item in title_ids
    ):
        raise ValueError("declaration target title IDs are malformed")

    powers: dict[str, int] = {}
    for name in (
        "actor_power_base_raw", "actor_power_total_raw",
        "primary_defender_power_base_raw",
        "primary_defender_power_total_raw",
        "prospective_joiner_base_power_raw",
        "primary_plus_joiner_base_power_raw",
        "primary_total_plus_joiner_base_power_raw",
    ):
        powers[name] = _integer(value.get(name), name)
        if powers[name] < 0:
            raise ValueError(f"{name} must be non-negative")
    if value.get("power_scale") != 100_000:
        raise ValueError("power scale changed")
    rows = value.get("prospective_joiners")
    if not isinstance(rows, list) or len(rows) > 64:
        raise ValueError("prospective joiners are malformed")
    normalized_rows: list[dict[str, int]] = []
    seen: set[int] = set()
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != {
            "character_id", "base_power_raw"
        }:
            raise ValueError(f"prospective_joiners[{index}] shape changed")
        character_id = _integer(
            row.get("character_id"),
            f"prospective_joiners[{index}].character_id", positive=True,
        )
        power = _integer(
            row.get("base_power_raw"),
            f"prospective_joiners[{index}].base_power_raw",
        )
        if power < 0 or character_id in seen or character_id in {
            actor_id, defender_id
        }:
            raise ValueError("prospective joiner identity/power is invalid")
        seen.add(character_id)
        total += power
        if total > 2**63 - 1:
            raise ValueError("prospective joiner power overflow")
        normalized_rows.append({"character_id": character_id,
                                "base_power_raw": power})
    if (
        total != powers["prospective_joiner_base_power_raw"]
        or powers["primary_plus_joiner_base_power_raw"]
        != powers["primary_defender_power_base_raw"] + total
        or powers["primary_total_plus_joiner_base_power_raw"]
        != powers["primary_defender_power_total_raw"] + total
    ):
        raise ValueError("prospective defender power totals disagree")
    return {
        **dict(value),
        "declaration": dict(declaration),
        "prospective_joiners": normalized_rows,
    }


def query_minor_religious_war_defenders_private_v1(
    driver: object,
    *,
    target_character_id: int,
    expected_revision: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Read exact prospective faith defenders without capability advertising."""
    if getattr(
        driver, "allow_private_minor_religious_war_defenders_query", False
    ) is not True:
        raise UnsupportedStepError(
            "private minor religious war defenders query is disabled"
        )
    if isinstance(target_character_id, bool) or not isinstance(
        target_character_id, int
    ) or target_character_id <= 0:
        raise ValueError("target_character_id must be a positive integer")
    if isinstance(expected_revision, bool) or not isinstance(
        expected_revision, int
    ) or expected_revision < 0:
        raise ValueError("expected_revision must be a non-negative integer")
    if isinstance(timeout_seconds, bool) or not isinstance(
        timeout_seconds, (int, float)
    ) or timeout_seconds <= 0:
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
            "minor religious war defenders query requires a current paused map frame"
        )
    request_id = "minor-religious-war-defenders-" + uuid.uuid4().hex
    step = STEP_PREFIX + str(target_character_id)
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError(
            "minor religious war defenders command_result timed out"
        )
    if (
        frame.get("type") != "command_result"
        or frame.get("protocol_version") != 1
        or frame.get("request_id") != request_id
        or frame.get("ok") is not True
    ):
        raise BridgeUnavailableError(
            "minor religious war defenders query returned RED: "
            + str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    expected_keys = {
        "step", "accepted", "status", "private_build", "read_only",
        "advertised", "backend_id", "minor_religious_war_defenders",
    }
    if (
        not isinstance(result, Mapping)
        or set(result) != expected_keys
        or result.get("step") != step
        or result.get("accepted") is not True
        or result.get("status") != "available"
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
        or result.get("backend_id") != "native-headless"
    ):
        raise BridgeUnavailableError(
            "minor religious war defenders private envelope changed"
        )
    try:
        normalized = _normalize(
            result.get("minor_religious_war_defenders"),
            expected_native_revision=native_revision,
            expected_date_raw=date_raw,
            expected_target_id=target_character_id,
            expected_actor_id=player["character_id"],
        )
    except ValueError as error:
        raise BridgeUnavailableError(
            f"minor religious war defenders result is malformed: {error}"
        ) from error
    after = driver.take_snapshot()
    if _binding(after) != _binding(before):
        raise BridgeUnavailableError(
            "minor religious war defenders query crossed its paused frame"
        )
    return {
        **dict(result),
        "minor_religious_war_defenders": normalized,
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "date_raw": date_raw,
    }
