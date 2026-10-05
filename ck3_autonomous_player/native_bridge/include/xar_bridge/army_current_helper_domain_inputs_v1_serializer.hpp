#pragma once
#include "xar_bridge/game_contract.hpp"
#include <string>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendArmyCurrentHelperDomainInputsV1(
    std::string &output, const ArmyCurrentHelperDomainInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  const auto integer = [&](std::string_view key, const auto &value) {
    output += ",\""; output += key; output += "\":";
    output += value ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    output += ",\""; output += key; output += "\":";
    output += value ? (*value ? "true" : "false") : "null";
  };
  output += "{\"status\":\"";
  output += inputs.available ? "available" : "unavailable";
  output += "\",\"ready\":"; output += inputs.available ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (inputs.unavailable_reason.empty()) output += "null";
  else append_json_string(output, inputs.unavailable_reason);
  output += ",\"entry_army_id\":" + number(inputs.entry_army_id);
  integer("group_count_5c_raw", inputs.group_count_5c_raw);
  output += ",\"rows\":";
  if (inputs.rows) {
    output += '['; bool first = true;
    for (const auto &row : *inputs.rows) {
      if (!first) output += ',';
      first = false;
      output += "{\"group_index\":" + number(row.group_index);
      output += ",\"stored_index\":" + number(row.stored_index);
      output += ",\"record_regiment_reference_id\":" + number(row.record_regiment_reference_id);
      output += ",\"chunk_index\":" + number(row.chunk_index);
      integer("record_regiment_resolved_id", row.record_regiment_resolved_id);
      boolean("record_regiment_used_fallback", row.record_regiment_used_fallback);
      integer("record_regiment_magic_14_raw", row.record_regiment_magic_14_raw);
      boolean("data_record_present", row.data_record_present);
      integer("data_state_18_raw", row.data_state_18_raw);
      integer("data_owner_regiment_reference_id", row.data_owner_regiment_reference_id);
      integer("receiver_regiment_resolved_id", row.receiver_regiment_resolved_id);
      boolean("receiver_regiment_used_fallback", row.receiver_regiment_used_fallback);
      integer("receiver_state_138_raw", row.receiver_state_138_raw);
      integer("receiver_title_reference_130_raw", row.receiver_title_reference_130_raw);
      integer("receiver_character_reference_12c_raw", row.receiver_character_reference_12c_raw);
      integer("owner_title_resolved_id", row.owner_title_resolved_id);
      boolean("owner_title_used_fallback", row.owner_title_used_fallback);
      integer("owner_title_holder_character_id_128_raw", row.owner_title_holder_character_id_128_raw);
      integer("selected_character_reference_id", row.selected_character_reference_id);
      integer("selected_character_resolved_id", row.selected_character_resolved_id);
      boolean("selected_character_used_fallback", row.selected_character_used_fallback);
      boolean("character_domain_child_present", row.character_domain_child_present);
      integer("domain_reference_id", row.domain_reference_id);
      integer("domain_resolved_id", row.domain_resolved_id);
      boolean("domain_used_fallback", row.domain_used_fallback);
      integer("domain_magic_0c_raw", row.domain_magic_0c_raw);
      boolean("domain_data_30_present", row.domain_data_30_present);
      integer("domain_flag_17e_raw", row.domain_flag_17e_raw);
      integer("count_base_128_raw", row.count_base_128_raw);
      output += ",\"count_records\":";
      if (row.count_records) {
        output += '['; bool first_count = true;
        for (const auto &record : *row.count_records) {
          if (!first_count) output += ',';
          first_count = false;
          output += "{\"stored_index\":" + number(record.stored_index);
          output += ",\"count_00_raw\":" + number(record.count_00_raw);
          output += ",\"count_04_raw\":" + number(record.count_04_raw);
          output += ",\"state_18_raw\":" + number(record.state_18_raw) + '}';
        }
        output += ']';
      } else output += "null";
      integer("domain_owner_character_reference_id", row.domain_owner_character_reference_id);
      integer("domain_owner_character_resolved_id", row.domain_owner_character_resolved_id);
      boolean("domain_owner_character_used_fallback", row.domain_owner_character_used_fallback);
      integer("domain_owner_character_magic_1c_raw", row.domain_owner_character_magic_1c_raw);
      integer("domain_value_48_raw64", row.domain_value_48_raw64);
      integer("domain_alias_ordinal", row.domain_alias_ordinal);
      output += '}';
    }
    output += ']';
  } else output += "null";
  output += '}';
}
} // namespace xar::game
