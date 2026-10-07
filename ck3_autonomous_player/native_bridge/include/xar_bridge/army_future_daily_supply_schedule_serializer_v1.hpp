#pragma once

#include "xar_bridge/army_future_daily_supply_schedule_v1.hpp"

#include <cstddef>
#include <string_view>

namespace xar::game {

template <class Number, class JsonString>
inline void AppendArmyFutureDailySupplyScheduleInputsV1(
    std::string &output, const ArmyFutureDailySupplyScheduleInputsV1 &input,
    Number number, JsonString append_json_string) {
  output += "{\"schema_version\":1,\"source\":\"native_future_daily_supply_schedule_inputs_12004\"";
  output += ",\"stage\":\"observed_current_all_phase_schedule\",\"status\":";
  append_json_string(output, input.status);
  output += ",\"ready\":";
  output += input.ready ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (input.unavailable_reason) append_json_string(output, *input.unavailable_reason);
  else output += "null";
  const auto numeric = [&](std::string_view key, const auto &value) {
    output += ',';
    append_json_string(output, key);
    output += ':';
    output += value ? number(*value) : "null";
  };
  numeric("subject_army_id_u32", input.subject_army_id_u32);
  numeric("subject_carmy_id_u32", input.subject_carmy_id_u32);
  numeric("current_date_storage_raw64", input.current_date_storage_raw64);
  numeric("current_date_raw_i32", input.current_date_raw_i32);
  numeric("native_day_index_raw_i32", input.native_day_index_raw_i32);
  numeric("selected_phase_index_i32", input.selected_phase_index_i32);
  output += ",\"secondary_identity\":\"game_data_plus_2a548\",\"phases\":[";
  for (std::size_t index = 0; index < input.phases.size(); ++index) {
    if (index != 0) output += ',';
    const auto &phase = input.phases[index];
    output += "{\"phase_index_i32\":";
    output += number(phase.phase_index_i32);
    output += ",\"status\":";
    append_json_string(output, phase.status);
    output += ",\"ready\":";
    output += phase.ready ? "true" : "false";
    output += ",\"unavailable_reason\":";
    if (phase.unavailable_reason) append_json_string(output, *phase.unavailable_reason);
    else output += "null";
    numeric("capacity_raw_i32", phase.capacity_raw_i32);
    numeric("count_raw_i32", phase.count_raw_i32);
    output += ",\"data_pointer_present\":";
    output += phase.data_pointer_present
        ? (*phase.data_pointer_present ? "true" : "false") : "null";
    output += ",\"matching_positions\":";
    if (phase.matching_positions) {
      output += '[';
      for (std::size_t position = 0; position < phase.matching_positions->size(); ++position) {
        if (position != 0) output += ',';
        output += number((*phase.matching_positions)[position]);
      }
      output += ']';
    } else output += "null";
    numeric("subject_occurrence_count_i32", phase.subject_occurrence_count_i32);
    output += '}';
  }
  output += ']';
  output += ",\"actual_future_callback_observed\":false";
  output += ",\"future_bucket_mutations_reconstructed\":false";
  output += ",\"full_daily_supply_transition_ready\":false,\"full_monthly_ready\":false}";
}

} // namespace xar::game
