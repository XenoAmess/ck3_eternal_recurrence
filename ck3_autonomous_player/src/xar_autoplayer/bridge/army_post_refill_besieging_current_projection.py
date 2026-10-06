"""Fixed-context besieging current and assault loss after an explicit overlay."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_full_land_supply_rate_projection import _native_fixed_div, _trunc0, _wrap64
from .army_regiment_refresh_projection import project_observed_raised_regiment_refresh

Q = 100000


def _wrap32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _merged_physical(
    occurrences: list, selected_physical_chunks: list | None,
) -> tuple[list[dict], int]:
    """Keep unchanged captured physical slots and overlay selected final values.

    An unavailable selected slot replaces its initial observation, because a
    missing derived value cannot stand for an unchanged physical identity.
    """
    physical = {}
    for occurrence in occurrences:
        if occurrence["eligible"] is not True:
            continue
        for regiment in occurrence["regiments"]:
            data = regiment["replenishment_records_v1"]
            if not isinstance(data, Mapping):
                continue
            for record in data["records"]:
                key = (record["persistent_regiment_id"], record["chunk_index"])
                ready = (record["status"] == "available" and
                         type(record["current_soldiers"]) is int and
                         type(record["maximum_soldiers"]) is int)
                observed = {
                    "persistent_regiment_id": key[0], "chunk_index": key[1],
                    "current_soldiers": record["current_soldiers"] if ready else None,
                    "maximum_soldiers": record["maximum_soldiers"] if ready else None,
                    "status": "available" if ready else "unavailable",
                    "input_basis": "unchanged_observed_besieging_DATA_physical_slot",
                }
                if key not in physical or physical[key]["status"] != "available":
                    physical[key] = observed
    selected_keys = set()
    for selected in selected_physical_chunks or []:
        key = (selected["persistent_regiment_id"], selected["chunk_index"])
        overlay = deepcopy(dict(selected))
        overlay["input_basis"] = "explicit_selected_refill_final_physical_slot"
        if selected.get("status") != "available":
            overlay.update(current_soldiers=None, maximum_soldiers=None)
        physical[key] = overlay
        selected_keys.add(key)
    return list(physical.values()), len(selected_keys)


def _assault_projection(family: Mapping, conditional_b: int | None) -> dict:
    """Apply the held25205C0 zero branches and signed fixed/whole arithmetic."""
    context = family["assault_context"]
    result = {
        "ready": False, "conditional_expected_loss": None, "zero_basis": None,
        "casualty_percentage_index": None, "casualty_percentage_raw": None,
        "wrapped_product_raw": None, "percentage_divisor_raw": 100 * Q,
        "divided_raw": None, "division_path": None, "missing_inputs": [],
    }

    def zero(basis):
        return {**result, "ready": True, "conditional_expected_loss": 0,
                "zero_basis": basis}

    # The early unavailable DTO uses -1 as unreadable metadata. It does not
    # prove that25205C0 reached its resolved invalid-Province zero branch.
    if family["province_id"] == -1 and family["status"] != "unavailable":
        return zero("no_valid_Province")
    if type(conditional_b) is int and conditional_b <= 0:
        return zero("nonpositive_conditional_B")
    if context["has_active_siege"] is False:
        return zero("no_active_Siege")
    breach = context["breach_level_raw"]
    count = context["casualty_percentage_count"]
    if type(breach) is int and type(count) is int:
        index = breach - 1
        result["casualty_percentage_index"] = index
        if index < 0 or index >= count:
            return zero("breach_index_outside_loaded_table")
    else:
        result["missing_inputs"].append("captured_breach_and_casualty_table_count")
    if context["has_active_siege"] is not True:
        result["missing_inputs"].append("captured_active_Siege")
    if conditional_b is None:
        result["missing_inputs"].append("conditional_besieging_strength")
    percentage = context["casualty_percentage_raw"]
    if type(percentage) is not int:
        result["missing_inputs"].append("captured_indexed_casualty_percentage_raw")
    if result["missing_inputs"]:
        return result
    # Held25205C0: native signed64 multiplication, fixed divide by100Q,
    # then whole truncation byQ and low32. No extra positive clamp exists.
    product = _wrap64(conditional_b * percentage)
    divided, path = _native_fixed_div(product, 100 * Q)
    whole = _wrap32(_trunc0(divided, Q))
    return {**result, "ready": True, "conditional_expected_loss": whole,
            "casualty_percentage_raw": percentage, "wrapped_product_raw": product,
            "divided_raw": divided, "division_path": path}


def project_post_refill_besieging_current_v1(
    army: Mapping[str, object], *, selected_physical_chunks: list | None = None,
) -> dict[str, object]:
    """Recount flags0 occurrences using selected final physical values once.

    The current admission, Province, breach and loaded percentage are captured
    premises. This executes no refill ADD and observes no actual after state.
    DATA, ArRg and Province repetitions retain their native count effects.
    """
    result = {
        "projection_kind": "conditional_post_refill_besieging_current",
        "source_contract_game_version": "1.20.0.3", "army_id": army.get("army_id"),
        "native_carmy_id": army.get("native_carmy_id"), "status": "unavailable",
        "input_basis": "explicit_selected_final_physical_overlay_and_unchanged_DATA; "
                       "fixed_captured_flags0_besieging_admission_and_assault_context",
        "native_besieging_strength": None, "native_besieging_strength_ready": False,
        "native_assault_expected_loss": None, "native_assault_expected_loss_ready": False,
        "conditional_besieging_strength": None,
        "conditional_besieging_strength_ready": False,
        "conditional_assault_expected_loss": None,
        "conditional_assault_expected_loss_ready": False,
        "contributors_ready": False, "selected_physical_changes_supplied": False,
        "selected_physical_overlay_count": 0, "refill_ADDs_executed": 0,
        "occurrences": [], "merged_physical_chunks": [], "assault_projection": None,
        "missing_inputs": [], "soldiers_scale": 1,
        "actual_replenishment": False, "actual_loss": False, "actual_effects": False,
        "actual_post_stage_current": None, "actual_post_besieging_strength": None,
        "actual_assault_loss": None, "full_regular_refill_ready": False,
        "full_daily_assault_ready": False, "full_monthly_ready": False,
    }
    family = army.get("current_province_besieging_contributors_v1")
    if not isinstance(family, Mapping):
        result["missing_inputs"] = ["current_province_besieging_contributors_v1"]
        return result
    if selected_physical_chunks is not None and not isinstance(selected_physical_chunks, list):
        raise ValueError("selected_physical_chunks must be an explicit list or null")
    physical, overlay_count = _merged_physical(family["occurrences"], selected_physical_chunks)
    count = family["native_province_unit_count"]
    count_known = type(count) is int
    source_empty = count_known and count <= 0 and family["contributors_ready"]
    roster_ready = bool(family["contributors_ready"] and count_known and
                        (count <= 0 or count == len(family["occurrences"])))
    modeled = []
    missing = []
    total = 0
    rows_ready = True
    for occurrence in family["occurrences"]:
        eligible = occurrence["eligible"]
        row = {
            "stored_index": occurrence["stored_index"],
            "public_unit_id": occurrence["public_unit_id"],
            "resolved_unit_id": occurrence["resolved_unit_id"],
            "unit_used_fallback": occurrence["unit_used_fallback"],
            "current_province_id": occurrence["current_province_id"],
            "current_province_used_fallback": occurrence["current_province_used_fallback"],
            "raw_unit18": occurrence["raw_unit18"],
            "raw_unit170": occurrence["raw_unit170"],
            "raw_unit44": occurrence["raw_unit44"],
            "native_carmy_id": occurrence["native_carmy_id"],
            "army_used_fallback": occurrence["army_used_fallback"],
            "eligible": eligible,
            "native_whole_current_soldiers": occurrence["native_whole_current_soldiers"],
            "conditional_ready": False, "conditional_whole_current_soldiers": None,
            "regiments": [], "missing_inputs": [],
        }
        if eligible is False:
            row.update(conditional_ready=True, conditional_whole_current_soldiers=0)
        elif eligible is None:
            row["missing_inputs"] = ["captured_native_besieging_admission"]
        else:
            current_sum = 0
            regiments_ready = bool(occurrence["available"])
            if not regiments_ready:
                row["missing_inputs"].append("complete_captured_admitted_ArRg_roster")
            for regiment in occurrence["regiments"]:
                data = regiment["replenishment_records_v1"]
                if isinstance(data, Mapping):
                    refresh = project_observed_raised_regiment_refresh(
                        data, physical_chunks_after=physical)
                else:
                    refresh = {"current_maximum_ready": False,
                               "missing_inputs": ["complete_captured_besieging_DATA"]}
                ready = refresh["current_maximum_ready"]
                projected = {
                    "stored_index": regiment["stored_index"],
                    "army_regiment_id": regiment["army_regiment_id"],
                    "current_soldiers_before": regiment["current_soldiers"],
                    "maximum_soldiers_before": regiment["maximum_soldiers"],
                    "conditional_ready": ready,
                    "conditional_current_soldiers": refresh["current_soldiers"] if ready else None,
                    "conditional_maximum_soldiers": refresh["maximum_soldiers"] if ready else None,
                    "refresh": refresh,
                }
                row["regiments"].append(projected)
                if ready:
                    current_sum = _wrap32(current_sum + refresh["current_soldiers"])
                else:
                    regiments_ready = False
                    row["missing_inputs"].append({
                        "regiment_stored_index": regiment["stored_index"],
                        "army_regiment_id": regiment["army_regiment_id"],
                        "inputs": refresh["missing_inputs"],
                    })
            if selected_physical_chunks is None and occurrence["regiments"]:
                regiments_ready = False
                row["missing_inputs"].append("explicit_selected_final_physical_changes")
            if regiments_ready:
                row.update(conditional_ready=True,
                           conditional_whole_current_soldiers=current_sum)
        if row["conditional_ready"]:
            total = _wrap32(total + row["conditional_whole_current_soldiers"])
        else:
            rows_ready = False
            missing.append({"province_stored_index": occurrence["stored_index"],
                            "public_unit_id": occurrence["public_unit_id"],
                            "inputs": row["missing_inputs"]})
        modeled.append(row)
    if not roster_ready:
        missing.append("complete_captured_Province_original_occurrence_roster")
    b_ready = bool(source_empty or (roster_ready and rows_ready))
    conditional_b = 0 if source_empty else total if b_ready else None
    assault = _assault_projection(family, conditional_b)
    if assault["missing_inputs"]:
        missing.append({"stage": "conditional_assault_expected_loss",
                        "inputs": assault["missing_inputs"]})
    native_b = family["native_besieging_strength"]
    native_loss = family["native_assault_expected_loss"]
    ready = b_ready and assault["ready"]
    any_ready = b_ready or assault["ready"] or native_b is not None or native_loss is not None
    return {
        **result, "status": "available" if ready else "partial" if any_ready else "unavailable",
        "province_id": family["province_id"], "native_province_unit_count": count,
        "native_observation_status": family["status"],
        "native_observation_unavailable_reason": family["unavailable_reason"],
        "native_besieging_strength": native_b, "native_besieging_strength_ready": native_b is not None,
        "native_assault_expected_loss": native_loss,
        "native_assault_expected_loss_ready": native_loss is not None,
        "contributors_ready": family["contributors_ready"],
        "conditional_besieging_strength": conditional_b,
        "conditional_besieging_strength_ready": b_ready,
        "conditional_assault_expected_loss": assault["conditional_expected_loss"],
        "conditional_assault_expected_loss_ready": assault["ready"],
        "selected_physical_changes_supplied": selected_physical_chunks is not None,
        "selected_physical_overlay_count": overlay_count,
        "merged_physical_chunks": physical, "occurrences": modeled,
        "assault_projection": assault, "missing_inputs": missing,
    }
