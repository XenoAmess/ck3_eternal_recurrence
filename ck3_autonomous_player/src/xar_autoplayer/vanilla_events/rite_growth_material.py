"""Independent fulfillment material for the reviewed actual4 Rite-growth choice.

The existing religion query owns native observation. This leaf retains only its
frame-bound result; it neither predicts the authored +5 nor submits a choice.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..bridge.driver import BridgeUnavailableError, UnsupportedStepError
from ..bridge.player_religion_context_private_transport import (
    normalize_player_religion_context_v1,
)
from ..bridge.version_identity import CK3_12004


OBSERVATION_SCHEMA = "xar.ck3.rite-growth-fulfillment-observation/v1"
METRIC = "player_religion.spiritual_fulfillment_raw"
STARTING_FIELD = "starting_rite_growth_fulfillment"
ENDING_FIELD = "ending_rite_growth_fulfillment"
_CONTEXT_FIELDS = (
    "schema", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "rite_id", "faith_id", "religion_id", "faith_main_rite_id", "faith_key",
    "religion_key", "faith_fervor_raw", "spiritual_fulfillment_raw", "raw_scale",
)


def _int(value: object) -> bool:
    return type(value) is int


def rite_growth_material_specification_v1() -> dict[str, object]:
    return {"metric": METRIC, "expected_relation": "non_decreasing",
            "material_change_required_for_evidence": True}


def rite_growth_fulfillment_observation_v1(
    query: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Detach actual4 religion output without rewriting null, zero or sign."""
    observation = {
        "schema": OBSERVATION_SCHEMA, "status": "unavailable",
        "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"), "character_id": None,
        "rite_id": None, "faith_id": None, "fulfillment_raw": None,
        "raw_scale": None, "capture_epoch": None,
        "unavailable_reason": "same_frame_rite_growth_religion_unavailable",
    }
    if not isinstance(query, Mapping):
        return observation
    try:
        context = normalize_player_religion_context_v1(
            {key: query.get(key) for key in _CONTEXT_FIELDS}, snapshot=snapshot,
        )
    except (ValueError, BridgeUnavailableError):
        return observation
    actor = snapshot.get("played_character")
    if not (
        query.get("game_version") == CK3_12004.game_version
        and query.get("executable_sha256") == CK3_12004.executable_sha256
        and query.get("backend_id") == CK3_12004.backend_id("player-religion-context-v1")
        and query.get("domain_key") == "player_religion_context_v1"
        and query.get("read_only") is True and query.get("status") == "observed"
        and context["available"] is True
        and snapshot.get("paused") is True and snapshot.get("map_ready") is True
        and isinstance(actor, Mapping) and actor.get("alive") is True
        and _int(actor.get("character_id")) and actor["character_id"] > 0
        and isinstance(snapshot.get("snapshot_id"), str) and snapshot["snapshot_id"]
        and _int(snapshot.get("revision")) and snapshot["revision"] > 0
        and _int(snapshot.get("native_revision")) and snapshot["native_revision"] > 0
        and query.get("queried_snapshot_id") == snapshot["snapshot_id"]
        and _int(query.get("queried_revision"))
        and query["queried_revision"] == snapshot["revision"]
        and _int(query.get("queried_native_revision"))
        and query["queried_native_revision"] == snapshot["native_revision"]
        and _int(query.get("snapshot_revision"))
        and query["snapshot_revision"] == snapshot["native_revision"]
        and query.get("query_date_raw") == snapshot.get("date_raw")
        and all(_int(context[key]) for key in ("rite_id", "faith_id"))
    ):
        return observation
    observation.update(
        status="available", character_id=context["played_character_id"],
        rite_id=context["rite_id"], faith_id=context["faith_id"],
        fulfillment_raw=context["spiritual_fulfillment_raw"],
        raw_scale=context["raw_scale"], capture_epoch=context["capture_epoch"],
        unavailable_reason=None,
    )
    return observation


def capture_rite_growth_fulfillment_observation_v1(
    driver: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Call only the existing religion query, once, for this supplied frame."""
    query_method = getattr(driver, "query_player_religion_context_private_v1", None)
    query = None
    if callable(query_method) and _int(snapshot.get("revision")) and snapshot["revision"] > 0:
        try:
            query = query_method(expected_revision=snapshot["revision"])
        except (BridgeUnavailableError, UnsupportedStepError) as error:
            observation = rite_growth_fulfillment_observation_v1(None, snapshot=snapshot)
            observation["unavailable_reason"] = f"religion_query_unavailable: {error}"
            return observation
    return rite_growth_fulfillment_observation_v1(query, snapshot=snapshot)


def _available(observation: object) -> bool:
    return bool(
        isinstance(observation, Mapping)
        and observation.get("schema") == OBSERVATION_SCHEMA
        and observation.get("status") == "available"
        and observation.get("game_version") == CK3_12004.game_version
        and observation.get("executable_sha256") == CK3_12004.executable_sha256
        and observation.get("unavailable_reason") is None
        and isinstance(observation.get("snapshot_id"), str) and observation["snapshot_id"]
        and all(_int(observation.get(key)) and observation[key] > 0
                for key in ("revision", "native_revision", "character_id", "capture_epoch"))
        and _int(observation.get("date_raw"))
        and all(_int(observation.get(key)) and 0 <= observation[key] <= 0xFFFFFFFF
                for key in ("rite_id", "faith_id"))
        and _int(observation.get("fulfillment_raw"))
        and -(1 << 63) <= observation["fulfillment_raw"] < (1 << 63)
        and type(observation.get("raw_scale")) is int and observation["raw_scale"] == 100000
    )


def plan_rite_growth_material_postcondition_v1(
    decision: Mapping[str, object], played_character: object, *,
    religion_context: object, snapshot_id: object, revision: object,
    native_revision: object, date_raw: object,
) -> dict[str, object] | None:
    """Bind the exact registered choice to one detached before observation."""
    if not (
        decision.get("status") == "recommended"
        and decision.get("event_definition_key") == "rite_growth.0010"
        and decision.get("ck3_build") == CK3_12004.game_version
        and type(decision.get("selected_native_option_index")) is int
        and decision["selected_native_option_index"] == 0
        and type(decision.get("selected_option_number")) is int
        and decision["selected_option_number"] == 1
    ):
        return None
    character = played_character if isinstance(played_character, Mapping) else {}
    before = religion_context
    ready = bool(
        _available(before) and _int(character.get("character_id"))
        and before["character_id"] == character["character_id"]
        and before["snapshot_id"] == snapshot_id
        and _int(revision) and before["revision"] == revision
        and _int(native_revision) and before["native_revision"] == native_revision
        and _int(date_raw) and before["date_raw"] == date_raw
    )
    return {
        "schema": "xar.ck3.vanilla-event-material-postcondition", "schema_version": 1,
        "event_definition_key": "rite_growth.0010", "ck3_build": CK3_12004.game_version,
        "selected_option_number": 1, "selected_native_option_index": 0,
        **rite_growth_material_specification_v1(),
        "status": "ready" if ready else "unavailable",
        "starting_snapshot_id": snapshot_id, "starting_revision": revision,
        "starting_native_revision": native_revision, "date_raw": date_raw,
        "character_id": character.get("character_id"),
        "starting_value": before["fulfillment_raw"] if ready else None,
        "starting_religion_observation": dict(before) if ready else None,
        "unavailable_reason": None if ready else "same_frame_rite_growth_religion_unavailable",
    }


def evaluate_rite_growth_material_postcondition_v1(
    expectation: Mapping[str, object], event_selection: object,
) -> dict[str, object]:
    """Require the consumed instance and independent, newer paused material."""
    result = dict(expectation)
    result.update(status="unavailable", relation_satisfied=None,
                  material_change_observed=None, ending_value=None, delta=None)
    if expectation.get("status") != "ready":
        return result
    selection = event_selection if isinstance(event_selection, Mapping) else {}
    before = selection.get(STARTING_FIELD)
    after = selection.get(ENDING_FIELD)
    if not _available(before) or not _available(after):
        result["unavailable_reason"] = "native_rite_growth_fulfillment_observation_unavailable"
        return result
    old_instance = selection.get("old_event_instance_id")
    new_instance = selection.get("new_event_instance_id")
    bound = bool(
        expectation.get("event_definition_key") == "rite_growth.0010"
        and expectation.get("ck3_build") == CK3_12004.game_version
        and expectation.get("metric") == METRIC
        and expectation.get("expected_relation") == "non_decreasing"
        and expectation.get("material_change_required_for_evidence") is True
        and expectation.get("selected_native_option_index") == 0
        and expectation.get("selected_option_number") == 1
        and selection.get("selected_native_option_index") == 0
        and selection.get("selected_option_number") == 1
        and selection.get("postcondition_verified") is True
        and _int(old_instance) and old_instance > 0
        and (new_instance is None or (_int(new_instance) and new_instance > 0))
        and new_instance != old_instance
        and before == expectation.get("starting_religion_observation")
        and before["fulfillment_raw"] == expectation.get("starting_value")
        and before["character_id"] == after["character_id"] == expectation.get("character_id")
        and before["date_raw"] == after["date_raw"] == expectation.get("date_raw")
        and before["rite_id"] == after["rite_id"] and before["faith_id"] == after["faith_id"]
        and before["snapshot_id"] == selection.get("starting_snapshot_id")
        == expectation.get("starting_snapshot_id")
        and before["revision"] == selection.get("starting_revision")
        == expectation.get("starting_revision")
        and before["native_revision"] == expectation.get("starting_native_revision")
        and after["snapshot_id"] == selection.get("ending_snapshot_id")
        and after["snapshot_id"] != before["snapshot_id"]
        and _int(selection.get("ending_revision"))
        and after["revision"] == selection["ending_revision"] > before["revision"]
        and after["native_revision"] > before["native_revision"]
        and after["capture_epoch"] > before["capture_epoch"]
    )
    if not bound:
        result.update(status="failed", relation_satisfied=False,
                      material_change_observed=False,
                      unavailable_reason="rite_growth_material_frame_or_identity_mismatch")
        return result
    delta = after["fulfillment_raw"] - before["fulfillment_raw"]
    result.update(
        status="verified_change" if delta > 0 else "verified_no_change" if delta == 0 else "failed",
        relation_satisfied=delta >= 0, material_change_observed=delta != 0,
        ending_value=after["fulfillment_raw"], delta=delta,
        ending_religion_observation=dict(after),
        unavailable_reason="spiritual_fulfillment_decreased" if delta < 0 else None,
    )
    return result
