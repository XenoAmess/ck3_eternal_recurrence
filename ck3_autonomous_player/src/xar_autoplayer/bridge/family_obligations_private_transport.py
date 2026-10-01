"""Native child-house preview and complete sampled betrothal-break terms."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity
from .version_identity import require_exact_native_build


STEP = "read-family-obligations-private-12002"
KIND = "ck3_12002_family_obligations_private_v1"


def _id(value: object) -> bool:
    return type(value) is int and 0 < value < (1 << 32)


def normalize_family_obligations_private_v1(
    value: object, *, snapshot: Mapping[str, object], subject_character_id: int,
    candidate_character_id: int, request_matrilineal_option: bool,
    break_recipient_character_id: int | None = None,
) -> dict[str, object]:
    if (not isinstance(value, dict) or value.get("kind") != KIND
            or value.get("schema_version") != 1
            or value.get("query_status") not in {"available", "partial", "unavailable"}):
        raise ValueError("family native observation schema is malformed")
    identity = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if identity != private_native_build_identity(snapshot):
        raise ValueError("family native observation belongs to another build")
    frame = value.get("frame")
    actor = snapshot.get("played_character")
    if (not isinstance(frame, Mapping) or not isinstance(actor, Mapping)
            or frame.get("snapshot_revision") != snapshot.get("native_revision")
            or frame.get("date_raw") != snapshot.get("date_raw")
            or frame.get("played_character_id") != actor.get("character_id")
            or frame.get("paused") is not True or frame.get("map_ready") is not True
            or frame.get("played_character_alive") is not True):
        raise ValueError("family native observation differs from its paused player frame")
    lineage = value.get("native_child_house_preview")
    if (not isinstance(lineage, Mapping) or lineage.get("status") not in {"available", "unavailable"}
            or lineage.get("subject_character_id") != subject_character_id
            or lineage.get("candidate_character_id") != candidate_character_id
            or lineage.get("requested_matrilineal_option") != request_matrilineal_option
            or not isinstance(lineage.get("reason"), str)):
        raise ValueError("family native lineage preview is bound to another pair")
    if lineage["status"] == "available":
        if (any(type(lineage.get(key)) is not bool for key in
                ("selected_matrilineal_option", "effective_matrilineal_if_accepted", "complete_can_send"))
                or not _id(lineage.get("native_selected_parent_character_id"))
                or any(lineage.get(key) is not None and (type(lineage[key]) is not int or lineage[key] < 0)
                       for key in ("house_id", "dynasty_id"))):
            raise ValueError("family native lineage preview values are malformed")
    alliance = value.get("alliance_obligations")
    if not isinstance(alliance, Mapping) or alliance.get("status") not in {"not_requested", "deferred_by_owner"}:
        raise ValueError("family observation includes an active deferred war-obligation source")
    terms = value.get("betrothal_break_terms")
    if not isinstance(terms, Mapping) or not isinstance(terms.get("reason"), str):
        raise ValueError("family betrothal-break observation is malformed")
    if break_recipient_character_id is None:
        if terms.get("status") != "not_requested":
            raise ValueError("family break terms were sampled without a requested recipient")
    else:
        if (terms.get("status") not in {"available", "no_betrothal", "unavailable"}
                or terms.get("requested_recipient_character_id") != break_recipient_character_id
                or terms.get("subject_character_id") != subject_character_id):
            raise ValueError("family break terms are bound to another request")
        if terms["status"] in {"available", "no_betrothal"}:
            if type(terms.get("final_legality_sampled")) is not bool or type(terms.get("native_send_costs_available")) is not bool:
                raise ValueError("family break native availability is malformed")
            if terms["final_legality_sampled"] and type(terms.get("complete_can_send")) is not bool:
                raise ValueError("family break final legality is malformed")
            costs = terms.get("native_send_costs_raw")
            if terms["native_send_costs_available"] and (not isinstance(costs, list) or len(costs) != 10 or any(type(raw) is not int for raw in costs)):
                raise ValueError("family break send costs are malformed")
            penalty = terms.get("outcome_resource_penalty")
            if (not isinstance(penalty, Mapping) or type(penalty.get("resource_penalty_available")) is not bool
                    or type(penalty.get("effects_complete")) is not bool
                    or not isinstance(penalty.get("source"), str)
                    or terms.get("outcome_penalty_available") != penalty["resource_penalty_available"]):
                raise ValueError("family break outcome penalty observation is malformed")
    return deepcopy(value)


def query_family_obligations_private_v1(
    driver: object, *, expected_revision: int, subject_character_id: int,
    candidate_character_id: int, request_matrilineal_option: bool = False,
    break_recipient_character_id: int | None = None, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if not _id(subject_character_id) or not _id(candidate_character_id) or subject_character_id == candidate_character_id:
        raise ValueError("family observation requires two distinct full character IDs")
    if type(request_matrilineal_option) is not bool or (break_recipient_character_id is not None and not _id(break_recipient_character_id)):
        raise ValueError("family observation option or break recipient is malformed")
    fields = {"subject_character_id": subject_character_id,
              "candidate_character_id": candidate_character_id,
              "request_matrilineal_option": request_matrilineal_option}
    if break_recipient_character_id is not None:
        fields["break_recipient_character_id"] = break_recipient_character_id
    snapshot, result = read_private_g2_native_query_v1(
        driver, permission="allow_private_family_obligations_query", step=STEP,
        expected_revision=expected_revision, request_fields=fields,
        timeout_seconds=timeout_seconds)
    try:
        value = normalize_family_obligations_private_v1(
            result, snapshot=snapshot, subject_character_id=subject_character_id,
            candidate_character_id=candidate_character_id,
            request_matrilineal_option=request_matrilineal_option,
            break_recipient_character_id=break_recipient_character_id)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_g2_query_metadata_v1(snapshot)}
