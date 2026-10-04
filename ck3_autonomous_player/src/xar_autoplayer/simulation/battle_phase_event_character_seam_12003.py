"""Independent .3 incapability primary model and existing person-field reader.

The person observation and supplied script predicate have different meanings.
Trait projection never rewrites observed effective properties, Entry caches,
knight identity, memberships or native memory state. Composition is external.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

from .battle_phase_events_12003 import (
    PhaseEventScriptOutcome12003, execute_selected_phase_event_12003,
)
from .phase_event_evaluator import FrozenPhaseEventManifest


CHARACTER_EVENT_KEY_12003 = "knight_becomes_incapable"
_CHILD_SOURCE = "selected compiledEffect+160 child under3765780/fire264E680"


@dataclass(frozen=True, slots=True)
class RootCharacterLocationScope12003:
    character_id: int
    province_id: int | None
    source_provenance: str | None


@dataclass(frozen=True, slots=True)
class CharacterPhaseEventInputs12003:
    root_location_scope: RootCharacterLocationScope12003 | None = None
    current_person_observation: Mapping[str, object] | None = None
    observation_source: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CurrentCharacterFields12003:
    character_id: int
    alive: bool | None
    incapable_trait: bool | None
    effective_prowess_points: int | None
    field_ledger: Mapping[str, object]
    missing_inputs: tuple[str, ...]
    source_context: Mapping[str, object] | None


@dataclass(frozen=True, slots=True)
class CharacterEventCallbackGap12003:
    kind: str
    character_id: int
    missing_input: str
    source_entry: str


@dataclass(frozen=True, slots=True)
class CharacterPhaseEventProjection12003:
    execution: Mapping[str, object]
    character_primary_deltas: tuple[Mapping[str, object], ...]
    current_person_reader: CurrentCharacterFields12003
    memory_requests: tuple[Mapping[str, object], ...]
    typed_callback_gaps: tuple[CharacterEventCallbackGap12003, ...]
    event_execution_consumed: bool
    condition_feedback_ready: bool
    ledger: Mapping[str, object]
    full_script_feedback_ready: bool = False
    complete_transition: bool = False
    complete_monte_carlo: bool = False
    actual_game_days_advanced: int = 0


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def _object(value):
    return value if isinstance(value, Mapping) else {}


def _presence(container, key):
    return "absent" if key not in container else "null" if container[key] is None else "value"


def read_current_character_fields_12003(
    payload: Mapping[str, object] | None, *, character_id: int,
    source_context: Mapping[str, object] | None = None,
) -> CurrentCharacterFields12003:
    """Read a matched normalized terminal row or leaf without any native call.

    Missing fields are diagnostic, independent from the selected event model.
    A known incapable flag remains usable when another injury flag is missing.
    The observed trait is not a proof of the complete script predicate.
    """
    if type(character_id) is not int or character_id <= 0:
        raise ValueError("character_id must be a positive full CharacterID")
    supplied = _object(payload)
    if "character_id" in supplied:
        rows = [supplied] if supplied.get("character_id") == character_id else []
    else:
        candidates = supplied.get("character_observations", ())
        rows = [row for row in candidates if isinstance(row, Mapping)
                and row.get("character_id") == character_id] if isinstance(candidates, (tuple, list)) else []
    missing = []
    if len(rows) != 1:
        missing.append("one current character_observations row matched by full CharacterID")
    row = rows[0] if len(rows) == 1 else {}
    alive = row.get("alive") if type(row.get("alive")) is bool else None
    if alive is None:
        missing.append(f"character_observations.alive ({_presence(row, 'alive')})")
    person = _object(row.get("current_person_state"))
    injury = _object(person.get("injury_traits"))
    flags = _object(injury.get("flags"))
    incapable = flags.get("incapable") if type(flags.get("incapable")) is bool else None
    if incapable is None:
        missing.append(f"current_person_state.injury_traits.flags.incapable ({_presence(flags, 'incapable')})")
    effective = _object(person.get("effective_prowess"))
    points = effective.get("points")
    prowess = (points if effective.get("status") == "available" and type(points) is int
               and -(1 << 31) <= points < (1 << 31) else None)
    if prowess is None:
        missing.append("current_person_state.effective_prowess available signed32 points")
    ledger = {
        "reader_scope": "independent_existing_normalized_character_observation",
        "matched_row_count": len(rows), "raw_current_person_state": deepcopy(person),
        "alive": {"presence": _presence(row, "alive"), "value": alive,
                  "native_source": "Character+1D0 death-data pointer"},
        "incapable_trait": {"presence": _presence(flags, "incapable"), "value": incapable,
                            "injury_group_status": injury.get("status"),
                            "script_is_incapable_equivalence_claimed": False},
        "effective_prowess": {"presence": _presence(effective, "points"),
                              "status": effective.get("status"), "points": prowess,
                              "unavailable_reason": effective.get("unavailable_reason"),
                              "native_source": "Character+EC signed32 effective property",
                              "script_base_skill_Q_equivalence_claimed": False},
        "leaf_identity": {"snapshot_revision": supplied.get("snapshot_revision"),
                          "observed_date_raw": supplied.get("observed_date_raw")},
        "source_context": deepcopy(source_context),
        "separate_query_same_native_sample_claimed": False,
        "event_causality_or_callback_boundary_claimed": False,
        "entry_refresh_gated_by_character_diagnostics": False,
        "knight_detach_or_command_permission_inferred": False,
    }
    return CurrentCharacterFields12003(character_id, alive, incapable, prowess,
                                      ledger, tuple(missing), deepcopy(source_context))


def _frame_diagnostics(event_source, observation_source, character_id):
    left, right = _object(event_source), _object(observation_source)
    fields = ("native_revision", "date_raw", "paused")
    comparable = all(left.get(key) is not None and right.get(key) is not None for key in fields)
    return {"character_id": character_id,
            "native_identity_comparable": comparable,
            "native_identity_equal": all(left[key] == right[key] for key in fields) if comparable else None,
            "coordinates": {key: {"event_source": left.get(key), "observation_source": right.get(key)}
                            for key in fields},
            "public_revisions_used_as_native_frame_identity": False,
            "comparison_gates_event_model": False,
            "event_causality_or_callback_boundary_claimed": False}


def execute_selected_character_phase_event_12003(
    context: Mapping[str, object], *, script_outcomes: Sequence[PhaseEventScriptOutcome12003] = (),
    source_context: Mapping[str, object] | None,
    inputs: CharacterPhaseEventInputs12003 | None = None,
    manifest: FrozenPhaseEventManifest | None = None,
) -> CharacterPhaseEventProjection12003:
    """Project the sole selected incapable event, with explicit callback gaps.

    Empty tape is mandatory. Current person fields are read as independent
    evidence; they never fill the supplied script predicate or an after-cache.
    This function does not establish calendar/main or event-selection admission.
    """
    if tuple(script_outcomes):
        raise ValueError("knight_becomes_incapable has no script outcome or RNG tape")
    if inputs is not None and not isinstance(inputs, CharacterPhaseEventInputs12003):
        raise TypeError("inputs must be CharacterPhaseEventInputs12003 or None")
    result = deepcopy(execute_selected_phase_event_12003(context, event_key=None, manifest=manifest))
    after = result["after_state"]
    root_id = context["root_character_id"]
    reader = read_current_character_fields_12003(
        None if inputs is None else inputs.current_person_observation,
        character_id=root_id, source_context=None if inputs is None else inputs.observation_source)
    refs = {**context.get("native_state_refs", {}), **context.get("offline_state_refs", {})}
    gaps, deltas, memory, log = [], [], [], []
    consumed, ready = False, False

    def gap(kind, missing, source=_CHILD_SOURCE):
        gaps.append(CharacterEventCallbackGap12003(kind, root_id, missing, source))

    role = "knight" in context["phase_roles"]
    if not role:
        gap("selected_role", "current selected event role knight")
    coordinate = _object(source_context)
    for key in ("combat_id", "snapshot_revision", "observed_date_raw"):
        if coordinate.get(key) is None:
            gap("model_source_coordinate", f"original observed {key}")
    predicate = refs.get("root.is_incapable")
    if type(predicate) is not bool:
        gap("script_predicate", "explicit root.is_incapable boolean; observed trait flag does not supply it")
        valid = None
    else:
        valid = not predicate
        if not valid:
            gap("selected_trigger_invalid", "selected event validity requires root.is_incapable False")
    alive = refs.get("root.alive")
    if type(alive) is not bool:
        gap("effect_guard", "explicit root.alive boolean")
    if role and valid is True and type(alive) is bool:
        log.append({"order": 0, "op": "save_scope_as", "name": "knight",
                    "character_id": root_id, "scope": "effect_local"})
        consumed = True
        if not alive:
            # There is no guarded trait, memory or location read on this branch.
            ready = not gaps
        else:
            before = refs.get("root.traits.incapable")
            if type(before) is not bool:
                before = None
                gap("primary_before_trait", "explicit before root.traits.incapable boolean")
            after["root"]["traits"]["incapable"] = True
            deltas.append({"character_id": root_id, "side_index": context["combat_side_index"],
                "field": "traits.incapable", "before": before, "after": True,
                "delta_raw": None, "unit": "trait_boolean", "before_known": before is not None,
                "origin": "selected_source_add_trait_primary_projection",
                "native_effective_property_claimed": False})
            log.append({"order": 1, "op": "add_trait", "character_id": root_id,
                        "trait": "incapable", "primary_after": True, "native_callback_executed": False})
            location = None if inputs is None else inputs.root_location_scope
            province, provenance = None, None
            if location is None:
                gap("memory_location_argument", "explicit current root location Province scope; no Combat province fallback")
            elif not isinstance(location, RootCharacterLocationScope12003):
                raise TypeError("root_location_scope must be RootCharacterLocationScope12003")
            elif location.character_id != root_id:
                gap("memory_location_argument", "location scope belongs to selected root full CharacterID")
            elif type(location.province_id) is not int or not location.source_provenance:
                gap("memory_location_argument", "root location Province identifier and declared provenance")
            else:
                province, provenance = location.province_id, location.source_provenance
            request = {"owner_character_id": root_id,
                "type": "became_incapable_due_to_battle_concussion",
                "scope_aliases": {"knight": root_id, "new_memory_to": "battle_memory"},
                "variables": {"battle_location": province},
                "location_source_provenance": provenance,
                "native_memory_id": None, "native_memory_commit_observed": False,
                "native_alias_materialization_observed": False, "request_only": True}
            memory.append(request)
            log.extend(({"order": 2, "op": "create_character_memory", "request": deepcopy(request)},
                        {"order": 3, "op": "save_scope_as", "source_scope": "new_memory",
                         "name": "battle_memory", "native_materialization_observed": False},
                        {"order": 4, "op": "set_variable", "target_scope": "battle_memory",
                         "name": "battle_location", "value_scope_province_id": province,
                         "native_store_observed": False}))
            after["recompute"]["character_stat_ids"] = list(dict.fromkeys(
                [*after["recompute"]["character_stat_ids"], root_id]))
            gap("trait_effective_property_callback", "actual add_trait callback to effective character properties",
                _CHILD_SOURCE + " / Character+EC")
            gap("native_memory_creation", "native memory creation commit and generated full memory ID",
                _CHILD_SOURCE + " create_character_memory")
            gap("native_memory_scope", "new_memory to battle_memory native alias materialization",
                _CHILD_SOURCE + " save_scope_as")
            gap("native_memory_variable_store", "actual battle_memory battle_location scope store",
                _CHILD_SOURCE + " set_variable")
            gap("cached_stats_and_role_callbacks", "actual cache refresh and role/commander effects; no trait-to-cache inference",
                "2657AC0 / 2C06D30 actual Character+EC;2634880 does not test trait/alive")
    if deltas or memory:
        after["modeled_memory_requests"] = deepcopy(memory)
        after.pop("state_sha256", None)
        after["state_sha256"] = _digest(after)
    result.update(
        status="selected_character_primary_partial" if alive is True and consumed else
               "selected_character_dead_guard_unchanged" if ready else "selected_character_inputs_partial",
        transition_version="ck3-1.20.0.3-one-incapable-character-primary-v1",
        event={"key": CHARACTER_EVENT_KEY_12003, "type": "knight", "global_load_index": 8,
               "type_load_index": 4, "trigger_valid": valid, "selection_origin": "caller_conditional"},
        after_state=after, state_changed=any(row["before"] is False for row in deltas),
        state_change_unknown=any(row["before"] is None for row in deltas),
        transition_log=log, feedback_pending=[value.missing_input for value in gaps],
        condition_numeric_deltas=deepcopy(deltas), modeled_memory_requests=deepcopy(memory),
        script_outcomes={"provided_count": 0, "consumed_count": 0, "records": [],
                         "native_rng_trace_claimed": False},
        primary_selected_effect_transition_ready=consumed,
        event_execution_consumed=consumed, condition_feedback_ready=ready,
        full_script_feedback_ready=False, complete_transition=False, complete_monte_carlo=False,
        actual_game_days_advanced=0, draw_state_consumed=False)
    result.pop("result_sha256", None)
    result["result_sha256"] = _digest(result)
    ledger = {"sole_event": CHARACTER_EVENT_KEY_12003,
        "scope_kind": "independent_selected_character_primary_and_existing_person_reader",
        "original_model_source_context": deepcopy(source_context),
        "current_person_observation_source": None if inputs is None else deepcopy(inputs.observation_source),
        "frame_identity_diagnostics": _frame_diagnostics(source_context,
            None if inputs is None else inputs.observation_source, root_id),
        "provided_script_predicate": predicate,
        "provided_alive_guard": alive, "observed_incapable_trait": reader.incapable_trait,
        "observed_effective_prowess_points": reader.effective_prowess_points,
        "reader_diagnostics_gate_primary_model": False,
        "observed_fields_overwritten_by_trait_model": False,
        "observed_trait_used_as_complete_script_predicate": False,
        "command_permission_or_native_knight_detach_inferred": False,
        "effective_property_or_six_cache_prediction_from_trait": False,
        "memory_native_ID_or_commit_invented": False,
        "battle_location_written_to_root_variable": False,
        "character_recompute_is_model_request_not_native_execution": bool(deltas),
        "horizon_or_adapter_composition_performed": False,
        "full_script_feedback_ready": False, "actual_game_days_advanced": 0}
    return CharacterPhaseEventProjection12003(result, tuple(deltas), reader, tuple(memory),
                                             tuple(gaps), consumed, ready, ledger)


__all__ = ["CHARACTER_EVENT_KEY_12003", "RootCharacterLocationScope12003",
           "CharacterPhaseEventInputs12003", "CurrentCharacterFields12003",
           "CharacterEventCallbackGap12003", "CharacterPhaseEventProjection12003",
           "read_current_character_fields_12003", "execute_selected_character_phase_event_12003"]
