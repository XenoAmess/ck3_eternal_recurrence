#include "xar_bridge/current_first_heir_relationship_v1.hpp"
#include "xar_bridge/current_first_heir_child_inputs_json_v1.hpp"
#include "xar_bridge/current_first_heir_conception_trait_inputs_v1.hpp"
#include "xar_bridge/current_first_heir_conception_candidate_inputs_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <algorithm>

namespace xar::ck3_11906 {
namespace {
void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}
std::string_view CurrentFirstHeirRelationshipFailureKeyV1(
    CurrentFirstHeirRelationshipFailureV1 failure) {
  using Failure = CurrentFirstHeirRelationshipFailureV1;
  switch (failure) {
  case Failure::none: return "none";
  case Failure::frame_changed: return "frame_changed";
  case Failure::heir_unavailable: return "heir_unavailable";
  case Failure::relationship_unavailable: return "relationship_unavailable";
  case Failure::partner_unavailable: return "partner_unavailable";
  case Failure::bilateral_inconsistent: return "bilateral_inconsistent";
  }
  return "unknown";
}

template <typename T>
void AppendOptionalNumber(std::string &json, const std::optional<T> &value) {
  json += value.has_value() ? std::to_string(*value) : "null";
}

void AppendOptionalBoolean(std::string &json, const std::optional<bool> &value) {
  json += value.has_value() ? (*value ? "true" : "false") : "null";
}


void AppendObservationHeader(std::string &json, std::string_view source,
                             std::string_view status, std::string_view reason) {
  json += "{\"source\":";
  AppendJsonString(json, source);
  json += ",\"status\":";
  AppendJsonString(json, status);
  json += ",\"unavailable_reason\":";
  if (status == "available") json += "null";
  else AppendJsonString(json, reason.empty() ? "native_input_unavailable" : reason);
}
template <typename T>
void AppendObservationNumber(std::string &json, std::string_view name,
                             const std::optional<T> &value) {
  json += ",\""; json += name; json += "\":";
  AppendOptionalNumber(json, value);
}
void AppendObservationBoolean(std::string &json, std::string_view name,
                              const std::optional<bool> &value) {
  json += ",\""; json += name; json += "\":";
  AppendOptionalBoolean(json, value);
}
void AppendCurrentConceptionRow(std::string &json,
    const CurrentCharacterConceptionCandidateRowV1 &row) {
  const auto &extended = row.extended_gate;
  json += ",\"native_conception_extended_gate\":";
  AppendObservationHeader(json, extended.source, extended.status, extended.unavailable_reason);
  AppendObservationBoolean(json, "extended_data_present", extended.extended_data_present);
  AppendObservationNumber(json, "extended_288_raw_u64", extended.extended_288_raw_u64);
  AppendObservationBoolean(json, "blocks_pair_conception", extended.blocks_pair_conception);
  json += '}';
  const auto &pending = row.pending_candidate;
  json += ",\"native_conception_candidate_pending\":";
  AppendObservationHeader(json, "native_conception_candidate_pending",
      pending.candidate_state_available ? "available" : "unavailable",
      pending.candidate_state_unavailable_reason);
  AppendObservationBoolean(json, "extended_data_present", pending.extended_data_present);
  AppendObservationNumber(json, "candidate_flag_raw_u8", pending.candidate_flag_raw);
  json += ",\"target_status\":";
  AppendJsonString(json, pending.target_status);
  json += ",\"target_unavailable_reason\":";
  if (pending.target_unavailable_reason.empty()) json += "null";
  else AppendJsonString(json, pending.target_unavailable_reason);
  AppendObservationNumber(json, "target_pointer_raw_u64", pending.target_pointer_raw);
  AppendObservationNumber(json, "target_full_id_raw_u32", pending.target_full_id_raw);
  AppendObservationNumber(json, "resolved_target_character_id", pending.resolved_target_character_id);
  json += '}';
  const auto &first = row.first_value;
  json += ",\"native_conception_first_value\":";
  AppendObservationHeader(json, first.source, first.status, first.unavailable_reason);
  AppendObservationNumber(json, "seed_after_children_raw", first.seed_after_children_raw);
  AppendObservationNumber(json, "adjusted_age_raw", first.adjusted_age_raw);
  AppendObservationNumber(json, "selected_age_band_index", first.selected_age_band_index);
  AppendObservationNumber(json, "age_product_raw", first.age_product_raw);
  AppendObservationNumber(json, "first_output_raw", first.first_output_raw);
  json += '}';
  const auto &second = row.second_value;
  json += ",\"native_conception_second_value\":";
  AppendObservationHeader(json, "native_conception_second_value",
      second.ready ? "available" : "unavailable", second.reason);
  AppendObservationNumber(json, "adjusted_age_raw", second.adjusted_age_raw);
  AppendObservationNumber(json, "selected_age_band_index", second.selected_band_index);
  AppendObservationNumber(json, "prefinal_raw", second.prefinal_raw);
  AppendObservationNumber(json, "second_output_raw", second.value_raw);
  json += '}';
  const auto &context = row.secondary_context;
  json += ",\"native_conception_secondary_context\":";
  AppendObservationHeader(json, context.source, context.status, context.unavailable_reason);
  AppendObservationNumber(json, "context_7d8_raw_i32", context.context_7d8_raw_i32);
  AppendObservationBoolean(json, "selects_alternate_relation_path", context.selects_alternate_relation_path);
  json += ",\"resolution\":[";
  for (std::size_t i = 0; i < context.resolution.size(); ++i) {
    if (i != 0) json += ',';
    json += "{\"status\":";
    AppendJsonString(json, context.resolution[i].status);
    AppendObservationNumber(json, "requested_full_id_raw_u32", context.resolution[i].requested_full_id);
    json += '}';
  }
  json += "]}";
}

std::string CurrentConceptionPairInputsJsonV1(
    const CurrentFirstHeirConceptionCandidateInputsReadV1 &read) {
  std::string json;
  AppendObservationHeader(json, "native_current_heir_household_conception_pair_inputs",
                          read.status, read.unavailable_reason);
  json += ",\"provider_mode_raw\":3,\"provider_fifth_argument_raw\":0,\"pairs\":[";
  for (std::size_t i = 0; i < read.pairs.size(); ++i) {
    if (i != 0) json += ',';
    const auto &pair = read.pairs[i];
    json += "{\"first_character_id\":" + std::to_string(pair.first_character_id);
    json += ",\"second_character_id\":" + std::to_string(pair.second_character_id);
    json += ",\"conditional_base_stage\":";
    const bool base_available = pair.base_stage.status == ck3_12004::conception_pair_value_inputs::BaseStatus::available;
    std::string_view base_reason = "native_base_first_raw_unavailable";
    if (pair.base_stage.status == ck3_12004::conception_pair_value_inputs::BaseStatus::second_raw_unavailable)
      base_reason = "native_base_second_raw_unavailable";
    else if (pair.base_stage.status == ck3_12004::conception_pair_value_inputs::BaseStatus::floor_unavailable)
      base_reason = "native_base_loaded_floor_unavailable";
    AppendObservationHeader(json, "conditional_native_conception_base_stage",
        base_available ? "available" : "unavailable", base_reason);
    std::string_view branch = "unavailable";
    using Branch = ck3_12004::conception_pair_value_inputs::BaseBranch;
    if (pair.base_stage.branch == Branch::signed_minimum) branch = "signed_minimum";
    else if (pair.base_stage.branch == Branch::fast_scale) branch = "fast_scale";
    else if (pair.base_stage.branch == Branch::split_scale) branch = "split_scale";
    json += ",\"branch\":"; AppendJsonString(json, branch);
    AppendObservationNumber(json, "base_raw", pair.base_stage.raw);
    json += '}';
    json += ",\"loaded_numeric_inputs\":";
    const auto &loaded = pair.loaded_numeric;
    AppendObservationHeader(json, "native_conception_loaded_numeric_inputs",
        loaded.inputs ? "available" : "unavailable", "native_loaded_numeric_slot_unavailable");
    AppendObservationNumber(json, "failed_slot_rva", loaded.inputs ? std::optional<std::uint32_t>{} : loaded.failed_slot_rva);
    const auto scalar = [&](std::string_view name, std::int64_t ck3_12004::conception_pair_value_inputs::LoadedNumericInputs::*member) {
      AppendObservationNumber(json, name, loaded.inputs ? std::optional<std::int64_t>{(*loaded.inputs).*member} : std::nullopt);
    };
    using Slots = ck3_12004::conception_pair_value_inputs::LoadedNumericInputs;
    scalar("base_average_floor", &Slots::base_average_floor);
    scalar("linked_pair_addend", &Slots::linked_pair_addend);
    scalar("linked_pair_title_state_addend", &Slots::linked_pair_title_state_addend);
    scalar("both_title_state_absent_multiplier", &Slots::both_title_state_absent_multiplier);
    scalar("first_relation_multiplier", &Slots::first_relation_multiplier);
    scalar("second_relation_multiplier", &Slots::second_relation_multiplier);
    scalar("alternate_relation_multiplier", &Slots::alternate_relation_multiplier);
    json += '}';
    const auto &bonus = pair.list_bonus;
    json += ",\"native_pair_list_bonus\":";
    AppendObservationHeader(json, "native_conception_pair_list_bonus", bonus.status, bonus.unavailable_reason);
    AppendObservationBoolean(json, "primary_relation_match", bonus.primary_relation_match);
    AppendObservationNumber(json, "first_child_count_raw", bonus.first_child_count_raw);
    AppendObservationNumber(json, "second_child_count_raw", bonus.second_child_count_raw);
    AppendObservationBoolean(json, "first_list_has_second_parent_witness", bonus.first_list_has_second_parent_witness);
    AppendObservationBoolean(json, "second_list_has_first_parent_witness", bonus.second_list_has_first_parent_witness);
    AppendObservationBoolean(json, "either_land_state_present", bonus.either_land_state_present);
    AppendObservationBoolean(json, "apply_relation_bonus", bonus.apply_relation_bonus);
    AppendObservationBoolean(json, "apply_land_state_bonus", bonus.apply_land_state_bonus);
    json += '}';
    const auto &related = pair.related_pair;
    json += ",\"native_related_pair\":";
    AppendObservationHeader(json, related.source, related.status, related.unavailable_reason);
    AppendObservationBoolean(json, "second_to_first_28b3c10", related.second_to_first_28b3c10);
    AppendObservationBoolean(json, "first_to_second_28b3c10", related.first_to_second_28b3c10);
    AppendObservationBoolean(json, "first_second_28b3e50", related.first_second_28b3e50);
    AppendObservationBoolean(json, "related_pair_predicate", related.related_pair_predicate);
    json += ",\"raw_characters\":[";
    for (std::size_t j = 0; j < related.raw_characters.size(); ++j) {
      if (j != 0) json += ',';
      const auto &r = related.raw_characters[j];
      json += '{';
      json += "\"magic_raw_u32\":"; AppendOptionalNumber(json, r.magic_raw_u32);
      AppendObservationNumber(json, "full_id_raw_u32", r.full_id_raw_u32);
      AppendObservationBoolean(json, "relationship_block_present", r.relationship_block_present);
      AppendObservationNumber(json, "parent_slot0_full_id", r.parent_slot0_full_id);
      AppendObservationNumber(json, "parent_slot1_full_id", r.parent_slot1_full_id);
      json += '}';
    }
    json += "]}";
    json += ",\"role_selection\":{\"first_title_state_present\":";
    AppendOptionalBoolean(json, pair.first_title_state_present);
    AppendObservationNumber(json, "first_highest_tier_raw", pair.first_highest_tier_raw);
    AppendObservationNumber(json, "second_highest_tier_raw", pair.second_highest_tier_raw);
    AppendObservationNumber(json, "selected_character_id", pair.selected_character_id);
    json += '}';
    const auto &tiers = pair.lineage_tiers;
    json += ",\"native_lineage_tiers\":";
    AppendObservationHeader(json, "native_conception_pair_lineage_tiers", tiers.status, tiers.unavailable_reason);
    AppendObservationNumber(json, "first_lineage_tier_max_raw", tiers.first_lineage_tier_max_raw);
    AppendObservationNumber(json, "second_lineage_tier_max_raw", tiers.second_lineage_tier_max_raw);
    AppendObservationNumber(json, "pair_lineage_tier_max_raw", tiers.pair_lineage_tier_max_raw);
    json += ",\"maximum_return_role\":";
    if (!tiers.maximum_return_role) json += "null";
    else AppendJsonString(json, *tiers.maximum_return_role == ck3_12004::ConceptionPairMaxReturnRole::first ? "first" : "second");
    json += '}';
    const auto &limit = pair.child_limit;
    json += ",\"native_child_limit\":";
    AppendObservationHeader(json, limit.source, limit.status == "complete" ? "available" : "unavailable", limit.unavailable_reason);
    AppendObservationNumber(json, "table_base_raw", limit.inputs.table_base_raw);
    AppendObservationNumber(json, "selected_relation20_living_count_raw", limit.inputs.selected_relation20_living_count_raw);
    AppendObservationNumber(json, "selected_relation50_count_raw", limit.inputs.selected_relation50_count_raw);
    AppendObservationNumber(json, "decrement_threshold_raw", limit.inputs.decrement_threshold_raw);
    AppendObservationNumber(json, "accumulated_before_decrement_raw", limit.value.accumulated_before_decrement_raw);
    AppendObservationNumber(json, "deterministic_remainder_raw", limit.value.deterministic_remainder_raw);
    AppendObservationBoolean(json, "decremented", limit.value.decremented);
    AppendObservationNumber(json, "child_limit_raw", limit.value.child_limit_raw);
    json += '}';
    const auto &count = pair.offspring_count;
    json += ",\"native_offspring_count\":";
    AppendObservationHeader(json, count.source, count.status, count.unavailable_reason);
    AppendObservationBoolean(json, "family_component_present", count.family_component_present);
    AppendObservationNumber(json, "offspring_list_count_raw_i32", count.offspring_list_count_raw_i32);
    AppendObservationNumber(json, "native_count", count.native_count);
    json += ",\"rows\":[";
    for (std::size_t j = 0; j < count.rows.size(); ++j) {
      if (j != 0) json += ',';
      const auto &r = count.rows[j];
      json += "{\"requested_full_id_raw_u32\":" + std::to_string(r.requested_full_id);
      AppendObservationBoolean(json, "used_character_fallback", r.used_character_fallback);
      AppendObservationNumber(json, "matched_full_id_raw_u32", r.matched_full_id);
      AppendObservationNumber(json, "character_1d0_raw_u64", r.character_1d0_raw_u64);
      AppendObservationNumber(json, "trait_count_raw_i32", r.trait_count_raw_i32);
      AppendObservationBoolean(json, "trait_4a9_equals_one", r.trait_4a9_equals_one);
      AppendObservationNumber(json, "first_matching_trait_id", r.first_matching_trait_id);
      AppendObservationBoolean(json, "counted", r.counted);
      json += '}';
    }
    json += "]}";
    if (pair.natural_conception_observations_json) {
      json += ",\"natural_conception_observations_v1\":";
      json += *pair.natural_conception_observations_json;
    }
    const auto &short_circuit = pair.short_circuit;
    json += ",\"conditional_short_circuit\":";
    AppendObservationHeader(json, short_circuit.source, short_circuit.status, short_circuit.reason);
    json += ",\"branch_reason\":"; AppendJsonString(json, short_circuit.reason);
    json += ",\"first_evaluated\":"; json += short_circuit.first_evaluated ? "true" : "false";
    json += ",\"second_evaluated\":"; json += short_circuit.second_evaluated ? "true" : "false";
    AppendObservationBoolean(json, "short_circuits_to_zero", short_circuit.short_circuits_to_zero);
    AppendObservationNumber(json, "first_output_raw", short_circuit.first_output_raw);
    const auto predicate = [&](std::string_view name,
        const ck3_12004::ConceptionCharacterPredicate12004Read &r) {
      json += ",\""; json += name; json += "\":";
      AppendObservationHeader(json, "conditional_native_conception_character_predicate", r.status, r.reason);
      json += ",\"branch_reason\":"; AppendJsonString(json, r.reason);
      AppendObservationBoolean(json, "predicate_true", r.predicate_true);
      AppendObservationNumber(json, "selected_measure", r.selected_measure);
      AppendObservationNumber(json, "selected_minimum", r.selected_minimum);
      AppendObservationNumber(json, "adjusted_maximum", r.adjusted_maximum);
      AppendObservationNumber(json, "rounded_modifier", r.rounded_modifier);
      json += ",\"trait_occurrences_evaluated\":" + std::to_string(r.trait_occurrences_evaluated);
      AppendObservationNumber(json, "first_blocking_trait_occurrence", r.first_blocking_trait_occurrence);
      json += '}';
    };
    predicate("first", short_circuit.first);
    predicate("second", short_circuit.second);
    json += '}';
    const auto &date = pair.last_child_date;
    json += ",\"native_last_child_date\":";
    AppendObservationHeader(json, "native_conception_last_child_date",
        date.date_inputs_available ? "available" : "unavailable", date.unavailable_reason);
    json += ",\"branch_status\":"; AppendJsonString(json, date.status);
    json += ",\"date_helper_demanded\":"; json += date.date_helper_demanded ? "true" : "false";
    AppendObservationBoolean(json, "first_family_present", date.source.first_family_present);
    AppendObservationNumber(json, "child_count_raw", date.source.child_count_raw);
    AppendObservationNumber(json, "last_requested_full_id_raw_u32", date.source.last_requested_full_id_raw);
    AppendObservationNumber(json, "selected_full_id_raw_u32", date.source.selected_full_id_raw);
    AppendObservationBoolean(json, "selected_is_native_fallback", date.source.selected_is_native_fallback);
    AppendObservationNumber(json, "selected_date_storage_raw64", date.selected_date_storage_raw64);
    AppendObservationNumber(json, "loaded_month_shift_raw_i32", date.loaded_month_shift_raw_i32);
    AppendObservationNumber(json, "current_date_raw_i32", date.current_date_raw_i32);
    AppendObservationNumber(json, "adjusted_date_raw_i32", date.adjusted_date_raw_i32);
    AppendObservationNumber(json, "adjusted_date_storage_raw64", date.adjusted_date_storage_raw64);
    AppendObservationBoolean(json, "recent_child_branch_passed", date.recent_child_branch_passed);
    json += '}';
    AppendObservationBoolean(json, "alternate_relation_path", pair.alternate_relation_path);
    const auto &close = pair.normal_close_family;
    json += ",\"native_normal_close_family\":";
    AppendObservationHeader(json, close.source, close.status, close.unavailable_reason);
    AppendObservationBoolean(json, "normal_close_family", close.normal_close_family);
    AppendObservationBoolean(json, "native_return_value", close.native_return_value);
    AppendObservationBoolean(json, "native_call_attempted",
                             std::optional<bool>{close.native_call_attempted});
    AppendObservationNumber(json, "first_full_id_before", close.first_full_id_before);
    AppendObservationNumber(json, "second_full_id_before", close.second_full_id_before);
    AppendObservationNumber(json, "first_full_id_after", close.first_full_id_after);
    AppendObservationNumber(json, "second_full_id_after", close.second_full_id_after);
    json += '}';

    json += ",\"native_second_title_state\":";
    AppendObservationHeader(json, "native_conception_second_title_state",
        pair.second_title_state_status, pair.second_title_state_unavailable_reason);
    AppendObservationNumber(json, "second_1c0_raw_u64", pair.second_1c0_raw_u64);
    AppendObservationBoolean(json, "second_title_state_present", pair.second_title_state_present);
    json += '}';
    const auto &membership = pair.secondary_family_membership;
    json += ",\"native_secondary_family_membership\":";
    AppendObservationHeader(json, "native_conception_secondary_family_membership",
                            membership.status, membership.unavailable_reason);
    AppendObservationBoolean(json, "second_family_present", membership.second_family_present);
    AppendObservationBoolean(json, "list_data_present", membership.list_data_present);
    AppendObservationNumber(json, "list_count_raw_i32", membership.list_count_raw_i32);
    AppendObservationNumber(json, "list_span_bytes", membership.list_span_bytes);
    AppendObservationNumber(json, "first_match_index", membership.first_match_index);
    AppendObservationBoolean(json, "second_family20_contains_first", membership.second_family20_contains_first);
    json += ",\"ordered_full_ids\":[";
    for (std::size_t index = 0; index < membership.ordered_full_ids.size(); ++index) {
      if (index != 0) json += ',';
      json += std::to_string(membership.ordered_full_ids[index]);
    }
    json += "]}";
    const auto &reverse = pair.reverse_close_or_extended;
    json += ",\"native_reverse_close_or_extended\":";
    AppendObservationHeader(json, reverse.source, reverse.status, reverse.unavailable_reason);
    AppendObservationBoolean(json, "alternate_close_or_extended", reverse.alternate_close_or_extended);
    json += '}';
    const auto &numeric = pair.provider_numeric;
    const std::array<std::optional<std::int64_t>, 7> scalar_values{
        numeric.base_average_floor, numeric.linked_pair_addend,
        numeric.linked_pair_title_state_addend, numeric.both_title_state_absent_multiplier,
        numeric.first_relation_multiplier, numeric.second_relation_multiplier,
        numeric.alternate_relation_multiplier};
    constexpr std::array<std::string_view, 7> scalar_names{
        "base_average_floor", "linked_pair_addend", "linked_pair_title_state_addend",
        "both_title_state_absent_multiplier", "first_relation_multiplier",
        "second_relation_multiplier", "alternate_relation_multiplier"};
    std::uint32_t mask = 0;
    for (std::size_t index = 0; index < scalar_values.size(); ++index)
      if (scalar_values[index]) mask |= std::uint32_t{1} << index;
    json += ",\"independent_numeric_inputs\":";
    AppendObservationHeader(json, "native_conception_independent_numeric_inputs",
        mask == 127 ? "available" : "unavailable",
        mask == 127 ? "" : "native_conception_independent_numeric_inputs_partial");
    AppendObservationNumber(json, "available_mask_u8", std::optional<std::uint32_t>{mask});
    for (std::size_t index = 0; index < scalar_values.size(); ++index)
      AppendObservationNumber(json, scalar_names[index], scalar_values[index]);
    json += '}';
    const auto &provider = pair.provider_result;
    json += ",\"conditional_pair_provider\":";
    AppendObservationHeader(json, "conditional_native_conception_pair_provider",
        provider.first_output_raw ? "available" : "unavailable",
        provider.first_output_raw ? "" : (provider.unavailable_input.empty() ?
            "native_conception_full_provider_input_unavailable" : provider.unavailable_input));
    AppendObservationNumber(json, "first_output_raw", provider.first_output_raw);
    AppendObservationBoolean(json, "actual_caller_zero_rejection", provider.actual_caller_zero_rejection);
    json += ",\"selected_count_role\":";
    if (!provider.selected_count_role) json += "null";
    else AppendJsonString(json, *provider.selected_count_role ==
        ck3_12004::ConceptionProviderCountRole12004::first ? "first" : "second");
    AppendObservationNumber(json, "reached_stages_mask_u64",
                            std::optional<std::uint64_t>{provider.reached_stages});
    AppendObservationNumber(json, "stop_stage_raw_u8", std::optional<std::uint8_t>{
        static_cast<std::uint8_t>(provider.stop_stage)});
    AppendObservationNumber(json, "source_pc_rva", std::optional<std::uint32_t>{provider.source_pc});
    AppendObservationNumber(json, "terminal_writer_rva", std::optional<std::uint32_t>{provider.terminal_writer_rva});
    json += ",\"unavailable_input\":";
    if (provider.unavailable_input.empty()) json += "null";
    else AppendJsonString(json, provider.unavailable_input);
    json += '}';
    json += '}';
  }
  json += "]}";
  return json;
}

std::string CurrentFirstHeirReproductiveInputsJsonV1(
    const CurrentFirstHeirReproductiveInputsV1 &read,
    std::uint64_t native_revision,
    const CurrentFirstHeirConceptionTraitInputsReadV1 *conception_trait_inputs,
    const CurrentFirstHeirConceptionCandidateInputsReadV1 *conception_candidate_inputs) {
  std::string json = "{\"source\":\"native_current_heir_household_inputs\",\"status\":";
  AppendJsonString(json, read.status);
  json += ",\"unavailable_reason\":";
  if (read.status == "available") json += "null";
  else AppendJsonString(json, read.unavailable_reason);
  json += ",\"native_revision\":" + std::to_string(native_revision);
  json += ",\"played_character_id\":";
  json += read.played_character_id > 0 ? std::to_string(read.played_character_id) : "null";
  json += ",\"heir_character_id\":";
  json += read.heir_character_id > 0 ? std::to_string(read.heir_character_id) : "null";
  json += ",\"date_raw\":";
  AppendOptionalNumber(json, read.date_raw);
  json += ",\"fertility_raw_scale\":100000,\"rows\":[";
  for (std::size_t index = 0; index < read.rows.size(); ++index) {
    if (index != 0) json += ',';
    const auto &row = read.rows[index];
    json += "{\"character_id\":" + std::to_string(row.character_id);
    json += ",\"roles\":[";
    for (std::size_t role = 0; role < row.roles.size(); ++role) {
      if (role != 0) json += ',';
      AppendJsonString(json, row.roles[role]);
    }
    json += "],\"status\":";
    AppendJsonString(json, row.available ? "available" : "unavailable");
    json += ",\"unavailable_reason\":";
    if (row.available) json += "null";
    else AppendJsonString(json, row.unavailable_reason);
    json += ",\"age_measure_raw\":";
    AppendOptionalNumber(json, row.age_measure_raw);
    json += ",\"sex_selector_raw\":";
    AppendOptionalNumber(json, row.sex_selector_raw);
    json += ",\"native_fertility\":";
    if (!row.available) {
      json += "null";
    } else {
      const auto &fertility = row.fertility;
      json += "{\"source\":\"native_marriage_fertility_input\",\"extension_present\":";
      json += fertility.extension_present ? "true" : "false";
      json += ",\"native_gate_evaluated\":";
      json += fertility.native_gate_evaluated ? "true" : "false";
      json += ",\"native_gate_allows\":";
      json += !fertility.native_gate_evaluated ? "null" :
          fertility.native_gate_allows ? "true" : "false";
      json += ",\"effective_raw\":" + std::to_string(fertility.effective_raw) + '}';
    }
    const auto &pregnancy = row.native_pregnancy;
    json += ",\"native_pregnancy\":{\"source\":\"native_is_pregnant\",\"status\":";
    AppendJsonString(json, pregnancy.status);
    json += ",\"unavailable_reason\":";
    if (pregnancy.status == "available") json += "null";
    else AppendJsonString(json, pregnancy.unavailable_reason);
    json += ",\"is_pregnant\":";
    AppendOptionalBoolean(json, pregnancy.is_pregnant);
    json += '}';
    if (conception_trait_inputs != nullptr) {
      CurrentCharacterConceptionTraitExclusionReadV1 exclusion{};
      exclusion.unavailable_reason = "native_conception_trait_row_unavailable";
      const auto found = std::find_if(conception_trait_inputs->rows.begin(),
          conception_trait_inputs->rows.end(),
          [&row](const auto &candidate) { return candidate.character_id == row.character_id; });
      if (found != conception_trait_inputs->rows.end()) exclusion = found->read;
      json += ",\"native_conception_trait_exclusion\":{\"source\":\"native_conception_trait_exclusion\",\"status\":";
      AppendJsonString(json, exclusion.status);
      json += ",\"unavailable_reason\":";
      if (exclusion.status == "available") json += "null";
      else AppendJsonString(json, exclusion.unavailable_reason);
      json += ",\"blocks_pair_conception\":";
      AppendOptionalBoolean(json, exclusion.blocks_pair_conception);
      json += '}';
    }
    if (conception_candidate_inputs != nullptr) {
      const auto found = std::find_if(conception_candidate_inputs->rows.begin(),
          conception_candidate_inputs->rows.end(), [&row](const auto &candidate) {
            return candidate.character_id == row.character_id;
          });
      if (found != conception_candidate_inputs->rows.end())
        AppendCurrentConceptionRow(json, *found);
    }
    json += '}';
  }
  json += "]";
  if (conception_candidate_inputs != nullptr) {
    json += ",\"conception_pair_inputs\":";
    json += CurrentConceptionPairInputsJsonV1(*conception_candidate_inputs);
  }
  json += '}';
  return json;
}

void AppendDescendantLineage(
    std::string &json, const CurrentFirstHeirDescendantLineageV1 &lineage) {
  json += "{\"status\":";
  AppendJsonString(json, lineage.available ? "available" : "unavailable");
  json += ",\"unavailable_reason\":";
  if (lineage.available) json += "null";
  else AppendJsonString(json, lineage.unavailable_reason);
  json += ",\"house_id_raw\":";
  json += lineage.available ? std::to_string(lineage.house_id_raw) : "null";
  json += ",\"dynasty_id_raw\":";
  json += lineage.available ? std::to_string(lineage.dynasty_id_raw) : "null";
  json += '}';
}

void AppendTypedWindows(std::string &json,
                        const CurrentFirstHeirTypedWindowsReadV1 &read,
                        std::uint64_t native_revision) {
  json += "{\"source\":\"native_fixed_window_type_diagnostic\",\"native_revision\":";
  json += std::to_string(native_revision);
  json += ",\"window_handler_status\":";
  AppendJsonString(json, read.window_handler_available ? "available" : "unavailable");
  json += ",\"window_handler_unavailable_reason\":";
  if (read.window_handler_available) json += "null";
  else AppendJsonString(json, read.window_handler_unavailable_reason);
  json += ",\"rows\":[";
  for (std::size_t index = 0; index < read.rows.size(); ++index) {
    if (index != 0) json += ',';
    const auto &row = read.rows[index];
    json += "{\"slot_index\":" + std::to_string(row.slot_index);
    json += ",\"handler_member_offset\":" + std::to_string(row.handler_member_offset);
    json += ",\"type_identifier\":" + std::to_string(row.type_identifier);
    json += ",\"registered_name_status\":";
    AppendJsonString(json, row.registered_name_available ? "available" : "unavailable");
    json += ",\"registered_name\":";
    if (row.registered_name) AppendJsonString(json, *row.registered_name);
    else json += "null";
    json += ",\"registered_name_unavailable_reason\":";
    if (row.registered_name_available) json += "null";
    else AppendJsonString(json, row.registered_name_unavailable_reason);
    json += ",\"window_presence\":";
    AppendJsonString(json, row.window_presence);
    json += ",\"object_type_status\":";
    AppendJsonString(json, row.object_type_status);
    json += ",\"object_vtable_rva\":";
    AppendOptionalNumber(json, row.object_vtable_rva);
    json += ",\"object_col_rva\":";
    AppendOptionalNumber(json, row.object_col_rva);
    json += ",\"object_type_descriptor_rva\":";
    AppendOptionalNumber(json, row.object_type_descriptor_rva);
    json += ",\"object_type_decorated_name\":";
    if (row.object_type_decorated_name)
      AppendJsonString(json, *row.object_type_decorated_name);
    else json += "null";
    json += ",\"object_type_unavailable_reason\":";
    if (row.object_type_status == "available" || row.object_type_status == "not_applicable")
      json += "null";
    else AppendJsonString(json, row.object_type_unavailable_reason);
    json += '}';
  }
  json += "]}";
}

void AppendChildInputs(std::string &json,
                       const CurrentFirstHeirChildInputsReadV1 &read,
                       std::uint64_t native_revision) {
  json += "{\"source\":\"native_current_heir_child_inputs\",\"status\":";
  AppendJsonString(json, read.status);
  json += ",\"unavailable_reason\":";
  if (read.status == "available") json += "null";
  else AppendJsonString(json, read.unavailable_reason);
  json += ",\"native_revision\":" + std::to_string(native_revision);
  json += ",\"played_character_id\":";
  json += read.played_character_id > 0 ? std::to_string(read.played_character_id) : "null";
  json += ",\"heir_character_id\":";
  json += read.heir_character_id > 0 ? std::to_string(read.heir_character_id) : "null";
  json += ",\"date_raw\":";
  AppendOptionalNumber(json, read.date_raw);
  json += ",\"rows\":[";
  for (std::size_t index = 0; index < read.rows.size(); ++index) {
    if (index != 0) json += ',';
    const auto &row = read.rows[index];
    json += "{\"character_id\":" + std::to_string(row.character_id);
    json += ",\"occurrence_indices\":[";
    for (std::size_t occurrence = 0; occurrence < row.occurrence_indices.size(); ++occurrence) {
      if (occurrence != 0) json += ',';
      json += std::to_string(row.occurrence_indices[occurrence]);
    }
    json += "],\"values\":{\"source\":\"native_character_age_and_sex\",\"status\":";
    AppendJsonString(json, row.values.available ? "available" : "unavailable");
    json += ",\"unavailable_reason\":";
    if (row.values.available) json += "null";
    else AppendJsonString(json, row.values.unavailable_reason);
    json += ",\"age_measure_raw\":";
    AppendOptionalNumber(json, row.values.age_measure_raw);
    json += ",\"sex_selector_raw\":";
    AppendOptionalNumber(json, row.values.sex_selector_raw);
    json += "},\"childhood_traits\":{\"source\":\"native_character_has_trait\",\"status\":";
    const auto &traits = row.childhood_traits;
    AppendJsonString(json, traits.available ? "available" : "unavailable");
    json += ",\"unavailable_reason\":";
    if (traits.available) json += "null";
    else AppendJsonString(json, traits.unavailable_reason);
    json += ",\"queried_trait_keys\":[";
    for (std::size_t key = 0; key < kChildhoodTraitKeysV1.size(); ++key) {
      if (key != 0) json += ',';
      AppendJsonString(json, kChildhoodTraitKeysV1[key]);
    }
    json += "],\"present_trait_keys\":";
    if (!traits.present_trait_keys) json += "null";
    else {
      json += '[';
      for (std::size_t key = 0; key < traits.present_trait_keys->size(); ++key) {
        if (key != 0) json += ',';
        AppendJsonString(json, (*traits.present_trait_keys)[key]);
      }
      json += ']';
    }
    json += '}';
    if (row.native_focus) {
      const auto &focus = *row.native_focus;
      json += ",\"native_focus\":{\"source\":\"native_character_current_focus\",\"status\":";
      AppendJsonString(json, focus.available ? "available" : "unavailable");
      json += ",\"unavailable_reason\":";
      if (focus.available) json += "null";
      else AppendJsonString(json, focus.unavailable_reason);
      json += ",\"presence\":";
      if (focus.available) AppendJsonString(json, focus.presence);
      else json += "null";
      json += ",\"key\":";
      if (focus.key) AppendJsonString(json, *focus.key);
      else json += "null";
      json += '}';
    }
    if (row.education_point_traits) {
      const auto &education_traits = *row.education_point_traits;
      json += ",\"education_point_traits\":{\"source\":\"native_character_has_trait\",\"status\":";
      AppendJsonString(json, education_traits.available ? "available" : "unavailable");
      json += ",\"unavailable_reason\":";
      if (education_traits.available) json += "null";
      else AppendJsonString(json, education_traits.unavailable_reason);
      json += ",\"queried_trait_keys\":[";
      for (std::size_t key = 0; key < kChildEducationPointTraitKeysV1.size(); ++key) {
        if (key != 0) json += ',';
        AppendJsonString(json, kChildEducationPointTraitKeysV1[key]);
      }
      json += "],\"present_trait_keys\":";
      if (!education_traits.present_trait_keys) json += "null";
      else {
        json += '[';
        for (std::size_t key = 0; key < education_traits.present_trait_keys->size(); ++key) {
          if (key != 0) json += ',';
          AppendJsonString(json, (*education_traits.present_trait_keys)[key]);
        }
        json += ']';
      }
      json += '}';
    }
    json += '}';
  }
  json += ']';
  if (read.typed_windows) {
    json += ",\"typed_windows\":";
    AppendTypedWindows(json, *read.typed_windows, native_revision);
  }
  if (read.character_window_identity) {
    const auto &identity = *read.character_window_identity;
    json += ",\"character_window_identity\":{\"receiver_available\":";
    json += identity.receiver_available ? "true" : "false";
    json += ",\"receiver_unavailable_reason\":";
    AppendJsonString(json, identity.receiver_unavailable_reason);
    json += ",\"raw_character_id\":";
    AppendOptionalNumber(json, identity.raw_character_id);
    json += ",\"character_available\":";
    json += identity.character_available ? "true" : "false";
    json += ",\"character_unavailable_reason\":";
    AppendJsonString(json, identity.character_unavailable_reason);
    json += ",\"character_id\":";
    AppendOptionalNumber(json, identity.character_id);
    json += '}';
  }
  json += '}';
}

std::string CurrentFirstHeirDescendantsJsonV1(
    const CurrentFirstHeirDescendantsReadV1 &read,
    std::uint64_t native_revision,
    const CurrentFirstHeirChildInputsReadV1 *child_inputs) {
  using Status = CurrentFirstHeirDescendantsStatusV1;
  std::string json = "{\"status\":";
  AppendJsonString(json, read.status == Status::available ? "available" :
      read.status == Status::partial ? "partial" : "unavailable");
  json += ",\"unavailable_reason\":";
  if (read.status == Status::available) json += "null";
  else AppendJsonString(json, read.unavailable_reason);
  json += ",\"native_revision\":" + std::to_string(native_revision);
  json += ",\"played_character_id\":";
  json += read.played_character_id > 0
      ? std::to_string(read.played_character_id) : "null";
  json += ",\"heir_character_id\":";
  json += read.heir_character_id > 0
      ? std::to_string(read.heir_character_id) : "null";
  json += ",\"date_raw\":";
  AppendOptionalNumber(json, read.date_raw);
  json += ",\"family_present\":";
  AppendOptionalBoolean(json, read.family_present);
  json += ",\"native_child_count_raw\":";
  AppendOptionalNumber(json, read.native_child_count_raw);
  json += ",\"data_pointer_present\":";
  AppendOptionalBoolean(json, read.data_pointer_present);
  json += ",\"roster_complete\":";
  json += read.roster_complete ? "true" : "false";
  json += ",\"played_lineage\":";
  AppendDescendantLineage(json, read.played_lineage);
  json += ",\"heir_lineage\":";
  AppendDescendantLineage(json, read.heir_lineage);
  json += ",\"rows\":[";
  for (std::size_t index = 0; index < read.rows.size(); ++index) {
    if (index != 0) json += ',';
    const auto &row = read.rows[index];
    json += "{\"occurrence_index\":" + std::to_string(row.occurrence_index);
    json += ",\"raw_character_id\":" + std::to_string(row.raw_character_id);
    json += ",\"generation_valid\":";
    json += row.generation_valid ? "true" : "false";
    json += ",\"alive\":";
    AppendOptionalBoolean(json, row.alive);
    json += ",\"parent_family_present\":";
    AppendOptionalBoolean(json, row.parent_family_present);
    json += ",\"parent_0_character_id_raw\":";
    AppendOptionalNumber(json, row.parent_0_character_id_raw);
    json += ",\"parent_4_character_id_raw\":";
    AppendOptionalNumber(json, row.parent_4_character_id_raw);
    json += ",\"child_of_heir\":";
    AppendOptionalBoolean(json, row.child_of_heir);
    json += ",\"lineage\":";
    AppendDescendantLineage(json, row.lineage);
    json += '}';
  }
  json += ']';
  if (child_inputs != nullptr) {
    json += ",\"child_inputs\":";
    AppendChildInputs(json, *child_inputs, native_revision);
  }
  json += '}';
  return json;
}
} // namespace

bool ValidateCurrentFirstHeirRawRelationshipV1(
    std::int32_t raw_betrothed_character_id,
    std::int32_t raw_primary_spouse_character_id,
    const std::vector<std::int32_t> &raw_spouse_character_ids,
    const MarriageHeirRelationshipV1 &filtered) noexcept {
  const auto scalar_matches = [](std::int32_t raw, std::int32_t observed) {
    return (raw == -1 || raw == 0) ? observed == -1
                                   : raw > 0 && observed == raw;
  };
  if (!scalar_matches(raw_betrothed_character_id,
                      filtered.betrothed_character_id) ||
      !scalar_matches(raw_primary_spouse_character_id,
                      filtered.primary_spouse_character_id) ||
      raw_spouse_character_ids != filtered.spouse_character_ids)
    return false;
  return std::all_of(raw_spouse_character_ids.begin(),
                     raw_spouse_character_ids.end(),
                     [](std::int32_t id) { return id > 0; });
}

bool ValidateCurrentFirstHeirBilateralRelationshipV1(
    std::int32_t heir_character_id,
    const MarriageHeirRelationshipV1 &heir,
    const std::vector<CurrentFirstHeirPartnerRelationshipV1> &partners) noexcept {
  if (heir_character_id <= 0 || heir.betrothed_character_id == 0 ||
      heir.primary_spouse_character_id == 0)
    return false;
  std::vector<std::int32_t> expected = heir.spouse_character_ids;
  for (const auto id : expected) {
    if (id <= 0 || id == heir_character_id ||
        std::count(expected.begin(), expected.end(), id) != 1)
      return false;
  }
  const auto add = [&](std::int32_t id) {
    if (id > 0 && std::find(expected.begin(), expected.end(), id) == expected.end())
      expected.push_back(id);
  };
  add(heir.primary_spouse_character_id);
  add(heir.betrothed_character_id);
  if (heir.betrothed_character_id > 0 &&
      (heir.betrothed_character_id == heir.primary_spouse_character_id ||
       std::find(heir.spouse_character_ids.begin(), heir.spouse_character_ids.end(),
                 heir.betrothed_character_id) != heir.spouse_character_ids.end()))
    return false;
  if (expected.size() != partners.size()) return false;
  for (const auto &partner : partners) {
    if (partner.character_id <= 0 || partner.character_id == heir_character_id ||
        std::find(expected.begin(), expected.end(), partner.character_id) ==
            expected.end())
      return false;
    if (std::count_if(partners.begin(), partners.end(), [&](const auto &row) {
          return row.character_id == partner.character_id;
        }) != 1)
      return false;
    if (partner.character_id == heir.betrothed_character_id) {
      if (partner.relationship.betrothed_character_id != heir_character_id)
        return false;
    } else if (partner.relationship.primary_spouse_character_id !=
                   heir_character_id &&
               std::find(partner.relationship.spouse_character_ids.begin(),
                         partner.relationship.spouse_character_ids.end(),
                         heir_character_id) ==
                   partner.relationship.spouse_character_ids.end()) {
      return false;
    }
  }
  return true;
}

std::string CurrentFirstHeirBetrothalActionabilityJsonV1(
    const CurrentFirstHeirBetrothalActionabilityReadV1 &read) {
  const bool available = read.unavailable_reason.empty();
  const bool not_applicable =
      read.unavailable_reason == "current_heir_has_no_betrothal";
  std::string json = "{\"status\":\"";
  json += available ? "available" : not_applicable ? "not_applicable" : "unavailable";
  json += "\",\"unavailable_reason\":";
  json += available ? "null" : "\"" + std::string(read.unavailable_reason) + "\"";
  const auto id = [&](std::string_view key, std::int32_t value) {
    json += ",\"" + std::string(key) + "\":";
    json += value > 0 ? std::to_string(value) : "null";
  };
  id("actor_character_id", read.actor_character_id);
  id("heir_character_id", read.heir_character_id);
  id("partner_character_id", read.partner_character_id);
  id("recipient_character_id", read.recipient_character_id);
  id("intermediary_character_id", read.intermediary_character_id);
  const auto boolean = [&](std::string_view key, bool known, bool value) {
    json += ",\"" + std::string(key) + "\":";
    json += known ? (value ? "true" : "false") : "null";
  };
  const auto number = [&](std::string_view key, bool known, std::int64_t value) {
    json += ",\"" + std::string(key) + "\":";
    json += known ? std::to_string(value) : "null";
  };
  boolean("adult_readback_available", true, read.adult_readback_available);
  boolean("heir_is_adult", read.adult_readback_available, read.adult.subject_is_adult);
  boolean("partner_is_adult", read.adult_readback_available, read.adult.candidate_is_adult);
  number("heir_adult_measure_raw", read.adult_readback_available, read.adult.subject_adult_measure_raw);
  number("partner_adult_measure_raw", read.adult_readback_available, read.adult.candidate_adult_measure_raw);
  number("heir_adult_threshold_raw", read.adult_readback_available, read.adult.subject_adult_threshold_raw);
  number("partner_adult_threshold_raw", read.adult_readback_available, read.adult.candidate_adult_threshold_raw);
  boolean("ready_to_marry_betrothed", read.has_betrothal && read.adult_readback_available,
          read.adult.subject_is_adult && read.adult.candidate_is_adult);
  boolean("final_legality_sampled", true, read.final_legality_sampled);
  boolean("complete_can_send", read.final_legality_sampled, read.complete_can_send);
  boolean("recipient_acceptance_ready", true, read.recipient_acceptance_ready);
  number("recipient_ai_accept_raw", read.recipient_acceptance_ready, read.recipient_ai_accept_raw);
  number("recipient_answer_status_raw", read.recipient_acceptance_ready, read.recipient_answer_status_raw);
  json += ",\"generic_costs\":";
  if (!read.generic_costs_available) {
    json += "null";
  } else {
    constexpr std::array<std::string_view, 10> keys{
        "gold_raw", "prestige_raw", "piety_raw", "renown_raw", "influence_raw",
        "herd_raw", "treasury_raw", "treasury_or_gold_raw", "merit_raw", "barter_goods_raw"};
    json += "{\"raw_scale\":100000,\"payer_role\":\"actor\",\"application_timing\":\"on_send\"";
    for (std::size_t index = 0; index < keys.size(); ++index) {
      json += ",\"" + std::string(keys[index]) + "\":" + std::to_string(read.generic_cost_raw[index]);
    }
    json += '}';
  }
  boolean("effective_matrilineal_if_accepted", read.lineality_available,
          read.effective_matrilineal_if_accepted);
  boolean("matrilineal_option_selected", read.matrilineal_option_selected.has_value(),
          read.matrilineal_option_selected.value_or(false));
  json += ",\"native_child_house_preview\":{\"status\":";
  AppendJsonString(json, not_applicable ? "not_applicable" :
      read.native_child_house_preview_available ? "available" : "unavailable");
  json += ",\"reason\":";
  AppendJsonString(json, not_applicable ? read.unavailable_reason :
                   read.native_child_house_preview_reason);
  id("subject_character_id", read.heir_character_id);
  id("candidate_character_id", read.partner_character_id);
  json += ",\"requested_matrilineal_option\":false";
  if (read.native_child_house_preview_available) {
    boolean("selected_matrilineal_option", true,
            read.matrilineal_option_selected.value_or(false));
    boolean("effective_matrilineal_if_accepted", true,
            read.effective_matrilineal_if_accepted);
    boolean("complete_can_send", true, read.complete_can_send);
    id("native_selected_parent_character_id", read.native_selected_parent_character_id);
    number("house_id", read.native_preview_lineage.house_id >= 0,
           read.native_preview_lineage.house_id);
    number("dynasty_id", read.native_preview_lineage.dynasty_id >= 0,
           read.native_preview_lineage.dynasty_id);
  }
  json += '}';
  json += ",\"predicted_outcome_if_accepted\":";
  json += !read.outcome_available ? "null" :
      read.adult.predicted_outcome == bridge::MarriagePredictedOutcomeV1::marriage
          ? "\"marriage\"" : "\"betrothal\"";
  json += '}';
  return json;
}

std::string CurrentFirstHeirRelationshipResultJsonV1(
    std::string_view request_id, std::uint64_t native_revision,
    std::int32_t heir_character_id,
    const CurrentFirstHeirRelationshipReadV1 &read,
    std::string_view override_unavailable_reason) {
  return CurrentFirstHeirRelationshipResultJsonV1(request_id, native_revision,
      heir_character_id, read, override_unavailable_reason, nullptr);
}

std::string CurrentFirstHeirRelationshipResultJsonV1(
    std::string_view request_id, std::uint64_t native_revision,
    std::int32_t heir_character_id,
    const CurrentFirstHeirRelationshipReadV1 &read,
    std::string_view override_unavailable_reason,
    const CurrentFirstHeirChildInputsReadV1 *child_inputs) {
  return CurrentFirstHeirRelationshipResultJsonV1(request_id, native_revision,
      heir_character_id, read, override_unavailable_reason, child_inputs, nullptr);
}

std::string CurrentFirstHeirRelationshipResultJsonV1(
    std::string_view request_id, std::uint64_t native_revision,
    std::int32_t heir_character_id,
    const CurrentFirstHeirRelationshipReadV1 &read,
    std::string_view override_unavailable_reason,
    const CurrentFirstHeirChildInputsReadV1 *child_inputs,
    const CurrentFirstHeirConceptionTraitInputsReadV1 *conception_trait_inputs) {
  return CurrentFirstHeirRelationshipResultJsonV1(request_id, native_revision,
      heir_character_id, read, override_unavailable_reason, child_inputs,
      conception_trait_inputs, nullptr);
}

std::string CurrentFirstHeirRelationshipResultJsonV1(
    std::string_view request_id, std::uint64_t native_revision,
    std::int32_t heir_character_id,
    const CurrentFirstHeirRelationshipReadV1 &read,
    std::string_view override_unavailable_reason,
    const CurrentFirstHeirChildInputsReadV1 *child_inputs,
    const CurrentFirstHeirConceptionTraitInputsReadV1 *conception_trait_inputs,
    const CurrentFirstHeirConceptionCandidateInputsReadV1 *conception_candidate_inputs) {
  const bool available = override_unavailable_reason.empty() &&
      read.failure == CurrentFirstHeirRelationshipFailureV1::none;
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, "query-current-first-heir-relationship-v1-private");
  result += ",\"accepted\":true,\"private_build\":true,"
            "\"read_only\":true,\"advertised\":false,\"status\":";
  AppendJsonString(result, available ? "available" : "unavailable");
  result += ",\"native_revision\":" + std::to_string(native_revision);
  result += ",\"subject_source\":\"public_campaign_root_primary_first_heir\","
            "\"heir_character_id\":" + std::to_string(heir_character_id);
  result += ",\"unavailable_reason\":";
  if (available) {
    result += "null";
  } else {
    AppendJsonString(result, override_unavailable_reason.empty()
        ? CurrentFirstHeirRelationshipFailureKeyV1(read.failure)
        : override_unavailable_reason);
  }
  result += ",\"bilateral_verified\":";
  result += available ? "true" : "false";
  result += ",\"betrothed_character_id\":";
  result += available && read.relationship.betrothed_character_id > 0
      ? std::to_string(read.relationship.betrothed_character_id) : "null";
  result += ",\"primary_spouse_character_id\":";
  result += available && read.relationship.primary_spouse_character_id > 0
      ? std::to_string(read.relationship.primary_spouse_character_id) : "null";
  result += ",\"spouse_character_ids\":";
  if (!available) {
    result += "null";
  } else {
    result += '[';
    for (std::size_t index = 0; index < read.relationship.spouse_character_ids.size(); ++index) {
      if (index != 0) result += ',';
      result += std::to_string(read.relationship.spouse_character_ids[index]);
    }
    result += ']';
  }
  result += ",\"betrothal_actionability\":";
  result += CurrentFirstHeirBetrothalActionabilityJsonV1(read.betrothal_actionability);
  if (read.descendants.has_value()) {
    result += ",\"current_first_heir_descendants_v1\":";
    result += CurrentFirstHeirDescendantsJsonV1(*read.descendants, native_revision,
                                              child_inputs);
  }
  if (read.reproductive_inputs.has_value()) {
    result += ",\"current_first_heir_reproductive_inputs_v1\":";
    result += CurrentFirstHeirReproductiveInputsJsonV1(
        *read.reproductive_inputs, native_revision, conception_trait_inputs,
        conception_candidate_inputs);
  }
  result += "}}";
  return result;
}

} // namespace xar::ck3_11906
#endif
