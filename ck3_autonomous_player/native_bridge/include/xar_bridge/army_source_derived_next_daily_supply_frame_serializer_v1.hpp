#pragma once

#include "xar_bridge/army_source_derived_next_daily_supply_frame_v1.hpp"

#include <string_view>

namespace xar::game {

template <class Number, class JsonString>
inline void AppendArmySourceDerivedNextDailySupplyFrameInputsV1(
    std::string &output, const ArmySourceDerivedNextDailySupplyFrameInputsV1 &input,
    Number number, JsonString append_json_string) {
  output += "{\"schema_version\":1,\"source\":\"native_source_derived_next_daily_supply_frame_inputs_12004\"";
  output += ",\"stage\":\"source_derived_conditional_next_date_pair\",\"status\":";
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
  numeric("current_native_day_index_raw_i32", input.current_native_day_index_raw_i32);
  numeric("source_derived_next_date_raw_i32", input.source_derived_next_date_raw_i32);
  numeric("source_derived_next_native_day_index_raw_i32", input.source_derived_next_native_day_index_raw_i32);
  numeric("source_derived_next_date_storage_raw64", input.source_derived_next_date_storage_raw64);
  numeric("source_derived_next_calendar_day_u8", input.source_derived_next_calendar_day_u8);
  numeric("source_derived_next_calendar_month_u8", input.source_derived_next_calendar_month_u8);
  output += ",\"source_derived_full_cdate64_ready\":";
  output += input.source_derived_full_cdate64_ready ? "true" : "false";
  output += ",\"actual_future_date_stage_observed\":false,\"actual_future_callback_observed\":false";
  output += ",\"future_bucket_mutations_reconstructed\":false,\"future_stock_or_strength_ready\":false";
  output += ",\"full_daily_supply_transition_ready\":false,\"full_monthly_ready\":false}";
}

} // namespace xar::game
