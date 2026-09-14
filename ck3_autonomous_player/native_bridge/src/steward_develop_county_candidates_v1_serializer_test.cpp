#include "xar_bridge/steward_develop_county_candidates_v1.hpp"

#include <array>
#include <iostream>
#include <string>
#include <string_view>
#include <utility>

namespace {

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

bool TestUnavailable() {
  xar::game::StewardDevelopCountyCandidatesV1 value{};
  value.snapshot_revision = 41;
  value.observed_date_raw = 222;
  value.unavailable_reason =
      xar::game::StewardDevelopCountyFailureReasonV1::native_reader_not_frozen;
  const auto json =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
  return Contains(json, "\"status\":\"unavailable\"") &&
         Contains(json, "\"unavailable_reason\":\"reader_not_implemented\"") &&
         Contains(json, "\"snapshot_revision\":41") &&
         Contains(json, "\"observed_date_raw\":222") &&
         Contains(json, "\"player_character_id\":null") &&
         Contains(json, "\"steward_character_id\":null") &&
         Contains(json, "\"shown\":null") &&
         Contains(json, "\"valid\":null") &&
         Contains(json, "\"task_failure_reason\":null") &&
         Contains(json,
                  "\"steward_increase_development_value_raw\":null") &&
         Contains(json, "\"current_gold_raw\":null") &&
         Contains(json, "\"no_ai_increase_development\":null") &&
         Contains(json,
                  "\"has_active_improve_development_directive\":null") &&
         Contains(json, "\"candidates\":[]") &&
         Contains(json, "\"same_frame_stable\":false") &&
         Contains(json, "\"readiness\":false") &&
         Contains(json,
                  "\"reader_mode\":"
                  "\"native_enumerator_observer_pending_live_reader\"") &&
         Contains(
             json,
             "\"next_reverse_engineering_entry\":"
             "\"paused_live_develop_county_enumerator_capture_then_row_identity_and_final_legality\"");
}

bool TestAvailable() {
  xar::game::StewardDevelopCountyCandidatesV1 value{};
  value.status =
      xar::game::StewardDevelopCountyCandidatesStatusV1::available;
  value.snapshot_revision = 42;
  value.observed_date_raw = 333;
  value.player_character_id = 0x02000001;
  value.steward_character_id = 0x02000002;
  value.shown = true;
  value.valid = true;
  value.steward_increase_development_value_raw = 5'000'000;
  value.current_gold_raw = 8'000'000;
  value.no_ai_increase_development = false;
  value.has_active_improve_development_directive = true;
  value.same_frame_stable = true;
  value.readiness.ready = true;
  xar::game::StewardDevelopCountyCandidateV1 candidate{};
  candidate.county_title_id = 0x03000011;
  candidate.capital_province_id = 77;
  candidate.holder_character_id = 0x02000001;
  candidate.is_player_capital = true;
  candidate.directly_held_by_player = true;
  candidate.native_legal = true;
  candidate.development_level_raw = 2'300'000;
  candidate.development_progress_raw = -4'000'000;
  candidate.monthly_development_rate_raw = -75'000;
  candidate.max_development_level_raw = 10'000'000;
  candidate.terrain_key = "plains";
  candidate.same_culture_as_player = true;
  candidate.cultural_acceptance_threshold_passed = true;
  value.candidates.push_back(candidate);

  const auto json =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
  return Contains(json, "\"status\":\"available\"") &&
         Contains(json, "\"unavailable_reason\":null") &&
         Contains(json, "\"player_character_id\":33554433") &&
         Contains(json, "\"steward_character_id\":33554434") &&
         Contains(json, "\"task_key\":\"task_develop_county\"") &&
         Contains(json, "\"shown\":true") &&
         Contains(json, "\"valid\":true") &&
         Contains(json,
                  "\"steward_increase_development_value_raw\":5000000") &&
         Contains(json, "\"current_gold_raw\":8000000") &&
         Contains(json,
                  "\"has_active_improve_development_directive\":true") &&
         Contains(json,
                  "\"target_selection_mode\":\"engine_random_unscored\"") &&
         Contains(json, "\"county_title_id\":50331665") &&
         Contains(json, "\"capital_province_id\":77") &&
         Contains(json, "\"native_legal\":true") &&
         Contains(json, "\"development_level_raw\":2300000") &&
         Contains(json, "\"development_progress_raw\":-4000000") &&
         Contains(json, "\"monthly_development_rate_raw\":-75000") &&
         Contains(json, "\"max_development_level_raw\":10000000") &&
         Contains(json, "\"terrain_key\":\"plains\"") &&
         Contains(json,
                  "\"cultural_acceptance_threshold_passed\":true") &&
         Contains(json, "\"same_frame_stable\":true") &&
         Contains(json, "\"readiness\":true");
}

bool TestUnavailableReasonMapping() {
  using Failure = xar::game::StewardDevelopCountyFailureReasonV1;
  constexpr std::array mappings{
      std::pair{Failure::native_reader_not_frozen, "reader_not_implemented"},
      std::pair{Failure::exact_build_not_admitted, "unsupported_build"},
      std::pair{Failure::application_main_thread_required,
                "requires_application_main"},
      std::pair{Failure::paused_player_unavailable, "requires_paused"},
      std::pair{Failure::same_frame_drift, "state_changed"},
  };
  for (const auto &[reason, expected] : mappings) {
    xar::game::StewardDevelopCountyCandidatesV1 value{};
    value.snapshot_revision = 99;
    value.unavailable_reason = reason;
    const auto json =
        xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
    const std::string token =
        std::string("\"unavailable_reason\":\"") + expected + '"';
    if (!Contains(json, token)) {
      return false;
    }
  }
  return true;
}

bool TestRejectsPartialValues() {
  xar::game::StewardDevelopCountyCandidatesV1 available{};
  available.status =
      xar::game::StewardDevelopCountyCandidatesStatusV1::available;
  available.snapshot_revision = 43;
  available.observed_date_raw = 444;
  available.readiness.ready = true;
  available.same_frame_stable = true;

  xar::game::StewardDevelopCountyCandidatesV1 unavailable{};
  unavailable.snapshot_revision = 44;
  unavailable.player_character_id = 1;
  unavailable.unavailable_reason =
      xar::game::StewardDevelopCountyFailureReasonV1::native_reader_not_frozen;
  return xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(available)
             .empty() &&
         xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(unavailable)
             .empty();
}

} // namespace

int main() {
  if (!TestUnavailable()) {
    std::cerr << "unavailable serialization fixture failed\n";
    return 1;
  }
  if (!TestAvailable()) {
    std::cerr << "available serialization fixture failed\n";
    return 1;
  }
  if (!TestUnavailableReasonMapping()) {
    std::cerr << "unavailable reason mapping fixture failed\n";
    return 1;
  }
  if (!TestRejectsPartialValues()) {
    std::cerr << "partial serialization rejection fixture failed\n";
    return 1;
  }
  std::cout << "steward-develop-county-candidates-v1 serializer passed\n";
  return 0;
}
