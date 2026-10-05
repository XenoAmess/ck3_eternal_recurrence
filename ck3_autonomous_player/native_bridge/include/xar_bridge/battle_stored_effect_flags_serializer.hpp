#pragma once

#include "xar_bridge/game_contract.hpp"

#include <string>

namespace xar::bridge {
inline std::string SerializeStoredEffectFlagsV1(const game::BattleStoredEffectFlagsV1 &flags) {
  const bool available = flags.flag88_raw.has_value() && flags.flag89_raw.has_value();
  std::string out = available ? "{\"status\":\"available\",\"flag88_raw\":"
                              : "{\"status\":\"unavailable\",\"flag88_raw\":";
  out += flags.flag88_raw ? std::to_string(*flags.flag88_raw) : "null";
  out += ",\"flag89_raw\":";
  out += flags.flag89_raw ? std::to_string(*flags.flag89_raw) : "null";
  out += ",\"unavailable_reason\":";
  if (available) out += "null";
  else out += '"' + flags.unavailable_reason + '"';
  out += '}';
  return out;
}
} // namespace xar::bridge
