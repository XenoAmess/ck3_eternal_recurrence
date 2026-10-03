"""Native occupation collector observations for one current full WarID.

Counts are measured native territory-side counters. They are not recomputed
from the declared war-goal capitals or used to predict an outcome here.
"""
from __future__ import annotations

from collections.abc import Mapping
import copy

QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY = (
    "game.command.query-war-occupation-targets-v1-N"
)
QUERY_WAR_OCCUPATION_TARGETS_V1_STEP_PREFIX = "query-war-occupation-targets-v1-"
WAR_OCCUPATION_TARGETS_V1_SCHEMA = "xar.ck3.war-occupation-targets.v1"


def _id(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 2**31 - 1:
        raise ValueError(f"{name} must be a full non-negative int32 ID")
    return value


def _count(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 2**31 - 1:
        raise ValueError(f"{name} must be a non-negative int32 count")
    return value


def _bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def query_war_occupation_targets_v1_step(war_id: int) -> str:
    return QUERY_WAR_OCCUPATION_TARGETS_V1_STEP_PREFIX + str(_id(war_id, "war_id"))


def parse_query_war_occupation_targets_v1_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(QUERY_WAR_OCCUPATION_TARGETS_V1_STEP_PREFIX):
        return None
    value = step[len(QUERY_WAR_OCCUPATION_TARGETS_V1_STEP_PREFIX):]
    if not value.isascii() or not value.isdecimal():
        return None
    war_id = int(value)
    if value != str(war_id) or war_id > 2**31 - 1:
        return None
    return war_id


def war_occupation_query_scope(snapshot: Mapping[str, object], war_id: int) -> tuple[int, str]:
    _id(war_id, "war_id")
    if snapshot.get("paused") is not True:
        raise ValueError("war occupation query requires a paused snapshot")
    actor = snapshot.get("played_character")
    if not isinstance(actor, dict) or actor.get("alive") is not True:
        raise ValueError("war occupation query lacks a living played character")
    actor_id = _id(actor.get("character_id"), "played CharacterID")
    active_wars = snapshot.get("active_wars")
    rows = [row for row in active_wars if isinstance(row, dict) and row.get("war_id") == war_id] if isinstance(active_wars, list) else []
    if len(rows) != 1 or rows[0].get("player_side") not in {"attacker", "defender"}:
        raise ValueError("war occupation query requires one current full WarID participant row")
    return actor_id, str(rows[0]["player_side"])


def normalize_war_occupation_targets_v1(
    value: object,
    *,
    expected_war_id: int,
    expected_actor_character_id: int,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_side: str | None = None,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("war occupation targets must be an object")
    if value.get("schema") != WAR_OCCUPATION_TARGETS_V1_SCHEMA or type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("war occupation targets use an unsupported schema")
    available = _bool(value.get("available"), "available")
    complete = _bool(value.get("collection_complete"), "collection_complete")
    if value.get("status") != ("available" if available else "unavailable"):
        raise ValueError("war occupation status disagrees with available")
    if type(expected_snapshot_revision) is not int or expected_snapshot_revision <= 0 or value.get("snapshot_revision") != expected_snapshot_revision:
        raise ValueError("war occupation targets differ from the native snapshot revision")
    if type(value.get("snapshot_revision")) is not int:
        raise ValueError("war occupation native revision must be an integer")
    if type(expected_date_raw) is not int or type(value.get("date_raw")) is not int or value["date_raw"] != expected_date_raw:
        raise ValueError("war occupation targets differ from the paused date")
    reason = value.get("unavailable_reason")
    if available:
        if not complete or reason is not None:
            raise ValueError("available occupation collection must be complete without a failure reason")
        if _id(value.get("war_id"), "war_id") != _id(expected_war_id, "expected_war_id"):
            raise ValueError("war occupation targets differ from the requested full WarID")
        if _id(value.get("actor_character_id"), "actor_character_id") != _id(expected_actor_character_id, "expected_actor_character_id"):
            raise ValueError("war occupation actor differs from the played character")
        for name in ("primary_attacker_character_id", "primary_defender_character_id"):
            _id(value.get(name), name)
        if value.get("player_side") not in {"attacker", "defender"} or (expected_player_side is not None and value["player_side"] != expected_player_side):
            raise ValueError("war occupation player side differs from the current participant side")
    elif complete or not isinstance(reason, str) or not reason:
        raise ValueError("unavailable occupation collection requires an explicit failure reason")
    # Build identity is native provenance. Existing exact-build adapter binding
    # determines support; this reader adds no separate version approval gate.
    if not isinstance(value.get("game_version"), str) or not isinstance(value.get("executable_sha256"), str):
        raise ValueError("war occupation targets lack native build provenance")
    counts = value.get("side_counts")
    rows = value.get("rows")
    if not isinstance(counts, list) or not isinstance(rows, list):
        raise ValueError("war occupation collection rows and side counts must be arrays")
    sides: list[str] = []
    for row in counts:
        if not isinstance(row, dict) or row.get("territory_side") not in {"attacker", "defender"}:
            raise ValueError("occupation side counter lacks its territory side")
        sides.append(str(row["territory_side"]))
        eligible = _count(row.get("eligible"), "side_counts.eligible")
        occupied = _count(row.get("occupied"), "side_counts.occupied")
        _count(row.get("native_candidate_count"), "side_counts.native_candidate_count")
        side_complete = _bool(row.get("collection_complete"), "side_counts.collection_complete")
        if occupied > eligible or (available and not side_complete):
            raise ValueError("occupation side counter is incomplete or exceeds its eligible denominator")
    if available and sorted(sides) != ["attacker", "defender"]:
        raise ValueError("complete occupation collection requires both territory-side counters")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("occupation target row must be an object")
        for name in ("holding_title_id", "province_id", "legal_holder_character_id"):
            _id(row.get(name), name)
        if row.get("territory_side") not in {"attacker", "defender"}:
            raise ValueError("occupation holding lacks its native territory side")
        observable = _bool(row.get("occupation_observable"), "occupation_observable")
        occupier_side = row.get("occupier_side")
        if occupier_side not in {"attacker", "defender", "outside_war", "none", "unavailable"}:
            raise ValueError("occupation holding has an unknown occupier side")
        if observable:
            occupied = _bool(row.get("is_occupied"), "is_occupied")
            _bool(row.get("counted_occupied_by_opposing_side"), "counted_occupied_by_opposing_side")
            if occupied:
                _id(row.get("occupying_character_id"), "occupying_character_id")
                if occupier_side not in {"attacker", "defender", "outside_war"}:
                    raise ValueError("occupied holding lacks an actual occupier side")
            elif row.get("occupying_character_id") is not None or occupier_side != "none":
                raise ValueError("unoccupied holding must preserve legal occupier absence")
        elif any(row.get(name) is not None for name in ("is_occupied", "occupying_character_id", "counted_occupied_by_opposing_side")) or occupier_side != "unavailable":
            raise ValueError("unobservable occupation must not substitute false or zero")
        if available and not observable:
            raise ValueError("complete occupation collection contains an unobservable holding")
    result = copy.deepcopy(value)
    result["executable_sha256"] = str(value["executable_sha256"]).lower()
    return result
