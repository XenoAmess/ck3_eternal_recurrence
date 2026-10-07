"""Paused current-player claims for ordered TitleIDs, independent of CWar.

This observes current native claim rows; it does not predict settlement effects
or identify a former claimant after the played character changes.
"""
from __future__ import annotations

from collections.abc import Mapping
import copy

QUERY_PLAYER_CLAIMS_V1_CAPABILITY = "game.command.query-player-claims-v1-IDS"
QUERY_PLAYER_CLAIMS_V1_STEP_PREFIX = "query-player-claims-v1-"
PLAYER_CLAIMS_V1_SCHEMA = "xar.ck3.player-claims.v1"
PLAYER_CLAIMS_V1_MAXIMUM_TITLES = 4096
PLAYER_CLAIMS_V1_GAME_VERSION = "1.20.0.4"
PLAYER_CLAIMS_V1_EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"

def _id(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= 2**31 - 1:
        raise ValueError(f"{name} must be a full non-negative int32 ID")
    return value

def player_claims_title_ids(value: object) -> list[int]:
    if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= PLAYER_CLAIMS_V1_MAXIMUM_TITLES:
        raise ValueError("title_ids must contain 1..4096 ordered TitleIDs")
    ids = [_id(item, "TitleID") for item in value]
    if len(set(ids)) != len(ids):
        raise ValueError("title_ids must not contain duplicates")
    return ids

def query_player_claims_v1_step(title_ids: object) -> str:
    return QUERY_PLAYER_CLAIMS_V1_STEP_PREFIX + ",".join(map(str, player_claims_title_ids(title_ids)))

def parse_query_player_claims_v1_step(step: object) -> list[int] | None:
    if not isinstance(step, str) or not step.startswith(QUERY_PLAYER_CLAIMS_V1_STEP_PREFIX):
        return None
    tokens = step[len(QUERY_PLAYER_CLAIMS_V1_STEP_PREFIX):].split(",")
    if not 1 <= len(tokens) <= PLAYER_CLAIMS_V1_MAXIMUM_TITLES:
        return None
    # An int32 literal is at most ten digits; reject oversized input before int().
    if any(not token.isascii() or not token.isdecimal() or len(token) > 10 or
           (len(token) > 1 and token[0] == "0") for token in tokens):
        return None
    try:
        return player_claims_title_ids([int(token) for token in tokens])
    except ValueError:
        return None

def player_claims_query_actor(snapshot: Mapping[str, object]) -> int:
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("player claims query requires a ready paused map")
    actor = snapshot.get("played_character")
    if not isinstance(actor, dict) or actor.get("alive") is not True:
        raise ValueError("player claims query lacks a living played character")
    return _id(actor.get("character_id"), "played CharacterID")

def normalize_player_claims_v1(value: object, *, expected_title_ids: object,
    expected_actor_character_id: int, expected_snapshot_revision: int,
    expected_date_raw: int) -> dict[str, object]:
    ids = player_claims_title_ids(expected_title_ids)
    actor = _id(expected_actor_character_id, "expected actor")
    if not isinstance(value, dict) or value.get("schema") != PLAYER_CLAIMS_V1_SCHEMA or type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("player claims uses an unsupported schema")
    sha = value.get("executable_sha256")
    if value.get("game_version") != PLAYER_CLAIMS_V1_GAME_VERSION or not isinstance(sha, str) or sha.upper() != PLAYER_CLAIMS_V1_EXE_SHA256:
        raise ValueError("player claims lacks exact actual4 build provenance")
    if type(expected_snapshot_revision) is not int or expected_snapshot_revision <= 0 or type(value.get("snapshot_revision")) is not int or value["snapshot_revision"] != expected_snapshot_revision:
        raise ValueError("player claims differs from native snapshot revision")
    if type(expected_date_raw) is not int or type(value.get("date_raw")) is not int or value["date_raw"] != expected_date_raw:
        raise ValueError("player claims differs from paused date")
    if _id(value.get("actor_character_id"), "actor_character_id") != actor:
        raise ValueError("player claims actor differs from current played character")
    if player_claims_title_ids(value.get("title_ids")) != ids:
        raise ValueError("player claims differs from ordered requested TitleIDs")
    available = value.get("available")
    if type(available) is not bool or value.get("status") != ("available" if available else "unavailable"):
        raise ValueError("player claims status disagrees with availability")
    if not available:
        if not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"] or value.get("claims") is not None:
            raise ValueError("unavailable player claims must preserve unknown rows and a reason")
        return copy.deepcopy(value)
    if value.get("unavailable_reason") is not None:
        raise ValueError("available player claims must not carry failure reason")
    rows = value.get("claims")
    if not isinstance(rows, list) or len(rows) != len(ids):
        raise ValueError("player claim rows must correspond one-to-one to ordered TitleIDs")
    for expected, row in zip(ids, rows):
        if not isinstance(row, dict) or set(row) != {"title_id", "present", "state", "strong", "implicit"}:
            raise ValueError("player claim row fields are malformed")
        if _id(row.get("title_id"), "claim TitleID") != expected or type(row.get("present")) is not bool:
            raise ValueError("player claim row identity/presence is malformed")
        if row["present"]:
            if type(row.get("strong")) is not bool or type(row.get("implicit")) is not bool:
                raise ValueError("present player claim requires native boolean flags")
            state = ("strong" if row["strong"] else "weak") + ("_implicit" if row["implicit"] else "_explicit")
            if row.get("state") != state:
                raise ValueError("player claim state disagrees with native flags")
        elif row.get("state") != "absent" or row.get("strong") is not None or row.get("implicit") is not None:
            raise ValueError("absent player claim must preserve absent optional flags")
    return copy.deepcopy(value)
