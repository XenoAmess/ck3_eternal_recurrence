"""Read the player's current religion and an already open Rite draft; no action."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_schema, private_native_build_identity, private_native_provenance
from .player_religion_creation_terms12003 import (
    COMPONENT_KEY as CREATION_TERMS_COMPONENT,
    READINESS_KEY as CREATION_TERMS_READY,
    SCHEMA as CREATION_TERMS_SCHEMA,
    normalize_current_draft_creation_terms12003,
)
from .version_identity import CK3_12002, CK3_12003, CK3_12004, require_exact_native_backend, require_exact_native_build


STEP = "query-player-religion-reform-context-v1"
DOMAIN_KEY = "player_religion_reform_context_v1"
SCHEMA = "ck3_12002_player_religion_reform_query_v1"
PERMISSION = "allow_private_player_religion_reform_context_query"
_TOP_KEYS = {
    "schema", "game_version", "executable_sha256", "available", "unavailable_reason",
    "scope", "capture_epoch", "date_raw", "played_character_id", "readiness",
    "current_context", "current_rite_model", "main_rite_unreformed",
    "current_creation_window", "current_draft_costs", "current_draft_eligibility",
    "current_popup_choices", "current_doctrine_selection",
}
_COMPONENTS = {
    "current_context": ("ck3_12002_religion_context_v1", "current_context_ready"),
    "current_rite_model": ("religion_reform12002_rite_model_v1", "current_rite_model_ready"),
    "main_rite_unreformed": (None, "main_rite_status_ready"),
    "current_creation_window": ("ck3_12002_current_rite_creation_window_v1",
                                "current_window_observation_ready"),
    "current_draft_costs": ("ck3_12002_rite_creation_costs_v1", "current_draft_cost_ready"),
    "current_draft_eligibility": ("ck3_12002_rite_draft_eligibility_v1",
                                 "current_draft_final_eligibility_ready"),
    "current_popup_choices": (None, "current_popup_collection_ready"),
    "current_doctrine_selection": ("ck3_12002_current_draft_doctrine_selection_v1",
                                    "doctrine_final_selection_ready"),
}


def _nullable_bool(value: object, field: str) -> None:
    if value is not None and type(value) is not bool:
        raise ValueError(f"native reform bool is malformed: {field}")


def _nullable_integer(value: object, field: str, *, full_ref: bool = False) -> None:
    low, high = (0, 0xFFFFFFFF) if full_ref else (-(1 << 63), (1 << 63) - 1)
    if value is not None and (type(value) is not int or not low <= value <= high):
        raise ValueError(f"native reform integer is malformed: {field}")


def normalize_player_religion_reform_context_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve actual component values and partial readiness without filling nulls."""
    snapshot_build = private_native_build_identity(snapshot)
    top_keys = _TOP_KEYS
    components = _COMPONENTS
    # The .4 basic owner publishes the original common shape while creation
    # terms remain disabled. Do not invent its component or readiness field.
    if snapshot_build == CK3_12003:
        top_keys = _TOP_KEYS | {CREATION_TERMS_COMPONENT}
        components = {
            **_COMPONENTS,
            CREATION_TERMS_COMPONENT: (CREATION_TERMS_SCHEMA, CREATION_TERMS_READY),
        }
    if not isinstance(value, dict) or set(value) != top_keys or value["schema"] != private_native_schema(SCHEMA, snapshot):
        raise ValueError("native player religion reform schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(snapshot):
        raise ValueError("native player religion reform belongs to another build")
    if (type(value["available"]) is not bool
            or value["scope"] != "played_character_current_model_and_already_open_draft"
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= (1 << 64) - 1
            or type(value["date_raw"]) is not int
            or type(value["played_character_id"]) is not int):
        raise ValueError("native player religion reform frame is malformed")
    actor = snapshot.get("played_character")
    if value["available"]:
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["unavailable_reason"] is not None):
            raise ValueError("native player religion reform differs from its queried frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("native player religion reform lost its unavailable reason")
    readiness = value["readiness"]
    expected_readiness = {pair[1] for pair in components.values()} | {
        "final_choice_legality_readiness",
    }
    if (not isinstance(readiness, dict) or set(readiness) != expected_readiness
            or any(type(flag) is not bool for flag in readiness.values())
            or readiness["final_choice_legality_readiness"] is not False):
        raise ValueError("native player religion reform readiness is malformed")
    for key, (schema, ready_key) in components.items():
        component = value[key]
        if (not isinstance(component, dict) or type(component.get("available")) is not bool
                or (schema is not None and component.get("schema") != private_native_schema(schema, snapshot))
                or readiness[ready_key] != component["available"]):
            raise ValueError(f"native player religion reform component is malformed: {key}")
        reason = component.get("unavailable_reason")
        if component["available"]:
            if key != "current_creation_window" and reason is not None:
                raise ValueError(f"available native reform component retains failure: {key}")
            if "capture_epoch" in component and (
                    component["capture_epoch"] != value["capture_epoch"]
                    or component["date_raw"] != value["date_raw"]
                    or component["played_character_id"] != value["played_character_id"]):
                raise ValueError(f"native reform component differs from its owner frame: {key}")
        elif not isinstance(reason, str) or not reason:
            raise ValueError(f"unavailable native reform component lost its reason: {key}")
        if "game_version" in component:
            if require_exact_native_build(component["game_version"],
                                          component["executable_sha256"]) != build:
                raise ValueError(f"native reform component belongs to another build: {key}")

    window = value["current_creation_window"]
    if any(type(window.get(key)) is not bool for key in ("present", "visible", "draft_observed")):
        raise ValueError("native current reform window flags are malformed")
    if window["draft_observed"] and not (window["available"] and window["present"] and window["visible"]):
        raise ValueError("native reform draft is not an actual visible window")
    draft_ready_keys = (
        "current_draft_cost_ready", "current_draft_final_eligibility_ready",
        "current_popup_collection_ready", "doctrine_final_selection_ready",
    )
    if build == CK3_12003:
        draft_ready_keys += (CREATION_TERMS_READY,)
    if not window["draft_observed"] and any(readiness[key] for key in draft_ready_keys):
        raise ValueError("native reform draft values have no current draft")
    if build == CK3_12003:
        terms = normalize_current_draft_creation_terms12003(
            value[CREATION_TERMS_COMPONENT], snapshot=snapshot,
        )
        if (any(terms[key] != value[key] for key in ("capture_epoch", "date_raw"))
                or terms["played_character_id"] != (value["played_character_id"] & 0xFFFFFFFF)):
            raise ValueError("native draft creation terms differs from its owner frame")
        if terms["available"] and (
                not value["available"] or not window["draft_observed"]
                or terms["source_rite_id"] != window.get("source_rite_id")):
            raise ValueError("native draft creation terms lost its actual current window")
    costs = value["current_draft_costs"]
    for key in ("piety_cost_raw", "piety_missing_signed_raw"):
        _nullable_integer(costs.get(key), key)
    for key in ("editing_owned_current_rite", "has_enough_piety"):
        _nullable_bool(costs.get(key), key)
    if (costs.get("raw_scale") != 100000
            or costs.get("final_creation_legality_observed") is not False
            or costs.get("other_resource_costs_observed") is not False):
        raise ValueError("native reform cost scope is malformed")
    eligibility = value["current_draft_eligibility"]
    _nullable_integer(eligibility.get("draft_actor_id"), "draft_actor_id", full_ref=True)
    for key in ("can_create_rite", "can_edit_rite"):
        _nullable_bool(eligibility.get(key), key)
        if not eligibility["available"] and eligibility.get(key) is not None:
            raise ValueError("unavailable native reform eligibility was filled")
    popup = value["current_popup_choices"]
    if (popup.get("scope") != "already_materialized_current_popup_candidates"
            or popup.get("collection_readiness") != popup["available"]
            or popup.get("final_choice_legality_readiness") is not False):
        raise ValueError("native reform popup collection scope is malformed")
    for collection in ("doctrines", "tenets"):
        rows = popup.get(collection)
        if popup["available"]:
            if not isinstance(rows, list):
                raise ValueError("observed native reform popup lost its collection")
            for row in rows:
                if (not isinstance(row, dict) or row.get("final_can_pick") is not None
                        or row.get("final_choice_legality_readiness") is not False):
                    raise ValueError("native reform popup inferred final choice legality")
        elif rows is not None:
            raise ValueError("unavailable native reform popup was made into an empty collection")
    selection = value["current_doctrine_selection"]
    if (selection.get("scope") != "already_materialized_current_popup_candidates"
            or type(selection.get("popup_observed")) is not bool
            or selection.get("selection_ready") != readiness["doctrine_final_selection_ready"]
            or not isinstance(selection.get("rows"), list)
            or not isinstance(selection.get("selectable_doctrine_keys"), list)):
        raise ValueError("native reform Doctrine selection scope is malformed")
    for row in selection["rows"]:
        if not isinstance(row, dict) or type(row.get("selectable")) is not bool:
            raise ValueError("native reform Doctrine selection lost its actual final gate")
    return deepcopy(value)


def query_player_religion_reform_context_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-reform-context-v1",
        )
        if (build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native reform envelope differs from the queried build/frame")
        value = normalize_player_religion_reform_context_v1(
            result.get("player_religion_reform_context"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native reform envelope lost its component status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
