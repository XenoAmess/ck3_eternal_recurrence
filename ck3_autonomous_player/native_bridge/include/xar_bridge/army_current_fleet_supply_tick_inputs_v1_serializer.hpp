#pragma once
#include "xar_bridge/army_current_fleet_supply_tick_inputs_v1.hpp"
#include <string_view>

namespace xar::game {
template <class Number, class JsonString>
inline void AppendArmyCurrentFleetSupplyTickInputsV1(
    std::string &output, const ArmyCurrentFleetSupplyTickInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  output += "{\"source\":\"native_current_fleet_supply_tick_inputs\",\"status\":";
  append_json_string(output, inputs.status);
  output += ",\"ready\":";
  output += inputs.ready ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (inputs.unavailable_reason) append_json_string(output, *inputs.unavailable_reason);
  else output += "null";
  const auto numeric = [&](std::string_view key, const auto &value) {
    output += ','; append_json_string(output, key); output += ':';
    output += value ? number(*value) : "null";
  };
  const auto boolean = [&](std::string_view key, const std::optional<bool> &value) {
    output += ','; append_json_string(output, key); output += ':';
    output += value ? (*value ? "true" : "false") : "null";
  };
  numeric("subject_army_id", inputs.subject_army_id);
  numeric("subject_carmy_id", inputs.subject_carmy_id);
  numeric("province_id", inputs.province_id);
  boolean("native_fleet_branch_applicable", inputs.native_fleet_branch_applicable);
  numeric("current_native_date_low32", inputs.current_native_date_low32);
  numeric("fleet_raw_full_id", inputs.fleet_raw_full_id);
  numeric("fleet_resolved_full_id", inputs.fleet_resolved_full_id);
  boolean("fleet_used_native_fallback", inputs.fleet_used_native_fallback);
  numeric("fleet_day_raw", inputs.fleet_day_raw);
  numeric("loaded_fleet_day_sentinel_raw", inputs.loaded_fleet_day_sentinel_raw);
  numeric("terrain_magic_38_raw", inputs.terrain_magic_38_raw);
  numeric("terrain_modifier_772_id", inputs.terrain_modifier_772_id);
  numeric("terrain_modifier_772_raw", inputs.terrain_modifier_772_raw);
  numeric("commander_raw_full_id", inputs.commander_raw_full_id);
  numeric("commander_resolved_full_id", inputs.commander_resolved_full_id);
  boolean("commander_used_native_fallback", inputs.commander_used_native_fallback);
  numeric("loaded_fleet_loss_raw", inputs.loaded_fleet_loss_raw);
  numeric("commander_modifier_1a9_raw", inputs.commander_modifier_1a9_raw);
  numeric("loaded_divisor_floor_raw", inputs.loaded_divisor_floor_raw);
  numeric("loaded_max_loss_raw", inputs.loaded_max_loss_raw);
  output += ",\"scale\":100000}";
}
} // namespace xar::game
