#pragma once
#include "xar_bridge/game_contract.hpp"
#include <string>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendArmyCurrentHelperPointStoreInputsV1(
    std::string &output, const ArmyCurrentHelperPointStoreInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  const auto integer = [&](std::string_view key, const auto &value) {
    output += ",\""; output += key; output += "\":";
    output += value ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    output += ",\""; output += key; output += "\":";
    output += value ? (*value ? "true" : "false") : "null";
  };
  output += "{\"status\":\""; output += inputs.available ? "available" : "unavailable";
  output += "\",\"ready\":"; output += inputs.available ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (inputs.unavailable_reason.empty()) output += "null";
  else append_json_string(output, inputs.unavailable_reason);
  output += ",\"entry_army_id\":" + number(inputs.entry_army_id);
  integer("helper_resolved_army_id", inputs.helper_resolved_army_id);
  boolean("helper_used_fallback", inputs.helper_used_fallback);
  boolean("helper_same_current_army_pointer", inputs.helper_same_current_army_pointer);
  integer("group_count_5c_raw", inputs.group_count_5c_raw);
  output += ",\"groups\":";
  if (inputs.groups) {
    output += '['; bool first_group = true;
    for (const auto &group : *inputs.groups) {
      if (!first_group) output += ',';
      first_group = false;
      output += "{\"group_index\":" + number(group.group_index);
      output += ",\"record_count_14_raw\":" + number(group.record_count_14_raw);
      output += ",\"record_rows\":";
      if (group.record_rows) {
        output += '['; bool first_record = true;
        for (const auto &row : *group.record_rows) {
          if (!first_record) output += ',';
          first_record = false;
          output += "{\"stored_index\":" + number(row.stored_index);
          output += ",\"record_regiment_reference_id\":" + number(row.record_regiment_reference_id);
          output += ",\"chunk_index\":" + number(row.chunk_index);
          integer("record_regiment_resolved_id", row.record_regiment_resolved_id);
          boolean("record_regiment_used_fallback", row.record_regiment_used_fallback);
          integer("record_regiment_magic_14_raw", row.record_regiment_magic_14_raw);
          boolean("data_record_present", row.data_record_present);
          integer("data_alias_ordinal", row.data_alias_ordinal);
          integer("data_byte_14_raw", row.data_byte_14_raw);
          integer("data_state_18_raw", row.data_state_18_raw);
          integer("data_owner_regiment_reference_id", row.data_owner_regiment_reference_id);
          integer("receiver_regiment_resolved_id", row.receiver_regiment_resolved_id);
          boolean("receiver_regiment_used_fallback", row.receiver_regiment_used_fallback);
          integer("receiver_title_reference_130_raw", row.receiver_title_reference_130_raw);
          integer("receiver_character_reference_12c_raw", row.receiver_character_reference_12c_raw);
          integer("owner_title_resolved_id", row.owner_title_resolved_id);
          boolean("owner_title_used_fallback", row.owner_title_used_fallback);
          integer("owner_title_holder_character_id_128_raw", row.owner_title_holder_character_id_128_raw);
          integer("selected_character_reference_id", row.selected_character_reference_id);
          integer("selected_character_resolved_id", row.selected_character_resolved_id);
          boolean("selected_character_used_fallback", row.selected_character_used_fallback);
          boolean("character_child_1c0_present", row.character_child_1c0_present);
          integer("membership_alias_ordinal", row.membership_alias_ordinal);
          integer("membership_count_2b4_raw", row.membership_count_2b4_raw);
          output += ",\"ordered_persistent_regiment_ids_2a8\":";
          if (row.ordered_persistent_regiment_ids_2a8) {
            output += '['; bool first_id = true;
            for (const auto id : *row.ordered_persistent_regiment_ids_2a8) {
              if (!first_id) output += ',';
              first_id = false; output += number(id);
            }
            output += ']';
          } else output += "null";
          output += '}';
        }
        output += ']';
      } else output += "null";
      output += ",\"character_count_2c_raw\":" + number(group.character_count_2c_raw);
      output += ",\"character_rows\":";
      if (group.character_rows) {
        output += '['; bool first_character = true;
        for (const auto &row : *group.character_rows) {
          if (!first_character) output += ',';
          first_character = false;
          output += "{\"stored_index\":" + number(row.stored_index);
          output += ",\"character_reference_id\":" + number(row.character_reference_id);
          integer("character_resolved_id", row.character_resolved_id);
          boolean("character_used_fallback", row.character_used_fallback);
          boolean("character_child_1b8_present", row.character_child_1b8_present);
          integer("child_1b8_alias_ordinal", row.child_1b8_alias_ordinal);
          integer("child_byte_108_raw", row.child_byte_108_raw);
          integer("child_character_reference_fc_raw", row.child_character_reference_fc_raw);
          boolean("character_child_1c8_present", row.character_child_1c8_present);
          boolean("character_child_1c0_present", row.character_child_1c0_present);
          output += '}';
        }
        output += ']';
      } else output += "null";
      output += '}';
    }
    output += ']';
  } else output += "null";
  output += '}';
}
} // namespace xar::game
