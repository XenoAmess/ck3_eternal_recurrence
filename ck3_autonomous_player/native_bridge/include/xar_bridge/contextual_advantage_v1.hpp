#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <string>
#include <string_view>

namespace xar::bridge {

namespace contextual_advantage_v1_detail {

inline void AppendJsonString(std::string &result, std::string_view value) {
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

inline void AppendSide(
    std::string &result,
    const xar::game::ContextualAdvantageSideSnapshot &side) {
  result += "{\"side_index\":" + std::to_string(side.side_index);
  result += ",\"ordered_public_cunit_ids\":[";
  for (std::size_t index = 0; index < side.ordered_public_cunit_ids.size();
       ++index) {
    if (index != 0) result += ',';
    result += std::to_string(side.ordered_public_cunit_ids[index]);
  }
  result += "],\"selected_commander_character_id\":";
  result += side.selected_commander_character_id == -1
                ? "null"
                : std::to_string(side.selected_commander_character_id);
  result += ",\"relation_kind_raw\":" + std::to_string(side.relation_kind_raw);
  result += ",\"commander_dynamic_raw\":" +
            std::to_string(side.commander_dynamic_raw);
  result += ",\"side_dynamic_raw\":" + std::to_string(side.side_dynamic_raw);
  result += ",\"target_conditionals_residual_raw\":" +
            std::to_string(side.target_conditionals_residual_raw);
  result += ",\"side_total_raw\":" + std::to_string(side.side_total_raw);
  result += '}';
}

}  // namespace contextual_advantage_v1_detail

// Pure typed serialization for the narrow, synthetic nonreligious context.
// The v2 caller controls optional presence with snapshot.attempted; availability
// here belongs only to this fragment and cannot grant full encounter readiness.
inline std::string SerializeContextualAdvantageV1(
    const xar::game::ContextualAdvantageSnapshot &snapshot) {
  std::string result = "{\"schema_version\":1,\"status\":";
  result += snapshot.available ? "\"available\"" : "\"unavailable\"";
  result += ",\"scope\":\"hypothetical_nonreligious_constructor_context\","
            "\"scale\":100000,\"target_province_id\":";
  result += std::to_string(snapshot.target_province_id);
  result += ",\"sides\":";
  if (snapshot.available) {
    result += '[';
    for (std::size_t index = 0; index < snapshot.sides.size(); ++index) {
      if (index != 0) result += ',';
      contextual_advantage_v1_detail::AppendSide(result, snapshot.sides[index]);
    }
    result += ']';
    result += ",\"base_nonreligious_accumulator_raw\":" +
              std::to_string(snapshot.base_nonreligious_accumulator_raw);
    result += ",\"synthetic_zero_roll_total_raw\":" +
              std::to_string(snapshot.synthetic_zero_roll_total_raw);
    result += ",\"synthetic_helper_total_match\":";
    result += snapshot.synthetic_helper_total_match ? "true" : "false";
  } else {
    result += "null,\"base_nonreligious_accumulator_raw\":null,"
              "\"synthetic_zero_roll_total_raw\":null,"
              "\"synthetic_helper_total_match\":null";
  }
  result += ",\"partial_context_observation_ready\":";
  result += snapshot.available ? "true" : "false";
  result += ",\"complete_encounter_advantage_ready\":false,"
            "\"missing_domains\":[\"religion_constructor_sources\"],"
            "\"unavailable_reason\":";
  if (snapshot.available) {
    result += "null";
  } else {
    contextual_advantage_v1_detail::AppendJsonString(
        result, snapshot.unavailable_reason.empty()
                    ? std::string_view("contextual_advantage_read_unavailable")
                    : std::string_view(snapshot.unavailable_reason));
  }
  result += '}';
  return result;
}

}  // namespace xar::bridge
