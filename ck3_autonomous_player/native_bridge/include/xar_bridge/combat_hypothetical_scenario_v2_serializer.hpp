#pragma once

#include "xar_bridge/game_contract.hpp"

#include <string>
#include <string_view>

namespace xar::game {
namespace detail {

inline void AppendCombatScenarioStringV2(std::string &result,
                                         std::string_view value) {
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

inline void AppendCombatScenarioIdsV2(
    std::string &result, const std::vector<std::int32_t> &values) {
  result += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) result += ',';
    result += std::to_string(values[index]);
  }
  result += ']';
}

} // namespace detail

// Shared production scenario wire for v2 and the v3 base_inputs projection.
// Legacy explicit-entry JSON is retained byte for byte. Constructor raw0 is
// a native geometry operand; downstream loaded effects still determine bonus.
inline std::string SerializeCombatHypotheticalScenarioV2(
    const CombatHypotheticalScenarioSnapshot &scenario) {
  const bool constructor_mode = scenario.constructor_adjacency_kind_raw.has_value();
  std::string result = "{\"kind\":\"explicit_hypothetical_contact\","
                       "\"attacker_entry_province_id\":";
  if (constructor_mode) {
    result += "null,\"contact_geometry_mode\":\"native_defender_constructor_zero\","
              "\"constructor_adjacency_kind_raw\":";
    result += std::to_string(*scenario.constructor_adjacency_kind_raw);
  } else {
    result += std::to_string(scenario.attacker_entry_province_id);
  }
  result += ",\"attacker_army_ids\":";
  detail::AppendCombatScenarioIdsV2(result, scenario.attacker_army_ids);
  result += ",\"defender_army_ids\":";
  detail::AppendCombatScenarioIdsV2(result, scenario.defender_army_ids);
  result += ",\"attacker_side\":";
  detail::AppendCombatScenarioStringV2(result, scenario.attacker_side);
  result += ",\"defender_side\":";
  detail::AppendCombatScenarioStringV2(result, scenario.defender_side);
  result += ",\"attacker_position_policy\":";
  result += constructor_mode ? "\"fixed_at_target_hypothetical\""
                             : "\"fixed_at_entry_hypothetical\"";
  result += ",\"defender_position_policy\":\"fixed_at_target_hypothetical\","
            "\"defender_insertion_order_policy\":\"explicit_request_order_hypothetical\","
            "\"actual_route_dependency\":false}";
  return result;
}

} // namespace xar::game
