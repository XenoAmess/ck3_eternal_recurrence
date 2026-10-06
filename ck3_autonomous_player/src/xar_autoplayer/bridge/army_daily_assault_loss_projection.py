"""Sequential current daily assault requests with target-only cached refresh."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .army_chunk_loss_writeback_projection import project_observed_writer_chunk_changes
from .army_daily_assault_active_table_projection import project_current_daily_assault_group_inputs_v1
from .army_loss_allocation_projection import _signed_i32, _truncate_toward_zero
from .army_full_land_supply_rate_projection import _native_fixed_div, _trunc0, _wrap64

Q = 100000


def _assault(group: Mapping, family: Mapping, current_b: int | None) -> dict:
    """Use the group's actual Province magic and actual Siege table operands."""
    context = family["assault_context"]
    result = {"ready": False, "conditional_expected_loss": None, "zero_basis": None,
              "wrapped_product_raw": None, "divided_raw": None, "division_path": None,
              "missing_inputs": []}
    if type(current_b) is int and current_b <= 0:
        return {**result, "ready": True, "conditional_expected_loss": 0,
                "zero_basis": "nonpositive_conditional_B"}
    if context["has_active_siege"] is False:
        return {**result, "ready": True, "conditional_expected_loss": 0,
                "zero_basis": "no_active_group_Siege"}
    breach = context["breach_level_raw"]
    count = context["casualty_percentage_count"]
    if type(breach) is int and type(count) is int and (breach - 1 < 0 or breach - 1 >= count):
        return {**result, "ready": True, "conditional_expected_loss": 0,
                "zero_basis": "breach_index_outside_loaded_table"}
    if group["province_magic_raw_u32"] != 0x50726F76:
        result["missing_inputs"].append("actual_group_Province_magic_85C")
    if type(current_b) is not int:
        result["missing_inputs"].append("conditional_group_B")
    if context["has_active_siege"] is not True:
        result["missing_inputs"].append("captured_actual_group_Siege")
    if type(breach) is not int or type(count) is not int:
        result["missing_inputs"].append("actual_group_breach_and_loaded_percentage_count")
    percentage = context["casualty_percentage_raw"]
    if type(percentage) is not int:
        result["missing_inputs"].append("actual_group_indexed_percentage_raw")
    if result["missing_inputs"]:
        return result
    product = _wrap64(current_b * percentage)
    divided, path = _native_fixed_div(product, 100 * Q)
    return {**result, "ready": True,
            "conditional_expected_loss": _signed_i32(_trunc0(divided, Q)),
            "wrapped_product_raw": product, "divided_raw": divided, "division_path": path}


def _key(row: Mapping) -> str | None:
    resolution = row.get("resolution")
    if not isinstance(resolution, Mapping) or resolution.get("ready") is not True:
        return None
    return resolution.get("object_identity")


def _selected_id(row: Mapping) -> int | None:
    resolution = row.get("resolution")
    if isinstance(resolution, Mapping) and resolution.get("ready") is True:
        value = resolution.get("selected_full_id_u32")
        return _signed_i32(value) if type(value) is int else None
    return None


def _same_resolution(left: Mapping, right: Mapping) -> bool:
    return (_key(left) is not None and _key(left) == _key(right) and
            _selected_id(left) == _selected_id(right))


def _cached_changes(cache: dict) -> dict:
    return {key: _signed_i32(row["current_soldiers"] - row["initial_current_soldiers"])
            for key, row in cache.items()
            if type(row["current_soldiers"]) is int and
            type(row["initial_current_soldiers"]) is int and
            row["current_soldiers"] != row["initial_current_soldiers"]}


def _group_budget(group: Mapping, changes: dict, ids: dict) -> dict:
    """Recount captured B multiplicity from cached deltas, never from DATA."""
    native = group["native_current_expected_loss"]
    result = {"ready": False, "expected_loss": None, "basis": None,
              "conditional_besieging_strength": None, "B_unchanged_proven": not changes,
              "B_delta_occurrences": [], "assault_projection": None, "missing_inputs": []}
    magic = group["province_magic_raw_u32"]
    if type(magic) is int and magic != 0x50726F76:
        return {**result, "ready": True, "expected_loss": 0,
                "basis": "source_invalid_Province_magic"}
    family = group["besieging_inputs_v1"]
    if not changes and type(native) is int:
        return {**result, "ready": True, "expected_loss": native,
                "conditional_besieging_strength": family["native_besieging_strength"] if isinstance(family, Mapping) else None,
                "basis": "native_current_scalar_with_unchanged_B"}
    if not isinstance(family, Mapping):
        return {**result, "missing_inputs": ["captured_group_Province_B_and_actual_Siege_context"]}
    baseline = family["native_besieging_strength"]
    complete = family["contributors_ready"] is True
    count = family["native_province_unit_count"]
    complete = complete and type(count) is int and (count <= 0 or count == len(family["occurrences"]))
    delta = 0
    witnesses = []
    if complete:
        for occurrence in family["occurrences"]:
            if occurrence["eligible"] is False:
                continue
            if occurrence["eligible"] is not True:
                complete = False
                break
            for regiment in occurrence["regiments"]:
                identity = regiment["army_regiment_id"]
                key = ids.get(identity)
                difference = changes.get(key, 0)
                delta = _signed_i32(delta + difference)
                witnesses.append({"province_stored_index": occurrence["stored_index"],
                    "regiment_stored_index": regiment["stored_index"],
                    "army_regiment_id": identity, "cached_current_delta_i32": difference})
    unchanged = complete and delta == 0
    conditional_b = _signed_i32(baseline + delta) if complete and type(baseline) is int else None
    result.update(B_unchanged_proven=unchanged, B_delta_occurrences=witnesses,
                  conditional_besieging_strength=conditional_b)
    # Only arithmetic and zero branches are reused; the overlay API which
    # refreshes every admitted ArRg is deliberately not this caller.
    arithmetic = _assault(group, family, conditional_b)
    result["assault_projection"] = arithmetic
    if arithmetic["ready"]:
        return {**result, "ready": True, "expected_loss": arithmetic["conditional_expected_loss"],
                "basis": "captured_group_B_plus_actual_target_cached_deltas"}
    if unchanged and type(native) is int:
        return {**result, "ready": True, "expected_loss": native,
                "basis": "native_current_scalar_with_proven_unchanged_B"}
    missing = list(arithmetic["missing_inputs"])
    if not complete:
        missing.append("complete_original_group_B_occurrences_to_test_changed_cached_targets")
    return {**result, "missing_inputs": missing}


def project_current_daily_assault_loss_v1(army: Mapping) -> dict:
    """Model an isolated current table invocation, preserving a ready prefix.

    Physical writes evolve across all captured DATA aliases. Only an actual
    modeled writer target receives the2633340 cache refresh. Captured context
    is fixed; no game call, monthly refill, queue append or release executes.
    """
    result = {
        "projection_kind": "conditional_current_daily_assault_loss",
        "source_contract_game_version": "1.20.0.3", "army_id": army.get("army_id"),
        "input_basis": "observed_current_physical_group_order; fixed_actual_group_Siege_context; "
                       "interleaved_writer_and_target_only_cached_refresh",
        "status": "unavailable", "sequential_numeric_ready": False,
        "physical_group_order_ready": False, "completed_group_count": 0,
        "observed_group_count": None, "groups": [], "ordered_queue_append_requests": [],
        "queue_requests_ready": False, "conditional_physical_chunks": [],
        "conditional_regiment_currents": [], "missing_inputs": [],
        "actual_loss": False, "actual_effects": False, "actual_daily_loss": False,
        "actual_post_stage": None, "actual_post_physical_chunks": None,
        "actual_post_regiment_currents": None, "native_writes_executed": 0,
        "full_daily_assault_ready": False, "full_regular_refill_ready": False,
        "full_monthly_ready": False, "full_calendar_ready": False,
        "release_effects_ready": False, "table_clear_effects_ready": False,
    }
    table = army.get("current_daily_assault_table_v1")
    if not isinstance(table, Mapping):
        return {**result, "missing_inputs": ["current_daily_assault_table_v1"]}
    observed = project_current_daily_assault_group_inputs_v1(army)
    order_ready = observed["physical_group_order_ready"]
    result.update(physical_group_order_ready=order_ready, observed_group_count=len(table["groups"]))
    if order_ready and not table["groups"] and table["header"]["occupied_count_raw_i32"] == 0:
        return {**result, "status": "available", "sequential_numeric_ready": True,
                "queue_requests_ready": True}
    inputs = army.get("current_daily_assault_loss_inputs_v1")
    if not isinstance(inputs, Mapping):
        return {**result, "missing_inputs": ["current_daily_assault_loss_inputs_v1"]}

    cache = {}
    targets = {}
    ids = {}
    all_data = []
    for target in inputs["target_regiments"]:
        key = _key(target)
        identity = _selected_id(target)
        if key is None or target["identity_valid"] is not True or identity is None:
            continue
        ids[identity] = key
        if key not in cache:
            cache[key] = {"object_identity": key, "army_regiment_id": identity,
                "initial_current_soldiers": target["current_soldiers"],
                "initial_maximum_soldiers": target["maximum_soldiers"],
                "current_soldiers": target["current_soldiers"],
                "maximum_soldiers": target["maximum_soldiers"]}
        data = deepcopy(target["replenishment_records_v1"])
        if isinstance(data, Mapping):
            all_data.append(data)
        if key not in targets or (targets[key]["data"] is None and data is not None):
            targets[key] = {"source": target, "data": data}
    # Preferred current is already a genuine demanded observation in the
    # table minimum, so it can supply a nullable parallel cache operand.
    for group in table["groups"]:
        for occurrence in group["arrgs"]["occurrences"]:
            key = _key(occurrence)
            identity = _selected_id(occurrence)
            if key is None or occurrence["identity_valid"] is not True or identity is None:
                continue
            ids[identity] = key
            current = occurrence["current_raw_i32"]
            if key not in cache:
                cache[key] = {"object_identity": key, "army_regiment_id": identity,
                    "initial_current_soldiers": current, "current_soldiers": current,
                    "initial_maximum_soldiers": None, "maximum_soldiers": None}
            elif cache[key]["current_soldiers"] is None and type(current) is int:
                cache[key].update(initial_current_soldiers=current, current_soldiers=current)
    for group in inputs["groups"]:
        family = group["besieging_inputs_v1"]
        if isinstance(family, Mapping):
            for occurrence in family["occurrences"]:
                for regiment in occurrence["regiments"]:
                    data = regiment["replenishment_records_v1"]
                    if isinstance(data, Mapping):
                        all_data.append(deepcopy(data))

    physical = {}
    for data in all_data:
        for record in data["records"]:
            key = (record["persistent_regiment_id"], record["chunk_index"])
            if record["status"] == "available":
                physical.setdefault(key, {"persistent_regiment_id": key[0], "chunk_index": key[1],
                    "current_soldiers": record["current_soldiers"],
                    "maximum_soldiers": record["maximum_soldiers"], "state_raw": record["state_raw"]})

    def write(occurrence, quantity):
        key = _key(occurrence)
        target = targets.get(key)
        if target is None:
            return False, {"missing_inputs": ["captured_valid_writer_target_admission_and_DATA"]}
        skipped = target["source"]["native_loss_writer_skipped"]
        if type(skipped) is not bool:
            return False, {"missing_inputs": ["native_loss_writer_skipped"]}
        data = target["data"]
        if skipped and not isinstance(data, Mapping):
            # The native character exit consumes no DATA and requests no
            # refresh. The existing helper needs only this admission row.
            data = {"army_regiment_id": cache[key]["army_regiment_id"],
                    "native_loss_writer_skipped": True, "records": []}
        if not isinstance(data, Mapping):
            return False, {"missing_inputs": ["complete_target_DATA"]}
        strength = {"army_regiment_id": cache[key]["army_regiment_id"],
                    "current_soldiers": cache[key]["current_soldiers"],
                    "maximum_soldiers": cache[key]["maximum_soldiers"]}
        request = {"army_regiment_id": strength["army_regiment_id"],
                   "writer_quantity_raw": quantity * Q, "writer_quantity_scale": Q}
        try:
            projected = project_observed_writer_chunk_changes(
                {"regiment_strengths": [strength], "regiment_replenishment_records_v1": [data]}, request)
        except ArithmeticError:
            return False, {"missing_inputs": ["native_signed_division_defined"]}
        if not projected["chunk_writeback_ready"]:
            return False, projected
        if projected["writer_skipped"]:
            return True, projected
        refresh = projected["conditional_raised_regiment_refresh"]
        if not refresh["current_maximum_ready"]:
            return False, projected
        changed = {(row["persistent_regiment_id"], row["chunk_index"]): row
                   for row in projected["physical_chunks_after"]}
        physical.update(changed)
        for alias in all_data:
            for record in alias["records"]:
                replacement = changed.get((record["persistent_regiment_id"], record["chunk_index"]))
                if replacement is not None:
                    current = replacement["current_soldiers"]
                    maximum = replacement["maximum_soldiers"]
                    record.update(current_soldiers=current, maximum_soldiers=maximum,
                        effective_current_soldiers=maximum if record["state_raw"] == 3 and current == 0 else current)
        cache[key].update(current_soldiers=refresh["current_soldiers"],
                          maximum_soldiers=refresh["maximum_soldiers"])
        return True, projected

    def allocate(group, budget, phase):
        output = {"phase": phase, "ready": False, "denominator_i32": None,
                  "initial_cap_i32": None, "original_overflow_i32": None,
                  "remaining_budget_i32": None, "remaining_denominator_i32": None,
                  "requests": [], "missing_inputs": []}
        vector = group["arrgs"]
        if vector["references_ready"] is not True:
            return {**output, "missing_inputs": ["complete_original_group_ArRg_occurrences"]}
        selected = []
        total = 0
        for occurrence in vector["occurrences"]:
            valid = occurrence["identity_valid"]
            if valid is False:
                continue
            if valid is not True:
                return {**output, "missing_inputs": ["native_ArRg_identity_valid"]}
            if phase == "preferred":
                kind = occurrence["definition_type_raw_i32"]
                if type(kind) is not int:
                    return {**output, "missing_inputs": ["native_definition_type_2a0"]}
                if kind > 0:
                    continue
            key = _key(occurrence)
            current = cache.get(key, {}).get("current_soldiers")
            if type(current) is not int:
                return {**output, "missing_inputs": ["current_cached_valid_group_ArRg"]}
            selected.append(occurrence)
            total = _signed_i32(total + current)
        cap = min(budget, total)
        overflow = _signed_i32(budget - cap)
        remaining = cap
        denominator = total
        output.update(denominator_i32=total, initial_cap_i32=cap, original_overflow_i32=overflow)
        for occurrence in selected:
            # The held inner loop requires both signed values positive. The
            # outer caller's distinct gate is budget == 0, never budget <= 0.
            if remaining <= 0 or denominator <= 0:
                break
            before = cache[_key(occurrence)]["current_soldiers"]
            product = _signed_i32(before * remaining)
            quantity = _truncate_toward_zero(product, denominator)
            request = {"native_index": occurrence["native_index"],
                "raw_full_id_u32": occurrence["raw_full_id_u32"],
                "army_regiment_id": _selected_id(occurrence),
                "current_before_call_i32": before, "remaining_before_i32": remaining,
                "denominator_before_i32": denominator, "wrapped_product_i32": product,
                "requested_loss_soldiers_i32": quantity, "writer_quantity_raw": quantity * Q}
            ready, projected = write(occurrence, quantity)
            request.update(writer_ready=ready, writer_projection=projected)
            output["requests"].append(request)
            if not ready:
                output.update(remaining_budget_i32=remaining, remaining_denominator_i32=denominator,
                              missing_inputs=[{"writer_native_index": occurrence["native_index"],
                                               "inputs": projected["missing_inputs"]}])
                return output
            remaining = _signed_i32(remaining - quantity)
            denominator = _signed_i32(denominator - before)
        return {**output, "ready": True, "remaining_budget_i32": remaining,
                "remaining_denominator_i32": denominator}

    completed = 0
    queues = []
    missing = [] if order_ready else ["complete_current_physical_group_order"]
    alive = order_ready
    groups = []
    for index, table_group in enumerate(table["groups"]):
        source = inputs["groups"][index] if index < len(inputs["groups"]) else None
        out = {"native_index": table_group["native_index"], "physical_slot_i64": table_group["physical_slot_i64"],
               "native_current_expected_loss": source["native_current_expected_loss"] if source else None,
               "native_current_expected_loss_ready": source is not None and type(source["native_current_expected_loss"]) is int,
               "sequential_entry_reached": alive, "numeric_ready": False,
               "conditional_budget": None, "preferred": None, "residual": None,
               "army_counts": [], "queue_requests_ready": False, "missing_inputs": []}
        if source is None or source["native_index"] != table_group["native_index"] or source["physical_slot_i64"] != table_group["physical_slot_i64"]:
            out["missing_inputs"] = ["same_query_loss_group_alignment"]
        elif alive:
            budget = _group_budget(source, _cached_changes(cache), ids)
            out["conditional_budget"] = budget
            if not budget["ready"]:
                out["missing_inputs"] = budget["missing_inputs"]
            else:
                whole = budget["expected_loss"]
                allocation_ready = True
                if whole != 0:
                    preferred = allocate(table_group, whole, "preferred")
                    out["preferred"] = preferred
                    allocation_ready = preferred["ready"]
                    if allocation_ready and preferred["original_overflow_i32"] > 0:
                        residual = allocate(table_group, preferred["original_overflow_i32"], "flags0_residual")
                        out["residual"] = residual
                        allocation_ready = residual["ready"]
                    if not allocation_ready:
                        failed = out["residual"] or preferred
                        out["missing_inputs"] = failed["missing_inputs"]
                out["numeric_ready"] = allocation_ready
                if allocation_ready:
                    army_vector = table_group["armies"]
                    army_ready = army_vector["references_ready"] is True and len(source["army_counts"]) == len(army_vector["occurrences"])
                    changes = _cached_changes(cache)
                    for ordinal, occurrence in enumerate(army_vector["occurrences"]):
                        count_input = source["army_counts"][ordinal] if ordinal < len(source["army_counts"]) else None
                        count = None
                        delta = 0
                        count_ready = (count_input is not None and count_input["native_index"] == occurrence["native_index"] and
                            count_input["raw_full_id_u32"] == occurrence["raw_full_id_u32"] and
                            _same_resolution(count_input, occurrence) and
                            type(count_input["native_whole_current_soldiers"]) is int)
                        if count_ready and changes:
                            count_ready = count_input["ready"] is True
                            for regiment in count_input["regiments"]:
                                if regiment["identity_valid"] is False:
                                    continue
                                key = _key(regiment)
                                if regiment["identity_valid"] is not True or key is None:
                                    count_ready = False
                                    break
                                delta = _signed_i32(delta + changes.get(key, 0))
                        if count_ready:
                            count = _signed_i32(count_input["native_whole_current_soldiers"] + delta)
                        count_row = {"native_index": occurrence["native_index"],
                            "raw_full_id_u32": occurrence["raw_full_id_u32"],
                            "ready": count_ready, "conditional_whole_current_soldiers_i32": count,
                            "cached_current_delta_i32": delta if count_ready else None,
                            "queue_append_requested": count_ready and count <= 0}
                        out["army_counts"].append(count_row)
                        if not count_ready:
                            army_ready = False
                            break
                        elif count <= 0:
                            queues.append({"group_native_index": index, "army_native_index": ordinal,
                                           "raw_full_id_u32": occurrence["raw_full_id_u32"]})
                    out["queue_requests_ready"] = army_ready
                    if not army_ready:
                        out["missing_inputs"] = ["complete_group_Army_flags0_count_and_changed_target_intersections"]
        if alive and (not out["numeric_ready"] or not out["queue_requests_ready"]):
            alive = False
            missing.append({"group_native_index": index, "inputs": out["missing_inputs"]})
        elif alive:
            completed += 1
        groups.append(out)
    ready = alive and completed == len(table["groups"])
    return {**result, "status": "available" if ready else "partial" if groups else "unavailable",
            "sequential_numeric_ready": ready, "queue_requests_ready": ready,
            "completed_group_count": completed, "groups": groups,
            "ordered_queue_append_requests": queues, "conditional_physical_chunks": list(physical.values()),
            "conditional_regiment_currents": list(cache.values()), "missing_inputs": missing}
