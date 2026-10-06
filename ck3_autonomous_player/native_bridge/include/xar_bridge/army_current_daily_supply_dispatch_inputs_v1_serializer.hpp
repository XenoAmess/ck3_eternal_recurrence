#pragma once
#include "xar_bridge/army_current_daily_supply_dispatch_inputs_v1.hpp"
#include <string_view>

namespace xar::game {
template <class Number, class JsonString>
inline void AppendArmyCurrentDailySupplyDispatchInputsV1(
    std::string &output, const ArmyCurrentDailySupplyDispatchInputsV1 &input,
    Number number, JsonString append_json_string) {
  output += "{\"source\":\"native_current_selected_supply_bucket_subject_occurrences\",\"status\":";
  append_json_string(output, input.status);
  output += ",\"ready\":"; output += input.ready ? "true" : "false";
  output += ",\"unavailable_reason\":";
  if (input.unavailable_reason) append_json_string(output, *input.unavailable_reason);
  else output += "null";
  const auto numeric = [&](std::string_view key, const auto &value) {
    output += ','; append_json_string(output, key); output += ':';
    output += value ? number(*value) : "null";
  };
  numeric("subject_army_id", input.subject_army_id);
  numeric("subject_carmy_id", input.subject_carmy_id);
  numeric("current_date_raw", input.current_date_raw);
  numeric("native_day_index", input.native_day_index);
  numeric("selected_bucket_phase", input.selected_bucket_phase);
  numeric("selected_bucket_capacity_raw", input.selected_bucket_capacity_raw);
  numeric("selected_bucket_count_raw", input.selected_bucket_count_raw);
  output += ",\"selected_bucket_data_present\":";
  output += input.selected_bucket_data_present
      ? (*input.selected_bucket_data_present ? "true" : "false") : "null";
  output += ",\"subject_occurrence_indices\":";
  if (input.subject_occurrence_indices) {
    output += '[';
    for (std::size_t i = 0; i < input.subject_occurrence_indices->size(); ++i) {
      if (i != 0) output += ',';
      output += number((*input.subject_occurrence_indices)[i]);
    }
    output += ']';
  } else output += "null";
  numeric("subject_dispatch_occurrence_count", input.subject_dispatch_occurrence_count);
  output += ",\"capture_boundary\":\"current_paused_strength\"";
  output += ",\"actual_callback_observed\":false,\"earlier_stage_outputs_reconstructed\":false";
  output += ",\"full_daily_supply_transition_ready\":false,\"full_monthly_ready\":false}";
}
} // namespace xar::game
