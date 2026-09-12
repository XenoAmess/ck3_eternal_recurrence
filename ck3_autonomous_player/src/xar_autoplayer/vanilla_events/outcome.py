"""Material postconditions for source-reviewed vanilla event choices."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final


VANILLA_EVENT_MATERIAL_POSTCONDITION_SCHEMA: Final = (
    "xar.ck3.vanilla-event-material-postcondition"
)
VANILLA_EVENT_MATERIAL_POSTCONDITION_SCHEMA_VERSION: Final = 1

_SUPPORTED_CHOICES: Final = {
    ("tgp_travel_events.0030", 1): {
        "metric": "played_character.stress_points",
        "expected_relation": "non_increasing",
        "material_change_required_for_evidence": True,
    }
}


def _integer(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _base(decision: Mapping[str, object]) -> dict[str, object] | None:
    event_key = decision.get("event_definition_key")
    native_index = _integer(decision.get("selected_native_option_index"))
    specification = _SUPPORTED_CHOICES.get((event_key, native_index))
    if specification is None:
        return None
    return {
        "schema": VANILLA_EVENT_MATERIAL_POSTCONDITION_SCHEMA,
        "schema_version": VANILLA_EVENT_MATERIAL_POSTCONDITION_SCHEMA_VERSION,
        "event_definition_key": event_key,
        "selected_option_number": decision.get("selected_option_number"),
        "selected_native_option_index": native_index,
        **specification,
    }


def plan_registered_event_material_postcondition_v1(
    decision: object,
    played_character: object,
    *,
    snapshot_id: object,
    revision: object,
) -> dict[str, object] | None:
    """Bind a supported event outcome to its same-frame player observation."""

    if not isinstance(decision, Mapping) or decision.get("status") != "recommended":
        return None
    response = _base(decision)
    if response is None:
        return None
    character = played_character if isinstance(played_character, Mapping) else {}
    character_id = _integer(character.get("character_id"))
    stress_points = _integer(character.get("stress_points"))
    typed_revision = _integer(revision)
    valid_binding = bool(
        character_id is not None
        and character_id > 0
        and stress_points is not None
        and 0 <= stress_points <= 2**31 - 1
        and isinstance(snapshot_id, str)
        and snapshot_id
        and typed_revision is not None
        and typed_revision >= 0
    )
    response.update(
        {
            "status": "ready" if valid_binding else "unavailable",
            "starting_snapshot_id": snapshot_id if valid_binding else None,
            "starting_revision": typed_revision if valid_binding else None,
            "character_id": character_id if valid_binding else None,
            "starting_value": stress_points if valid_binding else None,
            "unavailable_reason": (
                None if valid_binding else "same_frame_player_stress_unavailable"
            ),
        }
    )
    return response


def evaluate_registered_event_material_postcondition_v1(
    expectation: object,
    event_selection: object,
) -> dict[str, object]:
    """Evaluate a supported choice without inventing an unavailable delta."""

    expected = expectation if isinstance(expectation, Mapping) else {}
    response = {
        key: expected.get(key)
        for key in (
            "schema",
            "schema_version",
            "event_definition_key",
            "selected_option_number",
            "selected_native_option_index",
            "metric",
            "expected_relation",
            "material_change_required_for_evidence",
            "starting_snapshot_id",
            "starting_revision",
            "character_id",
            "starting_value",
        )
    }
    response.update(
        {
            "status": "unavailable",
            "relation_satisfied": None,
            "material_change_observed": None,
            "ending_value": None,
            "delta": None,
            "unavailable_reason": None,
        }
    )
    if expected.get("status") != "ready":
        response["unavailable_reason"] = expected.get(
            "unavailable_reason", "expectation_not_ready"
        )
        return response
    selection = event_selection if isinstance(event_selection, Mapping) else {}
    before = selection.get("starting_played_character_stress")
    after = selection.get("ending_played_character_stress")
    if not (
        selection.get("postcondition_verified") is True
        and isinstance(before, Mapping)
        and isinstance(after, Mapping)
        and before.get("status") == "available"
        and after.get("status") == "available"
    ):
        response["unavailable_reason"] = "native_event_stress_observation_unavailable"
        return response

    expected_character_id = _integer(expected.get("character_id"))
    expected_start = _integer(expected.get("starting_value"))
    before_character_id = _integer(before.get("character_id"))
    after_character_id = _integer(after.get("character_id"))
    before_value = _integer(before.get("stress_points"))
    after_value = _integer(after.get("stress_points"))
    binding_matches = bool(
        selection.get("starting_snapshot_id")
        == expected.get("starting_snapshot_id")
        and selection.get("starting_revision") == expected.get("starting_revision")
        and expected_character_id is not None
        and before_character_id == expected_character_id == after_character_id
        and expected_start is not None
        and before_value == expected_start
        and after_value is not None
        and after_value >= 0
    )
    if not binding_matches:
        response.update(
            {
                "status": "failed",
                "relation_satisfied": False,
                "material_change_observed": False,
                "unavailable_reason": "same_character_snapshot_binding_mismatch",
            }
        )
        return response

    assert before_value is not None
    assert after_value is not None
    delta = after_value - before_value
    response.update(
        {
            "status": (
                "verified_change"
                if delta < 0
                else "verified_no_change"
                if delta == 0
                else "failed"
            ),
            "relation_satisfied": delta <= 0,
            "material_change_observed": delta != 0,
            "ending_value": after_value,
            "delta": delta,
            "unavailable_reason": "stress_increased" if delta > 0 else None,
        }
    )
    return response


__all__ = [
    "VANILLA_EVENT_MATERIAL_POSTCONDITION_SCHEMA",
    "VANILLA_EVENT_MATERIAL_POSTCONDITION_SCHEMA_VERSION",
    "evaluate_registered_event_material_postcondition_v1",
    "plan_registered_event_material_postcondition_v1",
]
