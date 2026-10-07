#pragma once

#include "xar_bridge/army_current_unit_new_date_callback_entry_inputs_v1.hpp"

#include <string>
#include <string_view>

namespace xar::game {

template <class Number, class JsonString>
inline void AppendArmyCurrentUnitNewDateCallbackEntryInputsV1(
    std::string &output, const ArmyCurrentUnitNewDateCallbackEntryInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  output += "{\"schema_version\":" + number(inputs.schema_version);
  output += ",\"source\":";
  append_json_string(output, inputs.source);
  output += ",\"capture_boundary\":";
  append_json_string(output, inputs.capture_boundary);
  output += ",\"status\":";
  append_json_string(output, inputs.status);
  output += ",\"ready\":";
  output += inputs.ready ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (inputs.unavailable_reason) append_json_string(output, *inputs.unavailable_reason);
  else output += "null";
  const auto optional_number = [&](std::string_view key, const auto &value) {
    output += ',';
    append_json_string(output, key);
    output += ':';
    output += value ? number(*value) : "null";
  };
  optional_number("subject_army_id_u32", inputs.subject_army_id_u32);
  optional_number("subject_carmy_id_u32", inputs.subject_carmy_id_u32);
  optional_number("unit_route_count_i32", inputs.unit_route_count_i32);
  output += '}';
}

} // namespace xar::game
