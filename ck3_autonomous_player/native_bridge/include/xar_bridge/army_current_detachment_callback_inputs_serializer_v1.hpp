#pragma once

#include "xar_bridge/army_current_detachment_callback_inputs_v1.hpp"

#include <cstddef>
#include <string_view>

namespace xar::game {

template <class Number, class JsonString>
inline void AppendArmyCurrentDetachmentCallbackInputsV1(
    std::string &output, const ArmyCurrentDetachmentCallbackInputsV1 &input,
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
  const auto state_fields = [&](const auto &value) {
    output += "\"status\":"; append_json_string(output, value.status);
    output += ",\"ready\":"; output += value.ready ? "true" : "false";
    text_field("unavailable_reason", value.unavailable_reason);
  };
  output += "{\"schema_version\":1,\"source\":\"native_current_detachment_callback_inputs_12004\"";
  output += ",\"stage\":\"observed_current_detachment_callback_seed\",";
  state_fields(input);
  output += ",\"seed_selection_ready\":";
  output += input.seed_selection_ready ? "true" : "false";
  output += ",\"seed_roster_ready\":";
  output += input.seed_roster_ready ? "true" : "false";
  numeric("current_date_storage_raw64", input.current_date_storage_raw64);
  numeric("source_parent_wrapper_mode_i32", input.source_parent_wrapper_mode_i32);
  text_field("known_primary_vtable_identity", input.known_primary_vtable_identity);
  text_field("known_primary_slot0_target_identity", input.known_primary_slot0_target_identity);
  text_field("known_core_identity", input.known_core_identity);
  text_field("known_mode0_record_callback_identity", input.known_mode0_record_callback_identity);
  text_field("known_secondary_base_vtable_identity", input.known_secondary_base_vtable_identity);
  output += ",\"incoming\":[";
  for (std::size_t index = 0; index < input.incoming.size(); ++index) {
    if (index != 0) output += ',';
    const auto &incoming = input.incoming[index];
    output += '{'; state_fields(incoming);
    output += ",\"seed_incoming_native_indices\":[";
    for (std::size_t alias = 0; alias < incoming.seed_incoming_native_indices.size(); ++alias) {
      if (alias != 0) output += ',';
      output += number(incoming.seed_incoming_native_indices[alias]);
    }
    output += ']';
    text_field("arrg_identity", incoming.arrg_identity);
    numeric("arrg_full_id_u32", incoming.arrg_full_id_u32);
    text_field("arrg_primary_vtable_identity", incoming.arrg_primary_vtable_identity);
    text_field("arrg_primary_slot0_target_identity", incoming.arrg_primary_slot0_target_identity);
    output += ",\"data_pointer_present\":";
    output += incoming.data_pointer_present
        ? (*incoming.data_pointer_present ? "true" : "false") : "null";
    text_field("data_buffer_identity", incoming.data_buffer_identity);
    numeric("data_count_2c_raw_i32", incoming.data_count_2c_raw_i32);
    numeric("data_capacity_28_raw_i32", incoming.data_capacity_28_raw_i32);
    text_field("data_allocator_identity", incoming.data_allocator_identity);
    text_field("data_allocator_vtable_identity", incoming.data_allocator_vtable_identity);
    text_field("data_allocator_slot10_target_identity", incoming.data_allocator_slot10_target_identity);
    output += ",\"records\":[";
    for (std::size_t ordinal = 0; ordinal < incoming.records.size(); ++ordinal) {
      if (ordinal != 0) output += ',';
      const auto &record = incoming.records[ordinal];
      output += '{'; state_fields(record);
      output += ",\"native_index\":"; output += number(record.native_index);
      text_field("record_identity", record.record_identity);
      text_field("vtable_identity", record.vtable_identity);
      text_field("slot0_target_identity", record.slot0_target_identity);
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
