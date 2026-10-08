"""Annotate ordinary plans with one current native holy-war defender set."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .bridge.declaration_contract import normalize_declarable_wars
from .bridge.driver import BridgeUnavailableError, UnsupportedStepError
from .bridge.player_ordinary_holy_war_declaration_context_private_observation import (
    ORDINARY_HOLY_WAR_KEYS, SELECTED_FIELDS,
)
from .bridge.player_ordinary_holy_war_declaration_context_private_transport import PERMISSION


ANNOTATION_KEY = "ordinary_holy_war_candidate_observation"
_DEFENDER_KEY = "player_holy_war_defender_join_inputs"
_ROLE_FIELDS = (
    "context_actor_character_id", "context_recipient_character_id",
    "context_additional_role_character_id", "context_claimant_character_id",
    "recipient_uses_native_fallback", "additional_role_uses_native_fallback",
    "claimant_uses_native_fallback",
)
_DEFENDER_FIELDS = (
    "primary_attacker_character_id", "primary_defender_character_id",
    "primary_defender_faith_available",
    "primary_defender_faith_unavailable_reason", "primary_defender_rite_id",
    "primary_defender_faith_id", "cb_flags_raw", "defender_faith_can_join",
    "native_joiner_set_observed", "joiner_count", "joiners",
    "raw_scale", "unit", "is_final_join_score",
)


def _annotation(snapshot: Mapping[str, object], status: str) -> dict[str, object]:
    actor = snapshot.get("played_character")
    return {
        "status": status, "read_only": True,
        "source_frame": {
            "snapshot_id": snapshot.get("snapshot_id"), "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"), "date_raw": snapshot.get("date_raw"),
            "played_character_id": actor.get("character_id") if isinstance(actor, Mapping) else None,
        },
        "decision": "continue_current_war" if snapshot.get("active_wars") else "observation_only",
        "automatic_declaration_enabled": False,
    }


def project_ordinary_holy_war_defender_observation_v1(
    normalized_query: Mapping[str, object], *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Project the existing strict query without interpreting fervor as a score."""
    child = normalized_query.get(_DEFENDER_KEY)
    if not isinstance(child, Mapping):
        status = "defender_inputs_not_returned"
    elif child.get("native_joiner_set_observed") is not True:
        status = "native_defender_set_unavailable"
    elif child["joiner_count"] == 0:
        status = "no_extra_native_defenders_observed"
    else:
        status = "extra_native_defenders_observed"
    cost = normalized_query.get("cb_cost")
    out = {
        **_annotation(snapshot, status),
        "declaration_id": normalized_query.get("declaration_id"),
        "selected_declaration": deepcopy(normalized_query.get("selected_declaration")),
        "declaration_context_available": normalized_query.get("available"),
        "declaration_context_unavailable_reason": normalized_query.get("unavailable_reason"),
        "native_roles": {key: normalized_query.get(key) for key in _ROLE_FIELDS},
        "final_can_send": normalized_query.get("final_can_send"),
        "cb_cost_available": cost.get("available") if isinstance(cost, Mapping) else None,
        "cb_cost": deepcopy(cost),
        "generic_interaction_cost_raw": deepcopy(normalized_query.get("generic_interaction_cost_raw")),
        "total_declaration_cost_raw": deepcopy(normalized_query.get("total_declaration_cost_raw")),
        "total_cost_ready": normalized_query.get("total_cost_ready"),
        "query_status": normalized_query.get("query_status"),
        "query_backend_id": normalized_query.get("backend_id"),
        _DEFENDER_KEY: deepcopy(dict(child)) if isinstance(child, Mapping) else None,
        "defender_inputs_available": child.get("available") if isinstance(child, Mapping) else None,
        "defender_inputs_unavailable_reason": (
            child.get("unavailable_reason") if isinstance(child, Mapping) else None
        ),
    }
    # Keep native order and independent Faith/fervor availability, including
    # failed fervor rows and legal zeroes, after the collector accepted them.
    out.update({key: deepcopy(child.get(key)) if isinstance(child, Mapping) else None
                for key in _DEFENDER_FIELDS})
    return out


def plan_ordinary_holy_war_defender_observation_v1(
    service: object, *, planned: dict[str, object], snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Read the first current canonical candidate once and retain the action."""
    if getattr(getattr(service, "driver", None), PERMISSION, False) is not True:
        return planned
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        return planned

    def annotate(value: dict[str, object]) -> dict[str, object]:
        return {**planned, "plan": {**plan, ANNOTATION_KEY: value}}

    actor = snapshot.get("played_character")
    revision = planned.get("revision")
    native_revision = snapshot.get("native_revision")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or type(revision) is not int or revision <= 0 or revision != snapshot.get("revision")
            or type(native_revision) is not int or native_revision <= 0):
        return annotate(_annotation(snapshot, "frame_not_ready"))
    try:
        rows = normalize_declarable_wars(snapshot.get("declarable_wars"))
    except ValueError as error:
        return annotate({**_annotation(snapshot, "native_catalogue_unavailable"), "reason": str(error)})
    selected = next(((ordinal, row) for ordinal, row in enumerate(rows)
                     if row["casus_belli_key"] in ORDINARY_HOLY_WAR_KEYS), None)
    if selected is None:
        return annotate(_annotation(snapshot, "no_current_ordinary_holy_war_candidate"))
    source_ordinal, candidate = selected
    candidate_identity = {
        "source_ordinal": source_ordinal, "declaration_id": candidate["declaration_id"],
        "selected_declaration": {key: deepcopy(candidate[key]) for key in SELECTED_FIELDS},
    }
    query = getattr(service, "query_player_ordinary_holy_war_declaration_context_private_v1", None)
    if not callable(query):
        return annotate({**_annotation(snapshot, "query_unavailable"), **candidate_identity})
    try:
        observed = query(expected_revision=revision, declaration_id=candidate["declaration_id"])
    except (BridgeUnavailableError, UnsupportedStepError, ValueError, OSError, TimeoutError) as error:
        return annotate({**_annotation(snapshot, "query_failed"), **candidate_identity,
                         "reason": str(error)})
    observation = project_ordinary_holy_war_defender_observation_v1(observed, snapshot=snapshot)
    observation["source_ordinal"] = source_ordinal
    return annotate(observation)
