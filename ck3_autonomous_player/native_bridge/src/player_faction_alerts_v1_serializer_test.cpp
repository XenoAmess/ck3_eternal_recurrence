#include "xar_bridge/player_faction_alerts_v1.hpp"

#include <iostream>
#include <string>

namespace {

xar::game::PlayerFactionAlertsV1 CountOnly() {
  using namespace xar;
  game::PlayerFactionAlertsV1 value{};
  value.status = game::PlayerFactionAlertsStatusV1::available;
  value.snapshot_revision = 412;
  value.date_raw = 53'789'952;
  value.player_character_id = 32904;
  value.targeting_faction_count = 2;
  value.readiness = {true, true, false, false, false, true, false, false};
  value.component_unavailable_reasons.targeting_rows =
      ck3_11906::kPlayerFactionAlertsV1TargetingRowsUnavailableReason;
  value.component_unavailable_reasons.county_exposure =
      ck3_11906::kPlayerFactionAlertsV1CountyExposureUnavailableReason;
  return value;
}

bool TestCountOnly() {
  const auto json =
      xar::ck3_11906::SerializePlayerFactionAlertsV1(CountOnly());
  return !json.empty() &&
         json.find("\"status\":\"available\"") != std::string::npos &&
         json.find("\"targeting_faction_count\":2") != std::string::npos &&
         json.find("\"planner_projection\":{\"status\":\"unavailable\","
                   "\"present\":null,\"dangerous\":null") !=
             std::string::npos &&
         json.find("\"targeting_count_ready\":true") != std::string::npos &&
         json.find("\"alert_ready\":false") != std::string::npos &&
         json.find("\"unavailable_reason\":null") != std::string::npos;
}

bool TestUnavailable() {
  xar::game::PlayerFactionAlertsV1 value{};
  value.snapshot_revision = 412;
  value.date_raw = 53'789'952;
  value.unavailable_reason =
      xar::game::PlayerFactionAlertsFailureReasonV1::exact_build_not_admitted;
  const auto json =
      xar::ck3_11906::SerializePlayerFactionAlertsV1(value);
  return !json.empty() &&
         json.find("\"unavailable_reason\":\"unsupported_build\"") !=
             std::string::npos &&
         json.find("\"component_unavailable_reasons\":{"
                   "\"targeting_rows\":null,\"county_exposure\":null}") !=
             std::string::npos;
}

bool TestRejectsTampering() {
  auto partial = CountOnly();
  partial.planner_projection.present = true;
  if (!xar::ck3_11906::SerializePlayerFactionAlertsV1(partial).empty()) {
    return false;
  }

  auto full = CountOnly();
  full.targeting_faction_count = 1;
  full.readiness.targeting_rows_ready = true;
  full.readiness.stock_dangerous_predicate_ready = true;
  full.readiness.county_exposure_ready = true;
  full.readiness.alert_ready = true;
  full.component_unavailable_reasons = {};
  full.planner_projection.status =
      xar::game::PlayerFactionPlannerProjectionStatusV1::available;
  full.planner_projection.present = true;
  full.planner_projection.dangerous = true;
  xar::game::PlayerTargetingFactionV1 row{};
  row.faction_id = 771;
  row.faction_type_key = "peasant_faction";
  row.target_character_id = 32904;
  row.leader_character_id = 33011;
  row.power = {9'100'000, 100'000};
  row.power_threshold = {8'000'000, 100'000};
  row.discontent = {6'400'000, 100'000};
  row.discontent_per_month = {-100'000, 100'000};
  row.months_until_max_discontent = 13;
  row.dangerous_by_stock_rule = false;
  row.danger_reason = "peasant_ultimatum_not_within_12_months";
  full.targeting_factions.push_back(row);
  // The row is valid, but the planner claims danger and omits the watch ID.
  return xar::ck3_11906::SerializePlayerFactionAlertsV1(full).empty();
}

} // namespace

int main() {
  if (!TestCountOnly() || !TestUnavailable() || !TestRejectsTampering()) {
    std::cerr << "player-faction-alerts-v1 serializer fixture failed\n";
    return 1;
  }
  std::cout << "player-faction-alerts-v1 serializer fixture passed\n";
  return 0;
}
