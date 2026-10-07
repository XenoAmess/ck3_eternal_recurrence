#pragma once

#include "xar_bridge/army_current_character_detachment_inputs_v1.hpp"

#include <cstddef>
#include <string_view>

namespace xar::game {

template <class Number, class JsonString>
inline void AppendArmyCurrentCharacterDetachmentInputsV1(
    std::string &output, const ArmyCurrentCharacterDetachmentInputsV1 &input,
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
  const auto resolution = [&](std::string_view key,
                              const ArmyCharacterDetachmentResolutionV1 &value) {
    output += ','; append_json_string(output, key); output += ":{";
    state_fields(value);
    numeric("requested_full_id_u32", value.requested_full_id_u32);
    boolean("registry_loaded", value.registry_loaded);
    numeric("registry_capacity_u32", value.registry_capacity_u32);
    numeric("registry_index_u32", value.registry_index_u32);
    text_field("indexed_identity", value.indexed_identity);
    numeric("indexed_full_id_u32", value.indexed_full_id_u32);
    text_field("selection", value.selection);
    boolean("used_fallback", value.used_fallback);
    text_field("object_identity", value.object_identity);
    numeric("selected_full_id_u32", value.selected_full_id_u32);
    output += '}';
  };
  output += "{\"schema_version\":1,\"source\":\"native_current_character_detachment_inputs_12004\"";
  output += ",\"stage\":\"observed_current_character_detachment_seed\",";
  state_fields(input);
  output += ",\"seed_selection_ready\":";
  output += input.seed_selection_ready ? "true" : "false";
  output += ",\"seed_roster_ready\":";
  output += input.seed_roster_ready ? "true" : "false";
  numeric("current_date_storage_raw64", input.current_date_storage_raw64);
  text_field("source_parent_identity", input.source_parent_identity);
  output += ",\"requests\":[";
  for (std::size_t index = 0; index < input.requests.size(); ++index) {
    if (index != 0) output += ',';
    const auto &request = input.requests[index];
    output += '{'; state_fields(request);
    output += ",\"seed_incoming_native_index\":";
    output += number(request.seed_incoming_native_index);
    text_field("arrg_identity", request.arrg_identity);
    numeric("character_full_id_148_u32", request.character_full_id_148_u32);
    resolution("character_resolution", request.character_resolution);
    text_field("passed_province_identity", request.passed_province_identity);
    boolean("current_extension_1b8_present", request.current_extension_1b8_present);
    text_field("current_extension_1b8_identity", request.current_extension_1b8_identity);
    numeric("extension_f8_raw_u32", request.extension_f8_raw_u32);
    numeric("extension_100_raw64", request.extension_100_raw64);
    output += ",\"extension_reset_inputs_ready\":";
    output += request.extension_reset_inputs_ready ? "true" : "false";
    output += ",\"source_chain_ready\":";
    output += request.source_chain_ready ? "true" : "false";
    resolution("arrg_resolution", request.arrg_resolution);
    numeric("army_full_id_140_u32", request.army_full_id_140_u32);
    resolution("army_resolution", request.army_resolution);
    numeric("unit_full_id_124_u32", request.unit_full_id_124_u32);
    resolution("unit_resolution", request.unit_resolution);
    output += '}';
  }
  output += ']';
  output += ",\"actual_callback_observed\":false,\"actual_resource_return_observed\":false";
  output += ",\"actual_after_state_observed\":false,\"full_detachment_transition_ready\":false";
  output += ",\"full_daily_ready\":false,\"full_monthly_ready\":false";
  output += ",\"full_character_detachment_suffix_ready\":false,\"future_date_ready\":false}";
}

} // namespace xar::game
