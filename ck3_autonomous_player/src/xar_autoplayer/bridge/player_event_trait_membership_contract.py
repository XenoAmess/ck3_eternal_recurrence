"""Two persistent event traits for the current actual4 player, not a trait census."""

from __future__ import annotations

from collections.abc import Mapping

from .version_identity import CK3_12004


SCHEMA = "xar.ck3.player-event-trait-membership/v1"
TRAIT_KEYS = frozenset({"lifestyle_poet", "journaller"})
_FIELDS = frozenset({
    "schema", "game_version", "executable_sha256", "status",
    "snapshot_revision", "date_raw", "played_character_id", "traits",
    "unavailable_reason",
})


def _int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_player_event_trait_membership_v1(
    value: object, *, expected_character_id: int,
    expected_native_revision: int, expected_date_raw: int,
) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != _FIELDS:
        raise ValueError("event trait membership fields are invalid")
    if not (
        value["schema"] == SCHEMA
        and value["game_version"] == CK3_12004.game_version
        and value["executable_sha256"] == CK3_12004.executable_sha256
        and _int(expected_character_id) and expected_character_id > 0
        and _int(expected_native_revision) and expected_native_revision > 0
        and _int(expected_date_raw)
        and _int(value["snapshot_revision"])
        and value["snapshot_revision"] == expected_native_revision
        and _int(value["date_raw"]) and value["date_raw"] == expected_date_raw
        and _int(value["played_character_id"])
        and value["played_character_id"] == expected_character_id
    ):
        raise ValueError("event trait membership current-player binding differs")
    result = dict(value)
    if value["status"] == "available":
        traits = value["traits"]
        if not (
            value["unavailable_reason"] is None
            and isinstance(traits, Mapping) and set(traits) == TRAIT_KEYS
            and all(isinstance(item, bool) for item in traits.values())
        ):
            raise ValueError("available event trait membership is malformed")
        result["traits"] = dict(traits)
    elif value["status"] == "unavailable":
        if not (
            value["traits"] is None
            and isinstance(value["unavailable_reason"], str)
            and value["unavailable_reason"]
        ):
            raise ValueError("unavailable event trait membership is malformed")
    else:
        raise ValueError("event trait membership status is invalid")
    return result


def plan_poet_trait_material_postcondition_v1(
    decision: Mapping[str, object], played_character: object, *,
    snapshot_id: object, revision: object, native_revision: object,
    date_raw: object,
) -> dict[str, object] | None:
    index = decision.get("selected_native_option_index")
    if not (
        decision.get("status") == "recommended"
        and decision.get("event_definition_key") == "trait_specific.9001"
        and decision.get("ck3_build") == "1.20.0.4"
        and _int(index) and index in (0, 1)
    ):
        return None
    trait_key = "lifestyle_poet" if index == 0 else "journaller"
    character = played_character if isinstance(played_character, Mapping) else {}
    character_id = character.get("character_id")
    observed = None
    try:
        observed = normalize_player_event_trait_membership_v1(
            character.get("event_trait_membership"),
            expected_character_id=character_id,
            expected_native_revision=native_revision,
            expected_date_raw=date_raw,
        )
    except ValueError:
        pass
    ready = bool(
        isinstance(snapshot_id, str) and snapshot_id
        and _int(revision) and revision >= 0
        and observed is not None and observed["status"] == "available"
        and observed["traits"][trait_key] is False
    )
    return {
        "schema": "xar.ck3.vanilla-event-material-postcondition",
        "schema_version": 1,
        "event_definition_key": "trait_specific.9001",
        "selected_option_number": index + 1,
        "selected_native_option_index": index,
        "metric": f"played_character.event_traits.{trait_key}",
        "trait_key": trait_key,
        "expected_relation": "false_to_true",
        "material_change_required_for_evidence": True,
        "status": "ready" if ready else "unavailable",
        "starting_snapshot_id": snapshot_id,
        "starting_revision": revision,
        "starting_native_revision": native_revision,
        "date_raw": date_raw,
        "character_id": character_id,
        "starting_value": False if ready else None,
        "unavailable_reason": None if ready else "same_frame_event_trait_membership_unavailable",
    }


def evaluate_poet_trait_material_postcondition_v1(
    expectation: Mapping[str, object], event_selection: object,
) -> dict[str, object]:
    result = dict(expectation)
    result.update(status="unavailable", relation_satisfied=None,
        material_change_observed=None, ending_value=None, delta=None)
    if expectation.get("status") != "ready":
        return result
    selection = event_selection if isinstance(event_selection, Mapping) else {}
    end_native = None
    after_value = selection.get("ending_played_character_event_traits")
    if isinstance(after_value, Mapping):
        end_native = after_value.get("snapshot_revision")
    try:
        before = normalize_player_event_trait_membership_v1(
            selection.get("starting_played_character_event_traits"),
            expected_character_id=expectation.get("character_id"),
            expected_native_revision=expectation.get("starting_native_revision"),
            expected_date_raw=expectation.get("date_raw"),
        )
        after = normalize_player_event_trait_membership_v1(
            after_value, expected_character_id=expectation.get("character_id"),
            expected_native_revision=end_native,
            expected_date_raw=expectation.get("date_raw"),
        )
    except ValueError:
        result["unavailable_reason"] = "native_event_trait_observation_unavailable"
        return result
    if before["status"] != "available" or after["status"] != "available":
        result["unavailable_reason"] = "native_event_trait_observation_unavailable"
        return result
    trait_key = expectation.get("trait_key")
    bound = bool(
        trait_key in TRAIT_KEYS
        and selection.get("postcondition_verified") is True
        and selection.get("starting_snapshot_id") == expectation.get("starting_snapshot_id")
        and selection.get("starting_revision") == expectation.get("starting_revision")
        and isinstance(selection.get("ending_snapshot_id"), str)
        and selection["ending_snapshot_id"] != expectation.get("starting_snapshot_id")
        and _int(selection.get("ending_revision"))
        and selection["ending_revision"] > expectation["starting_revision"]
        and end_native > expectation["starting_native_revision"]
        and before["traits"][trait_key] is False
    )
    changed = bound and after["traits"][trait_key] is True
    result.update(
        status="verified_change" if changed else "failed",
        relation_satisfied=changed, material_change_observed=changed,
        ending_value=after["traits"].get(trait_key), delta=1 if changed else 0,
        unavailable_reason=None if changed else "event_trait_not_added_or_frame_binding_differs",
    )
    return result
