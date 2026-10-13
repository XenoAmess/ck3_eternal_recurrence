"""Observe .1070.c's new army using the existing player roster and core query.

An absent MAA type is retained as non-MAA manpower. It does not independently
identify a levy type; the 125-levy description belongs to the reviewed source.
"""

from __future__ import annotations

from collections.abc import Mapping


EVENT_KEY = "bookmark.1070"
MATERIAL_METRIC = "player_armies.bookmark1070_spawn"
MATERIAL_RELATION = "new_army_source_shape"
OBSERVATION_SCHEMA = "xar.ck3.bookmark1070-army-observation/v1"
_EXPECTED = {"non_maa": 125, "bowmen": 50, "light_horsemen": 50,
             "armored_horsemen": 25}
_FRAME_KEYS = ("character_id", "date_raw", "snapshot_id", "revision",
               "native_revision", "episode_run_id", "bridge_pid",
               "connection_generation")
_REGIMENT_KEYS = ("army_regiment_id", "current_soldiers", "maximum_soldiers",
                  "scale", "maa_type_status", "maa_type_key",
                  "composition_unavailable_reason")


def _integer(value: object, minimum: int = 0) -> bool:
    return type(value) is int and minimum <= value <= 2**31 - 1


def bookmark1070_army_observation_v1(
    snapshot: object, *, army_strengths: object = None,
    before_army_ids: object = None,
) -> dict[str, object]:
    """Project existing observations without copying Army history or journals.

    Before the choice, only the complete published player-army ID roster is
    needed. After it, pass the existing core query result and the earlier IDs;
    only new player-owned strength rows and their regiment fields are retained.
    """
    source = snapshot if isinstance(snapshot, Mapping) else {}
    player = source.get("played_character")
    player = player if isinstance(player, Mapping) else {}
    diagnostics = source.get("diagnostics")
    diagnostics = diagnostics if isinstance(diagnostics, Mapping) else {}
    result = {"schema": OBSERVATION_SCHEMA, "status": "unavailable",
        "character_id": player.get("character_id"),
        **{key: source.get(key) for key in _FRAME_KEYS[1:6]},
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
        "player_armies": None, "army_strengths": None,
        "unavailable_reason": "bookmark1070_player_army_frame_unavailable"}
    if not (source.get("paused") is True and source.get("map_ready") is True
            and player.get("alive") is True and _valid_frame(result)):
        return result
    rows = source.get("player_armies")
    if not isinstance(rows, list):
        return result
    armies = []
    seen = set()
    for row in rows:
        if not isinstance(row, Mapping) or not (
            _integer(row.get("army_id")) and row["army_id"] not in seen
            and _integer(row.get("owner_character_id"), 1)
        ):
            return result
        seen.add(row["army_id"])
        armies.append({key: row.get(key) for key in
            ("army_id", "owner_character_id", "current_province_id")})
    result.update(status="available", player_armies=armies, unavailable_reason=None)
    strengths = (army_strengths.get("army_strengths")
                 if isinstance(army_strengths, Mapping) else army_strengths)
    prior = set(before_army_ids) if isinstance(before_army_ids, (list, tuple, set)) else set()
    wanted = {row["army_id"] for row in armies
        if row["owner_character_id"] == result["character_id"]
        and row["army_id"] not in prior}
    if isinstance(strengths, list):
        compact = []
        for row in strengths:
            if not isinstance(row, Mapping) or row.get("army_id") not in wanted:
                continue
            item = {key: row.get(key) for key in ("status", "army_id",
                "native_carmy_id", "regiment_count", "current_soldiers",
                "maximum_soldiers", "unavailable_reason")}
            regiments = row.get("regiment_strengths")
            item["regiment_strengths"] = [
                {key: regiment.get(key) for key in _REGIMENT_KEYS}
                if isinstance(regiment, Mapping) else None
                for regiment in regiments] if isinstance(regiments, list) else None
            compact.append(item)
        result["army_strengths"] = compact
    return result


def _valid_frame(observation: Mapping[str, object]) -> bool:
    return bool(_integer(observation.get("character_id"), 1)
        and _integer(observation.get("date_raw"))
        and _integer(observation.get("revision"))
        and _integer(observation.get("native_revision"))
        and _integer(observation.get("bridge_pid"), 1)
        and _integer(observation.get("connection_generation"))
        and isinstance(observation.get("snapshot_id"), str)
        and observation["snapshot_id"]
        and isinstance(observation.get("episode_run_id"), str)
        and observation["episode_run_id"])


def plan_bookmark1070_army_material_postcondition_v1(
    decision: object, snapshot: object,
) -> dict[str, object] | None:
    """Bind the exact registered .4 third choice to the existing before roster."""
    if not isinstance(decision, Mapping) or not (
        decision.get("status") == "recommended"
        and decision.get("event_definition_key") == EVENT_KEY
        and decision.get("ck3_build") == "1.20.0.4"
        and decision.get("selected_native_option_index") == 2
    ):
        return None
    profile = decision.get("choice_effect_profile")
    specification = profile.get("observable_postcondition") if isinstance(profile, Mapping) else None
    if specification != {"metric": MATERIAL_METRIC,
            "expected_relation": MATERIAL_RELATION,
            "material_change_required_for_evidence": True}:
        return None
    before = bookmark1070_army_observation_v1(snapshot)
    active = snapshot.get("active_event") if isinstance(snapshot, Mapping) else None
    instance = active.get("instance_id") if isinstance(active, Mapping) else None
    ready = before["status"] == "available" and _integer(instance, 1)
    return {"schema": "xar.ck3.vanilla-event-material-postcondition",
        "schema_version": 1, "event_definition_key": EVENT_KEY,
        "selected_option_number": 3, "selected_native_option_index": 2,
        "metric": MATERIAL_METRIC, "expected_relation": MATERIAL_RELATION,
        "material_change_required_for_evidence": True,
        "status": "ready" if ready else "unavailable",
        "character_id": before["character_id"],
        "starting_snapshot_id": before["snapshot_id"],
        "starting_revision": before["revision"],
        "old_event_instance_id": instance,
        "before_army_observation": before,
        "source_expected_levies": 125, "expected_current_soldiers": 250,
        "unavailable_reason": None if ready else "bookmark1070_before_armies_unavailable"}


def _composition(strength: Mapping[str, object]) -> tuple[dict[str, int] | None, str | None]:
    rows = strength.get("regiment_strengths")
    if (strength.get("status") != "available" or not isinstance(rows, list)
            or not _integer(strength.get("regiment_count"))
            or len(rows) != strength["regiment_count"]):
        return None, "bookmark1070_new_army_regiments_unavailable"
    composition: dict[str, int] = {}
    seen = set()
    current = maximum = 0
    for row in rows:
        if not isinstance(row, Mapping) or not (
            _integer(row.get("army_regiment_id"))
            and row["army_regiment_id"] not in seen
            and _integer(row.get("current_soldiers"))
            and _integer(row.get("maximum_soldiers"))
            and type(row.get("scale")) is int and row["scale"] == 1
        ):
            return None, "bookmark1070_new_army_regiments_unavailable"
        seen.add(row["army_regiment_id"])
        type_status, key = row.get("maa_type_status"), row.get("maa_type_key")
        if type_status == "absent" and key is None:
            key = "non_maa"
        elif type_status != "available" or not isinstance(key, str) or not key:
            return None, "bookmark1070_new_army_type_unavailable"
        if row.get("composition_unavailable_reason") is not None:
            return None, "bookmark1070_new_army_type_unavailable"
        composition[key] = composition.get(key, 0) + row["current_soldiers"]
        current += row["current_soldiers"]
        maximum += row["maximum_soldiers"]
    if (current != strength.get("current_soldiers")
            or maximum != strength.get("maximum_soldiers")):
        return None, "bookmark1070_new_army_regiment_aggregate_mismatch"
    return composition, None


def evaluate_bookmark1070_army_material_postcondition_v1(
    expectation: object, event_selection: object,
) -> dict[str, object]:
    """Require a new player-owned army; never compare total army net manpower."""
    expected = expectation if isinstance(expectation, Mapping) else {}
    result = {key: expected.get(key) for key in ("schema", "schema_version",
        "event_definition_key", "selected_option_number", "selected_native_option_index",
        "metric", "expected_relation", "material_change_required_for_evidence",
        "starting_snapshot_id", "starting_revision", "character_id")}
    result.update(status="unavailable", relation_satisfied=None,
        material_change_observed=None, new_army_id=None, native_carmy_id=None,
        observed_composition=None, source_expected_levies=125,
        levy_type_identity_observed=False, total_army_net_gain_used=False,
        unavailable_reason="bookmark1070_army_observation_unavailable")

    def reject(reason: str, *, failed: bool = False) -> dict[str, object]:
        result.update(status="failed" if failed else "unavailable",
            relation_satisfied=False if failed else None,
            material_change_observed=False if failed else None,
            unavailable_reason=reason)
        return result

    if not (expected.get("status") == "ready"
            and expected.get("event_definition_key") == EVENT_KEY
            and expected.get("selected_native_option_index") == 2
            and expected.get("metric") == MATERIAL_METRIC
            and expected.get("expected_relation") == MATERIAL_RELATION):
        return reject(expected.get("unavailable_reason") or "bookmark1070_expectation_not_ready")
    selection = event_selection if isinstance(event_selection, Mapping) else {}
    before = selection.get("starting_bookmark1070_armies")
    after = selection.get("ending_bookmark1070_armies")
    if not (isinstance(before, Mapping) and isinstance(after, Mapping)
            and before.get("status") == after.get("status") == "available"
            and _valid_frame(before) and _valid_frame(after)):
        return result
    if not (before == expected.get("before_army_observation")
            and selection.get("status") == "event_instance_advanced"
            and selection.get("postcondition_verified") is True
            and selection.get("selected_native_option_index") == 2
            and selection.get("old_event_instance_id") == expected.get("old_event_instance_id")
            and selection.get("new_event_instance_id") != expected.get("old_event_instance_id")
            and all(before[key] == after[key] == selection.get(key)
                    for key in ("episode_run_id", "bridge_pid", "connection_generation"))
            and before["character_id"] == after["character_id"] == expected.get("character_id")
            and before["date_raw"] == after["date_raw"]
            and before["snapshot_id"] == selection.get("starting_snapshot_id")
            and after["snapshot_id"] == selection.get("ending_snapshot_id")
            and before["snapshot_id"] != after["snapshot_id"]
            and before["revision"] == selection.get("starting_revision")
            and after["revision"] == selection.get("ending_revision")
            and after["revision"] > before["revision"]
            and after["native_revision"] > before["native_revision"]):
        return reject("bookmark1070_army_frame_binding_mismatch", failed=True)
    prior = before.get("player_armies")
    current = after.get("player_armies")
    if not isinstance(prior, list) or not isinstance(current, list):
        return result
    old_ids = {row.get("army_id") for row in prior if isinstance(row, Mapping)}
    candidates = [row for row in current if isinstance(row, Mapping)
        and row.get("army_id") not in old_ids
        and row.get("owner_character_id") == expected["character_id"]]
    if len(candidates) != 1:
        return reject("bookmark1070_unique_new_player_army_not_observed", failed=True)
    army_id = candidates[0].get("army_id")
    strengths = after.get("army_strengths")
    matches = [row for row in strengths if isinstance(row, Mapping)
        and row.get("army_id") == army_id] if isinstance(strengths, list) else []
    if len(matches) != 1 or matches[0].get("status") != "available":
        return result
    strength = matches[0]
    native_id = strength.get("native_carmy_id")
    if type(native_id) is not int or not -(2**31) <= native_id <= 2**31 - 1 or native_id == -1:
        return reject("bookmark1070_new_army_identity_unavailable")
    composition, reason = _composition(strength)
    if composition is None:
        return reject(reason or "bookmark1070_new_army_composition_unavailable")
    result.update(new_army_id=army_id, native_carmy_id=native_id,
        observed_composition=composition,
        observed_current_soldiers=strength.get("current_soldiers"),
        observed_maximum_soldiers=strength.get("maximum_soldiers"))
    if composition != _EXPECTED or strength.get("current_soldiers") != 250 or strength.get("maximum_soldiers") != 250:
        return reject("bookmark1070_new_army_source_shape_mismatch", failed=True)
    result.update(status="verified_change", relation_satisfied=True,
        material_change_observed=True, unavailable_reason=None)
    return result
