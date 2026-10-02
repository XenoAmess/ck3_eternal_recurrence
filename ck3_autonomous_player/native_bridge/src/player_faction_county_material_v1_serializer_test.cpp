#include "xar_bridge/player_faction_alerts_v1.hpp"

#include <iostream>
#include <string>

namespace {

xar::game::PlayerFactionAlertsV1 MaterialFrame() {
  using namespace xar::game;
  PlayerFactionAlertsV1 value{};
  value.status = PlayerFactionAlertsStatusV1::available;
  value.snapshot_revision = 41;
  value.date_raw = 53'220'000;
  value.player_character_id = 29829;
  value.targeting_faction_count = 1;
  value.readiness = {true, true, true, true, true, true, true, false};
  value.planner_projection.status = PlayerFactionPlannerProjectionStatusV1::available;
  value.planner_projection.present = true;
  value.planner_projection.dangerous = true;
  value.planner_projection.dangerous_faction_ids = {188};
  PlayerTargetingFactionV1 row{};
  row.faction_id = 188;
  row.faction_type_key = "populist_faction";
  row.target_character_id = 29829;
  row.power = {9'912'500, 100'000};
  row.power_threshold = {8'000'000, 100'000};
  row.discontent = {2'500'000, 100'000};
  row.discontent_per_month = {500'000, 100'000};
  row.county_member_title_ids = {2111, 2115};
  row.dangerous_by_stock_rule = true;
  row.danger_reason = "non_peasant_discontent_increasing";
  PlayerFactionCountyMemberObservationV1 negative{};
  negative.county_title_id = 2111;
  negative.capital_province_id = 100;
  negative.holder_character_id = 29829;
  negative.county_opinion = -37;
  negative.native_county_join_score_raw = -4'294'967'297;
  negative.can_add_county = false;
  negative.removal_queued = false;
  negative.native_leave_score_threshold = -10;
  negative.opinion_status = "available";
  negative.native_final_status = "available";
  PlayerFactionCountyMemberObservationV1 zero{};
  zero.county_title_id = 2115;
  zero.county_opinion = 0;
  zero.native_county_join_score_raw = 0;
  zero.can_add_county = true;
  zero.removal_queued = false;
  zero.native_leave_score_threshold = 0;
  zero.opinion_status = "available";
  zero.native_final_status = "available";
  row.county_member_observations = {negative, zero};
  value.targeting_factions.push_back(row);
  return value;
}

bool Emit(const xar::game::PlayerFactionAlertsV1 &value) {
  const auto wire = xar::ck3_11906::SerializePlayerFactionAlertsWithProvenanceV1(
      value, "1.20.0.3",
      "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
      "ck3-1.20.0.3-native-player-faction-alerts-v1");
  if (wire.empty()) return false;
  std::cout << wire << '\n';
  return true;
}

} // namespace

int main() {
  auto full = MaterialFrame();
  if (!Emit(full)) return 1;
  auto &partial = full.targeting_factions.front().county_member_observations.front();
  partial.county_opinion.reset();
  partial.opinion_status = "unavailable";
  partial.native_county_join_score_raw.reset();
  partial.removal_queued = true;
  partial.native_final_status = "unavailable";
  if (!Emit(full)) return 1;
  full.targeting_factions.front().county_member_observations.clear();
  if (!Emit(full)) return 1;
  return 0;
}
