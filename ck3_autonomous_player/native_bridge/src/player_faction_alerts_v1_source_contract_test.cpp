#include "xar_bridge/player_faction_alerts_v1.hpp"

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

bool ContainsAll(std::string_view value,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (!Contains(value, token)) {
      std::cerr << "missing source-contract token: " << token << '\n';
      return false;
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 12) {
    std::cerr << "expected eleven source-contract paths\n";
    return 1;
  }
  const auto header = ReadAll(argv[1]);
  const auto reader = ReadAll(argv[2]);
  const auto serializer = ReadAll(argv[3]);
  const auto mailbox = ReadAll(argv[4]);
  const auto campaign_header = ReadAll(argv[5]);
  const auto campaign_reader = ReadAll(argv[6]);
  const auto game_adapter = ReadAll(argv[7]);
  const auto adapter = ReadAll(argv[8]);
  const auto bridge = ReadAll(argv[9]);
  const auto abi = ReadAll(argv[10]);
  const auto fixture = ReadAll(argv[11]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      mailbox.empty() || campaign_header.empty() || campaign_reader.empty() ||
      game_adapter.empty() || adapter.empty() || bridge.empty() || abi.empty() ||
      fixture.empty()) {
    std::cerr << "source-contract input is unreadable\n";
    return 1;
  }

  using namespace xar::ck3_11906;
  if (kPlayerFactionAlertsV1Capability !=
          "game.command.query-player-faction-alerts-v1" ||
      kPlayerFactionAlertsV1Step != "query-player-faction-alerts-v1" ||
      kPlayerFactionAlertsV1GameVersion != "1.19.0.6" ||
      kPlayerFactionAlertsV1ExecutableSha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86" ||
      kPlayerFactionAlertsV1NextReverseEngineeringEntry !=
          "faction_alert_targeting_span_and_sub_realm_county_membership_readers") {
    std::cerr << "frozen constants drifted\n";
    return 1;
  }

  if (!ContainsAll(
          serializer,
          {"\\\"schema_version\\\"", "\\\"status\\\"",
           "\\\"snapshot_revision\\\"", "\\\"date_raw\\\"",
           "\\\"player_character_id\\\"",
           "\\\"targeting_faction_count\\\"",
           "\\\"targeting_factions\\\"", "\\\"county_exposures\\\"",
           "\\\"planner_projection\\\"", "\\\"readiness\\\"",
           "\\\"targeting_count_ready\\\"", "\\\"alert_ready\\\"",
           "\\\"component_unavailable_reasons\\\"",
           "\\\"unavailable_reason\\\"", "\\\"provenance\\\"",
           "\\\"faction_type_key\\\"", "\\\"faction_at_war\\\"",
           "\\\"dangerous_by_stock_rule\\\"", "\\\"danger_reason\\\"",
           "\\\"exact_ultimatum_timing_ready\\\""}) ||
      !ContainsAll(reader,
                   {"human_faction_leader",
                    "peasant_ultimatum_within_12_months",
                    "peasant_ultimatum_not_within_12_months",
                    "non_peasant_discontent_increasing",
                    "non_peasant_discontent_not_increasing",
                    "player_county_in_powerful_liege_targeting_populist_faction",
                    "kPlayerFactionAlertsV1TargetingRowsUnavailableReason",
                    "kPlayerFactionAlertsV1CountyExposureUnavailableReason"}) ||
      !ContainsAll(header,
                   {"targeting_rows_native_reader_not_frozen",
                    "county_exposure_native_reader_not_frozen"}) ||
      !ContainsAll(mailbox,
                   {"ExecutePlayerFactionAlertsMailboxQueryV1",
                    "ReadCampaignRootTargetingFactionCountV1",
                    "MainThreadQueryMailboxStateV1::executing"}) ||
      !ContainsAll(campaign_header,
                   {"ReadCampaignRootTargetingFactionCountV1"}) ||
      !ContainsAll(campaign_reader,
                   {"ReadTargetingFactionCount",
                    "ReadCampaignRootTargetingFactionCountV1",
                    "kLandStateTargetingFactionsCountOffset"}) ||
      !ContainsAll(game_adapter,
                   {"ParsePlayerFactionAlertsV1Step",
                    "kPlayerFactionAlertsV1Capability"}) ||
      !Contains(adapter, "kPlayerFactionAlertsV1Capability") ||
      !ContainsAll(bridge,
                   {"PlayerFactionAlertsResultFrame", "player_faction_alerts",
                    "player_faction_alerts_ready", "native-headless"}) ||
      !ContainsAll(abi,
                   {"\"production_reader_enabled\": true",
                    "campaign_root_exact_build_reader_reuse",
                    "faction_alert_targeting_span_and_sub_realm_county_membership_readers"}) ||
      !ContainsAll(fixture,
                   {"\"zero_targeting_count_proves_empty_rows\": true",
                    "\"unknown_faction_type_key_preserved\": true",
                    "\"exact_ultimatum_timing_ready\": false",
                    "\"mutator_surface\": false"})) {
    return 1;
  }

  if (Contains(reader, "WriteProcessMemory") || Contains(reader, "SubmitPause") ||
      Contains(reader, "SubmitMove") || Contains(reader, "SubmitDeclare")) {
    std::cerr << "reader contains a mutator surface\n";
    return 1;
  }
  std::cout << "player-faction-alerts-v1 source contract passed\n";
  return 0;
}
