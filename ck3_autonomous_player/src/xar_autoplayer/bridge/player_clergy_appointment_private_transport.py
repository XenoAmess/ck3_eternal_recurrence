"""Observe the native current player's clergy predicates for an explicit candidate."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_county_conversion_private_observation import normalize_player_county_conversion_v1
from .player_clergy_candidate_terms_private_observation import normalize_player_clergy_candidate_terms_v1
from .player_clergy_mode0_source_12004 import player_clergy_mode0_source_from_query_12004
from .version_identity import CK3_12002, CK3_12003, CK3_12004, require_exact_native_backend, require_exact_native_build


STEP = "query-player-clergy-appointment-v1"
DOMAIN_KEY = "player_clergy_appointment_v1"
SCHEMA = "xar.ck3.religion-clergy-appointment/v1"
PERMISSION = "allow_private_player_clergy_appointment_query"
_KEYS = {
    "schema", "schema_version", "exact_build", "status", "failure", "capture_epoch",
    "date_raw", "owner_character_id", "candidate_character_id", "position_key",
    "position_present", "active_task_id", "incumbent_character_id",
    "candidate_court_owner_id", "owner_rite_id", "candidate_rite_id",
    "candidate_is_incumbent", "candidate_matches_owner_context", "native_valid_position",
    "native_valid_character", "native_can_reassign", "action_eligibility_complete",
}
_OPTIONAL_KEYS = {"native_can_fire"}
_NULLABLE_BOOLS = (
    "candidate_matches_owner_context", "native_valid_position", "native_valid_character",
    "native_can_reassign", "native_can_fire",
)


def _int32(value: object, key: str) -> None:
    if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
        raise ValueError(f"native clergy signed integer is malformed: {key}")


def _candidate_id(value: object) -> None:
    if type(value) is not int or not 0 < value < (1 << 31):
        raise ValueError("candidate_character_id must be an explicit positive int32 full CharacterID")


def normalize_player_clergy_appointment_v1(
    value: object, *, snapshot: Mapping[str, object], candidate_character_id: int,
) -> dict[str, object]:
    """Preserve independent native booleans, legal missing seats and partial failures."""
    _candidate_id(candidate_character_id)
    if (not isinstance(value, dict) or not _KEYS <= set(value) <= _KEYS | _OPTIONAL_KEYS
            or value["schema"] != SCHEMA
            or type(value["schema_version"]) is not int or value["schema_version"] != 1):
        raise ValueError("native clergy appointment schema is malformed")
    exact = value["exact_build"]
    if not isinstance(exact, dict) or set(exact) != {"game_version", "executable_sha256"}:
        raise ValueError("native clergy appointment exact build is malformed")
    build = require_exact_native_build(exact["game_version"], exact["executable_sha256"])
    if build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(snapshot):
        raise ValueError("native clergy appointment belongs to another build")
    if (value["status"] not in ("available", "unavailable")
            or not isinstance(value["failure"], str) or not value["failure"]
            or value["position_key"] != "councillor_court_chaplain"
            or type(value["position_present"]) is not bool
            or type(value["candidate_is_incumbent"]) is not bool
            or value["action_eligibility_complete"] is not False):
        raise ValueError("native clergy appointment status is malformed")
    if type(value["capture_epoch"]) is not int or not 0 <= value["capture_epoch"] < (1 << 64):
        raise ValueError("native clergy appointment capture epoch is malformed")
    for key in ("date_raw", "owner_character_id", "candidate_character_id"):
        _int32(value[key], key)
    if value["candidate_character_id"] != candidate_character_id:
        raise ValueError("native clergy appointment differs from its requested candidate")
    for key in ("active_task_id", "incumbent_character_id", "candidate_court_owner_id"):
        if value[key] is not None:
            _int32(value[key], key)
    for key in ("owner_rite_id", "candidate_rite_id"):
        if value[key] is not None and (type(value[key]) is not int or not 0 <= value[key] <= 0xFFFFFFFF):
            raise ValueError(f"native clergy full Rite reference is malformed: {key}")
    for key in _NULLABLE_BOOLS:
        if value.get(key) is not None and type(value[key]) is not bool:
            raise ValueError(f"native clergy nullable boolean is malformed: {key}")
    if value["status"] == "available":
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["owner_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["failure"] != "none" or value["capture_epoch"] == 0):
            raise ValueError("native clergy appointment differs from its queried player frame")
    # Unavailable retains actual partial fields/defaults and its original reason.
    # Native false/null predicates stay independent; no action-ready is derived.
    return deepcopy(value)


def query_player_clergy_appointment_private_v1(
    driver: object, *, expected_revision: int, candidate_character_id: int,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    _candidate_id(candidate_character_id)
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"candidate_character_id": candidate_character_id,
                        "expected_public_revision": expected_revision},
        timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-clergy-appointment-v1",
        )
        if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native clergy appointment envelope differs from the queried build/frame")
        value = normalize_player_clergy_appointment_v1(
            result.get("player_clergy_appointment"), snapshot=before,
            candidate_character_id=candidate_character_id,
        )
        if result.get("status") != ("observed" if value["status"] == "available" else "unavailable"):
            raise ValueError("native clergy appointment envelope lost its source status")
        county = (
            {"county_conversion": normalize_player_county_conversion_v1(
                result["county_conversion"], snapshot=before, clergy=value,
            )}
            if "county_conversion" in result else {}
        )
        terms = (
            {"candidate_terms": normalize_player_clergy_candidate_terms_v1(
                result["candidate_terms"], snapshot=before, clergy=value,
            )}
            if "candidate_terms" in result else {}
        )
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    source = player_clergy_mode0_source_from_query_12004(result, snapshot=before, clergy=value)
    return {
        **value, **county, **terms, **source, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "query_status": result["status"], "read_only": True, "advertised": False,
    }
