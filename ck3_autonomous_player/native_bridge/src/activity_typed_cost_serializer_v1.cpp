#include "xar_bridge/activity_typed_cost_serializer_v1.hpp"
#include <array>
#include <limits>

namespace xar::bridge {
namespace {
bool ValidQuote(const ActivityTypedPlannerCostQuoteV1 &quote) noexcept {
  const auto &contract = kOrdinaryPilgrimagePiousContractV1;
  if (!quote.observed || quote.kind != contract.kind ||
      quote.frame.revision == 0 || !quote.frame.application_main_thread ||
      !quote.frame.paused || !quote.frame.map_ready || !quote.frame.actor_alive ||
      quote.frame.actor_character_id <= 0 || quote.planning_stage != 5 ||
      quote.frame.date_raw < (std::numeric_limits<std::int32_t>::min)() ||
      quote.frame.date_raw > (std::numeric_limits<std::int32_t>::max)() ||
      quote.owner == 0 ||
      quote.normal_refresh_sequence == 0 || !quote.final_can_start_observed ||
      quote.failure_display_known ||
      !MatchesActivityTypedPlannerSelectionV1(quote.selection, quote.frame,
          quote.planner, quote.activity_type, 5, contract)) return false;
  std::array<bool,10> named{};
  for (const auto index : quote.known_name_resource_indices) {
    if (index >= named.size() || named[index]) return false;
    named[index] = true;
  }
  return named == quote.named_cost_verified;
}
} // namespace

std::string SerializeActivityTypedPlannerFullCostV1(
    const ActivityTypedFullCostResultV1 &result) {
  if (result.status != ActivityTypedFullCostStatusV1::observed ||
      !ValidQuote(result.quote)) return {};
  const auto &quote = result.quote;
  bool computed_unknown_positive = false;
  for (std::size_t index = 0; index < quote.configured_cost_raw.size(); ++index)
    if (quote.configured_cost_raw[index] > 0 && !quote.named_cost_verified[index])
      computed_unknown_positive = true;
  if (computed_unknown_positive != result.unknown_positive_configured_cost ||
      result.final_failure_display_unknown_reason !=
          "final_canstart_tooltip_getter_unbound") return {};
  std::string text =
      "{\"schema\":\"activity-pilgrimage-configured-full10-cost-v1\","
      "\"activity_key\":\"activity_pilgrimage\","
      "\"special_option_key\":\"pilgrimage_type_pious\","
      "\"observed\":true,\"read_only\":true,\"raw_pointer_fields_persisted\":false,"
      "\"snapshot_revision\":" + std::to_string(quote.frame.revision) +
      ",\"date_raw\":" + std::to_string(quote.frame.date_raw) +
      ",\"actor_character_id\":" + std::to_string(quote.frame.actor_character_id) +
      ",\"application_main_thread\":true,\"paused\":true,\"map_ready\":true,"
      "\"actor_alive\":true,\"planning_stage\":5,\"scale\":100000,"
      "\"normal_refresh_sequence\":" + std::to_string(quote.normal_refresh_sequence) +
      ",\"configuration_fingerprint\":" + std::to_string(quote.configuration_fingerprint) +
      ",\"selected_option\":{\"native_option_id\":" +
      std::to_string(quote.selection.native_option_id) +
      ",\"key\":\"pilgrimage_type_pious\"},\"known_cost_names\":[";
  for (std::size_t name = 0; name < kActivityTypedPlannerKnownCostNamesV1.size(); ++name) {
    if (name != 0) text += ',';
    text += "\"" + std::string(kActivityTypedPlannerKnownCostNamesV1[name]) + "\"";
  }
  text += "],\"known_name_resource_indices\":[";
  for (std::size_t name = 0; name < quote.known_name_resource_indices.size(); ++name) {
    if (name != 0) text += ',';
    text += std::to_string(quote.known_name_resource_indices[name]);
  }
  text += "],\"configured_cost_raw\":[";
  bool unknown_positive = false;
  for (std::size_t index = 0; index < quote.configured_cost_raw.size(); ++index) {
    if (index != 0) text += ',';
    text += std::to_string(quote.configured_cost_raw[index]);
    if (!quote.named_cost_verified[index] && quote.configured_cost_raw[index] > 0)
      unknown_positive = true;
  }
  text += "],\"diagnostic_aggregate_raw\":[";
  for (std::size_t index = 0; index < quote.diagnostic_aggregate_raw.size(); ++index) {
    if (index != 0) text += ',';
    text += std::to_string(quote.diagnostic_aggregate_raw[index]);
  }
  text += "],\"named_cost_verified\":[";
  for (std::size_t index = 0; index < quote.named_cost_verified.size(); ++index) {
    if (index != 0) text += ',';
    text += quote.named_cost_verified[index] ? "true" : "false";
  }
  text += "],\"unknown_positive_configured_cost\":";
  text += unknown_positive ? "true" : "false";
  text += ",\"final_can_start_observed\":true,\"final_can_start\":";
  text += quote.final_can_start ? "true" : "false";
  text += ",\"failure_display_known\":false,\"failure_display\":null,"
          "\"failure_display_unknown_reason\":\"final_canstart_tooltip_getter_unbound\"}";
  return text;
}

} // namespace xar::bridge
