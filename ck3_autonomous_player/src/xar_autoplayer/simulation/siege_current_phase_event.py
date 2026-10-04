"""Typed caller-selected siege phase-event conditions for exact CK3 1.20.0.3.

No native call, draw, clock or completion date is predicted. Each supplied step
has its own normal work and dynamic apply/event/post totals. The prepared enum
cache is explanatory data, never an implicit selection for a future step.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace
from enum import IntEnum
from pathlib import Path
from typing import Any, Mapping, Sequence

SCALE = 100000


class PhaseEvent(IntEnum):
    BREACH = 0
    STARVATION = 1
    DISEASE = 2
    DESERTION = 3
    STALEMATE = 4


@dataclass(frozen=True, slots=True)
class CurrentPhaseEventState:
    current_work_raw: int | None
    phase_counter: int | None = None
    breach_level: int | None = None
    starvation_level: int | None = None
    disease_level: int | None = None
    desertion_count: int | None = None
    stalemate_count: int | None = None


@dataclass(frozen=True, slots=True)
class PhaseEventStep:
    can_advance: bool | None
    normal_prepared_work_raw: int | None
    total_apply_raw: int | None
    phase_due: bool | None
    selected_event: PhaseEvent | None = None
    total_event_raw: int | None = None
    total_post_raw: int | None = None


@dataclass(frozen=True, slots=True)
class PhaseEventRules:
    breach_phase_adjustments_raw: tuple[int, ...]
    starvation_fractions_raw: tuple[int, ...]
    disease_daily_additions_raw: tuple[int, ...]
    desertion_work_raw: int
    origin: str


def stock_phase_event_rules() -> PhaseEventRules:
    """Explicit conditional installed-stock scenario, not loaded runtime rules."""
    return PhaseEventRules((-10000, -30000), (5000, 15000), (10000, 20000),
                           500000, "conditional_installed_stock_12003_not_runtime_effective")


def _mul(a: int, b: int) -> int:
    product = a * b
    return (abs(product) // SCALE) * (-1 if product < 0 else 1)


def adapt_current_phase_event_state(active_siege: Mapping[str, Any]) -> CurrentPhaseEventState:
    """Consume normalized actual state; unavailable individual scalars stay None.

    Loaded rule vector lengths may exceed stock two. Preserve observed levels
    above two instead of clamping them or turning them into an unavailable read.
    prepared_selected_phase_event_enum is intentionally not read as a selection.
    """
    measurement = active_siege.get("current_work")
    work = measurement.get("raw") if isinstance(measurement, Mapping) else None
    values = active_siege.get("phase_event_state")
    fields = values if isinstance(values, Mapping) else {}
    return CurrentPhaseEventState(work, active_siege.get("phase_counter"),
                                  fields.get("breach_level"), fields.get("starvation_level"),
                                  fields.get("disease_level"), fields.get("desertion_count"),
                                  fields.get("stalemate_count"))


def _missing(output: dict[str, Any], name: str) -> dict[str, Any]:
    output.update(status="unavailable", first_input_gap=name)
    return output


def _completion(work: int, total_post: int | None) -> bool | None:
    return work >= total_post if total_post is not None else None


def apply_current_phase_event(
    state: CurrentPhaseEventState, step: PhaseEventStep, *,
    rules: PhaseEventRules | None = None,
) -> dict[str, Any]:
    """Ordered finite normal-apply plus one explicit conditional event writer."""
    output: dict[str, Any] = {
        "scope_kind": "caller_selected_conditional_current_phase_event",
        "state_before": asdict(state), "state_after": None,
        "rules_origin": rules.origin if rules is not None else "unknown",
        "selection_origin": "explicit_caller_selected" if step.selected_event is not None else "unknown",
        "actual_selected_event_claimed": False, "rng_replay": "unknown",
        "outer_scheduler": "unknown", "complete_transition": False,
        "completion_date_prediction": None, "completion": None,
        "event_applied": False, "scale": SCALE,
    }
    if step.can_advance is None:
        return _missing(output, "can_advance")
    if not step.can_advance:
        output.update(status="blocked", state_after=asdict(state),
                      work_after_raw=state.current_work_raw,
                      native_stops_active_assault=True)
        return output
    if step.normal_prepared_work_raw is None:
        return _missing(output, "normal_prepared_work_raw")
    if step.total_apply_raw is None:
        return _missing(output, "total_apply_raw")
    counter = state.phase_counter + 1 if state.phase_counter is not None else None
    work = min(step.normal_prepared_work_raw, step.total_apply_raw)
    normal = replace(state, current_work_raw=work, phase_counter=counter)
    output.update(normal_applied_work_raw=work, state_after_normal=asdict(normal))
    if step.normal_prepared_work_raw >= step.total_apply_raw:
        output.update(status="normal_completion", state_after=asdict(normal),
                      work_after_raw=work, completion=True,
                      event_skipped_due_to_normal_completion=True,
                      rng_position_effect="not_advanced_normal_completion")
        return output
    if step.phase_due is None:
        return _missing(output, "phase_due")
    if not step.phase_due:
        output.update(status="no_phase_event", state_after=asdict(normal),
                      work_after_raw=work, completion=_completion(work, step.total_post_raw),
                      rng_position_effect="native_incomplete_branch_advance_position_unknown")
        return output
    if step.selected_event is None:
        output.update(status="event_pending", first_input_gap="caller_selected_event",
                      reason="actual_selected_event_unknown_no_cache_substitution")
        return output
    event = PhaseEvent(step.selected_event)
    name = event.name.lower()
    output.update(selected_event=int(event), selected_event_name=name)
    if event in (PhaseEvent.BREACH, PhaseEvent.STARVATION, PhaseEvent.DISEASE):
        field = name + "_level"
        level = getattr(state, field)
        if level is None:
            return _missing(output, "phase_event_state." + field)
        if rules is None:
            return _missing(output, "supplied_phase_event_rules")
        vector = {PhaseEvent.BREACH: rules.breach_phase_adjustments_raw,
                  PhaseEvent.STARVATION: rules.starvation_fractions_raw,
                  PhaseEvent.DISEASE: rules.disease_daily_additions_raw}[event]
        if level < 0 or level >= len(vector):
            output.update(status="ineligible_selected_event",
                          reason="current_level_reaches_supplied_rule_vector_count",
                          supplied_level_cap=len(vector))
            return output
        updated = replace(normal, **{field: level + 1})
        if event == PhaseEvent.BREACH:
            output["future_breach_phase_adjustment_raw"] = vector[level]
            output["selector_support"] = "unknown_breach_eligible_weight_not_supplied"
        if event == PhaseEvent.DISEASE:
            output["future_disease_daily_addition_raw"] = vector[level]
            output["same_tick_prepared_daily_rewritten"] = False
    else:
        field = name + "_count"
        count = getattr(state, field)
        updated = replace(normal, **{field: count + 1 if count is not None else None})
    # The level/count increments and history append precede the fresh reward
    # total getter. Missing reward operands need not hide that known prefix.
    output["state_after_level_increment"] = asdict(updated)
    output["history_effect"] = "native_append_after_increment_actual_ring_unknown"
    if event in (PhaseEvent.STARVATION, PhaseEvent.DESERTION):
        if step.total_event_raw is None:
            return _missing(output, "total_event_raw")
        if rules is None:
            return _missing(output, "supplied_phase_event_rules")
        bonus = (_mul(step.total_event_raw, rules.starvation_fractions_raw[state.starvation_level])
                 if event == PhaseEvent.STARVATION else rules.desertion_work_raw)
        work = min(work + bonus, step.total_event_raw)
        updated = replace(updated, current_work_raw=work)
        output.update(event_bonus_raw=bonus, total_event_raw=step.total_event_raw)
    else:
        output["event_bonus_raw"] = 0
    updated = replace(updated, phase_counter=0)
    output.update(status="conditional_event_applied", state_after=asdict(updated),
                  work_after_raw=work, event_applied=True,
                  completion=_completion(work, step.total_post_raw),
                  total_post_raw=step.total_post_raw,
                  rng_position_effect="native_incomplete_branch_advance_position_unknown",
                  post_total_reclamped_work=False)
    # Native post-total block only compares. A lower post total can yield
    # C > T_post; it does not cause another C assignment or clamp.
    if step.total_post_raw is None:
        output["completion_input_gap"] = "total_post_raw"
    return output


def apply_selected_phase_sequence(
    state: CurrentPhaseEventState, steps: Sequence[PhaseEventStep], *,
    rules: PhaseEventRules | None = None,
) -> dict[str, Any]:
    """At most two explicit conditional steps; no invented intervening ticks."""
    if not 1 <= len(steps) <= 2:
        raise ValueError("supply one or two explicitly conditioned steps")
    results = []
    current = state
    unknown_continuation = False
    for step in steps:
        result = apply_current_phase_event(current, step, rules=rules)
        results.append(result)
        after = result["state_after"]
        if after is None or result["completion"] is True or result["status"] == "blocked":
            break
        unknown_continuation |= result["completion"] is None and len(results) < len(steps)
        current = CurrentPhaseEventState(**after)
    return {"scope_kind": "maximum_two_caller_selected_conditional_steps", "steps": results,
            "intervening_inputs": "separately_explicit_no_time_or_rng_forecast",
            "continuation_with_unknown_completion": unknown_continuation and len(results) > 1,
            "actual_selected_event_claimed": False, "completion_date_prediction": None}


def _step_from_mapping(value: Mapping[str, Any]) -> PhaseEventStep:
    selected = value.get("selected_event")
    return PhaseEventStep(value.get("can_advance"), value.get("normal_prepared_work_raw"),
                          value.get("total_apply_raw"), value.get("phase_due"),
                          PhaseEvent(selected) if selected is not None else None,
                          value.get("total_event_raw"), value.get("total_post_raw"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    value = json.loads(args.input.read_text(encoding="utf-8-sig"))
    row = value["holding_row"]
    siege = row.get("active_siege")
    if row.get("siege_observable") is not True:
        result = {"status": "unavailable", "first_input_gap": "holding_row.siege_observable"}
    elif siege is None:
        result = {"status": "not_applicable", "reason": "no_current_siege"}
    else:
        state = adapt_current_phase_event_state(siege)
        supplied = value.get("rules")
        rules = (PhaseEventRules(tuple(supplied["breach_phase_adjustments_raw"]),
                                tuple(supplied["starvation_fractions_raw"]),
                                tuple(supplied["disease_daily_additions_raw"]),
                                supplied["desertion_work_raw"], supplied["origin"])
                 if supplied is not None else stock_phase_event_rules()
                 if value.get("rules_source") == "stock_conditional_12003" else None)
        steps = [_step_from_mapping(item) for item in value.get("steps", [value.get("step", {})])]
        result = apply_selected_phase_sequence(state, steps, rules=rules)
        result["observed_identity"] = {"province_id": row.get("province_id"),
                                      "siege_id": siege.get("siege_id")}
        result["prepared_selected_phase_event_enum"] = siege.get("prepared_selected_phase_event_enum")
        result["prepared_selection_interpretation"] = "last_prepare_cache_not_implicit_future_draw"
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
