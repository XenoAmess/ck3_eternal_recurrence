"""Finite .3 siege-work projection from one observed, frozen current condition.

This module uses files and supplied numbers only. It neither calls native code
nor predicts the next native besieger selection, event draw, engine clock,
war-score/occupation side effects, or a completion date. Effective character
0x11D is one phase term; it never multiplies ordinary daily work.
"""
from __future__ import annotations

import argparse
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCALE = 100000
PHASE_TERMS = (
    "breach_adjust_raw", "siege_phase_time_modifier_raw",
    "siege_cached_phase_time_modifier_raw", "province_phase_time_modifier_raw",
)
SAME_CAP_EXTENSION = {
    "mcp": "ck3_query_war_occupation_targets_v1",
    "reader": "ReadObjectiveProvince(...,rich=true), existing alive Siege",
    "fields": ["ordinary_daily_progress", "current_phase_length", "phase_counter",
               "can_advance", "internal_besieging_army_id", "actual_siege_commander_id"],
}


def _integer(value: Any, name: str, *, nonnegative: bool = False) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer or unavailable")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _measurement(value: Any, name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or value.get("scale") != SCALE:
        raise ValueError(f"{name} must be an observed Q100000 measurement")
    return _integer(value.get("raw"), f"{name}.raw", nonnegative=True)


def fixed_mul(a: int, b: int) -> int:
    """Native finite fixed-point multiplication, truncated toward zero."""
    product = a * b
    return (abs(product) // SCALE) * (-1 if product < 0 else 1)


def ceil_fixed_nonnegative(raw: int) -> int:
    if raw < 0:
        raise ValueError("phase length must be nonnegative")
    return raw // SCALE + int(raw % SCALE != 0)


def ordinary_daily_work_from_terms(
    *, army_progress_raw: int, maa_progress_raw: int,
    excess_strength_progress_raw: int, conditional_additive_raw: int,
    daily_multiplier_raw: int, fort_factor_raw: int,
) -> int:
    """Explicit complete terms only; preserve each native multiply and clamp."""
    base = (SCALE + army_progress_raw + maa_progress_raw
            + excess_strength_progress_raw + conditional_additive_raw)
    return max(50000, fixed_mul(fixed_mul(base, daily_multiplier_raw), fort_factor_raw))


def phase_length_from_terms(terms: Mapping[str, Any]) -> dict[str, Any]:
    """Effective 0x11D already includes character traits/XP; add it once."""
    values = [_integer(terms.get(name), name) for name in PHASE_TERMS]
    missing = [name for name, value in zip(PHASE_TERMS, values) if value is None]
    if missing:
        return {"status": "unavailable", "missing_inputs": missing,
                "phase_factor_raw": None, "phase_length_raw": None,
                "phase_threshold": None}
    factor = max(0, SCALE + sum(values))
    length = fixed_mul(20 * SCALE, factor)
    return {"status": "available", "missing_inputs": [],
            "phase_factor_raw": factor, "phase_length_raw": length,
            "phase_threshold": ceil_fixed_nonnegative(length)}


@dataclass(frozen=True, slots=True)
class CurrentSiegeCondition:
    holding_row: Mapping[str, Any]
    tick_operands: Mapping[str, Any]
    operand_origin: str
    commander_phase_observation: Mapping[str, Any] | None
    snapshot_revision: int | None
    observed_date_raw: int | None


def adapt_current_siege_condition(
    holding_row: Mapping[str, Any], *, snapshot_revision: int | None = None,
    observed_date_raw: int | None = None,
    tick_operands: Mapping[str, Any] | None = None,
    commander_phase_observation: Mapping[str, Any] | None = None,
) -> CurrentSiegeCondition:
    """Read a normalized occupation row; retain supplied operands separately.

    commander_phase_observation is explanatory input only. It cannot create a
    Siege, fill other phase terms, or be joined to an unobserved Siege commander.
    With no tick_operands, use only the same active_siege native measurements.
    An explicit tick_operands mapping selects a separate caller-supplied branch;
    it never silently fills an unavailable native measurement.
    """
    siege = holding_row.get("active_siege")
    native = {}
    if isinstance(siege, Mapping):
        native = {
            "ordinary_daily_work_raw": _measurement(
                siege.get("ordinary_daily_progress"), "active_siege.ordinary_daily_progress"),
            "phase_length_raw": _measurement(
                siege.get("current_phase_length"), "active_siege.current_phase_length"),
            "phase_counter": siege.get("phase_counter"),
            "native_can_advance": siege.get("can_advance"),
        }
    return CurrentSiegeCondition(
        copy.deepcopy(dict(holding_row)),
        copy.deepcopy(dict(tick_operands)) if tick_operands is not None else native,
        "explicit_caller_supplied" if tick_operands is not None else "observed_active_siege_native_fields",
        copy.deepcopy(dict(commander_phase_observation))
        if commander_phase_observation is not None else None,
        snapshot_revision, observed_date_raw,
    )


def _gap(output: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    output.update(status="unavailable", missing_inputs=missing,
                  first_runtime_input_gap=missing[0],
                  same_cap_extension=copy.deepcopy(SAME_CAP_EXTENSION))
    return output


def _selected_event(
    enum: int, work: int, total: int, operands: Mapping[str, Any],
) -> dict[str, Any]:
    """Conditional fixture branch; never supplies or replays a native draw."""
    names = ("breach", "starvation", "disease", "desertion", "stalemate")
    if enum not in range(5):
        raise ValueError("selected_event_raw must be native event enum 0..4")
    result: dict[str, Any] = {"event": names[enum], "selected_event_raw": enum,
                              "selection_origin": "explicit_caller_supplied",
                              "extra_work_raw": 0, "projected_work_raw": work}
    if enum in (0, 1, 2):
        field = ("breach_level", "starvation_level", "disease_level")[enum]
        level = _integer(operands.get(field), field, nonnegative=True)
        if level is None:
            return {**result, "status": "unavailable", "missing_inputs": [field]}
        if level >= 2:
            raise ValueError("native selector excludes capped breach/starvation/disease")
        result["new_level"] = level + 1
        if enum == 0:
            result["next_breach_adjust_raw"] = -10000 if level == 0 else -30000
        if enum == 2:
            result["future_daily_multiplier_addition_raw"] = 10000 if level == 0 else 20000
    if enum in (1, 3):
        event_total = _integer(operands.get("event_total_work_raw"),
                               "event_total_work_raw", nonnegative=True)
        if event_total is None:
            return {**result, "status": "unavailable",
                    "missing_inputs": ["event_total_work_raw"]}
        extra = (fixed_mul(event_total, 5000 if result["new_level"] == 1 else 15000)
                 if enum == 1 else 5 * SCALE)
        result.update(extra_work_raw=extra,
                      projected_work_raw=min(work + extra, event_total),
                      event_total_work_raw=event_total,
                      completion_at_supplied_event_total=(work + extra >= event_total))
    result.update(status="available", missing_inputs=[])
    # History, RNG position, dynamic post-event total and occupation are outside
    # this finite work projection. No claim of a full native transition follows.
    return result


def run_current_siege_tick(condition: CurrentSiegeCondition) -> dict[str, Any]:
    """One current-condition prepare/apply work projection, with no time loop."""
    row, operands = condition.holding_row, condition.tick_operands
    output: dict[str, Any] = {
        "scope_kind": "frozen_observed_current_siege_single_prepare_apply_work",
        "readiness": "offline_projection_pending_actual_qualification",
        "observed_frame": {"snapshot_revision": condition.snapshot_revision,
                           "observed_date_raw": condition.observed_date_raw,
                           "province_id": row.get("province_id"),
                           "holding_title_id": row.get("holding_title_id")},
        "operand_origin": condition.operand_origin,
        "commander_phase_observation": copy.deepcopy(condition.commander_phase_observation),
        "actual_next_draw_claimed": False, "complete_transition": False,
        "outer_scheduler": "unknown", "rng_replay": "unknown",
        "completion_date_prediction": None,
    }
    if row.get("siege_observable") is not True:
        return _gap(output, ["holding_row.siege_observable"])
    siege = row.get("active_siege")
    if siege is None:
        output.update(status="not_applicable", reason="no_current_siege")
        return output
    output["observed_frame"]["siege_id"] = siege.get("siege_id")
    output["observed_native_eta_days"] = siege.get("days_left")
    output["eta_interpretation"] = "current_native_estimate_only"
    output["observed_prepared_phase_length"] = copy.deepcopy(siege.get("prepared_phase_length"))
    for name, observed in (("siege_id", siege.get("siege_id")),
                           ("province_id", row.get("province_id"))):
        if operands.get(name) is not None and operands[name] != observed:
            raise ValueError(f"supplied {name} differs from observed current Siege")
    if condition.operand_origin == "explicit_caller_supplied":
        output["bound_current_besieger"] = {
            name: operands.get(name) for name in ("internal_besieging_army_id", "actual_siege_commander_id")
        }
    else:
        output["bound_current_besieger"] = {
            "besieging_army_id": siege.get("besieging_army_id"),
            "binding_source": "same_alive_Siege_native_reader_current_internal_army_plus_0x208",
        }
    current = _measurement(siege.get("current_work"), "active_siege.current_work")
    total = _measurement(siege.get("total_work"), "active_siege.total_work")
    missing = [name for name, value in (("active_siege.current_work", current),
                                       ("active_siege.total_work", total)) if value is None]
    if missing:
        return _gap(output, missing)
    can_advance = operands.get("native_can_advance")
    if can_advance is None:
        return _gap(output, ["active_siege.can_advance" if condition.operand_origin ==
                             "observed_active_siege_native_fields" else "native_can_advance"])
    if not isinstance(can_advance, bool):
        raise ValueError("native_can_advance must be boolean or unavailable")
    counter = _integer(operands.get("phase_counter"), "phase_counter", nonnegative=True)
    output.update(current_work_raw=current, current_total_work_raw=total,
                  phase_counter_before=counter, scale=SCALE)
    if not can_advance:
        output.update(status="blocked", projected_work_raw=current,
                      projected_phase_counter=counter, normal_work_applied=False,
                      native_stops_active_assault=True)
        return output
    assault = siege.get("assault_in_progress")
    output["observed_assault_in_progress"] = assault
    output["assault_side_effects"] = "outside_finite_normal_work_scope"
    if assault is True:
        output.update(status="not_applicable", reason="active_assault_outside_normal_work_scope")
        return output
    # The sealed supplement gives phase -> blocked -> due/event cache -> D.
    # All these values describe pre-event state. +0x20 is a last-prepare cache,
    # not a substitute for a fresh current phase getter after commander changes.
    length = _integer(operands.get("phase_length_raw"), "phase_length_raw", nonnegative=True)
    if length is None and condition.operand_origin == "explicit_caller_supplied":
        phase = phase_length_from_terms(operands.get("phase_terms") or {})
        output["supplied_phase_calculation"] = phase
        length = phase["phase_length_raw"]
    daily = _integer(operands.get("ordinary_daily_work_raw"),
                     "ordinary_daily_work_raw", nonnegative=True)
    missing = [name for name, value in (("ordinary_daily_work_raw", daily),
                                       ("phase_counter", counter),
                                       ("current_phase_length_raw_or_complete_phase_terms", length))
               if value is None]
    if missing:
        if condition.operand_origin == "observed_active_siege_native_fields":
            paths = {"ordinary_daily_work_raw": "active_siege.ordinary_daily_progress",
                     "phase_counter": "active_siege.phase_counter",
                     "current_phase_length_raw_or_complete_phase_terms": "active_siege.current_phase_length"}
            missing = [paths[name] for name in missing]
        return _gap(output, missing)
    threshold = ceil_fixed_nonnegative(length)
    due = counter + 1 >= threshold
    prepared = current + daily
    applied = min(prepared, total)
    normal_complete = prepared >= total
    output.update(ordinary_daily_work_raw=daily, current_phase_length_raw=length,
                  phase_threshold=threshold, phase_due=due,
                  prepared_next_work_raw=prepared, normal_applied_work_raw=applied,
                  normal_work_applied=True, normal_completion=normal_complete)
    if normal_complete or not due:
        output.update(status="projected", projected_work_raw=applied,
                      projected_phase_counter=counter + 1, event_pending=False,
                      event_skipped_due_to_normal_completion=normal_complete and due)
        return output
    selected = _integer(operands.get("selected_event_raw"), "selected_event_raw")
    if selected is None:
        output.update(status="event_pending", projected_work_raw=None,
                      projected_phase_counter=None, event_pending=True,
                      first_runtime_input_gap="native_prepared_selected_event_raw",
                      reason="deterministic_pre_event_work_only_actual_draw_unknown")
        return output
    event = _selected_event(selected, applied, total, operands)
    output["conditional_supplied_event"] = event
    if event["status"] != "available":
        output.update(event_pending=True)
        return _gap(output, event["missing_inputs"])
    output.update(status="projected_selected_event", event_pending=False,
                  projected_work_raw=event["projected_work_raw"],
                  projected_phase_counter=0,
                  actual_post_event_completion="unknown_dynamic_total_not_replayed")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="local JSON with normalized holding_row and optional supplied operands")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    value = json.loads(args.input.read_text(encoding="utf-8-sig"))
    condition = adapt_current_siege_condition(
        value["holding_row"], snapshot_revision=value.get("snapshot_revision"),
        observed_date_raw=value.get("observed_date_raw"),
        tick_operands=value.get("tick_operands"),
        commander_phase_observation=value.get("commander_phase_observation"),
    )
    rendered = json.dumps(run_current_siege_tick(condition), ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
