#pragma once

#include "xar_bridge/army_captured_target_land_supply_inputs_v1.hpp"

namespace xar::game {

template<class Number, class JsonString>
inline void AppendArmyCapturedTargetLandSupplyInputsV1(
    std::string &output, const ArmyCapturedTargetLandSupplyInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  output += "{\"source\":\"native_captured_target_land_supply_inputs\","
            "\"input_basis\":\"captured_owner_and_target_province\","
            "\"scale\":100000,\"status\":";
  append_json_string(output, inputs.status);
  const auto optional_number = [&](const char *key, const auto &value) {
    output += ",\"";
    output += key;
    output += "\":";
    output += value.has_value() ? number(*value) : "null";
  };
  const auto optional_bool = [&](const char *key, const std::optional<bool> &value) {
    output += ",\"";
    output += key;
    output += "\":";
    output += value.has_value() ? (*value ? "true" : "false") : "null";
  };
  const auto optional_string = [&](const char *key,
                                   const std::optional<std::string> &value) {
    output += ",\"";
    output += key;
    output += "\":";
    if (value.has_value()) append_json_string(output, *value);
    else output += "null";
  };
  output += ",\"current_inputs_ready\":";
  output += inputs.current_inputs_ready ? "true" : "false";
  optional_string("unavailable_reason", inputs.unavailable_reason);
  optional_number("subject_army_id", inputs.subject_army_id);
  optional_number("subject_carmy_id", inputs.subject_carmy_id);
  optional_number("owner_character_id", inputs.owner_character_id);
  optional_number("province_id", inputs.province_id);
  output += ",\"province_component_observation_ready\":";
  output += inputs.province_component_observation_ready ? "true" : "false";
  optional_string("province_component_unavailable_reason",
                  inputs.province_component_unavailable_reason);
  optional_bool("native_province_component_applicable",
                inputs.native_province_component_applicable);
  optional_number("province_component_raw", inputs.province_component_raw);
  output += ",\"resupply_observation_ready\":";
  output += inputs.resupply_observation_ready ? "true" : "false";
  optional_string("resupply_unavailable_reason", inputs.resupply_unavailable_reason);
  optional_bool("native_resupply_eligible", inputs.native_resupply_eligible);
  optional_number("loaded_gain_raw", inputs.loaded_gain_raw);
  output += '}';
}

} // namespace xar::game
