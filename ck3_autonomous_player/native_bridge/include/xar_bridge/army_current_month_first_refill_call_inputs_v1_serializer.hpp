#pragma once

#include "xar_bridge/army_current_month_first_refill_call_inputs_v1.hpp"
#include <string_view>

namespace xar::game {
template <class Number, class JsonString>
inline void AppendArmyCurrentMonthFirstRefillCallInputsV1(
    std::string &output, const ArmyCurrentMonthFirstRefillCallInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  output += "{\"source\":\"native_current_month_first_refill_call_inputs\",\"status\":";
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
  numeric("subject_army_id", inputs.subject_army_id);
  numeric("subject_carmy_id", inputs.subject_carmy_id);
  numeric("game_state_calendar_flags_raw_u8", inputs.game_state_calendar_flags_raw_u8);
  output += ",\"month_first_mask_2_set\":";
  output += inputs.month_first_mask_2_set
      ? (*inputs.month_first_mask_2_set ? "true" : "false") : "null";
  output += ",\"actual_pre_date_prepare_observed\":false,\"actual_post_date_refill_observed\":false"
            ",\"actual_after\":false,\"full_monthly_ready\":false}";
}
} // namespace xar::game
