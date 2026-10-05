"""Current2A98590 point effects, before group release, under stated returns."""
from __future__ import annotations

from typing import Mapping

from .army_current_helper_domain_projection import project_conditional_current_helper_domain_updates


def _int(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value < 1 << 31


def _ids(value: object) -> bool:
    return isinstance(value, list) and all(_int(item) for item in value)


def _admit_clear(row: Mapping[str, object]) -> bool | None:
    magic, identity = row.get("record_regiment_magic_14_raw"), row.get("record_regiment_resolved_id")
    if row.get("data_record_present") is False or identity == -1 or (type(magic) is int and magic != 0x52656769):
        return False
    if _int(identity) and magic == 0x52656769 and row.get("data_record_present") is True:
        return True
    return None


def _character_reference(row: Mapping[str, object]) -> int | None:
    title, character = row.get("receiver_title_reference_130_raw"), row.get("receiver_character_reference_12c_raw")
    if not _int(title) or not _int(character):
        return None
    if title != -1 and character == -1:
        holder = row.get("owner_title_holder_character_id_128_raw")
        return holder if (_int(row.get("owner_title_resolved_id"))
                          and type(row.get("owner_title_used_fallback")) is bool and _int(holder)) else None
    return character if title == -1 and character != -1 else -1


def _ordinary_return(army: Mapping[str, object], inputs: Mapping[str, object], group: int,
                     row: Mapping[str, object], domain: Mapping[str, object]) -> tuple[bool, str]:
    if inputs.get("helper_same_current_army_pointer") is not True:
        return False, "helper_physical_receiver_not_proven_same_current_army"
    raw = army.get("monthly_current_helper_domain_inputs_v1")
    if not isinstance(raw, Mapping) or raw.get("entry_army_id") != army.get("native_carmy_id"):
        return False, "same_query_current_domain_inputs_unavailable"
    source = next((item for item in (raw.get("rows") or []) if isinstance(item, Mapping)
                   and item.get("group_index") == group and item.get("stored_index") == row.get("stored_index")), None)
    projected = next((item for item in domain.get("record_projections", []) if isinstance(item, Mapping)
                      and item.get("group_index") == group and item.get("stored_index") == row.get("stored_index")), None)
    keys = ("record_regiment_reference_id", "chunk_index", "record_regiment_resolved_id", "record_regiment_used_fallback",
            "record_regiment_magic_14_raw", "data_record_present", "data_state_18_raw",
            "data_owner_regiment_reference_id", "receiver_regiment_resolved_id", "receiver_regiment_used_fallback")
    if (not isinstance(source, Mapping) or not isinstance(projected, Mapping)
            or not _int(row.get("receiver_regiment_resolved_id"))
            or any(source.get(key) != row.get(key) for key in keys)):
        return False, "same_query_domain_record_receiver_basis_not_matched"
    if projected.get("conditional_invocation_admitted") is True and projected.get("conditional_effect_ready") is True:
        return True, "source_closed_same_query_domain_record_ordinary_return"
    return False, "preceding_domain_call_ordinary_continuation_unresolved"


class _MembershipValues:
    def __init__(self):
        self.values: dict[int, list[int] | None] = {}
        self.unknown_target = False

    def poison(self, alias: object) -> None:
        if _int(alias) and alias >= 0:
            if self.values.get(alias) != []:
                self.values[alias] = None
        else:
            self.unknown_target = True
            for key, value in self.values.items():
                if value != []:
                    self.values[key] = None

    def erase(self, row: Mapping[str, object], result: dict[str, object]) -> None:
        alias, count = row.get("membership_alias_ordinal"), row.get("membership_count_2b4_raw")
        target, observed = row.get("data_owner_regiment_reference_id"), row.get("ordered_persistent_regiment_ids_2a8")
        if _int(count) and count <= 0:
            result.update(conditional_ready=True, conditional_removed_count=0, conditional_count_after=count,
                          conditional_ordered_ids_after=[] if count == 0 else None,
                          value_basis="native_nonpositive_count_no_write")
            if _int(alias) and count == 0:
                self.values[alias] = []
            return
        if not (_int(alias) and alias >= 0 and _int(target)):
            self.poison(alias)
            result["missing_inputs"].append("membership_alias_and_raw_DATA8_target")
            return
        if alias in self.values:
            before, basis = self.values[alias], "prior_conditional_membership_header_value"
        elif _ids(observed) and observed == [] and count == 0:
            before, basis = [], "observed_empty_erase_only_invariant"
        elif self.unknown_target:
            before, basis = None, "unresolved_earlier_membership_header"
        elif _int(count) and count > 0 and _ids(observed) and len(observed) == count:
            before, basis = list(observed), "observed_initial_membership_vector"
        else:
            before, basis = None, "membership_count_and_ordered_ids_unavailable"
        result.update(value_basis=basis, conditional_ordered_ids_before=None if before is None else list(before))
        if before is None:
            self.poison(alias)
            result["missing_inputs"].append("membership_value_after_prior_conditional_effects")
            return
        after = [raw_id for raw_id in before if raw_id != target]
        self.values[alias] = after
        result.update(conditional_ready=True, conditional_ordered_ids_after=list(after),
                      conditional_removed_count=len(before) - len(after), conditional_count_after=len(after))


def project_conditional_current_helper_point_stores(army: Mapping[str, object]) -> dict[str, object]:
    """Derive three leaf families; separately expose preceding return evidence."""
    result: dict[str, object] = {
        "projection_kind": "conditional_current_helper_point_stores", "native_helper_rva": "0x2A98590",
        "source_contract_game_version": "1.20.0.3", "status": "unavailable",
        "input_basis": "isolated_current_helper_point_stores_under_explicit_ordinary_return_conditions",
        "conditional_point_stores_ready": False, "data_clears_ready": False,
        "conditional_membership_erases_ready": False, "group_child_stores_ready": False,
        "membership_source_continuations_ready": False,
        "entry_army_id": None, "helper_resolved_army_id": None, "helper_used_fallback": None,
        "helper_same_current_army_pointer": None, "group_count_5c_raw": None,
        "record_projections": [], "character_projections": [], "ordered_effects": [],
        "membership_value_projections": [], "data_value_projections": [], "child_value_projections": [],
        "actual_effects_observed": False, "actual_loss": False, "actual_post_state": None,
        "real_late_caller_stage_ready": False, "full_helper_ready": False,
        "actual_full_army_lifecycle_ready": False, "missing_inputs": [],
    }
    inputs = army.get("monthly_current_helper_point_store_inputs_v1")
    if not isinstance(inputs, Mapping):
        return {**result, "missing_inputs": ["monthly_current_helper_point_store_inputs_v1"]}
    if not _int(inputs.get("entry_army_id")) or inputs["entry_army_id"] != army.get("native_carmy_id"):
        return {**result, "missing_inputs": ["explicit_entry_matches_current_native_army"]}
    for key in ("entry_army_id", "helper_resolved_army_id", "helper_used_fallback",
                "helper_same_current_army_pointer", "group_count_5c_raw"):
        result[key] = inputs.get(key)
    count = inputs.get("group_count_5c_raw")
    if not _int(count):
        return {**result, "missing_inputs": ["helper_group_count_5c"]}
    if count <= 0:
        return {**result, "status": "available", "conditional_point_stores_ready": True,
                "data_clears_ready": True, "conditional_membership_erases_ready": True,
                "group_child_stores_ready": True, "membership_source_continuations_ready": True}
    groups = inputs.get("groups")
    if not isinstance(groups, list):
        return {**result, "missing_inputs": ["ordered_helper_groups"]}
    traversal_ready = len(groups) == count
    data_ready = membership_ready = child_ready = continuation_ready = traversal_ready
    data_values: dict[int, int] = {}
    child_values: dict[int, tuple[int, int]] = {}
    possible_data_targets: set[int] = set()
    possible_child_targets: set[int] = set()
    unknown_data_target = unknown_child_target = False
    memberships = _MembershipValues()
    domain = project_conditional_current_helper_domain_updates(army)
    for group in groups:
        group_index = group["group_index"]
        record_count, records = group.get("record_count_14_raw"), group.get("record_rows")
        records_known = _int(record_count) and (record_count <= 0 or isinstance(records, list) and len(records) == record_count)
        if _int(record_count) and record_count <= 0:
            records = []
        if not records_known:
            data_ready = membership_ready = continuation_ready = False
            memberships.poison(None)
            unknown_data_target = True
            result["missing_inputs"].append(f"groups[{group_index}].record_traversal")
        for row in records if isinstance(records, list) else []:
            admitted = _admit_clear(row)
            alias, observed = row.get("data_alias_ordinal"), row.get("data_byte_14_raw")
            before = (data_values[alias] if alias in data_values else None
                      if unknown_data_target or alias in possible_data_targets else observed)
            clear = {"conditional_ready": admitted is not None, "conditional_store_admitted": admitted,
                     "data_alias_ordinal": alias, "observed_byte_14_raw": observed,
                     "conditional_byte_14_before": before, "conditional_byte_14_after": 0 if admitted else None,
                     "conditional_changed": before != 0 if admitted and type(before) is int else None}
            if admitted and _int(alias):
                data_values[alias] = 0
            elif admitted is not False:
                if _int(alias):
                    possible_data_targets.add(alias)
                else:
                    unknown_data_target = True
            state = row.get("data_state_18_raw")
            needs_return = admitted is True and state == 4
            normal, normal_basis = (True, "no_preceding_state4_call")
            if needs_return:
                normal, normal_basis = _ordinary_return(army, inputs, group_index, row, domain)
            elif (admitted is None and not (_int(state) and state != 4)
                  or admitted is True and not _int(state)):
                normal, normal_basis = False, "preceding_state4_call_admission_unresolved"
            member: dict[str, object] = {
                "conditional_ready": False, "conditional_call_admitted": None,
                "raw_DATA8_target": row.get("data_owner_regiment_reference_id"),
                "receiver_regiment_resolved_id": row.get("receiver_regiment_resolved_id"),
                "membership_alias_ordinal": row.get("membership_alias_ordinal"),
                "ordinary_return_condition": "preceding_2C57020_call_returns_ordinarily",
                "ordinary_return_ready": normal, "ordinary_return_basis": normal_basis,
                "value_basis": None, "conditional_ordered_ids_before": None,
                "conditional_ordered_ids_after": None, "conditional_removed_count": None,
                "conditional_count_after": None, "missing_inputs": [],
            }
            if admitted is False or _int(state) and state != 4:
                member.update(conditional_ready=True, conditional_call_admitted=False, conditional_removed_count=0)
            elif admitted is True and state == 4 and row.get("character_child_1c0_present") is False:
                member.update(conditional_ready=True, conditional_call_admitted=False, conditional_removed_count=0)
            elif admitted is True and state == 4:
                reference = _character_reference(row)
                if (reference is not None and row.get("selected_character_reference_id") == reference
                        and _int(row.get("selected_character_resolved_id"))
                        and type(row.get("selected_character_used_fallback")) is bool
                        and row.get("character_child_1c0_present") is True):
                    member["conditional_call_admitted"] = True
                    memberships.erase(row, member)
            if not member["conditional_ready"]:
                memberships.poison(row.get("membership_alias_ordinal"))
                if not member["missing_inputs"]:
                    member["missing_inputs"].append("state4_owner_route_and_child_membership_inputs")
            data_ready = data_ready and clear["conditional_ready"]
            membership_ready = membership_ready and member["conditional_ready"]
            continuation_ready = continuation_ready and normal
            projected = {"group_index": group_index, "stored_index": row["stored_index"],
                         "data_clear": clear, "membership_erase": member,
                         "actual_effects_observed": False, "actual_post_state": None}
            result["record_projections"].append(projected)
            for kind, effect in (("data_byte_14_clear", clear), ("membership_erase", member)):
                result["ordered_effects"].append({"kind": kind, "group_index": group_index,
                                                  "stored_index": row["stored_index"], **effect})
        characters, char_count = group.get("character_rows"), group.get("character_count_2c_raw")
        chars_known = _int(char_count) and (char_count == 0 or char_count > 0 and isinstance(characters, list) and len(characters) == char_count)
        if char_count == 0:
            characters = []
        if not chars_known:
            child_ready = False
            unknown_child_target = True
            result["missing_inputs"].append(f"groups[{group_index}].character_pointer_bound_traversal")
        for row in characters if isinstance(characters, list) and chars_known else []:
            admitted = row.get("character_child_1b8_present")
            ready = type(admitted) is bool
            alias = row.get("child_1b8_alias_ordinal")
            before = (child_values[alias] if alias in child_values else (None, None)
                      if unknown_child_target or alias in possible_child_targets else
                      (row.get("child_byte_108_raw"), row.get("child_character_reference_fc_raw")))
            effect = {"group_index": group_index, "stored_index": row["stored_index"],
                      "character_reference_id": row["character_reference_id"],
                      "character_resolved_id": row.get("character_resolved_id"),
                      "child_1b8_alias_ordinal": alias, "conditional_ready": ready,
                      "conditional_store_admitted": admitted, "conditional_byte_108_before": before[0],
                      "conditional_character_reference_fc_before": before[1],
                      "conditional_byte_108_after": 0 if admitted else None,
                      "conditional_character_reference_fc_after": -1 if admitted else None,
                      "conditional_byte_108_changed": before[0] != 0 if admitted and type(before[0]) is int else None,
                      "conditional_character_reference_fc_changed": before[1] != -1 if admitted and _int(before[1]) else None,
                      "source_store_order": ["byte108=0", "reload_Character_child1B8", "DWORD_FC=-1"],
                      "actual_effects_observed": False, "actual_post_state": None}
            if admitted and _int(alias):
                child_values[alias] = (0, -1)
            elif admitted is not False:
                if _int(alias):
                    possible_child_targets.add(alias)
                else:
                    unknown_child_target = True
            child_ready = child_ready and ready
            result["character_projections"].append(effect)
            result["ordered_effects"].append({"kind": "group_child_constants", **effect})
    combined = data_ready and membership_ready and child_ready and continuation_ready
    result.update(status="available" if combined else "partial", conditional_point_stores_ready=combined,
                  data_clears_ready=data_ready, conditional_membership_erases_ready=membership_ready,
                  group_child_stores_ready=child_ready, membership_source_continuations_ready=continuation_ready)
    result["membership_value_projections"] = [{"membership_alias_ordinal": alias, "conditional_ready": value is not None,
                                                "conditional_ordered_ids_after": None if value is None else list(value)}
                                               for alias, value in memberships.values.items()]
    result["data_value_projections"] = [{"data_alias_ordinal": alias, "conditional_byte_14_after": value}
                                        for alias, value in data_values.items()]
    result["child_value_projections"] = [{"child_1b8_alias_ordinal": alias, "conditional_byte_108_after": value[0],
                                         "conditional_character_reference_fc_after": value[1]} for alias, value in child_values.items()]
    return result
