#pragma once
#include "xar_bridge/army_county_entry_preview_condition_v1.hpp"
#include <string>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendCountyEntryPreviewConditionV1(
    std::string &output, const ArmyCountyEntryPreviewConditionV1 &row,
    Number number, JsonString append_json_string) {
  output += "{\"schema_version\":1,\"source\":\"native_preview_first_edge_county_entry_condition\","
      "\"input_basis\":\"current_unit_and_preview_first_remaining_province\",\"predicate_rva\":38674992,";
  output += "\"status\":\"" + std::string(row.available ? "available" : "unavailable") + "\",\"unavailable_reason\":";
  if (row.available) output += "null"; else append_json_string(output, row.unavailable_reason);
  const auto integer = [&](const char *key, const auto &value) {
    output += ",\"" + std::string(key) + "\":";
    output += value.has_value() ? number(*value) : "null";
  };
  const auto boolean = [&](const char *key, const auto &value) {
    output += ",\"" + std::string(key) + "\":";
    output += value.has_value() ? (*value ? "true" : "false") : "null";
  };
  const auto identity = [&](const char *key, const auto &value) {
    output += ",\"" + std::string(key) + "\":";
    if (value) append_json_string(output, "native:" + std::to_string(*value));
    else output += "null";
  };
  output += ",\"subject_army_id\":" + number(row.subject_army_id);
  output += ",\"requested_target_province_id\":" + number(row.requested_target_province_id);
  output += ",\"source_province_id\":" + number(row.source_province_id);
  integer("target_province_id", row.target_province_id);
  integer("native_carmy_id", row.native_carmy_id);
  integer("actor_character_id", row.actor_character_id);
  integer("mode", row.mode);
  integer("army_1d4_raw", row.army_1d4_raw);
  integer("source_definition_1b_u8", row.source_definition_1b_u8);
  integer("target_definition_1b_u8", row.target_definition_1b_u8);
  boolean("source_county_present", row.source_county_present);
  boolean("target_county_present", row.target_county_present);
  boolean("county_objects_differ", row.county_objects_differ);
  identity("source_county_identity", row.source_county_identity);
  identity("target_county_identity", row.target_county_identity);
  integer("target_county_magic_3e0_u32", row.target_county_magic_3e0_u32);
  output += ",\"inputs_observation_ready\":" + std::string(row.inputs_observation_ready ? "true" : "false");
  output += ",\"native_condition_called\":" + std::string(row.native_condition_called ? "true" : "false");
  boolean("native_condition_passes", row.native_condition_passes);
  output += ",\"identity_before_after_match\":" + std::string(row.identity_before_after_match ? "true" : "false");
  output += ",\"internal_subpredicates_observed\":false,\"actual_loss_observed\":false}";
}
} // namespace xar::game
