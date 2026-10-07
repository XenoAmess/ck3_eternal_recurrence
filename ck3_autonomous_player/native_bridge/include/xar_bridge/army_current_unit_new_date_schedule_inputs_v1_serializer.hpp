#pragma once

#include "xar_bridge/army_current_unit_new_date_schedule_inputs_v1.hpp"

#include <string>
#include <string_view>

namespace xar::game {

template <class Number, class JsonString>
inline void AppendArmyCurrentUnitNewDateScheduleInputsV1(
    std::string &output, const ArmyCurrentUnitNewDateScheduleInputsV1 &inputs,
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
  optional_number("vector_header_count_i32", inputs.vector_header_count_i32);
  output += ",\"vector_data_present\":";
  output += inputs.vector_data_present
      ? (*inputs.vector_data_present ? "true" : "false") : "null";
  output += ",\"subject_stored_id_positions\":";
  if (inputs.subject_stored_id_positions) {
    output += '[';
    for (std::size_t index = 0; index < inputs.subject_stored_id_positions->size(); ++index) {
      if (index != 0) output += ',';
      output += number((*inputs.subject_stored_id_positions)[index]);
    }
    output += ']';
  } else output += "null";
  optional_number("subject_stored_id_occurrence_count_i32",
                  inputs.subject_stored_id_occurrence_count_i32);
  // These are source boundaries, not callback or movement predictions.
  output += ",\"actual_unit_new_date_callback_observed\":false"
            ",\"actual_movement_or_arrival_observed\":false"
            ",\"earlier_stage_outputs_reconstructed\":false"
            ",\"full_daily_supply_transition_ready\":false"
            ",\"full_monthly_ready\":false}";
}

} // namespace xar::game
