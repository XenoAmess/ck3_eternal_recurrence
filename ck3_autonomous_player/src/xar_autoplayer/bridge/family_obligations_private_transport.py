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
    value: object, *, snapshot: Mapping[str, object], subject_character_id: int | None,
    candidate_character_id: int | None, request_matrilineal_option: bool,
    break_recipient_character_id: int | None = None, ally_character_id: int | None = None,
    enumerate_current_allies: bool = False,
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
    if (not isinstance(lineage, Mapping) or lineage.get("status") not in {"available", "unavailable", "not_requested"}
            or lineage.get("subject_character_id") != subject_character_id
            or lineage.get("candidate_character_id") != candidate_character_id
            or lineage.get("requested_matrilineal_option") != request_matrilineal_option
            or not isinstance(lineage.get("reason"), str)):
        raise ValueError("family native lineage preview is bound to another pair")
    if subject_character_id is None and lineage["status"] != "not_requested":
        raise ValueError("family lineage was sampled without a requested pair")
    if subject_character_id is not None and lineage["status"] == "not_requested":
        raise ValueError("family lineage pair was not sampled")
    if lineage["status"] == "available":
        if (any(type(lineage.get(key)) is not bool for key in
                ("selected_matrilineal_option", "effective_matrilineal_if_accepted", "complete_can_send"))
                or not _id(lineage.get("native_selected_parent_character_id"))
                or any(lineage.get(key) is not None and (type(lineage[key]) is not int or lineage[key] < 0)
                       for key in ("house_id", "dynasty_id"))):
            raise ValueError("family native lineage preview values are malformed")
    alliance = value.get("alliance_obligations")
    if not isinstance(alliance, Mapping):
        raise ValueError("family alliance observation is malformed")
    if ally_character_id is None:
        if alliance.get("status") not in {"not_requested", "deferred_by_owner"}:
            raise ValueError("family alliance source was sampled without a request")
    else:
        if (alliance.get("status") not in {"available", "unavailable"}
                or alliance.get("first_character_id") != actor.get("character_id")
                or alliance.get("second_character_id") != ally_character_id
                or not isinstance(alliance.get("reason"), str)):
            raise ValueError("family alliance source differs from the requested player pair")
        if alliance["status"] == "available":
            if (type(alliance.get("first_has_second")) is not bool
                    or type(alliance.get("second_has_first")) is not bool
                    or alliance.get("raw_scale") != 100000
                    or alliance.get("send_cost_slot_keys") != ["gold", "prestige", "piety", "renown", "influence", "herd", "treasury", "treasury_or_gold", "merit", "barter_goods"]):
                raise ValueError("family alliance native relation or cost slots are malformed")
            for collection, caller, recipient in (("first_wars", actor["character_id"], ally_character_id),
                                                  ("second_wars", ally_character_id, actor["character_id"])):
                rows = alliance.get(collection)
                if not isinstance(rows, list):
                    raise ValueError("family alliance active-war collection is unavailable")
                for row in rows:
                    if (not isinstance(row, Mapping) or type(row.get("war_id")) is not int
                            or row.get("caller_character_id") != caller
                            or row.get("recipient_character_id") != recipient
                            or row.get("caller_side") not in {"attacker", "defender"}
                            or row.get("recipient_side") not in {"attacker", "defender", "absent"}
                            or any(type(row.get(key)) is not bool for key in
                                   ("caller_is_primary_war_leader", "recipient_was_called",
                                    "native_target_can_be_picked", "native_target_row_selectable"))):
                        raise ValueError("family alliance war native terms are malformed")
                    # Older fully sampled rows have no availability field. Their
                    # complete value shape is still required by the true branch.
                    selected_context_available = row.get("native_selected_target_context_available", True)
                    if type(selected_context_available) is not bool:
                        raise ValueError("family alliance selected context availability is malformed")
                    if not selected_context_available:
                        if (row["native_target_can_be_picked"] is not False
                                or row["native_target_row_selectable"] is not False
                                or any(key not in row or row[key] is not None for key in
                                       ("native_complete_can_send", "send_cost_raw",
                                        "recipient_acceptance_raw", "native_auto_accept",
                                        "recipient_answer_status_raw"))):
                            raise ValueError("family alliance unselected war terms must remain unobserved")
                    elif (any(type(row.get(key)) is not bool for key in
                              ("native_complete_can_send", "native_auto_accept"))
                            or type(row.get("recipient_acceptance_raw")) is not int
                            or type(row.get("recipient_answer_status_raw")) is not int
                            or row["recipient_answer_status_raw"] not in {0, 1, 2}
                            or not isinstance(row.get("send_cost_raw"), list)
                            or len(row["send_cost_raw"]) != 10
                            or any(type(raw) is not int for raw in row["send_cost_raw"])):
                        raise ValueError("family alliance war native terms are malformed")
    collection = value.get("current_native_allies")
    if enumerate_current_allies:
        if (not isinstance(collection, Mapping)
                or collection.get("status") not in {"available", "unavailable"}
                or collection.get("played_character_id") != actor.get("character_id")
                or not isinstance(collection.get("reason"), str)):
            raise ValueError("current native ally collection differs from the player frame")
        if collection["status"] == "available":
            for key in ("source_character_ids", "unresolved_source_character_ids", "dead_source_character_ids"):
                ids = collection.get(key)
                if not isinstance(ids, list) or any(type(item) is not int for item in ids):
                    raise ValueError("current native ally source IDs are malformed")
            rows = collection.get("allies")
            if not isinstance(rows, list):
                raise ValueError("current native ally collection is malformed")
            for row in rows:
                if (not isinstance(row, Mapping) or not _id(row.get("character_id"))
                        or row["character_id"] == actor.get("character_id")
                        or row.get("player_has_ally") is not True
                        or row.get("ally_has_player") is not True
                        or type(row.get("has_realm_data")) is not bool):
                    raise ValueError("current native ally row lacks native bilateral membership")
    elif collection is not None and (not isinstance(collection, Mapping) or collection.get("status") != "not_requested"):
        raise ValueError("current native allies were sampled without an enumeration request")
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
    driver: object, *, expected_revision: int, subject_character_id: int | None = None,
    candidate_character_id: int | None = None, request_matrilineal_option: bool = False,
    break_recipient_character_id: int | None = None, ally_character_id: int | None = None,
    enumerate_current_allies: bool = False, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    pair_requested = subject_character_id is not None or candidate_character_id is not None
    if pair_requested and (not _id(subject_character_id) or not _id(candidate_character_id) or subject_character_id == candidate_character_id):
        raise ValueError("family observation requires two distinct full character IDs")
    if ally_character_id is not None and not _id(ally_character_id):
        raise ValueError("family alliance query requires one full ally candidate ID")
    if type(enumerate_current_allies) is not bool:
        raise ValueError("current native ally enumeration option is malformed")
    if not pair_requested and ((ally_character_id is None and not enumerate_current_allies)
                               or request_matrilineal_option or break_recipient_character_id is not None):
        raise ValueError("ally-only observation cannot request unrelated family terms")
    if type(request_matrilineal_option) is not bool or (break_recipient_character_id is not None and not _id(break_recipient_character_id)):
        raise ValueError("family observation option or break recipient is malformed")
    fields = {"request_matrilineal_option": request_matrilineal_option}
    if enumerate_current_allies:
        fields["enumerate_current_allies"] = True
    if pair_requested:
        fields.update(subject_character_id=subject_character_id, candidate_character_id=candidate_character_id)
    if ally_character_id is not None:
        fields["ally_character_id"] = ally_character_id
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
            break_recipient_character_id=break_recipient_character_id, ally_character_id=ally_character_id,
            enumerate_current_allies=enumerate_current_allies)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_g2_query_metadata_v1(snapshot)}
