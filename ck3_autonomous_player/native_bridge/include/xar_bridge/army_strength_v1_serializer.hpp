#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/owned_regiments_v1_serializer.hpp"
#include "xar_bridge/army_current_helper_domain_inputs_v1_serializer.hpp"
#include "xar_bridge/army_current_helper_point_store_inputs_v1_serializer.hpp"

#include <string>

namespace xar::game {

template <class Number, class JsonString>
inline void AppendNativeMaaRecruitmentQuoteV1(
    std::string &output, const NativeMaaRecruitmentQuoteV1 &quote,
    Number number, JsonString append_json_string) {
  output += "{\"context\":";
  append_json_string(output, quote.context);
  output += ",\"status\":";
  append_json_string(output, quote.status);
  output += ",\"unavailable_reason\":";
  if (quote.unavailable_reason.empty()) output += "null";
  else append_json_string(output, quote.unavailable_reason);
  output += ",\"resource_scale\":" + number(quote.resource_scale);
  output += ",\"resources_raw\":";
  if (quote.resources_raw) {
    output += '[';
    bool first = true;
    for (const auto raw : *quote.resources_raw) {
      if (!first) output += ',';
      first = false;
      output += number(raw);
    }
    output += ']';
  } else output += "null";
  output += '}';
}

template <class Number, class JsonString>
inline void AppendNativeMaaRecruitmentInputsV1(
    std::string &output, const NativeMaaRecruitmentInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  output += "{\"schema_version\":" + number(inputs.schema_version);
  output += ",\"status\":";
  append_json_string(output, inputs.status);
  output += ",\"unavailable_reason\":";
  if (inputs.unavailable_reason.empty()) output += "null";
  else append_json_string(output, inputs.unavailable_reason);
  output += ",\"owner_character_id\":";
  output += inputs.owner_character_id ? number(*inputs.owner_character_id) : "null";
  output += ",\"creation_kind\":" + number(inputs.creation_kind);
  output += ",\"creation_scope\":";
  append_json_string(output, inputs.creation_scope);
  output += ",\"command_class\":";
  append_json_string(output, inputs.command_class);
  output += ",\"title_id\":" + number(inputs.title_id);
  output += ",\"requested_quantity\":" + number(inputs.requested_quantity);
  output += ",\"pay_cost\":";
  output += inputs.pay_cost ? "true" : "false";
  output += ",\"catalog_observed\":";
  output += inputs.catalog_observed ? "true" : "false";
  output += ",\"types_in_native_order\":[";
  bool first = true;
  for (const auto &type : inputs.types_in_native_order) {
    if (!first) output += ',';
    first = false;
    output += "{\"type_key\":";
    append_json_string(output, type.type_key);
    output += ",\"type_index\":" + number(type.type_index);
    output += ",\"inputs_ready\":";
    output += type.inputs_ready ? "true" : "false";
    output += ",\"unavailable_reason\":";
    if (type.unavailable_reason.empty()) output += "null";
    else append_json_string(output, type.unavailable_reason);
    output += ",\"effective_quantity\":";
    output += type.effective_quantity ? number(*type.effective_quantity) : "null";
    output += ",\"can_create\":";
    output += type.can_create ? (*type.can_create ? "true" : "false") : "null";
    output += ",\"regular_personal_quote\":";
    AppendNativeMaaRecruitmentQuoteV1(output, type.regular_personal_quote, number, append_json_string);
    output += '}';
  }
  output += "],\"missing_type_keys\":[";
  first = true;
  for (const auto &key : inputs.missing_type_keys) {
    if (!first) output += ',';
    first = false;
    append_json_string(output, key);
  }
  output += "]}";
}

template <class Number, class JsonString>
inline void AppendArmyMonthlyLossBudgetInputsV1(
    std::string &output, const ArmyMonthlyLossBudgetInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  output += "{\"status\":\"";
  output += inputs.available ? "available" : "unavailable";
  output += "\",\"ready\":";
  output += inputs.available ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (inputs.unavailable_reason.empty()) output += "null";
  else append_json_string(output, inputs.unavailable_reason);
  output += ",\"scale\":100000";
  const auto integer = [&](std::string_view key, const auto &value) {
    output += ",\""; output += key; output += "\":";
    output += value.has_value() ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    output += ",\""; output += key; output += "\":";
    output += value.has_value() ? (*value ? "true" : "false") : "null";
  };
  const auto array = [&](std::string_view key, const auto &values) {
    output += ",\""; output += key; output += "\":";
    if (!values.has_value()) { output += "null"; return; }
    output += '[';
    bool first = true;
    for (const auto value : *values) {
      if (!first) output += ',';
      first = false;
      output += number(value);
    }
    output += ']';
  };
  integer("unit_native_170_raw", inputs.unit_native_170_raw);
  boolean("native_unit_in_combat", inputs.native_unit_in_combat);
  boolean("native_unit_gathering", inputs.native_unit_gathering);
  integer("army_gathering_count_raw", inputs.army_gathering_count_raw);
  array("loaded_supply_state_levels", inputs.loaded_supply_state_levels);
  array("loaded_supply_state_fractions_raw", inputs.loaded_supply_state_fractions_raw);
  boolean("native_fleet_supply_loss_suppressed", inputs.native_fleet_supply_loss_suppressed);
  boolean("commander_valid", inputs.commander_valid);
  integer("commander_supply_modifier_id", inputs.commander_supply_modifier_id);
  integer("commander_supply_modifier_raw", inputs.commander_supply_modifier_raw);
  output += '}';
}

template <class Number, class JsonString>
inline void AppendArmyMonthlyCallerEffectInputsV1(
    std::string &output, const ArmyMonthlyCallerEffectInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  const auto status = [&](bool available, const std::string &reason, bool ready) {
    output += "{\"status\":\"";
    output += available ? "available" : "unavailable";
    output += '"';
    if (ready) { output += ",\"ready\":"; output += available ? "true" : "false"; }
    output += ",\"unavailable_reason\":";
    if (reason.empty()) output += "null"; else append_json_string(output, reason);
  };
  const auto integer = [&](std::string_view key, const auto &value) {
    output += ",\""; output += key; output += "\":";
    output += value.has_value() ? number(*value) : "null";
  };
  status(inputs.available, inputs.unavailable_reason, true);
  integer("army_byte_22_raw", inputs.army_byte_22_raw);
  integer("current_date_storage_raw64", inputs.current_date_storage_raw64);
  integer("unit_actor_character_id", inputs.unit_actor_character_id);
  output += ",\"war_counter_rows\":";
  if (inputs.war_counter_rows) {
    output += '[';
    bool first = true;
    for (const auto &row : *inputs.war_counter_rows) {
      if (!first) output += ',';
      first = false;
      status(row.available, row.unavailable_reason, false);
      output += ",\"stored_index\":" + number(row.stored_index);
      output += ",\"war_reference_id\":" + number(row.war_reference_id);
      integer("resolved_war_id", row.resolved_war_id);
      output += ",\"used_fallback\":";
      output += row.used_fallback ? (*row.used_fallback ? "true" : "false") : "null";
      integer("native_selected_side", row.native_selected_side);
      integer("native_counter_30_raw", row.native_counter_30_raw);
      output += '}';
    }
    output += ']';
  } else output += "null";
  output += ",\"manager_army_id_list_2a5a8\":";
  if (inputs.manager_army_id_list_2a5a8) {
    output += '[';
    bool first = true;
    for (const auto id : *inputs.manager_army_id_list_2a5a8) {
      if (!first) output += ',';
      first = false;
      output += number(id);
    }
    output += ']';
  } else output += "null";
  output += '}';
}

template <class Number, class JsonString>
inline void AppendArmyDailyQueueInputsV1(
    std::string &output, const ArmyDailyQueueInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  const auto status = [&](bool available, const std::string &reason, bool ready) {
    output += "{\"status\":\"";
    output += available ? "available" : "unavailable";
    output += '"';
    if (ready) { output += ",\"ready\":"; output += available ? "true" : "false"; }
    output += ",\"unavailable_reason\":";
    if (reason.empty()) output += "null"; else append_json_string(output, reason);
  };
  const auto integer = [&](std::string_view key, const auto &value) {
    output += ",\""; output += key; output += "\":";
    output += value.has_value() ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    output += ",\""; output += key; output += "\":";
    output += value ? (*value ? "true" : "false") : "null";
  };
  status(inputs.available, inputs.unavailable_reason, true);
  output += ",\"manager_army_id_list_2a5a8\":";
  if (inputs.manager_army_id_list_2a5a8) {
    output += '['; bool first = true;
    for (const auto id : *inputs.manager_army_id_list_2a5a8) {
      if (!first) output += ','; first = false; output += number(id);
    }
    output += ']';
  } else output += "null";
  output += ",\"initial_army_resolution_rows\":";
  if (inputs.initial_army_resolution_rows) {
    output += '['; bool first = true;
    for (const auto &row : *inputs.initial_army_resolution_rows) {
      if (!first) output += ','; first = false;
      status(row.available, row.unavailable_reason, false);
      output += ",\"stored_index\":" + number(row.stored_index);
      output += ",\"raw_army_reference_id\":" + number(row.raw_army_reference_id);
      integer("resolved_army_id", row.resolved_army_id);
      boolean("used_fallback", row.used_fallback);
      integer("army_magic_14_raw", row.army_magic_14_raw);
      boolean("native_army_identity_valid", row.native_army_identity_valid);
      output += '}';
    }
    output += ']';
  } else output += "null";
  output += '}';
}

template <class Number, class JsonString>
inline void AppendArmyFirstRemovalCleanupInputsV1(
    std::string &output, const ArmyFirstRemovalCleanupInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  output += "{\"status\":\"";
  output += inputs.available ? "available" : "unavailable";
  output += "\",\"ready\":";
  output += inputs.available ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (inputs.unavailable_reason.empty()) output += "null";
  else append_json_string(output, inputs.unavailable_reason);
  const auto integer = [&](std::string_view key, const auto &value) {
    output += ",\""; output += key; output += "\":";
    output += value.has_value() ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    output += ",\""; output += key; output += "\":";
    output += value ? (*value ? "true" : "false") : "null";
  };
  boolean("candidate_found", inputs.candidate_found);
  integer("candidate_stored_index", inputs.candidate_stored_index);
  integer("argument_army_id", inputs.argument_army_id);
  integer("cleanup_resolved_army_id", inputs.cleanup_resolved_army_id);
  boolean("cleanup_used_fallback", inputs.cleanup_used_fallback);
  integer("selected_bucket_index", inputs.selected_bucket_index);
  output += ",\"id_lists\":[";
  bool first = true;
  for (const auto &row : inputs.id_lists) {
    if (!first) output += ',';
    first = false;
    output += "{\"manager_offset\":";
    append_json_string(output, row.manager_offset);
    output += ",\"ordered_army_ids\":";
    if (row.ordered_army_ids) {
      output += '[';
      bool first_id = true;
      for (const auto id : *row.ordered_army_ids) {
        if (!first_id) output += ',';
        first_id = false; output += number(id);
      }
      output += ']';
    } else output += "null";
    output += '}';
  }
  output += "],\"selected_bucket_rows\":";
  if (inputs.selected_bucket_rows) {
    output += '[';
    first = true;
    for (const auto &row : *inputs.selected_bucket_rows) {
      if (!first) output += ',';
      first = false;
      output += "{\"stored_index\":" + number(row.stored_index);
      integer("observed_army_id", row.observed_army_id);
      output += ",\"native_same_cleanup_army_pointer\":";
      output += row.native_same_cleanup_army_pointer ? "true" : "false";
      output += '}';
    }
    output += ']';
  } else output += "null";
  output += ",\"records_b0\":";
  if (inputs.records_b0) {
    output += '[';
    first = true;
    for (const auto &words : *inputs.records_b0) {
      if (!first) output += ',';
      first = false; output += '[';
      for (std::size_t index = 0; index < words.size(); ++index) {
        if (index != 0) output += ',';
        output += number(words[index]);
      }
      output += ']';
    }
    output += ']';
  } else output += "null";
  output += '}';
}

// One row implementation shared by the bridge and its production-reader fixture.
// The bridge supplies its existing number, array, and string-escaping helpers.
template <class Number, class Int32Array, class JsonString>
inline void AppendArmyStrengthV1(
    std::string &result,
    const ArmyStrengthSnapshot &strength, Number number,
    Int32Array append_int32_array, JsonString append_json_string) {
  result += "{\"status\":\"";
  result += strength.available ? "available" : "unavailable";
  result += "\",\"army_id\":";
  result += number(strength.army_id);
  result += ",\"native_carmy_id\":";
  if (strength.native_carmy_id_observable) {
    result += number(strength.native_carmy_id);
  } else {
    result += "null";
  }
  if (strength.native_army_resolution_v1.has_value()) {
    const auto &resolution = *strength.native_army_resolution_v1;
    result += ",\"native_army_resolution_v1\":{\"status\":\"";
    result += resolution.available ? "available" : "unavailable";
    result += "\",\"ready\":";
    result += resolution.available ? "true" : "false";
    result += ",\"branch\":";
    append_json_string(result, ArmyNativeResolutionBranchNameV1(resolution.branch));
    result += ",\"raw_reference\":";
    result += resolution.raw_reference.has_value() ? number(*resolution.raw_reference) : "null";
    result += ",\"reference_index\":";
    result += resolution.reference_index.has_value() ? number(*resolution.reference_index) : "null";
    result += ",\"storage_capacity\":";
    result += resolution.storage_capacity.has_value() ? number(*resolution.storage_capacity) : "null";
    result += ",\"entry_full_id\":";
    result += resolution.entry_full_id.has_value() ? number(*resolution.entry_full_id) : "null";
    result += '}';
  }
  if (strength.monthly_loss_budget_inputs_v1) {
    result += ",\"monthly_loss_budget_inputs_v1\":";
    AppendArmyMonthlyLossBudgetInputsV1(result, *strength.monthly_loss_budget_inputs_v1,
                                      number, append_json_string);
  }
  if (strength.monthly_caller_effect_inputs_v1) {
    result += ",\"monthly_caller_effect_inputs_v1\":";
    AppendArmyMonthlyCallerEffectInputsV1(result, *strength.monthly_caller_effect_inputs_v1,
                                        number, append_json_string);
  }
  if (strength.monthly_daily_queue_inputs_v1) {
    result += ",\"monthly_daily_queue_inputs_v1\":";
    AppendArmyDailyQueueInputsV1(result, *strength.monthly_daily_queue_inputs_v1,
                                number, append_json_string);
  }
  if (strength.monthly_first_removal_cleanup_inputs_v1) {
    result += ",\"monthly_first_removal_cleanup_inputs_v1\":";
    AppendArmyFirstRemovalCleanupInputsV1(result, *strength.monthly_first_removal_cleanup_inputs_v1,
                                        number, append_json_string);
  }
  if (strength.monthly_current_helper_domain_inputs_v1) {
    result += ",\"monthly_current_helper_domain_inputs_v1\":";
    AppendArmyCurrentHelperDomainInputsV1(result, *strength.monthly_current_helper_domain_inputs_v1,
                                         number, append_json_string);
  }
  if (strength.monthly_current_helper_point_store_inputs_v1) {
    result += ",\"monthly_current_helper_point_store_inputs_v1\":";
    AppendArmyCurrentHelperPointStoreInputsV1(result, *strength.monthly_current_helper_point_store_inputs_v1,
                                             number, append_json_string);
  }
  result += ",\"scope_role\":\"";
  switch (strength.scope_role) {
  case ArmyStrengthScopeRole::player:
    result += "player";
    break;
  case ArmyStrengthScopeRole::active_war_ally:
    result += "active_war_ally";
    break;
  case ArmyStrengthScopeRole::active_war_enemy:
    result += "active_war_enemy";
    break;
  }
  result += "\",\"war_ids\":";
  append_int32_array(result, strength.war_ids);
  if (strength.native_maa_recruitment_inputs_v1) {
    result += ",\"native_maa_recruitment_inputs_v1\":";
    AppendNativeMaaRecruitmentInputsV1(
        result, *strength.native_maa_recruitment_inputs_v1, number, append_json_string);
  }
  if (strength.owned_regiments_v1) {
    result += ",\"owned_regiments_v1\":";
    ck3_12003::AppendOwnedRegimentsV1(
        result, *strength.owned_regiments_v1, number, append_json_string);
  }
  result += ",\"regiment_count\":";
  if (strength.available) {
    result += number(strength.regiment_count);
  } else {
    result += "null";
  }
  result += ",\"current_soldiers\":";
  if (strength.available) {
    result += number(strength.current_soldiers);
  } else {
    result += "null";
  }
  result += ",\"maximum_soldiers\":";
  if (strength.available) {
    result += number(strength.maximum_soldiers);
  } else {
    result += "null";
  }
  result += ",\"ai_base_power_raw\":";
  if (strength.available) {
    result += number(strength.ai_base_power_raw);
  } else {
    result += "null";
  }
  result += ",\"ai_base_power_scale\":";
  result += number(strength.ai_base_power_scale);
  if (strength.available && strength.regiment_strengths.has_value()) {
    result += ",\"regiment_strengths\":[";
    bool first = true;
    for (const auto &regiment : *strength.regiment_strengths) {
      if (!first) result += ',';
      first = false;
      result += "{\"army_regiment_id\":";
      result += number(regiment.army_regiment_id);
      result += ",\"current_soldiers\":";
      result += number(regiment.current_soldiers);
      result += ",\"maximum_soldiers\":";
      result += number(regiment.maximum_soldiers);
      result += ",\"scale\":1,\"maa_type_status\":\"";
      switch (regiment.maa_type_status) {
      case ArmyRegimentTypeStatusV1::available: result += "available"; break;
      case ArmyRegimentTypeStatusV1::absent: result += "absent"; break;
      case ArmyRegimentTypeStatusV1::unavailable: result += "unavailable"; break;
      }
      result += "\",\"maa_type_key\":";
      if (regiment.maa_type_status == ArmyRegimentTypeStatusV1::available) {
        append_json_string(result, regiment.maa_type_key);
      } else {
        result += "null";
      }
      result += ",\"siege_tier_observable\":";
      result += regiment.siege_tier.has_value() ? "true" : "false";
      result += ",\"siege_tier\":";
      result += regiment.siege_tier.has_value() ? number(*regiment.siege_tier) : "null";
      result += ",\"composition_unavailable_reason\":";
      if (regiment.composition_unavailable_reason.empty()) result += "null";
      else append_json_string(result, regiment.composition_unavailable_reason);
      result += ",\"native_supply_loss_eligible\":";
      result += regiment.native_supply_loss_eligible.has_value()
                    ? (*regiment.native_supply_loss_eligible ? "true" : "false")
                    : "null";
      result += ",\"supply_loss_eligibility_unavailable_reason\":";
      if (regiment.supply_loss_eligibility_unavailable_reason.empty()) result += "null";
      else append_json_string(result, regiment.supply_loss_eligibility_unavailable_reason);
      result += '}';
    }
    result += ']';
  }
  if (strength.available && strength.merge_supply_destination_weight_raw.has_value()) {
    result += ",\"merge_supply_destination_weight_raw\":";
    result += number(*strength.merge_supply_destination_weight_raw);
    result += ",\"merge_supply_destination_weight_scale\":100000";
  }
  if (strength.available && strength.current_supply_raw.has_value()) {
    result += ",\"current_supply_raw\":";
    result += number(*strength.current_supply_raw);
    result += ",\"current_supply_scale\":100000";
  }
  if (strength.available && strength.current_supply_capacity_raw.has_value()) {
    result += ",\"current_supply_capacity_raw\":";
    result += number(*strength.current_supply_capacity_raw);
    result += ",\"current_supply_capacity_scale\":100000";
  }
  if (strength.available && strength.current_supply_change_monthly_raw.has_value()) {
    result += ",\"current_supply_change_monthly_raw\":";
    result += number(*strength.current_supply_change_monthly_raw);
    result += ",\"current_supply_change_monthly_scale\":100000";
  }
  if (strength.available && strength.current_attrition_fraction_raw.has_value()) {
    result += ",\"current_attrition_fraction_raw\":";
    result += number(*strength.current_attrition_fraction_raw);
    result += ",\"current_attrition_fraction_scale\":100000";
  }
  if (strength.available && strength.regiment_replenishment.has_value()) {
    result += ",\"regiment_replenishment\":[";
    bool first_regiment = true;
    for (const auto &regiment : *strength.regiment_replenishment) {
      if (!first_regiment) {
        result += ',';
      }
      first_regiment = false;
      result += "{\"army_regiment_id\":";
      result += number(regiment.army_regiment_id);
      result += ",\"native_data_record_count\":";
      if (regiment.native_data_record_count.has_value()) {
        result += number(*regiment.native_data_record_count);
      } else {
        result += "null";
      }
      result += ",\"status\":\"";
      result += regiment.available ? "available" : "unavailable";
      result += "\",\"source\":\"native_first_record\",\"unavailable_reason\":";
      if (regiment.available) {
        result += "null";
      } else {
        append_json_string(result, regiment.unavailable_reason);
      }
      result += ",\"chunks\":[";
      bool first_chunk = true;
      if (regiment.available) {
        for (const auto &chunk : regiment.chunks) {
          if (!first_chunk) {
            result += ',';
          }
          first_chunk = false;
          result += "{\"persistent_regiment_id\":";
          result += number(chunk.persistent_regiment_id);
          result += ",\"chunk_index\":";
          result += number(chunk.chunk_index);
          result += ",\"current_soldiers\":";
          result += number(chunk.current_soldiers);
          result += ",\"maximum_soldiers\":";
          result += number(chunk.maximum_soldiers);
          result += ",\"state_raw\":";
          result += number(chunk.state_raw);
          result += ",\"native_can_replenish\":";
          result += chunk.native_can_replenish ? "true" : "false";
          result += ",\"native_chunk_can_replenish\":";
          result += chunk.native_chunk_can_replenish ? "true" : "false";
          result += ",\"persistent_monthly_replenishment_fraction_raw\":";
          result += number(chunk.persistent_monthly_replenishment_fraction_raw);
          result += ",\"persistent_monthly_replenishment_fraction_scale\":100000}";
        }
      }
      result += "]}";
    }
    result += ']';
  }
  if (strength.available && strength.regiment_replenishment_records_v1.has_value()) {
    result += ",\"regiment_replenishment_records_v1\":[";
    bool first_regiment = true;
    for (const auto &regiment : *strength.regiment_replenishment_records_v1) {
      if (!first_regiment) result += ',';
      first_regiment = false;
      result += "{\"army_regiment_id\":" + number(regiment.army_regiment_id);
      result += ",\"source\":\"native_all_data_records\",\"status\":\"";
      switch (regiment.status) {
      case ArmyRegimentReplenishmentRecordsStatusV1::available: result += "available"; break;
      case ArmyRegimentReplenishmentRecordsStatusV1::partial: result += "partial"; break;
      default: result += "unavailable"; break;
      }
      result += "\",\"ready\":";
      result += regiment.status == ArmyRegimentReplenishmentRecordsStatusV1::available ? "true" : "false";
      result += ",\"native_data_record_count\":";
      result += regiment.native_data_record_count.has_value() ? number(*regiment.native_data_record_count) : "null";
      result += ",\"unavailable_reason\":";
      if (regiment.unavailable_reason.empty()) result += "null";
      else append_json_string(result,regiment.unavailable_reason);
      result += ",\"native_loss_writer_skipped\":";
      result += regiment.native_loss_writer_skipped.has_value()
          ? (*regiment.native_loss_writer_skipped ? "true" : "false") : "null";
      result += ",\"loss_writer_admission_unavailable_reason\":";
      if (regiment.loss_writer_admission_unavailable_reason.empty()) result += "null";
      else append_json_string(result,regiment.loss_writer_admission_unavailable_reason);
      result += ",\"records\":[";
      bool first_record=true;
      for (const auto &record : regiment.records) {
        if (!first_record) result += ',';
        first_record=false;
        result += "{\"record_index\":" + number(record.record_index);
        result += ",\"persistent_regiment_id\":" + number(record.persistent_regiment_id);
        result += ",\"chunk_index\":" + number(record.chunk_index);
        result += ",\"status\":\"";
        result += record.available ? "available" : "unavailable";
        result += "\",\"unavailable_reason\":";
        if (record.unavailable_reason.empty()) result += "null";
        else append_json_string(result,record.unavailable_reason);
        const auto optional_number=[&](std::string_view key,const auto &value) {
          result += ','; append_json_string(result,key); result += ':';
          result += value.has_value() ? number(*value) : "null";
        };
        const auto optional_bool=[&](std::string_view key,const auto &value) {
          result += ','; append_json_string(result,key); result += ':';
          result += value.has_value() ? (*value ? "true" : "false") : "null";
        };
        optional_number("current_soldiers",record.current_soldiers);
        optional_number("maximum_soldiers",record.maximum_soldiers);
        optional_number("effective_current_soldiers",record.effective_current_soldiers);
        optional_number("state_raw",record.state_raw);
        optional_number("chunk_army_regiment_id",record.chunk_army_regiment_id);
        optional_bool("native_can_replenish",record.native_can_replenish);
        optional_bool("native_chunk_can_replenish",record.native_chunk_can_replenish);
        optional_number("persistent_monthly_replenishment_fraction_raw",record.persistent_monthly_replenishment_fraction_raw);
        optional_number("persistent_prepared_replenishment_fraction_raw",record.persistent_prepared_replenishment_fraction_raw);
        result += ",\"persistent_monthly_replenishment_fraction_scale\":100000";
        result += ",\"persistent_prepared_replenishment_fraction_scale\":100000}";
      }
      result += "]}";
    }
    result += ']';
  }
  if (strength.current_movement_progress.has_value()) {
    const auto &movement = *strength.current_movement_progress;
    result += ",\"current_movement_progress\":{\"status\":\"";
    switch (movement.status) {
    case ArmyMovementProgressStatus::available: result += "available"; break;
    case ArmyMovementProgressStatus::partial: result += "partial"; break;
    case ArmyMovementProgressStatus::not_applicable: result += "not_applicable"; break;
    case ArmyMovementProgressStatus::unavailable: result += "unavailable"; break;
    }
    result += "\",\"source\":\"native_current_route_edge\",\"unit_state_raw\":";
    result += movement.unit_state_raw.has_value() ? number(*movement.unit_state_raw) : "null";
    result += ",\"accumulated_movement_weight_raw\":";
    result += movement.accumulated_movement_weight_raw.has_value()
                  ? number(*movement.accumulated_movement_weight_raw) : "null";
    result += ",\"cached_edge_speed_raw\":";
    result += movement.cached_edge_speed_raw.has_value()
                  ? number(*movement.cached_edge_speed_raw) : "null";
    const auto append_fixed = [&](const std::optional<std::int64_t> &raw) {
      if (raw.has_value()) {
        result += "{\"raw\":";
        result += number(*raw);
        result += ",\"scale\":100000}";
      } else {
        result += "null";
      }
    };
    result += ",\"normalized_edge_progress\":";
    append_fixed(movement.normalized_edge_progress_raw);
    result += ",\"first_route_edge_remaining_duration\":";
    append_fixed(movement.first_route_edge_remaining_duration_raw);
    result += ",\"unavailable_reason\":";
    if (movement.unavailable_reason.empty()) result += "null";
    else append_json_string(result, movement.unavailable_reason);
    if (movement.committed_route_timeline.has_value()) {
      const auto &timeline = *movement.committed_route_timeline;
      result += ",\"committed_route_timeline\":{\"status\":\"";
      const bool available = timeline.status == ArmyMovementProgressStatus::available;
      const bool empty = timeline.status == ArmyMovementProgressStatus::not_applicable;
      result += available ? "available" : (empty ? "not_applicable" : "unavailable");
      result += "\",\"source\":\"native_committed_route\",\"native_duration_scale\":100000";
      result += ",\"committed_route_province_ids\":";
      if (available || empty) append_int32_array(result, timeline.committed_route_province_ids);
      else result += "null";
      result += ",\"native_route_prefix_remaining_days_q100000\":";
      if (available || empty) {
        result += '[';
        for (std::size_t i = 0; i < timeline.native_route_prefix_remaining_days_q100000.size(); ++i) {
          if (i != 0) result += ',';
          result += number(timeline.native_route_prefix_remaining_days_q100000[i]);
        }
        result += ']';
      } else result += "null";
      result += ",\"native_full_route_remaining_days_q100000\":";
      result += timeline.native_full_route_remaining_days_q100000.has_value()
                    ? number(*timeline.native_full_route_remaining_days_q100000) : "null";
      result += ",\"projected_route_arrival_date_raws\":";
      if (available || empty) append_int32_array(result, timeline.projected_route_arrival_date_raws);
      else result += "null";
      result += ",\"unavailable_reason\":";
      if (timeline.unavailable_reason.empty()) result += "null";
      else append_json_string(result, timeline.unavailable_reason);
      result += '}';
    }
    result += '}';
  }
  if (strength.loss_application_inputs_v1.has_value()) {
    const auto &inputs = *strength.loss_application_inputs_v1;
    result += ",\"loss_application_inputs_v1\":{\"status\":\"";
    result += inputs.available ? "available" : "unavailable";
    result += "\",\"unavailable_reason\":";
    if (inputs.available) result += "null";
    else append_json_string(result, inputs.unavailable_reason);
    const auto append_number = [&](std::string_view key, std::int64_t value) {
      result += ',';
      append_json_string(result, key);
      result += ':';
      result += inputs.available ? number(value) : "null";
    };
    const auto append_boolean = [&](std::string_view key, bool value) {
      result += ',';
      append_json_string(result, key);
      result += ':';
      result += inputs.available ? (value ? "true" : "false") : "null";
    };
    append_number("raid_association_id", inputs.raid_association_id);
    append_boolean("siege_active", inputs.siege_active);
    append_boolean("raid_active", inputs.raid_active);
    append_number("siege_rate_raw", inputs.siege_rate_raw);
    append_number("raid_rate_raw", inputs.raid_rate_raw);
    append_number("whole_soldiers", inputs.whole_soldiers);
    append_number("definition_le_zero_soldiers", inputs.definition_le_zero_soldiers);
    append_number("supply_eligible_soldiers", inputs.supply_eligible_soldiers);
    append_number("definition_le_zero_supply_eligible_soldiers",
                  inputs.definition_le_zero_supply_eligible_soldiers);
    append_number("current_supply_loss_budget", inputs.current_supply_loss_budget);
    append_number("siege_loss_budget", inputs.siege_loss_budget);
    append_number("raid_loss_budget", inputs.raid_loss_budget);
    result += ",\"fraction_scale\":100000,\"soldier_scale\":1}";
  }
  if (strength.county_entry_inputs_v1.has_value()) {
    const auto &inputs = *strength.county_entry_inputs_v1;
    result += ",\"county_entry_inputs_v1\":{\"status\":\"";
    result += inputs.available ? "available" : "unavailable";
    result += "\",\"source\":\"native_current_county_entry_inputs\",\"unavailable_reason\":";
    if (inputs.available) result += "null";
    else append_json_string(result, inputs.unavailable_reason);
    const auto append_number = [&](std::string_view key, std::int64_t value,
                                   bool available) {
      result += ',';
      append_json_string(result, key);
      result += ':';
      result += available ? number(value) : "null";
    };
    append_number("whole_soldiers", inputs.whole_soldiers, inputs.available);
    append_number("current_loss_budget", inputs.current_loss_budget, inputs.available);
    append_number("effective_fraction_raw", inputs.effective_fraction_raw, inputs.available);
    append_number("minimum_multiplier_raw", inputs.minimum_multiplier_raw, inputs.available);
    append_number("loaded_minimum_soldiers", inputs.loaded_minimum_soldiers, inputs.available);
    result += ",\"fraction_scale\":100000,\"soldier_scale\":1,\"condition\":{\"status\":\"";
    result += inputs.condition_available ? "available" : "unavailable";
    result += "\",\"source\":\"current_stored_route_first_province\",\"unavailable_reason\":";
    if (inputs.condition_available) result += "null";
    else append_json_string(result, inputs.condition_unavailable_reason);
    append_number("actor_character_id", inputs.actor_character_id, inputs.condition_available);
    append_number("source_province_id", inputs.source_province_id, inputs.condition_available);
    append_number("target_province_id", inputs.target_province_id, inputs.condition_available);
    append_number("mode", inputs.mode, inputs.condition_available);
    result += ",\"passes\":";
    result += inputs.condition_available ? (inputs.condition_passes ? "true" : "false") : "null";
    result += "}}";
  }
  if (strength.army_update_clock_v1.has_value()) {
    const auto &clock = *strength.army_update_clock_v1;
    result += ",\"army_update_clock_v1\":{\"status\":";
    append_json_string(result, ArmySupplyTimingStatusName(clock.status));
    result += ",\"ready\":";
    result += clock.ready ? "true" : "false";
    const auto append_optional = [&](std::string_view key, const auto &value) {
      result += ',';
      append_json_string(result, key);
      result += ':';
      result += value.has_value() ? number(*value) : "null";
    };
    append_optional("current_date_raw", clock.current_date_raw);
    append_optional("native_day_index", clock.native_day_index);
    append_optional("selected_bucket_phase", clock.selected_bucket_phase);
    append_optional("observed_army_bucket_phase", clock.observed_army_bucket_phase);
    append_optional("last_supply_update_date_storage_raw64", clock.last_supply_update_date_storage_raw64);
    append_optional("last_supply_update_date_raw", clock.last_supply_update_date_raw);
    append_optional("grace_anchor_date_storage_raw64", clock.grace_anchor_date_storage_raw64);
    append_optional("grace_anchor_date_raw", clock.grace_anchor_date_raw);
    append_optional("loaded_grace_days", clock.loaded_grace_days);
    result += ",\"unavailable_reason\":";
    if (clock.unavailable_reason.empty()) result += "null";
    else append_json_string(result, clock.unavailable_reason);
    result += '}';
  }
  result += ",\"gathering_days_left\":";
  if (strength.gathering_days_status == ArmyGatheringDaysStatus::available &&
      strength.gathering_days_left.has_value()) {
    result += number(*strength.gathering_days_left);
  } else {
    result += "null";
  }
  result += ",\"gathering_days_status\":\"";
  switch (strength.gathering_days_status) {
  case ArmyGatheringDaysStatus::available:
    result += "available";
    break;
  case ArmyGatheringDaysStatus::not_gathering:
    result += "not_gathering";
    break;
  case ArmyGatheringDaysStatus::unavailable:
    result += "unavailable";
    break;
  }
  result += "\",\"gathering_days_ready\":";
  result += strength.gathering_days_status != ArmyGatheringDaysStatus::unavailable
                ? "true" : "false";
  result += ",\"unavailable_reason\":";
  if (strength.available) {
    result += "null";
  } else {
    append_json_string(result, strength.unavailable_reason);
  }
  result += '}';
}

template <class Number, class JsonString>
inline void AppendArmyProvinceSupplyRowV1(
    std::string &output, const ArmyProvinceSupplyRow &row,
    Number number, JsonString append_json_string) {
  output += "{\"status\":\"";
  output += row.available ? "available" : "unavailable";
  output += "\",\"unavailable_reason\":";
  if (row.available) output += "null";
  else append_json_string(output, row.unavailable_reason);
  output += ",\"role\":\"";
  output += row.role == ArmyProvinceSupplyRole::current ? "current" : "target";
  output += "\",\"province_id\":" + number(row.province_id);
  output += ",\"native_supply_limit_soldiers\":";
  output += row.native_supply_limit_soldiers.has_value()
      ? number(*row.native_supply_limit_soldiers) : "null";
  output += ",\"native_supply_usage_soldiers\":";
  output += row.native_supply_usage_soldiers.has_value()
      ? number(*row.native_supply_usage_soldiers) : "null";
  output += ",\"scale\":1}";
}

template <class Number, class JsonString>
inline void AppendArmyProvinceSupplyV1(
    std::string &output, const ArmyProvinceSupplySnapshot &supply,
    Number number, JsonString append_json_string) {
  output += "{\"status\":\"";
  switch (supply.status) {
  case ArmyProvinceSupplyStatus::available: output += "available"; break;
  case ArmyProvinceSupplyStatus::partial: output += "partial"; break;
  case ArmyProvinceSupplyStatus::unavailable: output += "unavailable"; break;
  }
  output += "\",\"unavailable_reason\":";
  if (supply.status == ArmyProvinceSupplyStatus::available) output += "null";
  else append_json_string(output, supply.unavailable_reason);
  output += ",\"army_id\":" + number(supply.army_id);
  output += ",\"native_carmy_id\":";
  output += supply.native_carmy_id.has_value() ? number(*supply.native_carmy_id) : "null";
  output += ",\"owner_character_id\":";
  output += supply.owner_character_id.has_value() ? number(*supply.owner_character_id) : "null";
  output += ",\"commander_character_id\":";
  output += supply.commander_character_id.has_value() ? number(*supply.commander_character_id) : "null";
  output += ",\"current\":";
  AppendArmyProvinceSupplyRowV1(output, supply.current, number, append_json_string);
  output += ",\"target\":";
  AppendArmyProvinceSupplyRowV1(output, supply.target, number, append_json_string);
  output += '}';
}

// The same route-preview row body is used by the real bridge and its focused
// native producer. Existing helpers preserve number/array/string semantics.
template <class Number, class Int32Array, class JsonString>
inline void AppendMoveRoutePreviewV1(
    std::string &output, const PreviewMoveArmyResult &preview,
    Number number, Int32Array append_int32_array, JsonString append_json_string) {
  output += "{\"status\":\"available\",\"army_id\":" + number(preview.army_id);
  output += ",\"origin_province_id\":" + number(preview.origin_province_id);
  output += ",\"target_province_id\":" + number(preview.target_province_id);
  output += ",\"route_province_ids\":";
  append_int32_array(output, preview.route_province_ids);
  if (preview.province_supply.has_value()) {
    output += ",\"province_supply\":";
    AppendArmyProvinceSupplyV1(output, *preview.province_supply, number,
                               append_json_string);
  }
  output += '}';
}

} // namespace xar::game
