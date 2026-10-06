"""Actual-source current standalone 2A99B40 admission, without native calls.

The whole original roster is independent of ArmyStrength scope. This replays
only the source-closed current operands, not earlier dispatch/callbacks or the
next date. Raw observations and independent late decisions survive a partial
continuous request prefix. No normalizer is imported by this pure module.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy


class _MissingInput(Exception):
    pass


def _require(value, reason):
    if value is None:
        raise _MissingInput(reason)
    return value


def _selected(resolution):
    return (resolution["selected_object_ready"] is True
            and resolution["object_identity"] is not None)


def _demand_operand(resolution, name):
    if not _selected(resolution):
        raise _MissingInput(name + "_selected_operand_unavailable")


def _wrap_i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _fnv(full_id):
    result = 0x811C9DC5
    for shift in (0, 8, 16, 24):
        result = ((result ^ ((full_id >> shift) & 255)) * 0x01000193) & 0xFFFFFFFF
    return result


def _references_ready(references):
    count = references["count_raw_i32"]
    rows = references["occurrences"]
    return (count is not None and count >= 0 and len(rows) == count
            and all(row["native_index"] == index and row["raw_full_id_u32"] is not None
                    for index, row in enumerate(rows)))


def _membership(references, target, name):
    """Demand original search order; a reached match needs no later rows."""
    count = _require(references["count_raw_i32"], name + "_count_unavailable")
    if count < 0:
        raise _MissingInput(name + "_negative_count_native_precondition_unclosed")
    if count == 0:
        return False
    # Approved current queue reuse retains actual count/order/elements even
    # when independent data-pointer metadata failed. Membership uses the IDs.
    rows = {row["native_index"]: row for row in references["occurrences"]}
    for index in range(count):
        row = rows.get(index)
        if row is None or row["raw_full_id_u32"] is None:
            raise _MissingInput(name + "_occurrence_unavailable")
        if row["raw_full_id_u32"] == target:
            return True
    return False


def _empty_relation():
    return {"ready": False, "unavailable_reason": "not_demanded",
            "candidate_slot_index_i64": None, "selection": None,
            "selected_relationship_identity": None,
            "selected_relationship_war_id_raw_u32": None,
            "probe_ledger": []}


def _derive_relation(raw):
    result = _empty_relation()
    probes = raw["probes"]
    cursor = 0

    def key(kind, slot):
        nonlocal cursor
        if cursor >= len(probes):
            raise _MissingInput("relation_" + kind + "_key_unavailable")
        probe = probes[cursor]
        if probe["kind"] != kind or probe["slot_index_i64"] != slot:
            raise ValueError("Relation probes do not follow the literal native lookup order")
        cursor += 1
        result["probe_ledger"].append(deepcopy(probe))
        return _require(probe["key_character_id_raw_u32"], "relation_" + kind + "_key_unavailable")

    try:
        present = _require(raw["component_present"], "relation_component_pointer_unavailable")
        if not present:
            selection = "native_fallback"
        else:
            count = _require(raw["table_count_raw_i32"], "relation_count_unavailable")
            if count < 0:
                raise _MissingInput("relation_negative_count_native_precondition_unclosed")
            end, base, remaining, candidate = count, 0, count, 0
            if remaining > 0:
                if raw["table_data_present"] is not True:
                    raise _MissingInput("relation_table_data_native_read_precondition_unclosed")
                target = _require(raw["target_character_full_id_raw_u32"], "relation_target_full_id_unavailable")
                while True:
                    half = remaining >> 1
                    pivot = key("pivot", base + half)
                    if pivot < target:  # Native unsigned CMOVB; no sorting/equality gate.
                        base += remaining - half
                    candidate = base
                    remaining = half
                    if half == 0:
                        break
            result["candidate_slot_index_i64"] = candidate
            if candidate == end:
                selection = "native_fallback"
            elif target < key("candidate", candidate):  # Native unsigned JB only; count>0 here.
                selection = "native_fallback"
            elif _wrap_i32(candidate) < 0:
                selection = "native_fallback"
            else:
                selection = "pair_map"
        result["selection"] = selection
        if selection == "native_fallback":
            if raw["default_relationship_present"] is not True:
                raise _MissingInput("default_relationship_native_read_precondition_unclosed")
            identity = _require(raw["default_relationship_identity"], "default_relationship_pointer_unavailable")
        else:
            if raw["selected_relationship_present"] is not True:
                raise _MissingInput("selected_relationship_native_read_precondition_unclosed")
            identity = _require(raw["selected_relationship_identity"], "selected_relationship_pointer_unavailable")
        if raw["selected_relationship_identity"] != identity:
            raise ValueError("Selected relationship does not retain its actual native selection")
        result["selected_relationship_identity"] = identity
        war_id = _require(raw["selected_relationship_war_id_raw_u32"], "selected_relationship_war_id_unavailable")
        result.update(ready=True, unavailable_reason=None, selected_relationship_war_id_raw_u32=war_id)
    except _MissingInput as error:
        result["unavailable_reason"] = str(error)
    return result


def _derive_gate(raw, original_resolution):
    result = {"ready": False, "verdict": None, "unavailable_reason": "not_demanded",
              "relation_lookup": _empty_relation(), "source_ledger": []}

    def demand(name):
        value = _require(raw[name], name + "_unavailable")
        result["source_ledger"].append({"field": name, "value": value})
        return value

    def finish(verdict):
        result.update(ready=True, verdict=verdict, unavailable_reason=None)
        return result

    try:
        _demand_operand(original_resolution, "original_army")
        demand("original_army_unit_id_raw_u32")
        _demand_operand(raw["original_unit_resolution"], "original_unit")
        if demand("original_unit_kind_raw_u32") != 0:
            return finish(False)
        if not demand("original_unit_province_present"):
            raise _MissingInput("original_province_pointer_native_read_precondition_unclosed")
        original = demand("original_province_identity_raw_u32")
        if original != demand("selected_province_comparison_identity_raw_u32"):
            return finish(False)
        if demand("original_unit_counter_170_raw_i32") > 0:
            return finish(False)
        demand("associated_army_id_raw_u32")
        _demand_operand(raw["associated_army_resolution"], "associated_army")
        if demand("province_siege_id_raw_u32") == 0xFFFFFFFF:
            return finish(False)
        if demand("province_counter_850_raw_i32") <= 0:
            return finish(False)
        if demand("associated_army_flag_1d4_raw_u8") != 0:
            return finish(False)
        if demand("associated_army_flag_1ec_raw_u8") != 0:
            return finish(False)
        demand("associated_army_unit_id_raw_u32")
        _demand_operand(raw["associated_unit_resolution"], "associated_unit")
        demand("associated_unit_character_id_raw_u32")
        _demand_operand(raw["associated_character_resolution"], "associated_character")
        if demand("province_character_id_73c_raw_u32") == 0xFFFFFFFF:
            classifier_fields = (
                "native_2c099f0_character_identity", "native_2c099f0_province_identity",
                "native_2c099f0_third_argument_is_null", "native_2c099f0_returned",
                "native_2c099f0_classification_raw_i32")
            if (all(raw.get(name) is None for name in classifier_fields if name != "native_2c099f0_returned")
                    and raw.get("native_2c099f0_returned", False) is False):
                raise _MissingInput("province_73c_requires_2c099f0_inputs")
            character = demand("native_2c099f0_character_identity")
            province = demand("native_2c099f0_province_identity")
            if character != raw["associated_character_resolution"]["object_identity"]:
                raise _MissingInput("province_73c_2c099f0_character_operand_mismatch")
            if province != raw["original_unit_province_identity"]:
                raise _MissingInput("province_73c_2c099f0_province_operand_mismatch")
            if demand("native_2c099f0_third_argument_is_null") is not True:
                raise _MissingInput("province_73c_2c099f0_third_argument_not_null")
            if demand("native_2c099f0_returned") is not True:
                raise _MissingInput("province_73c_2c099f0_getter_unbound")
            return finish(demand("native_2c099f0_classification_raw_i32") == 0)
        _demand_operand(raw["province_character_resolution"], "province_character")
        associated = demand("associated_character_full_id_raw_u32")
        if associated == demand("province_character_full_id_raw_u32"):
            return finish(False)
        relation = _derive_relation(raw["relation_lookup"])
        result["relation_lookup"] = relation
        if not relation["ready"]:
            raise _MissingInput(relation["unavailable_reason"])
        if relation["selected_relationship_war_id_raw_u32"] == 0xFFFFFFFF:
            raise _MissingInput("2c09640_remaining_relation_predicates_unclosed")
        # Selected/fallback War fullID metadata and generic resolution.ready
        # are not predicates. Native selection and the actual byte358 suffice.
        _demand_operand(raw["selected_war_resolution"], "selected_war")
        if demand("selected_war_ended_358_raw_u8") != 0:
            raise _MissingInput("2c09640_remaining_relation_predicates_unclosed")
        return finish(True)
    except _MissingInput as error:
        result["unavailable_reason"] = str(error)
        return result


def _empty_pending():
    return {"ready": False, "unavailable_reason": "not_demanded",
            "target_army_full_id_u32": None, "hash_raw_u32": None,
            "home_slot_i64": None, "selected_physical_slot_i64": None,
            "selected_is_end_marker": None, "selected_control_raw_u8": None,
            "probe_ledger": []}


def _derive_pending(raw, target):
    result = _empty_pending()
    result.update(target_army_full_id_u32=target, hash_raw_u32=_fnv(target))
    cursor, distance = 0, 1
    try:
        if raw["entries_present"] is not True:
            raise _MissingInput("pending_entries_native_read_precondition_unclosed")
        mask = _require(raw["mask_raw_i32"], "pending_mask_unavailable")
        slot = _wrap_i32(result["hash_raw_u32"]) & mask
        result["home_slot_i64"] = slot
        while True:
            if cursor >= len(raw["probes"]):
                raise _MissingInput("pending_probe_unavailable")
            probe = raw["probes"][cursor]
            cursor += 1
            if probe["physical_slot_i64"] != slot or probe["distance_raw_u8"] != distance:
                raise ValueError("Pending probes do not follow the native full-ID probe order")
            result["probe_ledger"].append(deepcopy(probe))
            control = _require(probe["control_raw_u8"], "pending_probe_control_unavailable")
            if control < distance:
                tail = _require(raw["tail_distance_raw_u8"], "pending_tail_unavailable")
                slot = _wrap_i32(mask + tail + 1)
                is_end = True
                break
            key = _require(probe["key_raw_full_id_u32"], "pending_probe_key_unavailable")
            if key == target:
                is_end = False
                break
            slot, distance = slot + 1, (distance + 1) & 255
        result.update(selected_physical_slot_i64=slot, selected_is_end_marker=is_end)
        control = _require(raw["selected_control_raw_u8"], "pending_selected_control_unavailable")
        result.update(ready=True, unavailable_reason=None, selected_control_raw_u8=control)
    except _MissingInput as error:
        result["unavailable_reason"] = str(error)
    return result


def _derive_occurrence(raw, removal_queue):
    result = {"native_index": raw["native_index"], "raw_full_id_u32": raw["raw_full_id_u32"],
              "ready": False, "unavailable_reason": None,
              "original_army_selection_ready": _selected(raw["original_army_resolution"]),
              "gate": {"ready": False, "verdict": None, "unavailable_reason": "not_demanded",
                       "relation_lookup": _empty_relation(), "source_ledger": []},
              "removal_contains_selected_army": None,
              "army_append_ready": False, "army_append": None,
              "army_append_siege_full_id_u32": None, "army_append_full_id_u32": None,
              "pending_selection": _empty_pending(), "arrg_occurrences": [],
              "arrg_append_ready": False, "arrg_append_full_ids_u32": None,
              "source_ledger": []}

    def skip(reason):
        result.update(ready=True, army_append_ready=True, army_append=False,
                      arrg_append_ready=True, arrg_append_full_ids_u32=[])
        result["source_ledger"].append({"stage": "source_bound_skip", "reason": reason})
        return result

    try:
        _require(raw["raw_full_id_u32"], "original_army_raw_reference_unavailable")
        gate = _derive_gate(raw["gate"], raw["original_army_resolution"])
        result["gate"] = gate
        if not gate["ready"]:
            raise _MissingInput(gate["unavailable_reason"])
        if not gate["verdict"]:
            return skip("24e8560_false")
        _require(raw["caller_army_unit_id_raw_u32"], "caller_army_unit_id_unavailable")
        _demand_operand(raw["caller_unit_resolution"], "caller_unit")
        if raw["caller_province_present"] is not True:
            raise _MissingInput("caller_selected_province_native_read_precondition_unclosed")
        _require(raw["caller_province_siege_id_raw_u32"], "caller_province_siege_id_unavailable")
        _demand_operand(raw["siege_resolution"], "caller_siege")
        flag = _require(raw["siege_flag_44c_raw_u8"], "siege_flag_44c_unavailable")
        if flag == 0:
            return skip("siege_44c_zero")
        army_id = _require(raw["selected_army_full_id_raw_u32"], "selected_army_full_id_unavailable")
        removed = _membership(removal_queue, army_id, "removal_queue")
        result["removal_contains_selected_army"] = removed
        if removed:
            return skip("removal_queue_match")
        siege_id = _require(raw["siege_resolution"]["selected_full_id_u32"], "selected_siege_full_id_unavailable")
        result.update(army_append_ready=True, army_append=True,
                      army_append_siege_full_id_u32=siege_id, army_append_full_id_u32=army_id)
        result["source_ledger"].append({"stage": "verified_conditional_army_append",
                                       "siege_full_id_u32": siege_id, "army_full_id_u32": army_id,
                                       "native_append_executed": False})
        pending = _derive_pending(raw["pending_selection"], army_id)
        result["pending_selection"] = pending
        if not pending["ready"]:
            raise _MissingInput(pending["unavailable_reason"])
        if pending["selected_control_raw_u8"] == 255:
            result.update(ready=True, arrg_append_ready=True, arrg_append_full_ids_u32=[])
            return result
        references = raw["original_arrg_references"]
        count = _require(references["count_raw_i32"], "original_arrg_count_unavailable")
        if count < 0:
            raise _MissingInput("original_arrg_negative_count_native_precondition_unclosed")
        if count == 0:
            result.update(ready=True, arrg_append_ready=True, arrg_append_full_ids_u32=[])
            return result
        if references["data_present"] is not True:
            raise _MissingInput("original_arrg_data_unavailable")
        suppression = raw["pending_selection"]["suppression_references"]
        first_reason = None
        for observed in references["occurrences"]:
            row = {"native_index": observed["native_index"], "raw_full_id_u32": observed["raw_full_id_u32"],
                   "ready": False, "pending_contains": None, "append": None, "unavailable_reason": None}
            try:
                full_id = _require(observed["raw_full_id_u32"], "original_arrg_occurrence_unavailable")
                contains = _membership(suppression, full_id, "pending_suppression")
                row.update(ready=True, pending_contains=contains, append=not contains)
            except _MissingInput as error:
                row["unavailable_reason"] = str(error)
                first_reason = first_reason or str(error)
            result["arrg_occurrences"].append(row)
        complete = _references_ready(references) and all(row["ready"] for row in result["arrg_occurrences"])
        if not complete:
            raise _MissingInput(first_reason or "original_arrg_references_incomplete")
        admitted = [row["raw_full_id_u32"] for row in result["arrg_occurrences"] if row["append"]]
        result.update(ready=True, arrg_append_ready=True, arrg_append_full_ids_u32=admitted)
        return result
    except _MissingInput as error:
        result["unavailable_reason"] = str(error)
        return result


def _request_row(occurrence, observed):
    return {"siege_full_id_u32": occurrence["army_append_siege_full_id_u32"],
            "army_full_id_u32": occurrence["army_append_full_id_u32"],
            "arrg_full_ids_u32": deepcopy(occurrence["arrg_append_full_ids_u32"]),
            "source_provenance": {
                "source": "observed_current_standalone_2a99b40_admission",
                "original_roster_native_index": occurrence["native_index"],
                "requested_army_full_id_u32": occurrence["raw_full_id_u32"],
                "original_army_resolution": deepcopy(observed["original_army_resolution"]),
                "siege_resolution": deepcopy(observed["siege_resolution"]),
                "gate_source_ledger": deepcopy(occurrence["gate"]["source_ledger"]),
                "relation_lookup": deepcopy(occurrence["gate"]["relation_lookup"]),
                "pending_selection": deepcopy(occurrence["pending_selection"]),
                "admitted_original_arrg_native_indices": [row["native_index"]
                    for row in occurrence["arrg_occurrences"] if row["append"] is True],
                "earlier_callbacks_replayed": False, "actual_next_callback_ready": False}}


def project_current_daily_assault_roster_admission_12003(normalized_leaf: Mapping | None) -> dict:
    """Derive current conditional admission, preserving raw and partial facts."""
    result = {"schema_version": 1, "source": "source_bound_current_standalone_2a99b40_admission",
              "stage": "observed_current_standalone_2a99b40_admission",
              "source_contract_game_version": "1.20.0.3",
              "status": "unavailable", "ready": False, "unavailable_reason": None,
              "raw_roster_references_ready": False, "raw_roster_ready": False,
              "removal_queue_references_ready": False,
              "original_army_selections_ready": False, "army_appends_ready": False,
              "arrg_appends_ready": False, "conditional_admission_ready": False,
              "current_conditional_admission_ready": False,
              "actual_next_callback_ready": False, "actual_tomorrow_roster_ready": False,
              "full_future_table_placement_ready": False, "full_daily_assault_ready": False,
              "full_daily": False, "full_monthly": False,
              "native_calls_executed": 0, "native_writes_executed": 0,
              "earlier_dispatch_replayed": False, "earlier_callbacks_replayed": False,
              "observed_current_roster_admission": deepcopy(dict(normalized_leaf)) if normalized_leaf is not None else None,
              "original_roster": None, "removal_queue": None, "occurrences": [],
              "raw_roster_occurrences": [], "raw_roster_reference_count": None,
              "request_prefix": [], "independently_derived_requests": [],
              "verified_army_append_facts": [], "first_partial_native_index": None,
              "missing_inputs": []}
    if normalized_leaf is None:
        result.update(unavailable_reason="current_daily_assault_roster_admission_unavailable",
                      missing_inputs=["current_daily_assault_roster_admission_v1"])
        return result
    if (normalized_leaf["source"] != "native_current_daily_assault_roster_admission"
            or normalized_leaf["stage"] != "observed_current_standalone_2a99b40_admission"):
        raise ValueError("Admission input must be the genuine current standalone native leaf")
    original, removal = normalized_leaf["original_roster"], normalized_leaf["removal_queue"]
    raw_ready = _references_ready(original)
    observed_rows = normalized_leaf["occurrences"]
    occurrences = [_derive_occurrence(row, removal) for row in observed_rows]
    count = original["count_raw_i32"]
    coverage = (count is not None and count >= 0 and len(occurrences) == count
                and [row["native_index"] for row in occurrences] == list(range(count)))
    complete = raw_ready and coverage and all(row["ready"] for row in occurrences)
    prefix_open = count is not None and count >= 0
    prefix_index = 0
    for derived, observed in zip(occurrences, observed_rows):
        if derived["native_index"] != prefix_index:
            prefix_open = False
            if result["first_partial_native_index"] is None:
                result["first_partial_native_index"] = prefix_index
        prefix_index = derived["native_index"] + 1
        if not derived["ready"]:
            result["missing_inputs"].append({"native_index": derived["native_index"],
                                              "reason": derived["unavailable_reason"]})
            if result["first_partial_native_index"] is None:
                result["first_partial_native_index"] = derived["native_index"]
            prefix_open = False
        if derived["army_append_ready"] and derived["army_append"]:
            result["verified_army_append_facts"].append({"native_index": derived["native_index"],
                "siege_full_id_u32": derived["army_append_siege_full_id_u32"],
                "army_full_id_u32": derived["army_append_full_id_u32"],
                "arrg_append_ready": derived["arrg_append_ready"], "native_append_executed": False})
        if derived["ready"] and derived["army_append"]:
            request = _request_row(derived, observed)
            result["independently_derived_requests"].append(request)
            if prefix_open:
                result["request_prefix"].append(deepcopy(request))
    if not raw_ready or not coverage:
        result["missing_inputs"].append("complete_original_roster_references_and_occurrence_coverage")
    result.update(status="available" if complete else "partial" if normalized_leaf["manager_loaded"] else "unavailable",
                  ready=complete, conditional_admission_ready=complete,
                  current_conditional_admission_ready=complete,
                  raw_roster_references_ready=raw_ready, raw_roster_ready=raw_ready,
                  removal_queue_references_ready=_references_ready(removal),
                  original_army_selections_ready=raw_ready and coverage and all(
                      row["original_army_selection_ready"] for row in occurrences),
                  army_appends_ready=raw_ready and coverage and all(row["army_append_ready"] for row in occurrences),
                  arrg_appends_ready=raw_ready and coverage and all(row["arrg_append_ready"] for row in occurrences),
                  original_roster=deepcopy(original), removal_queue=deepcopy(removal),
                  raw_roster_occurrences=deepcopy(original["occurrences"]),
                  raw_roster_reference_count=count, occurrences=occurrences,
                  unavailable_reason=None if complete else "current_conditional_admission_inputs_incomplete")
    return result


def daily_assault_roster_admission_requests_12003(projection: Mapping, *, prefix_only: bool = False) -> tuple:
    """Create full typed requests; partial input requires explicit prefix choice."""
    if not projection["conditional_admission_ready"] and not prefix_only:
        raise ValueError("Whole conditional admission is incomplete; explicitly choose prefix_only for its verified prefix")
    from .army_daily_assault_placement_12003 import DailyAssaultPlacementRequest12003
    return tuple(DailyAssaultPlacementRequest12003(
        row["siege_full_id_u32"], row["army_full_id_u32"], tuple(row["arrg_full_ids_u32"]),
        deepcopy(row["source_provenance"])) for row in projection["request_prefix"])


def validate_current_daily_assault_roster_admission_declared_12003(raw: Mapping, projection: Mapping | None = None) -> dict:
    """Compare producer decision flags/results with raw-source derivation once.

    Structural/type/status validation belongs to the parent-owned contract.
    Diagnostic wording is intentionally not compared. Return the derived result
    so callers may reuse it; this helper never calls a transport normalizer.
    """
    derived = project_current_daily_assault_roster_admission_12003(raw) if projection is None else projection

    def same(declared, expected, fields, name):
        for field in fields:
            if declared[field] != expected[field]:
                raise ValueError(f"{name}.{field} disagrees with actual source inputs")

    same(raw, derived, ("ready", "raw_roster_references_ready", "original_army_selections_ready",
                       "army_appends_ready", "arrg_appends_ready", "conditional_admission_ready"), "admission")
    same(raw["original_roster"], {"ready": derived["raw_roster_references_ready"],
                                "references_ready": derived["raw_roster_references_ready"]},
         ("ready", "references_ready"), "original_roster")
    for observed, row in zip(raw["occurrences"], derived["occurrences"]):
        same(observed, row, ("ready", "removal_contains_selected_army", "army_append_ready", "army_append",
                             "army_append_siege_full_id_u32", "army_append_full_id_u32",
                             "arrg_append_ready", "arrg_append_full_ids_u32"), "roster_occurrence")
        same(observed["gate"], row["gate"], ("ready", "verdict"), "gate")
        relation = row["gate"]["relation_lookup"]
        same(observed["gate"]["relation_lookup"], relation,
             ("ready", "candidate_slot_index_i64", "selection"), "relation_lookup")
        pending = row["pending_selection"]
        same(observed["pending_selection"], pending,
             ("ready", "selected_physical_slot_i64", "selected_is_end_marker", "selected_control_raw_u8"), "pending_selection")
        if len(observed["arrg_occurrences"]) != len(row["arrg_occurrences"]):
            raise ValueError("ArRg admission occurrence coverage disagrees with source demands")
        for declared_arrg, derived_arrg in zip(observed["arrg_occurrences"], row["arrg_occurrences"]):
            same(declared_arrg, derived_arrg, ("native_index", "raw_full_id_u32", "ready", "pending_contains", "append"), "arrg_occurrence")
    return dict(derived)
