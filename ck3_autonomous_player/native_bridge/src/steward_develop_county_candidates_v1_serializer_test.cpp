#include "xar_bridge/steward_develop_county_candidates_v1.hpp"
#include "xar_bridge/ck3_12003_steward_develop_county.hpp"

#include <array>
#include <iostream>
#include <limits>
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

// These values test only the serializer contract. The independent provider
// fixture exercises native callbacks and emits actual production JSON.
xar::game::StewardDevelopCountyCandidatesV1 MaterialValue() {
  xar::game::StewardDevelopCountyCandidatesV1 value{};
  value.status = xar::game::StewardDevelopCountyCandidatesStatusV1::available;
  value.snapshot_revision = 77;
  value.observed_date_raw = 53328600;
  value.player_character_id = 31853;
  value.steward_character_id = 39761;
  value.shown = true;
  value.valid = true;
  value.same_frame_stable = true;
  value.readiness.ready = true;
  value.material.emplace();
  value.material->candidate_collection_complete = true;
  xar::game::CampaignRootCouncilPositionV1 binding{};
  binding.position_key = "councillor_steward";
  binding.incumbent_character_id = 39761;
  binding.task_key = "task_collect_taxes";
  binding.task_type = xar::game::CampaignRootCouncilTaskTypeV1::general;
  binding.frozen = false;
  binding.progress.emplace();
  value.material->current_active_task_binding = binding;
  xar::game::StewardDevelopCountyMaterialCandidateV1 first{};
  first.county_title_id = 0x03000011;
  first.capital_province_id = 77;
  first.holder_character_id = 31853;
  first.is_player_capital = true;
  first.directly_held_by_player = true;
  first.native_collection_ordinal = 4;
  first.native_target_valid = true;
  first.monthly_development_rate = {-75'000, 100'000};
  first.development_progress_current = {-4'000'000, 100'000};
  first.development_progress_maximum = {10'000'000, 100'000};
  value.material->candidates.push_back(first);
  auto second = first;
  second.county_title_id = 0x03000012;
  second.capital_province_id = 88;
  second.holder_character_id = 45678;
  second.is_player_capital = false;
  second.directly_held_by_player = false;
  second.native_collection_ordinal = 9;
  second.native_target_valid = false;
  second.monthly_development_rate = {0, 100'000};
  second.development_progress_current = {0, 100'000};
  value.material->candidates.push_back(second);
  return value;
}

std::size_t MemberCount(std::string_view json) {
  std::size_t members = 0;
  std::size_t depth = 0;
  bool quoted = false;
  bool escaped = false;
  for (const char character : json) {
    if (quoted) {
      if (escaped) escaped = false;
      else if (character == '\\') escaped = true;
      else if (character == '"') quoted = false;
      continue;
    }
    if (character == '"') quoted = true;
    else if (character == '{' || character == '[') ++depth;
    else if (character == '}' || character == ']') {
      if (depth == 0) return 0;
      if (--depth == 0) return members;
    } else if (character == ':' && depth == 1) ++members;
  }
  return 0;
}

bool TestMaterialAvailableAndSignedValues() {
  const auto value = MaterialValue();
  const auto json =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
  const auto direct =
      xar::ck3_12003::SerializeStewardDevelopCountyMaterial12003(value);
  const auto binding = json.find("{\"position_key\"");
  const auto candidate = json.find("{\"county_title_id\"");
  return !json.empty() && json == direct && MemberCount(json) == 19 &&
         binding != std::string::npos &&
         MemberCount(std::string_view(json).substr(binding)) == 7 &&
         candidate != std::string::npos &&
         MemberCount(std::string_view(json).substr(candidate)) == 9 &&
         Contains(json, "\"contract_stage\":\"native_player_realm_develop_county_material_v1\"") &&
         Contains(json, "\"status\":\"available\",\"unavailable_reason\":null") &&
         Contains(json, "\"observed_date_raw\":53328600") &&
         Contains(json, "\"player_character_id\":31853,\"steward_character_id\":39761") &&
         Contains(json, "\"task_key\":\"task_collect_taxes\",\"task_type\":\"general\",\"target\":null") &&
         Contains(json, "\"progress\":{\"kind\":\"infinite\",\"current\":null,\"maximum\":null}") &&
         Contains(json, "\"candidate_collection_scope\":\"player_realm\",\"candidate_collection_complete\":true") &&
         Contains(json, "\"native_collection_ordinal\":4,\"native_target_valid\":true") &&
         Contains(json, "\"native_collection_ordinal\":9,\"native_target_valid\":false") &&
         Contains(json, "\"monthly_development_rate\":{\"raw\":-75000,\"scale\":100000}") &&
         Contains(json, "\"monthly_development_rate\":{\"raw\":0,\"scale\":100000}") &&
         Contains(json, "\"development_progress\":{\"current\":{\"raw\":-4000000,\"scale\":100000},\"maximum\":{\"raw\":10000000,\"scale\":100000}}") &&
         Contains(json, "\"same_frame_stable\":true,\"readiness\":true") &&
         Contains(json, "\"game_version\":\"1.20.0.3\"") &&
         Contains(json, "\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\"") &&
         Contains(json, "\"backend_id\":\"ck3-1.20.0.3-native-steward-develop-county-material-v1\"") &&
         Contains(json, "\"reader_mode\":\"native_player_realm_enumerator_predicates_and_current_growth\"") &&
         Contains(json, "\"next_reverse_engineering_entry\":\"native_develop_county_ai_inputs_and_proposed_task_growth\"") &&
         !Contains(json, "native_can_assign") &&
         !Contains(json, "target_selection_mode") &&
         !Contains(json, "steward_increase_development_value_raw") &&
         !Contains(json, "current_gold_raw") &&
         !Contains(json, "no_ai_increase_development") &&
         !Contains(json, "terrain_key");
}

bool TestMaterialTaskBlockedAndEmpty() {
  auto value = MaterialValue();
  value.material->candidates.clear();
  const auto empty =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
  if (!Contains(empty, "\"candidates\":[]") ||
      !Contains(empty, "\"readiness\":true")) return false;
  value.shown = false;
  value.valid = false;
  value.task_failure_reason = "task_not_shown";
  const auto hidden =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
  if (!Contains(hidden, "\"status\":\"available\"") ||
      !Contains(hidden, "\"shown\":false,\"valid\":false") ||
      !Contains(hidden, "\"task_failure_reason\":\"task_not_shown\"") ||
      !Contains(hidden, "\"candidate_collection_complete\":true") ||
      !Contains(hidden, "\"candidates\":[]") ||
      !Contains(hidden, "\"readiness\":true")) return false;
  value.shown = true;
  value.task_failure_reason = "task_invalid";
  const auto invalid =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
  return Contains(invalid, "\"status\":\"available\"") &&
         Contains(invalid, "\"shown\":true,\"valid\":false") &&
         Contains(invalid, "\"task_failure_reason\":\"task_invalid\"") &&
         Contains(invalid, "\"candidates\":[]") &&
         Contains(invalid, "\"readiness\":true");
}

bool TestMaterialUnavailableAndPartial() {
  xar::game::StewardDevelopCountyCandidatesV1 unavailable{};
  unavailable.snapshot_revision = 81;
  unavailable.observed_date_raw = 53328600;
  unavailable.unavailable_reason =
      xar::game::StewardDevelopCountyFailureReasonV1::same_frame_drift;
  unavailable.material.emplace();
  const auto json =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(unavailable);
  if (MemberCount(json) != 19 ||
      !Contains(json, "\"status\":\"unavailable\",\"unavailable_reason\":\"state_changed\"") ||
      !Contains(json, "\"current_active_task_binding\":null") ||
      !Contains(json, "\"candidate_collection_complete\":false") ||
      !Contains(json, "\"candidates\":[]") ||
      !Contains(json, "\"readiness\":false") ||
      !Contains(json, "\"game_version\":\"1.20.0.3\"")) return false;
  unavailable.material->candidate_collection_complete = true;
  if (!xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(unavailable).empty())
    return false;
  auto value = MaterialValue();
  value.material->candidate_collection_complete = false;
  if (!xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value).empty())
    return false;
  value = MaterialValue();
  value.material->current_active_task_binding.reset();
  if (!xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value).empty())
    return false;
  value = MaterialValue();
  value.material->candidates.front().monthly_development_rate.scale = 1;
  if (!xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value).empty())
    return false;
  value = MaterialValue();
  value.shown = false;
  value.task_failure_reason = "task_not_shown";
  return xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value).empty();
}

bool TestMaterialBindingAndInt64Precision() {
  auto value = MaterialValue();
  auto &binding = *value.material->current_active_task_binding;
  binding.task_key = "task_develop_county";
  binding.task_type = xar::game::CampaignRootCouncilTaskTypeV1::county;
  binding.target.emplace();
  binding.target->province_id = 77;
  binding.progress->kind = xar::game::CampaignRootCouncilProgressKindV1::value;
  binding.progress->current = xar::game::FixedPointValue{0, 100'000};
  binding.progress->maximum = xar::game::FixedPointValue{10'000'000, 100'000};
  value.material->candidates.front().monthly_development_rate.raw =
      std::numeric_limits<std::int64_t>::min();
  value.material->candidates.back().monthly_development_rate.raw =
      std::numeric_limits<std::int64_t>::max();
  const auto json =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
  return Contains(json, "\"task_type\":\"county\",\"target\":{\"kind\":\"province\",\"province_id\":77}") &&
         Contains(json, "\"progress\":{\"kind\":\"value\",\"current\":{\"raw\":0,\"scale\":100000},\"maximum\":{\"raw\":10000000,\"scale\":100000}}") &&
         Contains(json, "\"monthly_development_rate\":{\"raw\":-9223372036854775808,\"scale\":100000}") &&
         Contains(json, "\"monthly_development_rate\":{\"raw\":9223372036854775807,\"scale\":100000}");
}

bool TestQueryResultEnvelope() {
  const auto value = MaterialValue();
  const auto payload =
      xar::ck3_11906::SerializeStewardDevelopCountyCandidatesV1(value);
  const auto frame = xar::ck3_11906::SerializeStewardDevelopCountyQueryResultV1(
      "quoted\"\\\n", 91, value);
  const auto result = frame.find("\"result\":{");
  if (MemberCount(frame) != 5 || result == std::string::npos ||
      MemberCount(std::string_view(frame).substr(result + 9)) != 7 ||
      !Contains(frame, "\"request_id\":\"quoted\\\"\\\\\\u000A\"") ||
      !Contains(frame, "\"ok\":true,\"result\":{\"step\":\"query-steward-develop-county-candidates-v1\",\"accepted\":true,\"status\":\"available\"") ||
      !Contains(frame, "\"query_sequence\":91,\"snapshot_revision\":77") ||
      !Contains(frame, "\"steward_develop_county_candidates\":" + payload) ||
      !Contains(frame, "\"backend_id\":\"native-headless\"")) return false;
  xar::game::StewardDevelopCountyCandidatesV1 unavailable{};
  unavailable.snapshot_revision = 81;
  unavailable.unavailable_reason =
      xar::game::StewardDevelopCountyFailureReasonV1::same_frame_drift;
  unavailable.material.emplace();
  const auto unavailable_frame =
      xar::ck3_11906::SerializeStewardDevelopCountyQueryResultV1(
          "unavailable", 92, unavailable);
  if (!Contains(unavailable_frame, "\"accepted\":true,\"status\":\"unavailable\""))
    return false;
  auto partial = value;
  partial.material->candidate_collection_complete = false;
  return xar::ck3_11906::SerializeStewardDevelopCountyQueryResultV1(
             "partial", 93, partial).empty();
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
  if (!TestMaterialAvailableAndSignedValues()) {
    std::cerr << "current material serialization fixture failed\n";
    return 1;
  }
  if (!TestMaterialTaskBlockedAndEmpty()) {
    std::cerr << "observed blocked task material fixture failed\n";
    return 1;
  }
  if (!TestMaterialUnavailableAndPartial()) {
    std::cerr << "unavailable or partial material fixture failed\n";
    return 1;
  }
  if (!TestMaterialBindingAndInt64Precision()) {
    std::cerr << "current binding and signed precision fixture failed\n";
    return 1;
  }
  if (!TestQueryResultEnvelope()) {
    std::cerr << "query result envelope fixture failed\n";
    return 1;
  }
  std::cout << "steward-develop-county-candidates-v1 serializer passed\n";
  return 0;
}
