#include "xar_bridge/steward_develop_county_candidates_v1.hpp"

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
  if (argc != 10) {
    std::cerr << "expected nine source-contract paths\n";
    return 1;
  }
  const auto header = ReadAll(argv[1]);
  const auto reader = ReadAll(argv[2]);
  const auto serializer = ReadAll(argv[3]);
  const auto mailbox = ReadAll(argv[4]);
  const auto game_adapter = ReadAll(argv[5]);
  const auto adapter = ReadAll(argv[6]);
  const auto bridge = ReadAll(argv[7]);
  const auto abi = ReadAll(argv[8]);
  const auto fixture = ReadAll(argv[9]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      mailbox.empty() || game_adapter.empty() || adapter.empty() ||
      bridge.empty() || abi.empty() || fixture.empty()) {
    std::cerr << "source-contract input is unreadable\n";
    return 1;
  }

  using namespace xar::ck3_11906;
  if (kStewardDevelopCountyCandidatesV1Capability !=
          "game.command.query-steward-develop-county-candidates-v1" ||
      kStewardDevelopCountyCandidatesV1Step !=
          "query-steward-develop-county-candidates-v1" ||
      kStewardDevelopCountyCandidatesV1GameVersion != "1.19.0.6" ||
      kStewardDevelopCountyCandidatesV1ExecutableSha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86" ||
      kStewardDevelopCountyCandidatesV1BackendId !=
          "ck3-1.19.0.6-native-steward-develop-county-candidates-v1" ||
      kStewardDevelopCountyCandidatesV1TargetSelectionMode !=
          "engine_random_unscored") {
    std::cerr << "frozen public constants drifted\n";
    return 1;
  }

  if (!ContainsAll(
          serializer,
          {"\\\"schema_version\\\"", "\\\"contract_stage\\\"",
           "\\\"status\\\"", "\\\"unavailable_reason\\\"",
           "\\\"snapshot_revision\\\"", "\\\"observed_date_raw\\\"",
           "\\\"player_character_id\\\"", "\\\"steward_character_id\\\"",
           "\\\"task_key\\\"", "\\\"shown\\\"", "\\\"valid\\\"",
           "\\\"task_failure_reason\\\"",
           "\\\"steward_increase_development_value_raw\\\"",
           "\\\"current_gold_raw\\\"",
           "\\\"no_ai_increase_development\\\"",
           "\\\"has_active_improve_development_directive\\\"",
           "\\\"target_selection_mode\\\"", "\\\"candidates\\\"",
           "\\\"same_frame_stable\\\"", "\\\"readiness\\\"",
           "\\\"provenance\\\"", "\\\"county_title_id\\\"",
           "\\\"capital_province_id\\\"", "\\\"holder_character_id\\\"",
           "\\\"is_player_capital\\\"",
           "\\\"directly_held_by_player\\\"", "\\\"native_legal\\\"",
           "\\\"development_level_raw\\\"",
           "\\\"development_progress_raw\\\"",
           "\\\"monthly_development_rate_raw\\\"",
           "\\\"max_development_level_raw\\\"", "\\\"terrain_key\\\"",
           "\\\"same_culture_as_player\\\"",
           "\\\"cultural_acceptance_threshold_passed\\\""}) ||
      !ContainsAll(
          header,
          {"exact_build_contract_fixture_pending_live_reader",
           "contract_fixture_pending_live_reader",
           "task_develop_county_native_candidate_enumerator_and_final_legality_call"})) {
    return 1;
  }

  if (!ContainsAll(serializer,
                   {"reader_not_implemented", "unsupported_build",
                    "requires_application_main", "requires_paused",
                    "state_changed"}) ||
      !ContainsAll(reader,
                   {"native_reader_not_frozen", "exact_build_not_admitted",
                    "paused_player_unavailable", "same_frame_drift",
                    "offline_fixture_source",
                    "ReadStewardDevelopCountyCandidatesV1"}) ||
      !ContainsAll(mailbox,
                   {"ParseStewardDevelopCountyCandidatesExpectedRevisionV1",
                    "ExecuteStewardDevelopCountyCandidatesMailboxQueryV1",
                    "MainThreadQueryMailboxStateV1::executing"}) ||
      !ContainsAll(game_adapter,
                   {"ParseStewardDevelopCountyCandidatesV1Step",
                    "kStewardDevelopCountyCandidatesV1Capability"}) ||
      !Contains(adapter, "kStewardDevelopCountyCandidatesV1Capability") ||
      !ContainsAll(bridge,
                   {"StewardDevelopCountyCandidatesResultFrame",
                    "steward_develop_county_candidates",
                    "native-headless"}) ||
      !ContainsAll(abi,
                   {"\"production_reader_enabled\": false",
                    "\"admitted_rvas\": []",
                    "task_develop_county_native_candidate_enumerator_and_final_legality_call"}) ||
      !ContainsAll(fixture,
                   {"\"production_reader\": \"strict_unavailable_by_default\"",
                    "\"available_status_scope\": \"offline_fixture_only\"",
                    "\"available_requires_two_stable_samples\": true",
                    "\"mutator_surface\": false"})) {
    return 1;
  }

  if (Contains(reader, "WriteProcessMemory") ||
      Contains(reader, "SubmitPause") || Contains(reader, "SubmitMove") ||
      Contains(reader, "SubmitDeclare")) {
    std::cerr << "reader contains a mutator surface\n";
    return 1;
  }

  std::cout << "steward-develop-county-candidates-v1 source contract passed\n";
  return 0;
}
