"""Isolated ordered 2C57020 effects from an explicit current 2A98590 entry."""
from __future__ import annotations

from typing import Mapping

_REGI = 0x52656769
_DOMI = 0x446F6D69
_CHAR = 0x43686172


def _integer(value: object, bits: int = 32) -> bool:
    return type(value) is int and -(1 << (bits - 1)) <= value < 1 << (bits - 1)


def _wrap(value: int, bits: int) -> int:
    return ((value + (1 << (bits - 1))) % (1 << bits)) - (1 << (bits - 1))


def _count(row: Mapping[str, object]) -> tuple[int | None, list[int | None], bool]:
    base, records = row.get("count_base_128_raw"), row.get("count_records")
    if not _integer(base) or not isinstance(records, list) or len(records) != 7:
        return None, [], False
    acc, deltas, complete_witness = base, [], True
    for index, record in enumerate(records):
        if not isinstance(record, Mapping) or record.get("stored_index") != index:
            return None, deltas, False
        a, b, state = (record.get("count_00_raw"), record.get("count_04_raw"), record.get("state_18_raw"))
        complete_witness = complete_witness and all(_integer(item) for item in (a, b, state))
        if not _integer(a):
            delta = None
        elif a == 0:
            delta = 0
        elif not _integer(b):
            delta = None
        elif b != 0:
            delta = _wrap(b - a, 32)
        elif not _integer(state):
            delta = None
        else:
            delta = 0 if state == 3 else _wrap(-a, 32)
        deltas.append(delta)
        if delta is not None:
            acc = _wrap(acc + delta, 32)
    return (acc if all(item is not None for item in deltas) else None), deltas, complete_witness


def _character_reference(row: Mapping[str, object]) -> tuple[int | None, str | None]:
    title, character = row.get("receiver_title_reference_130_raw"), row.get("receiver_character_reference_12c_raw")
    if not _integer(title) or not _integer(character):
        return None, None
    if title != -1 and character == -1:
        holder = row.get("owner_title_holder_character_id_128_raw")
        if (not _integer(row.get("owner_title_resolved_id"))
                or type(row.get("owner_title_used_fallback")) is not bool or not _integer(holder)):
            return None, "title_holder"
        return holder, "title_holder"
    if title == -1 and character != -1:
        return character, "direct_character"
    return -1, "minus_one_character_fallback"


def _project_record(row: Mapping[str, object]) -> dict[str, object]:
    count, deltas, witness = _count(row)
    reference, route = _character_reference(row)
    result: dict[str, object] = {
        "group_index": row.get("group_index"), "stored_index": row.get("stored_index"),
        "record_regiment_reference_id": row.get("record_regiment_reference_id"), "chunk_index": row.get("chunk_index"),
        "receiver_regiment_resolved_id": row.get("receiver_regiment_resolved_id"),
        "conditional_branch": None, "conditional_invocation_admitted": None,
        "conditional_invocation_ready": False, "predicate_admitted": None,
        "owner_character_route": route, "derived_selected_character_reference_id": reference,
        "conditional_native_count_ready": count is not None, "conditional_native_count": count,
        "conditional_count_record_deltas": deltas, "count_source_witness_ready": witness,
        "conditional_delta_raw64": None if count is None else count * 100000,
        "domain_resolved_id": row.get("domain_resolved_id"), "domain_alias_ordinal": row.get("domain_alias_ordinal"),
        "conditional_domain_store_admitted": None, "conditional_store_admission_ready": False,
        "conditional_effect_ready": False, "conditional_domain_value_ready": False,
        "domain_value_input_basis": None, "conditional_domain_value_48_before_raw64": None,
        "conditional_domain_value_48_after_raw64": None, "missing_inputs": [],
        "actual_effects_observed": False, "actual_domain_value_48_after_raw64": None,
    }

    def no_store(branch: str, invocation: bool | None = None) -> dict[str, object]:
        result.update(conditional_branch=branch, conditional_domain_store_admitted=False,
                      conditional_store_admission_ready=True, conditional_effect_ready=True)
        if invocation is not None:
            result.update(conditional_invocation_admitted=invocation, conditional_invocation_ready=True)
        return result

    def unknown(missing: str) -> dict[str, object]:
        result["missing_inputs"].append(missing)
        return result

    # A captured null DATA branch cannot invoke the subsystem, regardless
    # of other unread identity operands on this independent record family.
    if row.get("data_record_present") is False:
        return no_store("null_data_record", False)
    resolved, magic = row.get("record_regiment_resolved_id"), row.get("record_regiment_magic_14_raw")
    if resolved == -1 or (type(magic) is int and magic != _REGI):
        return no_store("invalid_containing_regiment", False)
    if not _integer(resolved) or magic != _REGI:
        return unknown("containing_regiment_identity_10_14")
    if row.get("data_record_present") is not True:
        return unknown("data_record_present")
    state = row.get("data_state_18_raw")
    if not _integer(state):
        return unknown("data_state_18_raw")
    if state != 4:
        return no_store("data_not_state4", False)
    result.update(conditional_invocation_admitted=True, conditional_invocation_ready=True)
    receiver_state = row.get("receiver_state_138_raw")
    if not _integer(receiver_state):
        return unknown("receiver_state_138_raw")
    if receiver_state != 4:
        return no_store("receiver_not_state4")
    if not _integer(row.get("receiver_regiment_resolved_id")):
        return unknown("selected_persistent_receiver")
    if reference is None:
        return unknown("title_holder_or_direct_character_route")
    if row.get("selected_character_reference_id") != reference:
        return unknown("selected_character_reference_matches_source_route")
    if (not _integer(row.get("selected_character_resolved_id"))
            or type(row.get("selected_character_used_fallback")) is not bool):
        return unknown("selected_character_generation_resolution")
    child = row.get("character_domain_child_present")
    if type(child) is not bool or not _integer(row.get("domain_reference_id")):
        return unknown("character_domain_child_reference")
    if not child and row["domain_reference_id"] != -1:
        return unknown("absent_character_child_selects_minus_one_domain")
    domain_id, domain_magic = row.get("domain_resolved_id"), row.get("domain_magic_0c_raw")
    if domain_id == -1 or (type(domain_magic) is int and domain_magic != _DOMI):
        result["predicate_admitted"] = False
        return no_store("invalid_predicate_domain")
    if not _integer(domain_id) or domain_magic != _DOMI:
        return unknown("domain_identity_8_0c")
    # The first predicate dereferences Domain+30 without checking nullptr.
    if row.get("domain_data_30_present") is not True:
        return unknown("readable_unchecked_domain_data_30_receiver")
    flag = row.get("domain_flag_17e_raw")
    if type(flag) is not int or not 0 <= flag < 256:
        return unknown("domain_flag_17e_raw")
    result["predicate_admitted"] = flag != 0
    if flag == 0:
        return no_store("zero_predicate_flag")
    if count is None:
        return unknown("native_seven_record_count")
    if count == 0:
        return no_store("zero_native_count")
    owner_id, owner_magic = row.get("domain_owner_character_resolved_id"), row.get("domain_owner_character_magic_1c_raw")
    if owner_id == -1 or (type(owner_magic) is int and owner_magic != _CHAR):
        return no_store("invalid_domain_owner_character")
    if not _integer(owner_id) or owner_magic != _CHAR:
        return unknown("domain_owner_character_identity_18_1c")
    result.update(conditional_branch="domain_update", conditional_domain_store_admitted=True,
                  conditional_store_admission_ready=True)
    return result


def project_conditional_current_helper_domain_updates(army: Mapping[str, object]) -> dict[str, object]:
    """Carry exact native pointer aliases across only this closed subsystem."""
    result: dict[str, object] = {
        "projection_kind": "conditional_current_helper_domain_updates", "native_subsystem_rva": "0x2C57020",
        "parent_helper_rva": "0x2A98590", "source_contract_game_version": "1.20.0.3",
        "input_basis": "isolated_ordered_2C57020_invocations_from_explicit_current_helper_entry",
        "status": "unavailable", "conditional_domain_updates_ready": False,
        "conditional_invocation_order_ready": False, "entry_army_id": None, "group_count_5c_raw": None,
        "record_projections": [], "domain_value_projections": [], "conditional_domain_store_count": None,
        "actual_effects_observed": False, "actual_domain_value_48_after_raw64": None,
        "real_late_caller_stage_ready": False, "full_helper_ready": False,
        "actual_full_army_lifecycle_ready": False, "actual_loss": False, "actual_post_state": None,
        "actual_post_stage_current": None, "full_monthly_applied_loss_ready": False,
        "missing_inputs": [],
    }
    raw = army.get("monthly_current_helper_domain_inputs_v1")
    if not isinstance(raw, Mapping):
        return {**result, "missing_inputs": ["monthly_current_helper_domain_inputs_v1"]}
    entry, count = raw.get("entry_army_id"), raw.get("group_count_5c_raw")
    if not _integer(entry) or entry != army.get("native_carmy_id"):
        return {**result, "missing_inputs": ["explicit_entry_matches_current_native_carmy_id"]}
    result.update(entry_army_id=entry, group_count_5c_raw=count)
    if not _integer(count):
        return {**result, "missing_inputs": ["group_count_5c_raw"]}
    if count <= 0:
        return {**result, "status": "available", "conditional_domain_updates_ready": True,
                "conditional_invocation_order_ready": True, "conditional_domain_store_count": 0}
    rows = raw.get("rows")
    if not isinstance(rows, list):
        return {**result, "missing_inputs": ["ordered_current_group_records"]}
    result["conditional_invocation_order_ready"] = True
    # None is a poisoned alias value, not a request to reread its initial raw
    # value. Unknown target identity may alias any later target in this scope.
    values: dict[int, int | None] = {}
    identities: dict[int, int | None] = {}
    initial: dict[int, int | None] = {}
    unknown_target_write = False
    projected = []
    stores = 0
    for row in rows:
        if not isinstance(row, Mapping):
            result["missing_inputs"].append("ordered_current_group_record")
            unknown_target_write = True
            for alias in values:
                values[alias] = None
            continue
        item = _project_record(row)
        alias = row.get("domain_alias_ordinal")
        known_alias = _integer(alias) and alias >= 0
        if known_alias:
            identities.setdefault(alias, row.get("domain_resolved_id"))
            initial.setdefault(alias, row.get("domain_value_48_raw64"))
        admitted = item["conditional_domain_store_admitted"]
        if admitted is True:
            stores += 1
            if not known_alias:
                item["missing_inputs"].append("native_domain_alias_ordinal")
                unknown_target_write = True
                for prior_alias in values:
                    values[prior_alias] = None
            else:
                if unknown_target_write:
                    before, basis = None, "unresolved_earlier_domain_target"
                elif alias in values:
                    before, basis = values[alias], "prior_conditional_domain_alias_value"
                else:
                    before, basis = row.get("domain_value_48_raw64"), "observed_initial_domain_value"
                item.update(domain_value_input_basis=basis,
                            conditional_domain_value_48_before_raw64=before)
                if _integer(before, 64):
                    after = max(0, _wrap(before + item["conditional_delta_raw64"], 64))
                    values[alias] = after
                    item.update(conditional_domain_value_ready=True, conditional_effect_ready=True,
                                conditional_domain_value_48_after_raw64=after)
                else:
                    values[alias] = None
                    item["missing_inputs"].append("domain_value_basis_after_prior_conditional_effects")
        elif admitted is None:
            if known_alias:
                values[alias] = None
            else:
                unknown_target_write = True
                for prior_alias in values:
                    values[prior_alias] = None
        elif known_alias and alias not in values:
            observed = row.get("domain_value_48_raw64")
            values[alias] = observed if not unknown_target_write and _integer(observed, 64) else None
        projected.append(item)
    result["record_projections"] = projected
    result["domain_value_projections"] = [{
        "domain_alias_ordinal": alias, "domain_resolved_id": identities.get(alias),
        "observed_initial_domain_value_48_raw64": initial.get(alias),
        "conditional_ready": _integer(value, 64), "conditional_domain_value_48_after_raw64": value,
        "actual_domain_value_48_after_raw64": None,
    } for alias, value in values.items()]
    ready = len(projected) == len(rows) and all(item["conditional_effect_ready"] for item in projected)
    result.update(status="available" if ready else "partial", conditional_domain_updates_ready=ready,
                  conditional_domain_store_count=stores if all(item["conditional_store_admission_ready"] for item in projected) else None)
    result["missing_inputs"].extend(f"rows[{item['group_index']}:{item['stored_index']}].{missing}"
                                    for item in projected for missing in item["missing_inputs"])
    return result
