"""Associate fresh native entry occupants with current character observations.

The caller has already performed authoritative current-condition refresh. This
ledger preserves that result unchanged; it does not run native refresh, predict
membership, infer injury causality, or replace stored entry statistics.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .battle_current_adapter import CurrentBattleCondition, CurrentBattleEntry
from .battle_current_refresh import DynamicRefreshContext
from .combat_core import wrap_int64


@dataclass(frozen=True, slots=True)
class KnightEntryRefreshAssociation:
    refreshed: DynamicRefreshContext
    ledger: Mapping[str, Any]
    scope_kind: str = "current_observed_knight_entry_association"
    complete_transition: bool = False
    complete_monte_carlo: bool = False

    @property
    def condition(self) -> CurrentBattleCondition:
        return self.refreshed.condition


def _identity(entry: CurrentBattleEntry) -> dict[str, Any]:
    return {
        "bucket": entry.bucket, "bucket_index": entry.bucket_index,
        "regiment_id": entry.state.regiment_id,
        "native_carmy_id": entry.native_carmy_id,
        "public_cunit_id": entry.public_cunit_id,
        "owner_character_id": entry.owner_character_id,
    }


def _knight(entry: CurrentBattleEntry) -> dict[str, Any]:
    present = "knight_character_id_raw" in entry.source_entry
    raw = entry.knight_character_id_raw
    if not present:
        kind = "absent"
    elif raw is None:
        kind = "null"
    elif raw == -1:
        kind = "native_no_knight"
    elif isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
        kind = "occupied_positive_full_character_id"
    else:
        kind = "invalid_not_published_native_identity"
    return {"present": present, "raw": raw, "kind": kind}


def _binding(
    leaf: Mapping[str, object] | None,
    person: Mapping[str, object] | None,
    control: Mapping[str, object] | None,
    condition: CurrentBattleCondition,
) -> dict[str, Any]:
    leaf_checks = {
        key: leaf.get(key) == getattr(condition, key) if leaf is not None else None
        for key in ("snapshot_revision", "observed_date_raw")
    }
    native_checks = {}
    for key in ("native_revision", "date_raw", "paused", "player_character_id", "actor_character_id"):
        native_checks[key] = (
            person[key] == control[key]
            if person is not None and control is not None and key in person and key in control
            else None
        )
    core = ("native_revision", "date_raw", "paused")
    matched = (
        person is not None and control is not None
        and all(native_checks[key] is True for key in core)
        and person.get("paused") is True and control.get("paused") is True
        and all(value is not False for value in native_checks.values())
        and all(value is True for value in leaf_checks.values())
        and person.get("native_revision") == condition.snapshot_revision
        and person.get("date_raw") == condition.observed_date_raw
    )
    return {
        "status": "same_paused_native_sample_coordinates" if matched else
                  "native_sample_coordinates_unbound_or_mismatched",
        "leaf_coordinate_checks": leaf_checks,
        "native_source_checks": native_checks,
        "is_runtime_gate": False,
        "native_effect_to_entry_refresh_order_proven": False,
    }


_ENTRY_ATTRIBUTE_FIELDS = (
    "effective_max_size", "effective_siege_raw", "effective_damage_raw",
    "effective_toughness_raw", "effective_pursuit_raw", "effective_screen_raw",
)


def _current_knight_evaluation(entry, character_id, armies, query_source):
    """Join normalized current observations; this selects no refresh callback."""
    matches = []
    for army in armies or ():
        if (army.get("native_carmy_id") != entry.native_carmy_id
                or army.get("army_id") != entry.public_cunit_id):
            continue
        leaf = army.get("knights")
        if not isinstance(leaf, Mapping) or leaf.get("status") != "available":
            continue
        for member in leaf.get("members") or ():
            if (member.get("character_id") == character_id
                    and member.get("source_regiment_id") == entry.state.regiment_id
                    and member.get("army_id") == entry.native_carmy_id):
                matches.append((leaf, member))
    if len(matches) != 1:
        return {"status": "unavailable", "unavailable_reason": "current_knight_identity_not_uniquely_observed",
                "observation": None, "source_context": copy.deepcopy(query_source),
                "refresh_boundary_selected": None, "selected_effect_receiver_granted": False}
    leaf, member = matches[0]
    multipliers = {name: copy.deepcopy(leaf[name]) for name in
                  ("loaded_damage_multiplier", "loaded_toughness_multiplier") if name in leaf}
    operands = {"after_effective_prowess_points": member["prowess"],
                "effectiveness_raw": member["knight_effectiveness_raw"], **multipliers}
    formula = {"effective_damage_raw": None, "effective_toughness_raw": None}
    p = max(1, member["prowess"])
    common = wrap_int64(p * member["knight_effectiveness_raw"])
    for target, multiplier in (("effective_damage_raw", "loaded_damage_multiplier"),
                               ("effective_toughness_raw", "loaded_toughness_multiplier")):
        if multipliers.get(multiplier) is not None:
            formula[target] = wrap_int64(common * multipliers[multiplier])
    stored = entry.source_entry
    fresh = {"effective_damage_raw": member["effective_damage_raw"],
             "effective_toughness_raw": member["effective_toughness_raw"]}
    return {"status": "available", "unavailable_reason": None,
            "observation": copy.deepcopy(member), "loaded_multipliers": multipliers,
            "literal_current_numeric_operands": operands,
            "current_formula_attributes": formula, "province_evaluated_attributes": fresh,
            "stored_matches_current_evaluation": {key: stored.get(key) == value for key, value in fresh.items()},
            "source_context": copy.deepcopy(query_source),
            "origin": "existing_12003_combat_inputs_current_knight_read",
            "refresh_boundary_selected": None, "selected_effect_receiver_granted": False,
            "native_queue_admission_observed": False, "requested_effects_committed": False}


def associate_current_knight_entries(
    refreshed: DynamicRefreshContext,
    *,
    previous_condition: CurrentBattleCondition | None = None,
    current_person_observation: Mapping[str, object] | None = None,
    person_query_source: Mapping[str, object] | None = None,
    control_query_source: Mapping[str, object] | None = None,
    current_combat_armies: Sequence[Mapping[str, object]] | None = None,
    combat_query_source: Mapping[str, object] | None = None,
) -> KnightEntryRefreshAssociation:
    """Attach existing normalized current-character rows without changing state.

    The person argument is the normalized terminal-transition leaf. Its top
    transition readiness is independent of current-character row coverage.
    Source coordinate binding is diagnostic; an unbound row remains an explicitly
    independent current observation. Only positive occupied native knight IDs
    associate. Previous identities are compared only inside the same full combat.
    """
    condition = refreshed.condition
    same_combat = (previous_condition.combat_id == condition.combat_id
                   if previous_condition is not None else None)
    observed_rows = (current_person_observation.get("character_observations")
                     if current_person_observation is not None else None)
    rows = observed_rows if isinstance(observed_rows, (list, tuple)) else ()
    people = {row["character_id"]: row for row in rows}
    binding = _binding(current_person_observation, person_query_source,
                       control_query_source, condition)
    sides = []
    for side in condition.sides:
        old_side = next((row for row in previous_condition.sides
                         if row.side_index == side.side_index), None) if same_combat else None
        prior = {(row.bucket, row.state.regiment_id): row for row in old_side.entries} if old_side else {}
        entries = []
        for entry in side.entries:
            old = prior.pop((entry.bucket, entry.state.regiment_id), None)
            knight = _knight(entry)
            old_knight = _knight(old) if old is not None else None
            if old is None:
                change = "no_previous_entry_in_current_combat_scope"
            elif old_knight == knight:
                change = "retained"
            elif (old_knight["kind"] == knight["kind"] == "occupied_positive_full_character_id"):
                change = "rebound"
            else:
                change = "identity_observation_changed"
            person = people.get(knight["raw"]) if knight["kind"] == "occupied_positive_full_character_id" else None
            entries.append({
                "identity": _identity(entry),
                "previous_identity": _identity(old) if old is not None else None,
                "membership": "retained" if old is not None else "new_in_fresh_frame" if same_combat else "previous_scope_not_supplied_or_different_combat",
                "order_changed": entry.bucket_index != old.bucket_index if old is not None else None,
                "army_or_owner_changed": any(getattr(entry, key) != getattr(old, key)
                    for key in ("native_carmy_id", "public_cunit_id", "owner_character_id")) if old is not None else None,
                "previous_knight_identity": old_knight, "knight_identity": knight,
                "knight_identity_change": change,
                "person_row_present": person is not None,
                "current_person_observation": copy.deepcopy(person),
                "stored_combat_entry_attributes": {key: copy.deepcopy(entry.source_entry.get(key))
                    for key in _ENTRY_ATTRIBUTE_FIELDS},
                "stored_entry_attribute_presence": {key: key in entry.source_entry
                    for key in _ENTRY_ATTRIBUTE_FIELDS},
                "current_knight_evaluation": _current_knight_evaluation(
                    entry, knight["raw"], current_combat_armies, combat_query_source)
                    if knight["kind"] == "occupied_positive_full_character_id" else None,
                "person_attribution": ("same_paused_native_sample" if binding["status"] == "same_paused_native_sample_coordinates"
                                       else "independent_current_character_observation") if person is not None else None,
            })
        sides.append({
            "side_index": side.side_index, "entries_in_native_order": entries,
            "absent_entries_in_previous_native_order": [dict(
                identity=_identity(row), knight_identity=_knight(row),
                membership="absent_from_fresh_frame", absence_cause=None,
            ) for row in prior.values()],
        })
    return KnightEntryRefreshAssociation(refreshed, {
        "previous_same_combat": same_combat, "sides": sides,
        "person_observation_present": current_person_observation is not None,
        "character_rows_present": current_person_observation is not None and "character_observations" in current_person_observation,
        "character_observations_in_request_order": copy.deepcopy(observed_rows),
        "person_leaf_snapshot_revision": current_person_observation.get("snapshot_revision") if current_person_observation is not None else None,
        "person_leaf_observed_date_raw": current_person_observation.get("observed_date_raw") if current_person_observation is not None else None,
        "person_query_source": copy.deepcopy(person_query_source),
        "control_query_source": copy.deepcopy(control_query_source), "binding": binding,
        "current_combat_armies_supplied": current_combat_armies is not None,
        "combat_query_source": copy.deepcopy(combat_query_source),
        "current_knight_read_grants_selected_receiver": False,
        "current_knight_read_selects_refresh_boundary": False,
        "fresh_condition_modified": False, "draw_consumed": False,
        "previous_predicted_losses_reapplied": False,
        "person_state_used_to_remove_entry": False,
        "person_state_used_to_replace_stored_stats": False,
        "future_membership_or_absence_cause_inferred": False,
    })
