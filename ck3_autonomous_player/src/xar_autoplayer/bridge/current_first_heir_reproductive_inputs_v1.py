"""Optional existing-query observation of the current heir's household inputs."""

from __future__ import annotations

from copy import deepcopy

from .driver import BridgeUnavailableError
from .player_child_marriage_value_private_transport import _native_fertility_input_valid

LEAF = "current_first_heir_reproductive_inputs_v1"



def _nullable_int(value: dict[str, object], key: str, low: int, high: int) -> None:
    if key not in value or (value[key] is not None and
            (type(value[key]) is not int or not low <= value[key] <= high)):
        raise BridgeUnavailableError(f"native conception {key} is malformed")


def _nullable_bool(value: dict[str, object], key: str) -> None:
    if key not in value or (value[key] is not None and type(value[key]) is not bool):
        raise BridgeUnavailableError(f"native conception {key} is malformed")


def _observation(value: object, source: str) -> dict[str, object]:
    if (not isinstance(value, dict) or value.get("source") != source
            or value.get("status") not in {"available", "unavailable"}
            or "unavailable_reason" not in value
            or (value["unavailable_reason"] is not None if value["status"] == "available"
                else not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"])):
        raise BridgeUnavailableError("native conception observation is malformed")
    return value


def _validate_conception_row_fields(row: dict[str, object]) -> None:
    if "native_conception_extended_gate" in row:
        gate = _observation(row["native_conception_extended_gate"], "native_conception_extended_gate")
        _nullable_bool(gate, "extended_data_present")
        _nullable_bool(gate, "blocks_pair_conception")
        _nullable_int(gate, "extended_288_raw_u64", 0, 2**64-1)
        if gate["status"] == "available":
            present, raw, blocked = (gate[k] for k in ("extended_data_present", "extended_288_raw_u64", "blocks_pair_conception"))
            if (type(present) is not bool or type(blocked) is not bool
                    or (raw is None if present else raw is not None or blocked)
                    or (present and blocked is not (raw != 0))):
                raise BridgeUnavailableError("native extended gate lost its zero/null distinction")
        elif gate["blocks_pair_conception"] is not None:
            raise BridgeUnavailableError("unavailable extended gate became a pair decision")
    if "native_conception_candidate_pending" in row:
        pending = _observation(row["native_conception_candidate_pending"], "native_conception_candidate_pending")
        _nullable_bool(pending, "extended_data_present")
        _nullable_int(pending, "candidate_flag_raw_u8", 0, 255)
        _nullable_int(pending, "target_pointer_raw_u64", 0, 2**64-1)
        _nullable_int(pending, "target_full_id_raw_u32", 0, 2**32-1)
        _nullable_int(pending, "resolved_target_character_id", -2**31, 2**31-1)
        target_status = pending.get("target_status")
        target_reason = pending.get("target_unavailable_reason")
        if (target_status not in {"not_sampled", "not_requested", "unavailable", "null_pointer", "invalid_identity", "generation_mismatch", "resolved"}
                or "target_unavailable_reason" not in pending
                or (target_reason is not None and (not isinstance(target_reason, str) or not target_reason))):
            raise BridgeUnavailableError("native pending target diagnostics are malformed")
        flag = pending["candidate_flag_raw_u8"]
        if pending["status"] == "available":
            if flag is None or pending["extended_data_present"] is not True:
                raise BridgeUnavailableError("available pending state lacks its actual byte")
            if flag == 0 and (target_status != "not_requested" or target_reason is not None
                    or any(pending[k] is not None for k in ("target_pointer_raw_u64", "target_full_id_raw_u32", "resolved_target_character_id"))):
                raise BridgeUnavailableError("zero pending byte sampled an unused target")
            if flag != 0 and target_status in {"not_sampled", "not_requested"}:
                raise BridgeUnavailableError("nonzero pending byte lost its target result")
        elif flag is not None or target_status != "not_sampled":
            raise BridgeUnavailableError("unavailable pending state became an observed byte")
        if target_status == "resolved":
            target_id = pending["target_full_id_raw_u32"]
            resolved = pending["resolved_target_character_id"]
            if (not pending["target_pointer_raw_u64"] or target_id in (None, 2**32-1)
                    or resolved is None or (resolved & (2**32-1)) != target_id or target_reason is not None):
                raise BridgeUnavailableError("pending target lost its complete generation identity")
        elif pending["resolved_target_character_id"] is not None:
            raise BridgeUnavailableError("unresolved pending target became a character")
        if target_status == "null_pointer" and (pending["target_pointer_raw_u64"] != 0
                or pending["target_full_id_raw_u32"] is not None or target_reason is not None):
            raise BridgeUnavailableError("null pending target lost its literal pointer zero")
        if target_status in {"unavailable", "invalid_identity", "generation_mismatch"} and not target_reason:
            raise BridgeUnavailableError("pending target failure lacks its reason")
    for key, source, i32_keys, i64_keys, output in (
        ("native_conception_first_value", "native_conception_first_value",
         ("adjusted_age_raw", "selected_age_band_index"),
         ("seed_after_children_raw", "age_product_raw", "first_output_raw"), "first_output_raw"),
        ("native_conception_second_value", "native_conception_second_value",
         ("adjusted_age_raw", "selected_age_band_index"),
         ("prefinal_raw", "second_output_raw"), "second_output_raw"),
    ):
        if key not in row:
            continue
        read = _observation(row[key], source)
        for field in i32_keys:
            _nullable_int(read, field, -2**31, 2**31-1)
        for field in i64_keys:
            _nullable_int(read, field, -2**63, 2**63-1)
        if (read["status"] == "available") is not (read[output] is not None):
            raise BridgeUnavailableError("native character provider output lacks its completed inputs")
    if "native_conception_secondary_context" in row:
        context = _observation(row["native_conception_secondary_context"], "native_conception_secondary_context")
        _nullable_int(context, "context_7d8_raw_i32", -2**31, 2**31-1)
        _nullable_bool(context, "selects_alternate_relation_path")
        steps = context.get("resolution")
        if not isinstance(steps, list) or len(steps) != 3:
            raise BridgeUnavailableError("native secondary context lost its three actual resolutions")
        for step in steps:
            if not isinstance(step, dict) or step.get("status") not in {"not_read", "resolved_full_id", "native_fallback"}:
                raise BridgeUnavailableError("native secondary resolution is malformed")
            _nullable_int(step, "requested_full_id_raw_u32", 0, 2**32-1)
        if context["status"] == "available":
            if (context["context_7d8_raw_i32"] is None
                    or context["selects_alternate_relation_path"] is not (context["context_7d8_raw_i32"] > 0)):
                raise BridgeUnavailableError("native secondary branch lost its signed field")
        elif context["selects_alternate_relation_path"] is not None:
            raise BridgeUnavailableError("unread secondary context became a branch")


def _validate_conception_pair_fields(value: object, heir: int, relation: dict[str, object]) -> None:
    read = _observation(value, "native_current_heir_household_conception_pair_inputs")
    pairs = read.get("pairs")
    if (type(read.get("provider_mode_raw")) is not int or read["provider_mode_raw"] != 3
            or type(read.get("provider_fifth_argument_raw")) is not int or read["provider_fifth_argument_raw"] != 0
            or not isinstance(pairs, list)):
        raise BridgeUnavailableError("conception pair scope is malformed")
    spouses: list[int] = []
    for character_id in [relation.get("primary_spouse_character_id"), *relation.get("spouse_character_ids", [])]:
        if type(character_id) is int and character_id > 0 and character_id != heir and character_id not in spouses:
            spouses.append(character_id)
    if read["status"] == "unavailable":
        if pairs:
            raise BridgeUnavailableError("unavailable conception frame retains pair inputs")
        return
    if len(pairs) != len(spouses):
        raise BridgeUnavailableError("conception pairs differ from the current married household")
    for pair, spouse in zip(pairs, spouses):
        if (not isinstance(pair, dict) or type(pair.get("first_character_id")) is not int
                or pair["first_character_id"] != heir or type(pair.get("second_character_id")) is not int
                or pair["second_character_id"] != spouse):
            raise BridgeUnavailableError("native conception pair identity changed")
        base = _observation(pair.get("conditional_base_stage"), "conditional_native_conception_base_stage")
        _nullable_int(base, "base_raw", -2**63, 2**63-1)
        if (base.get("branch") not in {"unavailable", "signed_minimum", "fast_scale", "split_scale"}
                or (base["status"] == "available") is not (base["base_raw"] is not None)
                or (base["status"] == "unavailable") is not (base["branch"] == "unavailable")):
            raise BridgeUnavailableError("conditional base stage lost its raw output")
        loaded = _observation(pair.get("loaded_numeric_inputs"), "native_conception_loaded_numeric_inputs")
        _nullable_int(loaded, "failed_slot_rva", 0, 2**32-1)
        for key in ("base_average_floor", "linked_pair_addend", "linked_pair_title_state_addend",
                    "both_title_state_absent_multiplier", "first_relation_multiplier",
                    "second_relation_multiplier", "alternate_relation_multiplier"):
            _nullable_int(loaded, key, -2**63, 2**63-1)
            if (loaded["status"] == "available") is not (loaded[key] is not None):
                raise BridgeUnavailableError("loaded numerical input became an inferred zero")
        bonus = _observation(pair.get("native_pair_list_bonus"), "native_conception_pair_list_bonus")
        for key in ("first_child_count_raw", "second_child_count_raw"):
            _nullable_int(bonus, key, -2**31, 2**31-1)
        for key in ("primary_relation_match", "first_list_has_second_parent_witness",
                    "second_list_has_first_parent_witness", "either_land_state_present",
                    "apply_relation_bonus", "apply_land_state_bonus"):
            _nullable_bool(bonus, key)
        if bonus["status"] == "available" and any(bonus[k] is None for k in ("apply_relation_bonus", "apply_land_state_bonus")):
            raise BridgeUnavailableError("available bonus condition lacks its result")
        related = _observation(pair.get("native_related_pair"), "native_conception_related_pair")
        for key in ("second_to_first_28b3c10", "first_to_second_28b3c10", "first_second_28b3e50", "related_pair_predicate"):
            _nullable_bool(related, key)
        if (related["status"] == "available") is not (related["related_pair_predicate"] is not None):
            raise BridgeUnavailableError("related pair lacks its completed predicate")
        if not isinstance(related.get("raw_characters"), list):
            raise BridgeUnavailableError("native related pair raw inputs are malformed")
        for raw in related["raw_characters"]:
            if not isinstance(raw, dict):
                raise BridgeUnavailableError("native related Character row is malformed")
            for key in ("magic_raw_u32", "full_id_raw_u32", "parent_slot0_full_id", "parent_slot1_full_id"):
                _nullable_int(raw, key, 0, 2**32-1)
            _nullable_bool(raw, "relationship_block_present")
        role = pair.get("role_selection")
        if not isinstance(role, dict):
            raise BridgeUnavailableError("native role selection is malformed")
        _nullable_bool(role, "first_title_state_present")
        for key in ("first_highest_tier_raw", "second_highest_tier_raw", "selected_character_id"):
            _nullable_int(role, key, -2**31, 2**31-1)
        if role["selected_character_id"] not in (None, heir, spouse):
            raise BridgeUnavailableError("native child-limit receiver escaped the household pair")
        tiers = _observation(pair.get("native_lineage_tiers"), "native_conception_pair_lineage_tiers")
        for key in ("first_lineage_tier_max_raw", "second_lineage_tier_max_raw", "pair_lineage_tier_max_raw"):
            _nullable_int(tiers, key, -2**31, 2**31-1)
        if tiers.get("maximum_return_role") not in (None, "first", "second"):
            raise BridgeUnavailableError("native lineage maximum role is malformed")
        limit = _observation(pair.get("native_child_limit"), "native_conception_child_limit")
        for key in ("table_base_raw", "selected_relation20_living_count_raw", "selected_relation50_count_raw",
                    "accumulated_before_decrement_raw", "child_limit_raw"):
            _nullable_int(limit, key, -2**31, 2**31-1)
        _nullable_int(limit, "decrement_threshold_raw", -2**63, 2**63-1)
        _nullable_int(limit, "deterministic_remainder_raw", 0, 2**32-1)
        _nullable_bool(limit, "decremented")
        if (limit["status"] == "available") is not (limit["child_limit_raw"] is not None):
            raise BridgeUnavailableError("native child-limit output became an incomplete threshold")
        count = _observation(pair.get("native_offspring_count"), "native_conception_selected_role_offspring_count")
        _nullable_bool(count, "family_component_present")
        _nullable_int(count, "offspring_list_count_raw_i32", -2**31, 2**31-1)
        _nullable_int(count, "native_count", -2**31, 2**31-1)
        if (count["status"] == "available") is not (count["native_count"] is not None):
            raise BridgeUnavailableError("native offspring aggregate became a partial count")
        if not isinstance(count.get("rows"), list):
            raise BridgeUnavailableError("native offspring occurrences are malformed")
        for raw in count["rows"]:
            if not isinstance(raw, dict) or type(raw.get("requested_full_id_raw_u32")) is not int:
                raise BridgeUnavailableError("native offspring full-ID occurrence is malformed")
            for key in ("requested_full_id_raw_u32", "matched_full_id_raw_u32"):
                _nullable_int(raw, key, 0, 2**32-1)
            _nullable_int(raw, "character_1d0_raw_u64", 0, 2**64-1)
            for key in ("trait_count_raw_i32", "first_matching_trait_id"):
                _nullable_int(raw, key, -2**31, 2**31-1)
            for key in ("used_character_fallback", "trait_4a9_equals_one", "counted"):
                _nullable_bool(raw, key)
        _nullable_bool(pair, "alternate_relation_path")
        short = _observation(pair.get("conditional_short_circuit"), "conditional_actual4_pair_provider_shortcircuit")
        _nullable_bool(short, "short_circuits_to_zero")
        _nullable_int(short, "first_output_raw", -2**63, 2**63-1)
        if (not isinstance(short.get("branch_reason"), str)
                or type(short.get("first_evaluated")) is not bool or type(short.get("second_evaluated")) is not bool
                or (short["status"] == "available") is not (short["short_circuits_to_zero"] is not None)
                or (short["short_circuits_to_zero"] is True and short["first_output_raw"] != 0)
                or (short["short_circuits_to_zero"] is not True and short["first_output_raw"] is not None)):
            raise BridgeUnavailableError("conditional short circuit became a final pair value")
        for key in ("first", "second"):
            predicate = _observation(short.get(key), "conditional_native_conception_character_predicate")
            _nullable_bool(predicate, "predicate_true")
            for field in ("selected_measure", "selected_minimum", "adjusted_maximum"):
                _nullable_int(predicate, field, -2**31, 2**31-1)
            _nullable_int(predicate, "rounded_modifier", -2**63, 2**63-1)
            _nullable_int(predicate, "first_blocking_trait_occurrence", 0, 2**32-1)
            if (type(predicate.get("trait_occurrences_evaluated")) is not int
                    or not 0 <= predicate["trait_occurrences_evaluated"] < 2**32
                    or not isinstance(predicate.get("branch_reason"), str)
                    or (predicate["status"] == "available") is not (predicate["predicate_true"] is not None)):
                raise BridgeUnavailableError("native character predicate is malformed")
        date = _observation(pair.get("native_last_child_date"), "native_conception_last_child_date")
        if (date.get("branch_status") not in {"unavailable", "mode_bit0_disabled", "family_absent_bypass", "children_empty_bypass", "conditional_date_comparison_available"}
                or type(date.get("date_helper_demanded")) is not bool):
            raise BridgeUnavailableError("native last-child date branch is malformed")
        for key in ("first_family_present", "selected_is_native_fallback", "recent_child_branch_passed"):
            _nullable_bool(date, key)
        for key in ("child_count_raw", "loaded_month_shift_raw_i32", "current_date_raw_i32", "adjusted_date_raw_i32"):
            _nullable_int(date, key, -2**31, 2**31-1)
        for key in ("last_requested_full_id_raw_u32", "selected_full_id_raw_u32"):
            _nullable_int(date, key, 0, 2**32-1)
        for key in ("selected_date_storage_raw64", "adjusted_date_storage_raw64"):
            _nullable_int(date, key, -2**63, 2**63-1)
        if (date["status"] == "available") is not (date["recent_child_branch_passed"] is not None):
            raise BridgeUnavailableError("native last-child condition became an unread date")


def validate_current_first_heir_reproductive_inputs_v1(
    value: object, *, actor: int, heir: int | None, native_revision: int,
    date_raw: int, relation: dict[str, object],
) -> dict[str, object]:
    """Retain native zero and signed raw values as independent readonly evidence."""
    if not isinstance(value, dict):
        raise BridgeUnavailableError("current household inputs are malformed")
    status, reason, rows = (value.get(key) for key in ("status", "unavailable_reason", "rows"))
    if (value.get("source") != "native_current_heir_household_inputs"
            or status not in {"available", "partial", "unavailable"}
            or (reason is not None if status == "available"
                else not isinstance(reason, str) or not reason)
            or value.get("native_revision") != native_revision
            or value.get("played_character_id") not in (None, actor)
            or value.get("heir_character_id") != heir
            or value.get("date_raw") not in (None, date_raw)
            or value.get("fertility_raw_scale") != 100000
            or not isinstance(rows, list)):
        raise BridgeUnavailableError("current household inputs crossed the native frame")
    if status == "unavailable":
        if rows:
            raise BridgeUnavailableError("unavailable household retains observed rows")
        if "conception_pair_inputs" in value:
            pair_inputs = _observation(value["conception_pair_inputs"],
                "native_current_heir_household_conception_pair_inputs")
            if pair_inputs["status"] != "unavailable":
                raise BridgeUnavailableError("unavailable household retains a conception frame")
            _validate_conception_pair_fields(pair_inputs, heir, relation)
        return deepcopy(value)
    if (value.get("played_character_id") != actor or value.get("date_raw") != date_raw
            or relation.get("status") != "available" or heir is None):
        raise BridgeUnavailableError("available household lacks its current relation")
    expected: dict[int, list[str]] = {}

    def add(character_id: object, role: str) -> None:
        if type(character_id) is int and character_id > 0:
            roles = expected.setdefault(character_id, [])
            if role not in roles:
                roles.append(role)

    add(heir, "heir")
    add(relation.get("primary_spouse_character_id"), "primary_spouse")
    for character_id in relation.get("spouse_character_ids", []):
        add(character_id, "spouse")
    add(relation.get("betrothed_character_id"), "betrothed")
    if len(rows) != len(expected):
        raise BridgeUnavailableError("household receivers differ from the current relation")
    all_available = True
    for row, (character_id, roles) in zip(rows, expected.items()):
        if (not isinstance(row, dict) or row.get("character_id") != character_id
                or row.get("roles") != roles or row.get("status") not in {"available", "unavailable"}):
            raise BridgeUnavailableError("household receiver identity changed")
        if "native_pregnancy" in row:
            pregnancy = row["native_pregnancy"]
            if (not isinstance(pregnancy, dict)
                    or pregnancy.get("source") != "native_is_pregnant"
                    or pregnancy.get("status") not in {"available", "unavailable"}
                    or "unavailable_reason" not in pregnancy
                    or "is_pregnant" not in pregnancy):
                raise BridgeUnavailableError("native household pregnancy is malformed")
            if pregnancy["status"] == "available":
                if (pregnancy["unavailable_reason"] is not None
                        or type(pregnancy["is_pregnant"]) is not bool):
                    raise BridgeUnavailableError("available native pregnancy lacks its boolean")
            elif (pregnancy["is_pregnant"] is not None
                    or not isinstance(pregnancy["unavailable_reason"], str)
                    or not pregnancy["unavailable_reason"]):
                raise BridgeUnavailableError("unavailable native pregnancy became a boolean")
        if "native_conception_trait_exclusion" in row:
            exclusion = row["native_conception_trait_exclusion"]
            if (not isinstance(exclusion, dict)
                    or exclusion.get("source") != "native_conception_trait_exclusion"
                    or exclusion.get("status") not in {"available", "unavailable"}
                    or "unavailable_reason" not in exclusion
                    or "blocks_pair_conception" not in exclusion):
                raise BridgeUnavailableError("native household conception trait exclusion is malformed")
            if exclusion["status"] == "available":
                if (exclusion["unavailable_reason"] is not None
                        or type(exclusion["blocks_pair_conception"]) is not bool):
                    raise BridgeUnavailableError("available native conception trait exclusion lacks its boolean")
            elif (exclusion["blocks_pair_conception"] is not None
                    or not isinstance(exclusion["unavailable_reason"], str)
                    or not exclusion["unavailable_reason"]):
                raise BridgeUnavailableError("unavailable native conception trait exclusion became a boolean")
        _validate_conception_row_fields(row)
        available = row["status"] == "available"
        all_available = all_available and available
        if available:
            fertility = row.get("native_fertility")
            if (row.get("unavailable_reason") is not None
                    or type(row.get("age_measure_raw")) is not int
                    or not -2**15 <= row["age_measure_raw"] < 2**15
                    or type(row.get("sex_selector_raw")) is not int
                    or row["sex_selector_raw"] not in (0, 1)
                    or not _native_fertility_input_valid(fertility)
                    or not -2**63 <= fertility["effective_raw"] < 2**63):
                raise BridgeUnavailableError("observed household value is malformed")
        elif (not isinstance(row.get("unavailable_reason"), str)
                or not row["unavailable_reason"]
                or any(row.get(key) is not None for key in (
                    "age_measure_raw", "sex_selector_raw", "native_fertility"))):
            raise BridgeUnavailableError("unavailable household value became native zero")
    if (status == "available") is not all_available:
        raise BridgeUnavailableError("household availability disagrees with observed values")
    if "conception_pair_inputs" in value:
        _validate_conception_pair_fields(value["conception_pair_inputs"], heir, relation)
    return deepcopy(value)
