#pragma once

#include "xar_bridge/game_contract.hpp"
#include <string>
#include <string_view>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendArmyCurrentLandResupplyV1(
    std::string &result, const ArmyCurrentLandResupplyV1 &inputs,
    Number number, JsonString append_json_string) {
  result += "{\"source\":\"native_current_province_land_resupply\",\"status\":";
  append_json_string(result, inputs.status);
  result += ",\"unavailable_reason\":";
  if (inputs.unavailable_reason.empty()) result += "null";
  else append_json_string(result, inputs.unavailable_reason);
  result += ",\"current_observation_ready\":";
  result += inputs.current_observation_ready ? "true" : "false";
  const auto numeric = [&](std::string_view key, const auto &value) {
    result += ','; append_json_string(result, key); result += ':';
    result += value ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    result += ','; append_json_string(result, key); result += ':';
    result += value ? (*value ? "true" : "false") : "null";
  };
  numeric("province_id", inputs.province_id);
  numeric("owner_character_id", inputs.owner_character_id);
  boolean("native_land_branch_applicable", inputs.native_land_branch_applicable);
  boolean("native_resupply_eligible", inputs.native_resupply_eligible);
  numeric("loaded_gain_raw", inputs.loaded_gain_raw);
  result += ",\"scale\":100000}";
}
} // namespace xar::game
