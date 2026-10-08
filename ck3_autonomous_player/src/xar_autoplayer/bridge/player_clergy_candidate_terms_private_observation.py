"""Preserve exact .3/.4 candidate membership and independent appointment terms."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .version_identity import CK3_12003, CK3_12004, require_exact_native_build


SCHEMA = "xar.ck3.clergy-candidate-terms/v1"
_FIELDS = {
    "schema", "schema_version", "exact_build", "available", "failure",
    "capture_epoch", "public_revision", "native_revision", "date_raw",
    "owner_character_id", "candidate_character_id", "position_key",
    "active_task_id", "incumbent_character_id", "candidate_collection_available",
    "candidate_count", "candidate_match_count", "candidate_in_native_collection",
    "native_collection_ordinal", "candidate_learning", "final_predicates_available",
    "candidate_already_councillor", "candidate_is_guest", "pending_character_interaction",
    "native_can_confirm_replacement", "action_eligibility_complete",
}
_TERMS = (
    "candidate_already_councillor", "candidate_is_guest", "pending_character_interaction",
    "native_can_confirm_replacement",
)


def _integer(value: object, name: str, minimum: int, maximum: int) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"native clergy candidate integer is malformed: {name}")


def normalize_player_clergy_candidate_terms_v1(
    value: object, *, snapshot: Mapping[str, object], clergy: Mapping[str, object],
) -> dict[str, object]:
    """Validate the actual sibling without deriving a playable assignment route."""
    if (not isinstance(value, dict) or set(value) != _FIELDS
            or value["schema"] != SCHEMA or type(value["schema_version"]) is not int
            or value["schema_version"] != 1):
        raise ValueError("native clergy candidate terms schema is malformed")
    exact = value["exact_build"]
    if (not isinstance(exact, dict) or set(exact) != {"game_version", "executable_sha256"}
            or require_exact_native_build(exact["game_version"], exact["executable_sha256"])
            not in (CK3_12003, CK3_12004)):
        raise ValueError("native clergy candidate terms require the exact .3 or .4 build")
    if exact != clergy.get("exact_build"):
        raise ValueError("native clergy candidate terms differ from the clergy build")
    for key in ("available", "candidate_collection_available", "final_predicates_available"):
        if type(value[key]) is not bool:
            raise ValueError(f"native clergy candidate flag is malformed: {key}")
    if (value["position_key"] != "councillor_court_chaplain"
            or value["action_eligibility_complete"] is not False
            or not isinstance(value["failure"], str) or not value["failure"]):
        raise ValueError("native clergy candidate status is malformed")
    for key in ("capture_epoch", "public_revision", "native_revision"):
        _integer(value[key], key, 0, (1 << 64) - 1)
    for key in ("date_raw", "owner_character_id", "candidate_character_id"):
        _integer(value[key], key, -(1 << 31), (1 << 31) - 1)
    if value["candidate_character_id"] != clergy.get("candidate_character_id"):
        raise ValueError("native clergy candidate terms changed the requested candidate")
    for key in ("active_task_id", "incumbent_character_id"):
        if value[key] is not None:
            _integer(value[key], key, -(1 << 31), (1 << 31) - 1)
    for key in ("candidate_count", "candidate_match_count", "native_collection_ordinal"):
        if value[key] is not None:
            _integer(value[key], key, 0, (1 << 32) - 1)
    if value["candidate_learning"] is not None:
        _integer(value["candidate_learning"], "candidate_learning", 0, (1 << 31) - 1)
    for key in ("candidate_in_native_collection", *_TERMS):
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native clergy candidate nullable flag is malformed: {key}")

    if value["candidate_collection_available"]:
        if (value["candidate_count"] is None or value["candidate_match_count"] not in (0, 1)
                or value["candidate_match_count"] > value["candidate_count"]
                or value["candidate_in_native_collection"] is not (value["candidate_match_count"] == 1)):
            raise ValueError("native clergy candidate collection lost exact membership")
        if value["candidate_in_native_collection"]:
            if value["native_collection_ordinal"] is None or value["candidate_learning"] is None:
                raise ValueError("native clergy candidate collection lost native skill/ordinal")
        elif value["native_collection_ordinal"] is not None or value["candidate_learning"] is not None:
            raise ValueError("native clergy candidate absent row acquired invented skill/ordinal")
    elif any(value[key] is not None for key in (
        "candidate_count", "candidate_match_count", "candidate_in_native_collection",
        "native_collection_ordinal", "candidate_learning",
    )):
        raise ValueError("native clergy unread collection acquired invented membership")

    if value["final_predicates_available"]:
        if (value["candidate_in_native_collection"] is not True
                or any(type(value[key]) is not bool for key in _TERMS[:3])
                or (value["incumbent_character_id"] is None) is not
                    (value["native_can_confirm_replacement"] is None)):
            raise ValueError("native clergy final terms lost route/vacancy semantics")
    elif any(value[key] is not None for key in _TERMS):
        raise ValueError("native clergy unread predicates acquired invented booleans")

    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping) or value["owner_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["public_revision"] != snapshot.get("revision")
                or value["native_revision"] != snapshot.get("native_revision")
                or value["capture_epoch"] == 0 or value["failure"] != "none"
                or value["candidate_collection_available"] is not True
                or value["active_task_id"] is None
                or (value["candidate_in_native_collection"] is True
                    and value["final_predicates_available"] is not True)):
            raise ValueError("native clergy candidate terms differ from the actual queried frame")
        if clergy.get("status") == "available" and (
            value["owner_character_id"] != clergy.get("owner_character_id")
            or value["active_task_id"] != clergy.get("active_task_id")
            or value["incumbent_character_id"] != clergy.get("incumbent_character_id")
            or value["capture_epoch"] != clergy.get("capture_epoch")
        ):
            raise ValueError("native clergy candidate terms differ from the actual clergy seat")
    elif value["failure"] == "none" or value["final_predicates_available"]:
        raise ValueError("native clergy unavailable terms lost their failure semantics")
    return deepcopy(value)
