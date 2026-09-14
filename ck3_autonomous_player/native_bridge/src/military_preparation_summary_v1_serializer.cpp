#include "xar_bridge/military_preparation_summary_v1_serializer.hpp"

#include <string>

namespace xar::bridge {
namespace {

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

std::string_view StatusName(MilitaryPreparationSummaryStatusV1 status) {
  switch (status) {
  case MilitaryPreparationSummaryStatusV1::disabled:
    return "disabled";
  case MilitaryPreparationSummaryStatusV1::available:
    return "available";
  case MilitaryPreparationSummaryStatusV1::unavailable:
  default:
    return "unavailable";
  }
}

} // namespace

std::string SerializeMilitaryPreparationSummaryV1(
    const MilitaryPreparationSummaryResultV1 &result) {
  std::string output;
  output.reserve(1024);
  output += "{\"schema\":\"xar.ck3.private.military_preparation_summary_v1\",";
  output += "\"schema_version\":1,\"private_key\":\"";
  output += kMilitaryPreparationSummaryPrivateKeyV1;
  output += "\",\"status\":\"";
  output += StatusName(result.status);
  output += "\",\"failure_flags\":" + std::to_string(result.failure_flags);
  output += ",\"exact_build\":{\"game_version\":\"1.19.0.6\",";
  output += "\"executable_sha256\":\"";
  output += kMilitaryPreparationSummaryExecutableSha256V1;
  output += "\"},\"source\":{";
  output += "\"snapshot_revision\":" +
            std::to_string(result.frame.snapshot_revision);
  output += ",\"date_raw\":" + std::to_string(result.frame.date_raw);
  output += ",\"paused\":";
  AppendBool(output, result.frame.paused);
  output += ",\"played_character_id\":" +
            std::to_string(result.frame.played_character_id);
  output += ",\"gameplay_rng_fingerprint\":" +
            std::to_string(result.frame.gameplay_rng_fingerprint);
  output += "},\"stock_final_values\":{";
  output += "\"current_military_strength_raw\":" +
            std::to_string(result.values.current_military_strength_raw);
  output += ",\"max_military_strength_raw\":" +
            std::to_string(result.values.max_military_strength_raw);
  output += ",\"number_of_knights_raw\":" +
            std::to_string(result.values.number_of_knights_raw);
  output += ",\"max_number_of_knights_raw\":" +
            std::to_string(result.values.max_number_of_knights_raw);
  output += ",\"scale\":" +
            std::to_string(kMilitaryPreparationSummaryFixedPointScaleV1);
  output += "},\"maa_gold_band\":{";
  output += "\"expense_relative_raw\":" +
            std::to_string(result.values.maa_gold_expense_relative_raw);
  output += ",\"min_raw\":" +
            std::to_string(result.values.maa_gold_min_raw);
  output += ",\"ideal_raw\":" +
            std::to_string(result.values.maa_gold_ideal_raw);
  output += ",\"max_raw\":" +
            std::to_string(result.values.maa_gold_max_raw);
  output += ",\"chance_below_min_raw\":" +
            std::to_string(result.values.maa_gold_chance_below_min_raw);
  output += ",\"chance_below_ideal_raw\":" +
            std::to_string(result.values.maa_gold_chance_below_ideal_raw);
  output += ",\"scale\":" +
            std::to_string(kMilitaryPreparationSummaryFixedPointScaleV1);
  output += "},\"observation_ready\":";
  AppendBool(output, result.observation_ready);
  output += ",\"offline_fixture\":";
  AppendBool(output, result.offline_fixture);
  output += ",\"raw_pointer_fields_persisted\":false}";
  return output;
}

} // namespace xar::bridge
