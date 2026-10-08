"""Current native holder and realm relationships for one exact TitleID.

This query includes titles outside the player's held-title partition. An
unheld title is an available observation with a null holder, not a failed read.
"""
from __future__ import annotations

from collections.abc import Mapping
import copy
import re

QUERY_TITLE_HOLDER_V1_CAPABILITY = "game.command.query-title-holder-v1-N"
QUERY_TITLE_HOLDER_V1_STEP_PREFIX = "query-title-holder-v1-"
TITLE_HOLDER_V1_SCHEMA = "xar.ck3.title-holder.v1"
_TITLE_KEY = re.compile(r"[bcdkeh]_[a-z0-9][a-z0-9_]*", re.ASCII)
_TITLE_KEY_PREFIX = {1: "b_", 2: "c_", 3: "d_", 4: "k_", 5: "e_", 6: "h_"}


def title_holder_id(value: object, name: str = "title_id") -> int:
    if type(value) is not int or not 0 <= value <= 2**31 - 1:
        raise ValueError(f"{name} must be a full non-negative int32 ID")
    return value


def query_title_holder_v1_step(title_id: int) -> str:
    return QUERY_TITLE_HOLDER_V1_STEP_PREFIX + str(title_holder_id(title_id))


def parse_query_title_holder_v1_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(QUERY_TITLE_HOLDER_V1_STEP_PREFIX):
        return None
    value = step[len(QUERY_TITLE_HOLDER_V1_STEP_PREFIX):]
    if not value.isascii() or not value.isdecimal():
        return None
    title_id = int(value)
    if value != str(title_id) or title_id > 2**31 - 1:
        return None
    return title_id


def title_holder_query_actor(snapshot: Mapping[str, object]) -> int:
    if snapshot.get("paused") is not True:
        raise ValueError("title holder query requires a paused snapshot")
    actor = snapshot.get("played_character")
    if not isinstance(actor, dict) or actor.get("alive") is not True:
        raise ValueError("title holder query lacks a living played character")
    return title_holder_id(actor.get("character_id"), "played CharacterID")


def normalize_title_holder_v1(
    value: object,
    *,
    expected_title_id: int,
    expected_actor_character_id: int,
    expected_snapshot_revision: int,
    expected_date_raw: int,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("title holder must be an object")
    if value.get("schema") != TITLE_HOLDER_V1_SCHEMA or type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("title holder uses an unsupported schema")
    available = value.get("available")
    if type(available) is not bool or value.get("status") != ("available" if available else "unavailable"):
        raise ValueError("title holder status disagrees with availability")
    if type(expected_snapshot_revision) is not int or expected_snapshot_revision <= 0 or type(value.get("snapshot_revision")) is not int or value["snapshot_revision"] != expected_snapshot_revision:
        raise ValueError("title holder differs from the native snapshot revision")
    if type(expected_date_raw) is not int or type(value.get("date_raw")) is not int or value["date_raw"] != expected_date_raw:
        raise ValueError("title holder differs from the paused date")
    if title_holder_id(value.get("title_id")) != title_holder_id(expected_title_id, "expected_title_id"):
        raise ValueError("title holder differs from the requested TitleID")
    if title_holder_id(value.get("actor_character_id"), "actor_character_id") != title_holder_id(expected_actor_character_id, "expected_actor_character_id"):
        raise ValueError("title holder actor differs from the played character")
    if not isinstance(value.get("game_version"), str) or not isinstance(value.get("executable_sha256"), str):
        raise ValueError("title holder lacks native build provenance")
    reason = value.get("unavailable_reason")
    if available:
        if reason is not None:
            raise ValueError("available title holder must not carry a failure reason")
        tier_raw = value.get("title_tier_raw")
        tiers = {1: "barony", 2: "county", 3: "duchy", 4: "kingdom", 5: "empire", 6: "hegemony"}
        if type(tier_raw) is not int or value.get("title_tier_key") != tiers.get(tier_raw):
            raise ValueError("title holder native tier pair is inconsistent")
        for field in ("holder_is_player", "holder_in_player_realm"):
            if type(value.get(field)) is not bool:
                raise ValueError(f"title holder {field} must be observable")
        holder = value.get("holder_character_id")
        immediate = value.get("holder_immediate_liege_character_id")
        top = value.get("holder_top_liege_character_id")
        if holder is None:
            if value["holder_is_player"] or value["holder_in_player_realm"] or immediate is not None or top is not None:
                raise ValueError("unheld title must preserve legal holder and liege absence")
        else:
            title_holder_id(holder, "holder_character_id")
            if immediate is not None:
                title_holder_id(immediate, "holder_immediate_liege_character_id")
            title_holder_id(top, "holder_top_liege_character_id")
            if value["holder_is_player"] is not (holder == expected_actor_character_id):
                raise ValueError("title holder player identity is inconsistent")
            if value["holder_is_player"] and not value["holder_in_player_realm"]:
                raise ValueError("player-held title must be in the player realm")
    elif not isinstance(reason, str) or not reason:
        raise ValueError("unavailable title holder requires an explicit reason")
    elif any(value.get(field) is not None for field in (
        "title_tier_raw", "title_tier_key", "holder_character_id",
        "holder_is_player", "holder_in_player_realm",
        "holder_immediate_liege_character_id", "holder_top_liege_character_id",
    )):
        raise ValueError("unavailable title holder must preserve unknown fields as null")
    key_fields = ("title_key", "title_key_available", "title_key_status",
                  "title_key_unavailable_reason")
    # Historical v1 packets may omit this additive observation. Current4
    # must distinguish a copied key from a factual unavailable key.
    if value["game_version"] == "1.20.0.4" or any(field in value for field in key_fields):
        if any(field not in value for field in key_fields):
            raise ValueError("title holder lacks the complete title-key observation")
        key_available = value["title_key_available"]
        if type(key_available) is not bool or value["title_key_status"] != (
            "available" if key_available else "unavailable"
        ):
            raise ValueError("title key status disagrees with availability")
        title_key = value["title_key"]
        key_reason = value["title_key_unavailable_reason"]
        if key_available:
            if (not available or key_reason is not None or
                not isinstance(title_key, str) or not title_key.isascii() or
                not 3 <= len(title_key) <= 1024 or _TITLE_KEY.fullmatch(title_key) is None or
                not title_key.startswith(_TITLE_KEY_PREFIX[value["title_tier_raw"]])):
                raise ValueError("available title key lacks an exact canonical tier/key pair")
        elif title_key is not None or not isinstance(key_reason, str) or not key_reason:
            raise ValueError("unavailable title key requires null key and explicit reason")
    return copy.deepcopy(value)
