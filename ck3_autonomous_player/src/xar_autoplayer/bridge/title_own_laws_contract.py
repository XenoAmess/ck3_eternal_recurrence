"""Complete own-law rows for one current full unsigned TitleID.

This reads the title's physical ordered law array. It does not infer a holder,
realm-law inheritance, installation cause, script trigger or Faith selector.
"""
from __future__ import annotations

from collections.abc import Mapping
import copy

QUERY_TITLE_OWN_LAWS_V1_CAPABILITY = "game.command.query-title-own-laws-v1-ID"
QUERY_TITLE_OWN_LAWS_V1_STEP_PREFIX = "query-title-own-laws-v1-"
TITLE_OWN_LAWS_V1_SCHEMA = "xar.ck3.title-own-laws.v1"
TITLE_OWN_LAWS_V1_GAME_VERSION = "1.20.0.4"
TITLE_OWN_LAWS_V1_EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
TITLE_OWN_LAWS_V1_MAXIMUM_LAWS = 256
TITLE_OWN_LAWS_V1_MAXIMUM_KEY_BYTES = 256
_UINT32_MAX = 2**32 - 1


def title_own_laws_id(value: object) -> int:
    if type(value) is not int or not 0 <= value < _UINT32_MAX:
        raise ValueError("title_id must be a full uint32 ID below the invalid sentinel")
    return value


def title_own_laws_revision(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("expected_revision must be a non-negative integer")
    return value


def query_title_own_laws_v1_step(title_id: object) -> str:
    return QUERY_TITLE_OWN_LAWS_V1_STEP_PREFIX + str(title_own_laws_id(title_id))


def parse_query_title_own_laws_v1_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(QUERY_TITLE_OWN_LAWS_V1_STEP_PREFIX):
        return None
    token = step[len(QUERY_TITLE_OWN_LAWS_V1_STEP_PREFIX):]
    if not token.isascii() or not token.isdecimal() or len(token) > 10:
        return None
    if len(token) > 1 and token[0] == "0":
        return None
    value = int(token)
    return value if value < _UINT32_MAX else None


def title_own_laws_query_actor(snapshot: Mapping[str, object]) -> int:
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("title own-laws query requires a ready paused map")
    actor = snapshot.get("played_character")
    if not isinstance(actor, dict) or actor.get("alive") is not True:
        raise ValueError("title own-laws query lacks a living played character")
    actor_id = actor.get("character_id")
    if type(actor_id) is not int or not 0 <= actor_id <= 2**31 - 1:
        raise ValueError("title own-laws query lacks a full current played CharacterID")
    return actor_id


def normalize_title_own_laws_v1(
    value: object, *, expected_title_id: int, expected_actor_character_id: int,
    expected_snapshot_revision: int, expected_date_raw: int,
) -> dict[str, object]:
    title_id = title_own_laws_id(expected_title_id)
    if not isinstance(value, dict) or value.get("schema") != TITLE_OWN_LAWS_V1_SCHEMA:
        raise ValueError("title own-laws uses an unsupported schema")
    if set(value) != {
        "schema", "schema_version", "game_version", "executable_sha256",
        "status", "available", "unavailable_reason", "snapshot_revision",
        "date_raw", "actor_character_id", "title_id", "native_law_count",
        "laws", "single_heir_member",
    }:
        raise ValueError("title own-laws requires every agreed DTO field")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("title own-laws uses an unsupported schema version")
    sha = value.get("executable_sha256")
    if value.get("game_version") != TITLE_OWN_LAWS_V1_GAME_VERSION or not isinstance(sha, str) or sha.upper() != TITLE_OWN_LAWS_V1_EXE_SHA256:
        raise ValueError("title own-laws lacks exact actual4 build provenance")
    if type(expected_snapshot_revision) is not int or expected_snapshot_revision < 0 or type(value.get("snapshot_revision")) is not int or value["snapshot_revision"] != expected_snapshot_revision:
        raise ValueError("title own-laws differs from native snapshot revision")
    if type(expected_date_raw) is not int or type(value.get("date_raw")) is not int or value["date_raw"] != expected_date_raw:
        raise ValueError("title own-laws differs from paused date")
    if type(expected_actor_character_id) is not int or not 0 <= expected_actor_character_id <= 2**31 - 1 or type(value.get("actor_character_id")) is not int or value["actor_character_id"] != expected_actor_character_id:
        raise ValueError("title own-laws differs from current played character")
    if title_own_laws_id(value.get("title_id")) != title_id:
        raise ValueError("title own-laws differs from requested full TitleID")
    available = value.get("available")
    if type(available) is not bool or value.get("status") != ("available" if available else "unavailable"):
        raise ValueError("title own-laws status disagrees with availability")
    if not available:
        reason = value.get("unavailable_reason")
        if not isinstance(reason, str) or not reason or any(value.get(field) is not None for field in ("native_law_count", "laws", "single_heir_member")):
            raise ValueError("unavailable title own-laws requires null unknown fields and a reason")
        return copy.deepcopy(value)
    if value.get("unavailable_reason") is not None:
        raise ValueError("available title own-laws must not carry a failure reason")
    count = value.get("native_law_count")
    laws = value.get("laws")
    if type(count) is not int or not 0 <= count <= TITLE_OWN_LAWS_V1_MAXIMUM_LAWS or not isinstance(laws, list) or len(laws) != count:
        raise ValueError("title own-laws must contain the complete native law count")
    for row in laws:
        if not isinstance(row, dict) or set(row) != {"native_definition_id", "key"}:
            raise ValueError("title own-law row fields are malformed")
        definition_id = row["native_definition_id"]
        if type(definition_id) is not int or not 0 <= definition_id <= _UINT32_MAX:
            raise ValueError("title own-law definition ID must preserve its complete uint32 value")
        key = row["key"]
        if not isinstance(key, str) or not 0 < len(key) < TITLE_OWN_LAWS_V1_MAXIMUM_KEY_BYTES or any(not 0x21 <= ord(character) <= 0x7E for character in key):
            raise ValueError("title own-law key differs from the native printable ASCII bound")
    member = value.get("single_heir_member")
    if type(member) is not bool or member is not any(row["key"] == "single_heir_succession_law" for row in laws):
        raise ValueError("title own-laws single-heir membership disagrees with complete ordered keys")
    return copy.deepcopy(value)
