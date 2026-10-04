"""One .3 selected SCRIPT row: accolade qualification variable feedback.

The selected branch is caller data. Army query primitives are independent
from retained combat rows. Model variables remain separate from the observed
snapshot and native setter/UI callbacks are not reproduced.
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
from .combat_core import FIXED_SCALE, fixed_mul, trunc_div_toward_zero
from .phase_event_evaluator import FrozenPhaseEventManifest


ACCOLADE_QUALIFICATION_EVENT_KEY_12003 = "knight_qualify_for_accolade"
ACCOLADE_UNLOCK_PURPOSE_12003 = "knight_qualify_for_accolade:attribute_unlock:source_order"
ACCOLADE_ATTRIBUTES_12003 = (
    "skirmisher", "archer", "crossbowmen", "pike", "vanguard", "outrider",
    "lancer", "camelry", "elephantry", "horse_archer", "gunpowder", "fanatic", "valiant",
)
_UNIT_TYPES = ("skirmishers", None, None, "pikemen", "heavy_infantry", "light_cavalry",
               "heavy_cavalry", "camel_cavalry", "elephant_cavalry", "archer_cavalry", "gunpowder")
_CROSSBOW_TYPES = ("crossbowmen", "shenbigong", "accolade_maa_crossbowers")
_NATIVE_REMAINDER = (
    "compiled set_variable generic internal callbacks at3765780/fire264E680",
    "send_interface_message primitive and tooltip callbacks",
    "later attribute-unlock consumers and actual accolade acquisition",
)


@dataclass(frozen=True, slots=True)
class ScriptNumericVariableState12003:
    present: bool | None
    value_raw: int | None = None


@dataclass(frozen=True, slots=True)
class ScriptBooleanVariableState12003:
    present: bool | None
    value: bool | None = None


@dataclass(frozen=True, slots=True)
class AccoladeQualificationInputs12003:
    liege_full_character_id: int | None = None
    liege_scope_present: bool | None = None
    liege_accolade_progress: ScriptNumericVariableState12003 | None = None
    root_unlock_variables: Mapping[str, ScriptBooleanVariableState12003] | None = None
    count_base_by_type: Mapping[str, int | None] | None = None
    count_exact_type: Mapping[str, int | None] | None = None
    total_army_maa_regiment_count: int | None = None
    any_unit_type: Mapping[str, bool | None] | None = None
    any_non_crossbow_archer: bool | None = None
    any_crossbow_variant: bool | None = None
    attribute_trigger_by_attribute: Mapping[str, bool | None] | None = None
    enemy_any_faith_hostility_at_least_evil: bool | None = None
    own_side_army_size_raw: int | None = None
    enemy_side_army_size_raw: int | None = None
    fixed_current_combat_context: bool | None = None


def _digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _value(value, name, kind, missing):
    if value is None:
        missing.append(name)
        return None
    if type(value) is not kind:
        raise ValueError(f"{name} must be {kind.__name__} or None")
    return value


def _mapped(mapping, key, name, kind, missing):
    return _value(None if mapping is None else mapping.get(key), f"{name}.{key}", kind, missing)


def _stored(state, name, numeric, missing):
    expected = ScriptNumericVariableState12003 if numeric else ScriptBooleanVariableState12003
    if state is None:
        missing.append(f"{name} stored variable presence/value")
        return None, None
    if not isinstance(state, expected):
        raise TypeError(f"{name} must be {expected.__name__}")
    present = _value(state.present, f"{name}.present", bool, missing)
    value = state.value_raw if numeric else state.value
    if present is True:
        value = _value(value, f"{name}.stored_value", int if numeric else bool, missing)
    elif present is False:
        if value is not None:
            raise ValueError(f"absent {name} must have None value")
        value = None
    return present, value


def _weights(inputs, missing):
    exact = [_mapped(inputs.count_exact_type, name, "count_exact_type", int, missing)
             for name in _CROSSBOW_TYPES]
    total = _value(inputs.total_army_maa_regiment_count, "total_army_maa_regiment_count", int, missing)
    own = _value(inputs.own_side_army_size_raw, "own_side_army_size_raw", int, missing)
    enemy = _value(inputs.enemy_side_army_size_raw, "enemy_side_army_size_raw", int, missing)
    half_count = None if total is None else trunc_div_toward_zero(total * FIXED_SCALE, 2)
    rows, weights = [], []
    for index, attribute in enumerate(ACCOLADE_ATTRIBUTES_12003):
        already = _mapped(inputs.attribute_trigger_by_attribute, attribute,
                          "attribute_trigger_by_attribute", bool, missing)
        if index == 1:
            exists = _value(inputs.any_non_crossbow_archer, "any_non_crossbow_archer", bool, missing)
            archers = _mapped(inputs.count_base_by_type, "archers", "count_base_by_type", int, missing)
            count = None if archers is None or any(value is None for value in exact) else archers
            if count is not None:
                for value in exact:
                    count -= value
            factor = None if count is None else count * FIXED_SCALE
        elif index == 2:
            exists = _value(inputs.any_crossbow_variant, "any_crossbow_variant", bool, missing)
            count = None if any(value is None for value in exact) else sum(exact)
            factor = None if count is None else count * FIXED_SCALE
        elif index == 11:
            exists = _value(inputs.enemy_any_faith_hostility_at_least_evil,
                            "enemy_any_faith_hostility_at_least_evil", bool, missing)
            factor = half_count
        elif index == 12:
            exists = None if own is None or enemy is None else own >= fixed_mul(enemy, 66_000)
            factor = half_count
        else:
            unit = _UNIT_TYPES[index]
            exists = _mapped(inputs.any_unit_type, unit, "any_unit_type", bool, missing)
            count = _mapped(inputs.count_base_by_type, unit, "count_base_by_type", int, missing)
            factor = None if count is None else count * FIXED_SCALE
        predicate = (False if exists is False or already is True else
                     None if exists is None or already is None else True)
        base = (50 if index == 12 else 10) * FIXED_SCALE
        weight = 0 if predicate is False else None if predicate is None or factor is None else fixed_mul(base, factor)
        weights.append(weight)
        rows.append({"branch_index": index, "attribute": attribute, "predicate": predicate,
                     "base_weight_raw": base, "factor_raw": factor, "weight_raw": weight,
                     "eligible": None if weight is None else predicate is True and weight > 0})
    return weights, rows


def _delta(character_id, side_index, target, variable, before_present, before,
           after, numeric):
    return {"character_id": character_id, "side_index": side_index,
            "target_scope": target, "field": variable, "variable": variable,
            "before_present": before_present, "before": before,
            "after_present": True, "after": after,
            "delta_raw": after - before if numeric and type(before) is int else None,
            "unit": "script_variable_Q100000" if numeric else "script_variable_boolean",
            "origin": "source_closed_accolade_selected_direct_variable_write",
            "native_effective_property_claimed": False}


def execute_selected_accolade_qualification_12003(
    context: Mapping[str, object], *, script_outcomes: Sequence[PhaseEventScriptOutcome12003],
    inputs: AccoladeQualificationInputs12003 | None,
    source_context: Mapping[str, object] | None,
    manifest: FrozenPhaseEventManifest | None = None, advantage_model: object | None = None,
) -> dict[str, object]:
    """Compute direct variables with a valid explicit branch, retaining partials.

    Canonical no-event initialization provides the existing current snapshot
    shape and .3 manifest binding; this helper owns the sole additional effect.
    It performs no event selection/chance roll or native setter/UI call.
    """
    result = deepcopy(execute_selected_phase_event_12003(
        context, event_key=None, manifest=manifest, advantage_model=advantage_model))
    after = result["after_state"]
    missing, deltas, log, records = [], [], [], []
    weights, weight_rows, branch = [None] * 13, [], None
    prefix_applied = False
    outcomes = tuple(script_outcomes)
    if any(not isinstance(value, PhaseEventScriptOutcome12003) for value in outcomes):
        raise TypeError("script_outcomes must contain PhaseEventScriptOutcome12003")
    if len(outcomes) > 1:
        raise ValueError("unexplained additional accolade branch outcome records")
    refs = {**context.get("native_state_refs", {}), **context.get("offline_state_refs", {})}
    role_valid = "knight" in context["phase_roles"]
    if not role_valid:
        missing.append("selected accolade qualification requires current knight role")
    maa_q = _value(refs.get("root.knight_army.maa_regiment_count_raw"),
                   "root.knight_army.maa_regiment_count_raw", int, missing)
    can = _value(refs.get("root.can_be_acclaimed"), "root.can_be_acclaimed", bool, missing)
    prowess = _value(refs.get("root.skills.prowess_raw"), "root.skills.prowess_raw", int, missing)
    trigger = (None if maa_q is None or can is None or prowess is None else
               maa_q > 0 and can and prowess >= 800_000)
    if trigger is False:
        missing.append("selected accolade qualification trigger is false")
    if not isinstance(source_context, Mapping) or any(source_context.get(key) is None
            for key in ("combat_id", "snapshot_revision", "observed_date_raw")):
        missing.append("full CombatID and original observed coordinate")
    if inputs is None:
        missing.append("AccoladeQualificationInputs12003 current primitives")
    elif not isinstance(inputs, AccoladeQualificationInputs12003):
        raise TypeError("inputs must be AccoladeQualificationInputs12003 or None")
    else:
        liege = _value(inputs.liege_full_character_id, "liege_full_character_id", int, missing)
        scope = _value(inputs.liege_scope_present, "liege_scope_present", bool, missing)
        if liege is not None and liege <= 0:
            raise ValueError("liege_full_character_id must be positive")
        if scope is False:
            missing.append("actual present liege scope")
        fixed = _value(inputs.fixed_current_combat_context, "fixed_current_combat_context", bool, missing)
        if fixed is False:
            missing.append("declared fixed current combat context")
        before_present, before = _stored(inputs.liege_accolade_progress,
                                        "liege.accolade_progress", True, missing)
        weights, weight_rows = _weights(inputs, missing)
        if role_valid and trigger is True and liege is not None and scope is True:
            prefix_applied = True
            after["root"]["liege_full_character_id"] = liege
            after["root"]["liege_variable_updates"]["accolade_progress"] = 0
            deltas.append(_delta(liege, None, "liege", "accolade_progress", before_present, before, 0, True))
            log.extend(({"op": "save_scope_as", "scope": "acclaimed_knight",
                         "character_id": context["root_character_id"]},
                        {"op": "set_variable", "target_scope": "liege", "character_id": liege,
                         "name": "accolade_progress", "after_raw": 0}))
        if any(value is None for value in weights):
            missing.append("complete source random_list branch weights")
        elif not any(value > 0 for value in weights):
            missing.append("zero-positive SCRIPT random_list child semantics at3765780")
        elif not outcomes:
            missing.append("explicit caller selected attribute unlock branch")
        else:
            outcome = outcomes[0]
            if (outcome.purpose != ACCOLADE_UNLOCK_PURPOSE_12003 or outcome.branch_index is None
                    or outcome.character_id is not None or not 0 <= outcome.branch_index < 13):
                raise ValueError("malformed source-order accolade branch outcome")
            chosen = outcome.branch_index
            if weights[chosen] <= 0:
                raise ValueError("caller selected accolade branch has nonpositive source weight")
            variable = f"{ACCOLADE_ATTRIBUTES_12003[chosen]}_attribute_unlock"
            stored = None if inputs.root_unlock_variables is None else inputs.root_unlock_variables.get(variable)
            present, old = _stored(stored, f"root.{variable}", False, missing)
            # A source-valid selected child computes its literal writes even
            # when fixed-context/before-storage evidence is incomplete. Those
            # independent missing conditions still prevent horizon readiness.
            if prefix_applied:
                branch = chosen
                after["root"]["variable_updates"][variable] = True
                deltas.append(_delta(context["root_character_id"], context["combat_side_index"],
                                     "root", variable, present, old, True, False))
                message = {"recipient_character_id": liege, "type": "msg_accolade_eligibility",
                           "title": "maa_accolade_unlock.t",
                           "left_icon_character_id": context["root_character_id"],
                           "custom_tooltip": f"{ACCOLADE_ATTRIBUTES_12003[chosen]}_attribute.battle_message_tt",
                           "native_ui_acknowledged": False}
                after["observational_effects"].append(message)
                log.extend(({"op": "set_variable", "target_scope": "root", "name": variable,
                             "after": True}, {"op": "send_interface_message", "arguments": message}))
                records.append({"purpose": outcome.purpose, "branch_index": chosen,
                                "selection_origin": "caller_conditional", "native_rng_trace_claimed": False})
    if outcomes and branch is None:
        # Unresolved primitives leave the explicit record unconsumed; a fully
        # known all-nonpositive list cannot justify a selected child.
        if all(value is not None for value in weights) and not any(value > 0 for value in weights):
            raise ValueError("outcome supplied for all-nonpositive accolade random_list")
    ready = branch is not None and not missing
    after.pop("state_sha256", None)
    after["state_sha256"] = _digest(after)
    result.update(
        status="selected_accolade_direct_variables_applied" if ready else "selected_accolade_prefix_or_inputs_partial",
        transition_version="ck3-1.20.0.3-one-selected-accolade-direct-feedback-v1",
        event={"key": ACCOLADE_QUALIFICATION_EVENT_KEY_12003, "type": "knight",
               "global_load_index": 12, "type_load_index": 8,
               "trigger_valid": trigger, "selection_origin": "caller_conditional"},
        after_state=after, state_changed=any(
            row["before_present"] is False or
            row["before_present"] is True and row["before"] != row["after"] for row in deltas),
        state_change_unknown=any(row["before_present"] is None or
            row["before_present"] is True and row["before"] is None for row in deltas),
        script_outcomes={"provided_count": len(outcomes), "consumed_count": len(records),
                         "records": records, "native_rng_trace_claimed": False},
        transition_log=log, feedback_pending=list(dict.fromkeys(missing)),
        condition_numeric_deltas=deltas, branch_weights_raw=weights,
        branch_weight_ledger=weight_rows, selected_attribute_branch=branch,
        event_execution_consumed=prefix_applied, condition_feedback_ready=ready,
        condition_feedback_scope="declared_fixed_current_combat_direct_variable_subset",
        fixed_current_combat_context=None if inputs is None else inputs.fixed_current_combat_context,
        remaining_native_callbacks=list(_NATIVE_REMAINDER),
        primary_selected_effect_transition_ready=prefix_applied,
        full_script_feedback_ready=False, complete_transition=False, complete_monte_carlo=False,
        native_candidate_source_equivalence=False, native_event_selector_ready=False,
        native_rng_trace_claimed=False, actual_game_days_advanced=0,
        current_cache_quantity_membership_commander_direct_writes=False,
        modeled_source_context=deepcopy(source_context))
    result.pop("result_sha256", None)
    result["result_sha256"] = _digest(result)
    return result


__all__ = ["ACCOLADE_QUALIFICATION_EVENT_KEY_12003", "ACCOLADE_UNLOCK_PURPOSE_12003",
           "ACCOLADE_ATTRIBUTES_12003", "ScriptNumericVariableState12003",
           "ScriptBooleanVariableState12003", "AccoladeQualificationInputs12003",
           "execute_selected_accolade_qualification_12003"]
