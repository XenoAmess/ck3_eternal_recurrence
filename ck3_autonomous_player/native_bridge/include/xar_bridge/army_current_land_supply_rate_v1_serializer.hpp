#pragma once
#include "xar_bridge/game_contract.hpp"
#include <string>
#include <string_view>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendArmyCurrentLandSupplyRateInputsV1(
    std::string &result, const ArmyCurrentLandSupplyRateInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  result += "{\"source\":\"native_current_province_land_supply_rate_inputs\",\"status\":";
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
  numeric("subject_army_id", inputs.subject_army_id);
  numeric("subject_carmy_id", inputs.subject_carmy_id);
  numeric("owner_character_id", inputs.owner_character_id);
  numeric("commander_raw_full_id", inputs.commander_raw_full_id);
  numeric("commander_resolved_full_id", inputs.commander_resolved_full_id);
  boolean("native_land_branch_applicable", inputs.native_land_branch_applicable);
  boolean("commander_used_native_fallback", inputs.commander_used_native_fallback);
  boolean("native_province_component_applicable", inputs.native_province_component_applicable);
  numeric("province_component_raw", inputs.province_component_raw);
  numeric("commander_modifier_1a9_raw", inputs.commander_modifier_1a9_raw);
  numeric("loaded_excess_slope_raw", inputs.loaded_excess_slope_raw);
  numeric("loaded_min_loss_raw", inputs.loaded_min_loss_raw);
  numeric("loaded_max_loss_raw", inputs.loaded_max_loss_raw);
  numeric("loaded_divisor_floor_raw", inputs.loaded_divisor_floor_raw);
  result += ",\"scale\":100000}";
}
} // namespace xar::game
