"""Validate the existing SDK projection DTO; never issue Native custody or H.

The optional value is produced by the original NativeDriver query. Accepting its
shape does not authenticate a provider, create a token, or change its score.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import NoReturn, TypeGuard
from dataclasses import fields

from xar_autoplayer.player_heir_fixed_dynasty_projection_v1 import (
    FixedDynastyCandidateProjectionV1, GETTER_SOURCE_CLOSURE_SHA256,
    ROBERT_V20261019_T0_ANCHOR, _valid_core,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError

PROJECTION = "player_heir_fixed_dynasty_projection_v1"
COMPONENT = "player_heir_candidate_v1"
_BASE = {field.name for field in fields(FixedDynastyCandidateProjectionV1)}
_BOUND = {
    "machine_id", "game_identity", "native_provider_sha256", "owner_source_epoch",
    "query_id", "native_query_sequence", "capture_epoch_basis",
    "queried_snapshot_id", "queried_revision", "queried_native_revision",
}


def _require(value: object, reason: str) -> None:
    if not value:
        raise BridgeUnavailableError("campaign-root player-heir projection malformed: " + reason)


def _integer(value: object, low: int, high: int) -> TypeGuard[int]:
    return type(value) is int and low <= value <= high


def _text(value: object, limit: int) -> TypeGuard[str]:
    return isinstance(value, str) and 0 < len(value) <= limit


def _sha(value: object) -> TypeGuard[str]:
    return (isinstance(value, str) and len(value) == 64
            and all(character in "0123456789abcdef" for character in value))


def _mapping(value: object, reason: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        _fail(reason)
    return {key: item for key, item in value.items()}


def _fail(reason: str) -> NoReturn:
    raise BridgeUnavailableError("campaign-root player-heir projection malformed: " + reason)


def validate_player_heir_projection_service_v1(
    value: object, *, root: Mapping[str, object], result: Mapping[str, object],
) -> None:
    """Check one original optional result without importing/reading OS custody.

    Unknown DTOs may lack the provider binding, as the original SDK deliberately
    returns unknown before it has one. A positive witness must carry the entire
    original binding and agree with its already validated native component.
    """
    value = _mapping(value, "keys")
    _require(set(value) in (_BASE, _BASE | _BOUND), "keys")
    _require(isinstance(root, dict) and COMPONENT in root, "component absent")
    _require(value["status"] in ("unknown", "positive_witness"), "status")
    _require(_text(value["reason"], 1024), "reason")
    _require(type(value["fixed_dynasty_id_raw"]) is int
             and value["fixed_dynasty_id_raw"] == ROBERT_V20261019_T0_ANCHOR.founding_dynasty_id_raw,
             "fixed dynasty")
    candidate = value["candidate_character_id"]
    _require(candidate is None or _integer(candidate, -(2**31), 2**31 - 1)
             and candidate != -1, "candidate full ID")
    same = value["candidate_same_fixed_dynasty"]
    _require(same is None or type(same) is bool, "same dynasty type")
    _require(type(value["positive_same_dynasty_legal_witness"]) is bool, "witness type")
    _require(value["b"] is None and value["complete_backup_domain"] is False
             and value["scope"] == "pure_current_candidate_projection", "scope or backups")
    interval = value["H_interval"]
    if not isinstance(interval, (tuple, list)) or type(interval) not in (tuple, list):
        _fail("interval type")
    _require(len(interval) == 2
             and all(type(number) is int for number in interval), "interval type")
    positive = value["status"] == "positive_witness"
    if positive:
        _require(set(value) == _BASE | _BOUND and candidate is not None
                 and same is True and value["positive_same_dynasty_legal_witness"] is True
                 and type(value["k"]) is int and value["k"] == 1
                 and tuple(interval) == (70, 100)
                 and value["reason"] == "one_living_native_player_heir_in_fixed_D0",
                 "positive semantics")
    else:
        _require(value["k"] is None and value["positive_same_dynasty_legal_witness"] is False
                 and same is not True and tuple(interval) == (0, 100), "unknown semantics")
    if set(value) == _BASE | _BOUND:
        _require(_text(value["machine_id"], 256) and _text(value["query_id"], 1024)
                 and _sha(value["native_provider_sha256"])
                 and value["native_provider_sha256"] != GETTER_SOURCE_CLOSURE_SHA256
                 and _sha(value["owner_source_epoch"]), "provider binding types")
        game = _mapping(value["game_identity"], "exact game identity types")
        _require(isinstance(game, dict) and set(game) == {"pid", "creation_date", "executable"}
                 and _integer(game["pid"], 1, 2**31 - 1)
                 and _text(game["creation_date"], 128) and _text(game["executable"], 4096),
                 "exact game identity types")
        _require(_integer(value["native_query_sequence"], 1, 2**53 - 1)
                 and value["native_query_sequence"] == result["query_sequence"]
                 and value["capture_epoch_basis"] == "original_root_query_sequence",
                 "query sequence")
        for key in ("queried_snapshot_id", "queried_revision", "queried_native_revision"):
            _require(value[key] == result[key] and type(value[key]) is type(result[key]),
                     "query frame " + key)
    if positive:
        from xar_autoplayer.bridge.player_heir_candidate_component_v1 import (
            parse_optional_player_heir_component_v1,
        )
        parsed = parse_optional_player_heir_component_v1(root[COMPONENT], root=root)
        observation = parsed.observation
        _require(parsed.status == "parsed" and observation is not None, "native component")
        _require(root.get("player_character_alive") is True
                 and observation.source_fixture is False
                 and all(getattr(observation, key) is True for key in (
                     "available", "original_getter_source_bound", "getter_observed",
                     "candidate_present", "candidate_alive", "identity_and_frame_stable",
                     "lineage_available"))
                 and observation.unavailable_reason in (None, "")
                 and observation.lineage_unavailable_reason in (None, "")
                 and observation.before == observation.after
                 and _valid_core(observation.before) and _valid_core(observation.after)
                 and observation.candidate_lineage.house_id != -1
                 and observation.candidate_character_id == candidate
                 and candidate != observation.actor_character_id
                 and observation.candidate_lineage.dynasty_id == value["fixed_dynasty_id_raw"],
                 "native positive witness differs")
