#pragma once

#include "xar_bridge/army_current_detachment_store_inputs_v1.hpp"

#include <cstddef>
#include <string_view>

namespace xar::game {

template <class Number, class JsonString>
inline void AppendArmyCurrentDetachmentStoreInputsV1(
    std::string &output, const ArmyCurrentDetachmentStoreInputsV1 &input,
    Number number, JsonString append_json_string) {
  const auto numeric = [&](std::string_view key, const auto &value) {
    output += ','; append_json_string(output, key); output += ':';
    output += value ? number(*value) : "null";
  };
  const auto text_field = [&](std::string_view key, const auto &value) {
    output += ','; append_json_string(output, key); output += ':';
    if (value) append_json_string(output, *value);
    else output += "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    output += ','; append_json_string(output, key); output += ':';
    output += value ? (*value ? "true" : "false") : "null";
  };
  const auto state_fields = [&](const auto &value) {
    output += "\"status\":"; append_json_string(output, value.status);
    output += ",\"ready\":"; output += value.ready ? "true" : "false";
    text_field("unavailable_reason", value.unavailable_reason);
  };
  output += "{\"schema_version\":1,\"source\":\"native_current_detachment_store_inputs_12004\"";
  output += ",\"stage\":\"observed_current_detachment_store_seed\",";
  state_fields(input);
  output += ",\"seed_selection_ready\":";
  output += input.seed_selection_ready ? "true" : "false";
  output += ",\"seed_roster_ready\":";
  output += input.seed_roster_ready ? "true" : "false";
  numeric("current_date_storage_raw64", input.current_date_storage_raw64);
  text_field("source_parent_identity", input.source_parent_identity);
  numeric("source_parent_wrapper_mode_i32", input.source_parent_wrapper_mode_i32);
  text_field("registry_identity", input.registry_identity);
  numeric("store_48_raw_u8", input.store_48_raw_u8);
  numeric("slot_count_2c_raw_u32", input.slot_count_2c_raw_u32);
  text_field("slot_table_identity", input.slot_table_identity);
  numeric("active_count_3c_raw_u32", input.active_count_3c_raw_u32);
  numeric("registry_mark_4a_raw_u8", input.registry_mark_4a_raw_u8);
  numeric("high_water_38_raw_u32", input.high_water_38_raw_u32);
  numeric("free_head_40_raw_u32", input.free_head_40_raw_u32);
  output += ",\"requests\":[";
  for (std::size_t index = 0; index < input.requests.size(); ++index) {
    if (index != 0) output += ',';
    const auto &request = input.requests[index];
    output += '{'; state_fields(request);
    output += ",\"seed_incoming_native_indices\":[";
    for (std::size_t alias = 0; alias < request.seed_incoming_native_indices.size(); ++alias) {
      if (alias != 0) output += ',';
      output += number(request.seed_incoming_native_indices[alias]);
    }
    output += ']';
    text_field("incoming_arrg_identity", request.incoming_arrg_identity);
    numeric("requested_full_id_u32", request.requested_full_id_u32);
    numeric("index_low24_u32", request.index_low24_u32);
    text_field("slot_identity", request.slot_identity);
    boolean("selected_pointer_present", request.selected_pointer_present);
    text_field("selected_object_identity", request.selected_object_identity);
    numeric("selected_full_id_10_raw_u32", request.selected_full_id_10_raw_u32);
    text_field("selected_primary_vtable_identity", request.selected_primary_vtable_identity);
    text_field("selected_slot0_target_identity", request.selected_slot0_target_identity);
    output += ",\"trailing_slot_scan\":[";
    for (std::size_t ordinal = 0; ordinal < request.trailing_slot_scan.size(); ++ordinal) {
      if (ordinal != 0) output += ',';
      const auto &slot = request.trailing_slot_scan[ordinal];
      output += '{'; state_fields(slot);
      output += ",\"slot_index_u32\":"; output += number(slot.slot_index_u32);
      text_field("slot_identity", slot.slot_identity);
      boolean("object_pointer_present", slot.object_pointer_present);
      text_field("object_identity", slot.object_identity);
      output += '}';
    }
    output += "]}";
  }
  output += ']';
  output += ",\"actual_callback_observed\":false,\"actual_resource_return_observed\":false";
  output += ",\"actual_after_state_observed\":false,\"full_detachment_transition_ready\":false";
  output += ",\"full_daily_ready\":false,\"full_monthly_ready\":false}";
}

} // namespace xar::game
