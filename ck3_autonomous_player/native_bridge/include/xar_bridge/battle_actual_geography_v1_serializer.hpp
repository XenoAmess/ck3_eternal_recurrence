#pragma once

#include "xar_bridge/game_contract.hpp"

#include <string>
#include <string_view>

namespace xar::bridge {
namespace battle_actual_geography_v1_detail {

inline void String(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  out += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') {
      out += '\\';
      out += static_cast<char>(c);
    } else if (c < 0x20U) {
      out += "\\u00";
      out += hex[(c >> 4U) & 0x0FU];
      out += hex[c & 0x0FU];
    } else {
      out += static_cast<char>(c);
    }
  }
  out += '"';
}

} // namespace battle_actual_geography_v1_detail

inline std::string SerializeBattleActualGeographyV1(
    const game::BattleActualGeographyInputsV1 &inputs) {
  using battle_actual_geography_v1_detail::String;
  const auto &terrain = inputs.terrain;
  if (terrain.scale != 100'000 ||
      (terrain.available &&
       (terrain.key.empty() || !terrain.unavailable_reason.empty())) ||
      (!terrain.available && terrain.unavailable_reason.empty())) {
    return {};
  }
  std::string out = "{\"terrain\":{\"status\":";
  String(out, terrain.available ? "available" : "unavailable");
  out += ",\"key\":";
  if (terrain.available) String(out, terrain.key);
  else out += "null";
  out += ",\"combat_width_multiplier_raw\":";
  out += terrain.available
      ? std::to_string(terrain.combat_width_multiplier_raw) : "null";
  out += ",\"scale\":100000,\"unavailable_reason\":";
  if (terrain.available) out += "null";
  else String(out, terrain.unavailable_reason);
  out += "},\"constructor_adjacency_kind_raw\":";
  out += inputs.constructor_adjacency_kind_raw
      ? std::to_string(*inputs.constructor_adjacency_kind_raw) : "null";
  out += ",\"holding_defender\":";
  out += !inputs.holding_defender ? "null"
      : (*inputs.holding_defender ? "true" : "false");
  out += '}';
  return out;
}

} // namespace xar::bridge
