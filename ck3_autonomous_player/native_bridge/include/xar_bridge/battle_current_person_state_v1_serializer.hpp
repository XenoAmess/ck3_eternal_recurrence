#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <string>
#include <string_view>

namespace xar::bridge {
namespace battle_current_person_state_v1_detail {

inline void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output += '\\';
      output += static_cast<char>(character);
    } else if (character < 0x20U) {
      output += "\\u00";
      output += hex[(character >> 4U) & 0x0FU];
      output += hex[character & 0x0FU];
    } else {
      output += static_cast<char>(character);
    }
  }
  output += '"';
}

inline void AppendReason(std::string &output, bool observed,
                         std::string_view reason, std::string_view fallback) {
  if (observed) output += "null";
  else AppendString(output, reason.empty() ? fallback : reason);
}

inline std::string_view TraitStatusName(
    xar::game::BattleCurrentPersonInjuryTraitsStatusV1 status) {
  switch (status) {
  case xar::game::BattleCurrentPersonInjuryTraitsStatusV1::available:
    return "available";
  case xar::game::BattleCurrentPersonInjuryTraitsStatusV1::partial:
    return "partial";
  case xar::game::BattleCurrentPersonInjuryTraitsStatusV1::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

}  // namespace battle_current_person_state_v1_detail

// A current-character read; it does not project historical injury causality.
// The enclosing serializer controls optional presence and current-only scope.
inline std::string SerializeBattleCurrentPersonStateV1(
    const xar::game::BattleCurrentPersonStateSnapshotV1 &state) {
  using namespace battle_current_person_state_v1_detail;
  const auto &prowess = state.effective_prowess;
  const auto &injury = state.injury_traits;
  std::string output = "{\"scope\":\"current_character\","
                       "\"effective_prowess\":{\"status\":";
  AppendString(output, prowess.available ? "available" : "unavailable");
  output += ",\"points\":";
  output += prowess.available && prowess.points.has_value()
                ? std::to_string(*prowess.points) : "null";
  output += ",\"unavailable_reason\":";
  AppendReason(output, prowess.available, prowess.unavailable_reason,
               "effective_prowess_unavailable");
  output += "},\"injury_traits\":{\"status\":";
  AppendString(output, TraitStatusName(injury.status));
  output += ",\"flags\":{";
  constexpr std::string_view keys[] = {
      "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
      "one_eyed", "disfigured", "incapable"};
  for (std::size_t index = 0; index < injury.flags.size(); ++index) {
    if (index != 0) output += ',';
    AppendString(output, keys[index]);
    output += ':';
    output += injury.flags[index].has_value()
                  ? (*injury.flags[index] ? "true" : "false") : "null";
  }
  output += "},\"wounded_rank\":";
  output += injury.wounded_rank.has_value()
                ? std::to_string(*injury.wounded_rank) : "null";
  output += ",\"wounded_rank_unavailable_reason\":";
  AppendReason(output, injury.wounded_rank.has_value(),
               injury.wounded_rank_unavailable_reason, "wounded_rank_unavailable");
  output += ",\"unavailable_reason\":";
  AppendReason(output,
               injury.status == xar::game::BattleCurrentPersonInjuryTraitsStatusV1::available,
               injury.unavailable_reason, "injury_trait_reads_unavailable");
  output += "}}";
  return output;
}

}  // namespace xar::bridge
