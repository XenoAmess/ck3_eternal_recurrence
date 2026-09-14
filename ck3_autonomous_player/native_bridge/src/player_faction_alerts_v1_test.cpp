#include "xar_bridge/player_faction_alerts_v1.hpp"

#include <cstdint>
#include <iostream>
#include <string>

namespace {

using namespace xar;

struct Fixture {
  game::PlayerFactionAlertsFrameV1 frame{};
  ck3_11906::PlayerFactionAlertsSourceSampleV1 first{};
  ck3_11906::PlayerFactionAlertsSourceSampleV1 second{};
  std::int32_t count = 0;
  std::uint32_t frame_calls = 0;
  std::uint32_t source_calls = 0;
  std::uint32_t count_calls = 0;
  bool main_thread = true;
};

bool Capture(void *opaque, game::PlayerFactionAlertsFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.frame_calls;
  output = fixture.frame;
  return true;
}

bool IsMain(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool ReadSource(
    void *opaque,
    ck3_11906::PlayerFactionAlertsSourceSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = fixture.source_calls++ == 0 ? fixture.first : fixture.second;
  return true;
}

bool ReadCount(void *opaque, std::int32_t expected_player,
               std::int32_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.count_calls;
  if (expected_player != fixture.frame.played_character_id) return false;
  output = fixture.count;
  return true;
}

game::PlayerFactionFixedPointV1 Fixed(std::int64_t raw) {
  return {raw, 100'000};
}

ck3_11906::PlayerTargetingFactionSourceRowV1 Row(
    std::int32_t id, std::string type, bool leader_human,
    std::optional<std::int32_t> months, std::int64_t monthly,
    bool at_war = false) {
  ck3_11906::PlayerTargetingFactionSourceRowV1 source{};
  source.row.faction_id = id;
  source.row.faction_type_key = std::move(type);
  source.row.target_character_id = 32904;
  source.row.leader_character_id = id + 10'000;
  source.row.leader_is_human = leader_human;
  source.row.faction_at_war = at_war;
  if (at_war) source.row.faction_war_id = id + 20'000;
  source.row.power = Fixed(9'100'000);
  source.row.power_threshold = Fixed(8'000'000);
  source.row.discontent = Fixed(6'400'000);
  source.row.discontent_per_month = Fixed(monthly);
  source.row.months_until_max_discontent = months;
  source.row.character_member_ids = {id + 10'000, id + 10'001};
  source.faction_identity_round_trip = true;
  source.target_identity_round_trip = true;
  source.leader_identity_round_trip = true;
  source.war_identity_round_trip = at_war;
  source.member_identities_round_trip = true;
  // These are deliberately wrong; the reader must derive both fields.
  source.row.dangerous_by_stock_rule = false;
  source.row.danger_reason = "fixture_must_not_cross_reader";
  return source;
}

Fixture Base() {
  Fixture fixture{};
  fixture.frame.snapshot_revision = 412;
  fixture.frame.date_raw = 53'789'952;
  fixture.frame.paused = true;
  fixture.frame.map_ready = true;
  fixture.frame.has_played_character = true;
  fixture.frame.played_character_alive = true;
  fixture.frame.played_character_id = 32904;
  fixture.first.player_character_id = 32904;
  fixture.first.player_identity_round_trip = true;
  fixture.second = fixture.first;
  return fixture;
}

ck3_11906::PlayerFactionAlertsAccessV1 Access(Fixture &fixture,
                                               bool offline) {
  ck3_11906::PlayerFactionAlertsAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.read_targeting_faction_count = offline ? nullptr : &ReadCount;
  access.read_offline_fixture_source = offline ? &ReadSource : nullptr;
  return access;
}

bool TestProductionCountOnly(std::int32_t count) {
  auto fixture = Base();
  fixture.count = count;
  auto environment =
      ck3_11906::BindPlayerFactionAlertsNativeEnvironmentV1(0x10000000, true);
  game::PlayerFactionAlertsV1 result{};
  const auto status = ck3_11906::ReadPlayerFactionAlertsV1(
      environment, Access(fixture, false), {412}, result);
  const bool empty = count == 0;
  return status == game::ReadPlayerFactionAlertsResultV1::available &&
         result.status == game::PlayerFactionAlertsStatusV1::available &&
         result.player_character_id == 32904 &&
         result.targeting_faction_count == count &&
         result.readiness.identity_ready &&
         result.readiness.targeting_count_ready &&
         result.readiness.same_frame_ready &&
         result.readiness.targeting_rows_ready == empty &&
         result.readiness.stock_dangerous_predicate_ready == empty &&
         !result.readiness.county_exposure_ready &&
         !result.readiness.alert_ready &&
         result.component_unavailable_reasons.targeting_rows.has_value() !=
             empty &&
         result.component_unavailable_reasons.county_exposure ==
             ck3_11906::kPlayerFactionAlertsV1CountyExposureUnavailableReason &&
         result.planner_projection.status ==
             game::PlayerFactionPlannerProjectionStatusV1::unavailable &&
         !result.planner_projection.present.has_value() &&
         fixture.count_calls == 2 && fixture.frame_calls == 2 &&
         !ck3_11906::SerializePlayerFactionAlertsV1(result).empty();
}

bool TestFullFixture() {
  auto fixture = Base();
  fixture.first.targeting_factions = {
      Row(101, "independence_faction", true, std::nullopt, -100'000),
      Row(102, "peasant_faction", false, 12, -100'000),
      Row(103, "peasant_faction", false, 13, 900'000),
      Row(104, "modded_faction", false, std::nullopt, 100'000),
      Row(105, "liberty_faction", false, std::nullopt, 100'000, true),
  };
  fixture.first.targeting_faction_count = 5;
  ck3_11906::PlayerFactionCountyExposureSourceRowV1 exposure{};
  exposure.row.county_title_id = 441;
  exposure.row.faction_id = 880;
  exposure.row.faction_type_key = "populist_faction";
  exposure.row.target_character_id = 32000;
  exposure.row.power = Fixed(8'500'000);
  exposure.row.power_threshold = Fixed(8'000'000);
  exposure.county_identity_round_trip = true;
  exposure.faction_identity_round_trip = true;
  exposure.target_identity_round_trip = true;
  fixture.first.county_exposures = {exposure};
  fixture.second = fixture.first;

  auto environment =
      ck3_11906::BindPlayerFactionAlertsNativeEnvironmentV1(0, true);
  environment.offline_fixture_source = true;
  game::PlayerFactionAlertsV1 result{};
  const auto status = ck3_11906::ReadPlayerFactionAlertsV1(
      environment, Access(fixture, true), {412}, result);
  if (status != game::ReadPlayerFactionAlertsResultV1::available ||
      !result.readiness.alert_ready ||
      result.planner_projection.status !=
          game::PlayerFactionPlannerProjectionStatusV1::available ||
      result.targeting_factions.size() != 5 ||
      result.county_exposures.size() != 1 ||
      result.targeting_factions[0].danger_reason != "human_faction_leader" ||
      result.targeting_factions[1].danger_reason !=
          "peasant_ultimatum_within_12_months" ||
      result.targeting_factions[2].danger_reason !=
          "peasant_ultimatum_not_within_12_months" ||
      result.targeting_factions[2].dangerous_by_stock_rule ||
      result.targeting_factions[3].danger_reason !=
          "non_peasant_discontent_increasing" ||
      !result.targeting_factions[4].dangerous_by_stock_rule ||
      result.planner_projection.dangerous_faction_ids !=
          std::vector<std::int32_t>({101, 102, 104}) ||
      result.planner_projection.watch_faction_ids !=
          std::vector<std::int32_t>({103}) ||
      result.planner_projection.war_handoff_faction_ids !=
          std::vector<std::int32_t>({105}) ||
      result.planner_projection.exposed_county_title_ids !=
          std::vector<std::int32_t>({441}) ||
      result.readiness.exact_ultimatum_timing_ready ||
      result.planner_projection.exact_ultimatum_timing_ready) {
    return false;
  }
  const auto json = ck3_11906::SerializePlayerFactionAlertsV1(result);
  return json.find("\"player_character_id\":32904") != std::string::npos &&
         json.find("\"faction_type_key\":\"modded_faction\"") !=
             std::string::npos &&
         json.find("\"exact_ultimatum_timing_ready\":false") !=
             std::string::npos;
}

bool TestRejectsTamperedFixture() {
  auto fixture = Base();
  fixture.first.targeting_factions = {
      Row(101, "independence_faction", false, std::nullopt, 100'000)};
  fixture.first.targeting_faction_count = 1;
  fixture.first.targeting_factions[0].row.target_character_id = 999;
  fixture.second = fixture.first;
  auto environment =
      ck3_11906::BindPlayerFactionAlertsNativeEnvironmentV1(0, true);
  environment.offline_fixture_source = true;
  game::PlayerFactionAlertsV1 result{};
  return ck3_11906::ReadPlayerFactionAlertsV1(
             environment, Access(fixture, true), {412}, result) ==
             game::ReadPlayerFactionAlertsResultV1::unavailable &&
         result.unavailable_reason ==
             game::PlayerFactionAlertsFailureReasonV1::identity_round_trip_failed &&
         result.component_unavailable_reasons.targeting_rows == std::nullopt;
}

} // namespace

int main() {
  if (!TestProductionCountOnly(0) || !TestProductionCountOnly(2)) {
    std::cerr << "player-faction-alerts production count fixture failed\n";
    return 1;
  }
  if (!TestFullFixture()) {
    std::cerr << "player-faction-alerts full planner fixture failed\n";
    return 1;
  }
  if (!TestRejectsTamperedFixture()) {
    std::cerr << "player-faction-alerts tamper rejection fixture failed\n";
    return 1;
  }
  std::cout << "player-faction-alerts-v1 reader fixture passed\n";
  return 0;
}
