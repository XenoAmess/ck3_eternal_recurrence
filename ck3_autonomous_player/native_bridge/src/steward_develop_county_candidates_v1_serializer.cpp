#include "xar_bridge/ck3_12004_steward_develop_county.hpp"
#include "xar_bridge/steward_develop_county_candidates_v1.hpp"
#include "xar_bridge/ck3_12003_steward_develop_county.hpp"

#include <array>
#include <charconv>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

std::string Number(std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  return result.ec == std::errc{}
             ? std::string(buffer.data(), result.ptr)
             : std::string{};
}

std::string SignedNumber(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  return result.ec == std::errc{}
             ? std::string(buffer.data(), result.ptr)
             : std::string{};
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

bool StableKey(std::string_view value) noexcept {
  if (value.empty()) {
    return false;
  }
  for (const char character : value) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

std::string_view WireUnavailableReason(
    game::StewardDevelopCountyFailureReasonV1 reason) noexcept {
  using enum game::StewardDevelopCountyFailureReasonV1;
  switch (reason) {
  case exact_build_not_admitted:
    return "unsupported_build";
  case native_reader_not_frozen:
  case offline_fixture_source_not_authorized:
  case fixture_source_failed:
  case reader_exception:
    return "reader_not_implemented";
  case application_main_thread_required:
    return "requires_application_main";
  case frame_capture_failed:
  case paused_player_unavailable:
    return "requires_paused";
  case invalid_request:
  case snapshot_revision_mismatch:
  case identity_round_trip_failed:
  case identity_drift:
  case same_frame_drift:
  case native_sample_drift:
  case schema_invariant_failed:
  case task_not_shown:
  case task_invalid:
  case candidate_invalid:
    return "state_changed";
  case none:
    break;
  }
  return {};
}

bool ValidAvailable(const game::StewardDevelopCountyCandidatesV1 &value) {
  if (value.snapshot_revision == 0 || !value.observed_date_raw.has_value() ||
      !value.player_character_id.has_value() ||
      value.player_character_id.value() <= 0 ||
      !value.steward_character_id.has_value() ||
      value.steward_character_id.value() <= 0 ||
      value.task_key != kStewardDevelopCountyCandidatesV1TaskKey ||
      value.target_selection_mode !=
          kStewardDevelopCountyCandidatesV1TargetSelectionMode ||
      value.unavailable_reason !=
          game::StewardDevelopCountyFailureReasonV1::none ||
      !value.shown.has_value() || !value.valid.has_value() ||
      !value.steward_increase_development_value_raw.has_value() ||
      !value.current_gold_raw.has_value() ||
      !value.no_ai_increase_development.has_value() ||
      !value.has_active_improve_development_directive.has_value() ||
      !value.same_frame_stable || !value.readiness.ready) {
    return false;
  }
  if ((!value.shown.value() || !value.valid.value()) &&
      (!value.task_failure_reason.has_value() || !value.candidates.empty())) {
    return false;
  }
  if (value.shown.value() && value.valid.value() &&
      value.task_failure_reason.has_value()) {
    return false;
  }
  if (value.task_failure_reason.has_value() &&
      !StableKey(value.task_failure_reason.value())) {
    return false;
  }
  for (const auto &candidate : value.candidates) {
    if (candidate.county_title_id <= 0 || candidate.capital_province_id <= 0 ||
        candidate.holder_character_id <= 0 ||
        !candidate.native_legal || candidate.development_level_raw < 0 ||
        candidate.development_level_raw >
            std::numeric_limits<std::int32_t>::max() ||
        candidate.max_development_level_raw < 0 ||
        candidate.max_development_level_raw >
            std::numeric_limits<std::int32_t>::max() ||
        !StableKey(candidate.terrain_key)) {
      return false;
    }
  }
  return true;
}

bool ValidUnavailable(const game::StewardDevelopCountyCandidatesV1 &value) {
  return value.snapshot_revision > 0 &&
         !WireUnavailableReason(value.unavailable_reason).empty() &&
         !value.player_character_id.has_value() &&
         !value.steward_character_id.has_value() && !value.shown.has_value() &&
         !value.valid.has_value() && !value.task_failure_reason.has_value() &&
         !value.steward_increase_development_value_raw.has_value() &&
         !value.current_gold_raw.has_value() &&
         !value.no_ai_increase_development.has_value() &&
         !value.has_active_improve_development_directive.has_value() &&
         value.candidates.empty() && !value.same_frame_stable &&
         !value.readiness.ready &&
         value.task_key == kStewardDevelopCountyCandidatesV1TaskKey &&
         value.target_selection_mode ==
             kStewardDevelopCountyCandidatesV1TargetSelectionMode;
}

void AppendCandidate(std::string &output,
                     const game::StewardDevelopCountyCandidateV1 &candidate) {
  output += "{\"county_title_id\":";
  output += SignedNumber(candidate.county_title_id);
  output += ",\"capital_province_id\":";
  output += SignedNumber(candidate.capital_province_id);
  output += ",\"holder_character_id\":";
  output += SignedNumber(candidate.holder_character_id);
  output += ",\"is_player_capital\":";
  output += candidate.is_player_capital ? "true" : "false";
  output += ",\"directly_held_by_player\":";
  output += candidate.directly_held_by_player ? "true" : "false";
  output += ",\"native_legal\":";
  output += candidate.native_legal ? "true" : "false";
  output += ",\"development_level_raw\":";
  output += SignedNumber(candidate.development_level_raw);
  output += ",\"development_progress_raw\":";
  output += SignedNumber(candidate.development_progress_raw);
  output += ",\"monthly_development_rate_raw\":";
  output += SignedNumber(candidate.monthly_development_rate_raw);
  output += ",\"max_development_level_raw\":";
  output += SignedNumber(candidate.max_development_level_raw);
  output += ",\"terrain_key\":";
  AppendJsonString(output, candidate.terrain_key);
  output += ",\"same_culture_as_player\":";
  output += candidate.same_culture_as_player ? "true" : "false";
  output += ",\"cultural_acceptance_threshold_passed\":";
  output += candidate.cultural_acceptance_threshold_passed ? "true" : "false";
  output.push_back('}');
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":";
  AppendJsonString(output, kStewardDevelopCountyCandidatesV1GameVersion);
  output += ",\"executable_sha256\":";
  AppendJsonString(output,
                   kStewardDevelopCountyCandidatesV1ExecutableSha256);
  output += ",\"backend_id\":";
  AppendJsonString(output, kStewardDevelopCountyCandidatesV1BackendId);
  output += ",\"reader_mode\":";
  AppendJsonString(output, kStewardDevelopCountyCandidatesV1ReaderMode);
  output += ",\"next_reverse_engineering_entry\":";
  AppendJsonString(
      output, kStewardDevelopCountyCandidatesV1NextReverseEngineeringEntry);
  output.push_back('}');
}

std::string_view MaterialTaskTypeKey(
    game::CampaignRootCouncilTaskTypeV1 kind) noexcept {
  using enum game::CampaignRootCouncilTaskTypeV1;
  switch (kind) {
  case general: return "general";
  case county: return "county";
  case court: return "court";
  }
  return {};
}

std::string_view MaterialProgressKindKey(
    game::CampaignRootCouncilProgressKindV1 kind) noexcept {
  using enum game::CampaignRootCouncilProgressKindV1;
  switch (kind) {
  case infinite: return "infinite";
  case percentage: return "percentage";
  case value: return "value";
  }
  return {};
}

bool ValidMaterialBinding(
    const game::CampaignRootCouncilPositionV1 &binding,
    std::int32_t steward_id) noexcept {
  if (binding.position_key != "councillor_steward" ||
      binding.incumbent_character_id != steward_id ||
      !binding.task_key.has_value() || !StableKey(*binding.task_key) ||
      !binding.task_type.has_value() ||
      MaterialTaskTypeKey(*binding.task_type).empty() ||
      !binding.frozen.has_value() || !binding.progress.has_value()) {
    return false;
  }
  const auto &progress = *binding.progress;
  if (MaterialProgressKindKey(progress.kind).empty()) return false;
  if (progress.kind == game::CampaignRootCouncilProgressKindV1::infinite) {
    if (progress.current.has_value() || progress.maximum.has_value())
      return false;
  } else if (!progress.current.has_value() || !progress.maximum.has_value() ||
             progress.current->scale != 100'000 ||
             progress.maximum->scale != 100'000) {
    return false;
  }
  if (*binding.task_type == game::CampaignRootCouncilTaskTypeV1::general)
    return !binding.target.has_value();
  if (!binding.target.has_value()) return false;
  const auto &target = *binding.target;
  if (*binding.task_type == game::CampaignRootCouncilTaskTypeV1::county)
    return target.province_id.has_value() && *target.province_id > 0 &&
           !target.character_id.has_value();
  return target.character_id.has_value() && *target.character_id > 0 &&
         !target.province_id.has_value();
}

bool ValidMaterialAvailable(
    const game::StewardDevelopCountyCandidatesV1 &value) noexcept {
  if (!value.material.has_value() || value.snapshot_revision == 0 ||
      !value.observed_date_raw.has_value() ||
      !value.player_character_id.has_value() || *value.player_character_id <= 0 ||
      !value.steward_character_id.has_value() || *value.steward_character_id <= 0 ||
      value.task_key != kStewardDevelopCountyCandidatesV1TaskKey ||
      value.unavailable_reason != game::StewardDevelopCountyFailureReasonV1::none ||
      !value.shown.has_value() || !value.valid.has_value() ||
      !value.same_frame_stable || !value.readiness.ready) {
    return false;
  }
  const auto &material = *value.material;
  if (!material.candidate_collection_complete ||
      !material.current_active_task_binding.has_value() ||
      !ValidMaterialBinding(*material.current_active_task_binding,
                            *value.steward_character_id)) {
    return false;
  }
  if (!*value.shown || !*value.valid) {
    const std::string_view reason =
        !*value.shown ? "task_not_shown" : "task_invalid";
    return material.candidates.empty() &&
           value.task_failure_reason.has_value() &&
           *value.task_failure_reason == reason;
  }
  if (value.task_failure_reason.has_value()) return false;
  for (const auto &candidate : material.candidates) {
    if (candidate.county_title_id <= 0 || candidate.capital_province_id <= 0 ||
        candidate.holder_character_id <= 0 ||
        candidate.monthly_development_rate.scale != 100'000 ||
        candidate.development_progress_current.scale != 100'000 ||
        candidate.development_progress_maximum.scale != 100'000) {
      return false;
    }
  }
  return true;
}

void AppendMaterialFixedPoint(std::string &output,
                              const game::FixedPointValue &value) {
  output += "{\"raw\":";
  output += SignedNumber(value.raw);
  output += ",\"scale\":";
  output += SignedNumber(value.scale);
  output.push_back('}');
}

void AppendMaterialBinding(
    std::string &output, const game::CampaignRootCouncilPositionV1 &binding) {
  output += "{\"position_key\":";
  AppendJsonString(output, binding.position_key);
  output += ",\"incumbent_character_id\":";
  output += SignedNumber(*binding.incumbent_character_id);
  output += ",\"task_key\":";
  AppendJsonString(output, *binding.task_key);
  output += ",\"task_type\":";
  AppendJsonString(output, MaterialTaskTypeKey(*binding.task_type));
  output += ",\"target\":";
  if (!binding.target.has_value()) {
    output += "null";
  } else if (binding.target->province_id.has_value()) {
    output += "{\"kind\":\"province\",\"province_id\":";
    output += SignedNumber(*binding.target->province_id);
    output.push_back('}');
  } else {
    output += "{\"kind\":\"character\",\"character_id\":";
    output += SignedNumber(*binding.target->character_id);
    output.push_back('}');
  }
  output += ",\"frozen\":";
  output += *binding.frozen ? "true" : "false";
  output += ",\"progress\":{\"kind\":";
  AppendJsonString(output, MaterialProgressKindKey(binding.progress->kind));
  output += ",\"current\":";
  if (binding.progress->current.has_value())
    AppendMaterialFixedPoint(output, *binding.progress->current);
  else
    output += "null";
  output += ",\"maximum\":";
  if (binding.progress->maximum.has_value())
    AppendMaterialFixedPoint(output, *binding.progress->maximum);
  else
    output += "null";
  output += "}}";
}

void AppendMaterialCandidate(
    std::string &output,
    const game::StewardDevelopCountyMaterialCandidateV1 &candidate) {
  output += "{\"county_title_id\":";
  output += SignedNumber(candidate.county_title_id);
  output += ",\"capital_province_id\":";
  output += SignedNumber(candidate.capital_province_id);
  output += ",\"holder_character_id\":";
  output += SignedNumber(candidate.holder_character_id);
  output += ",\"is_player_capital\":";
  output += candidate.is_player_capital ? "true" : "false";
  output += ",\"directly_held_by_player\":";
  output += candidate.directly_held_by_player ? "true" : "false";
  output += ",\"native_collection_ordinal\":";
  output += Number(candidate.native_collection_ordinal);
  output += ",\"native_target_valid\":";
  output += candidate.native_target_valid ? "true" : "false";
  output += ",\"monthly_development_rate\":";
  AppendMaterialFixedPoint(output, candidate.monthly_development_rate);
  output += ",\"development_progress\":{\"current\":";
  AppendMaterialFixedPoint(output, candidate.development_progress_current);
  output += ",\"maximum\":";
  AppendMaterialFixedPoint(output, candidate.development_progress_maximum);
  output += "}}";
}

std::string SerializeMaterialProfile(
    const game::StewardDevelopCountyCandidatesV1 &value,
    std::string_view version, std::string_view executable_sha256,
    std::string_view backend) {
  using Status = game::StewardDevelopCountyCandidatesStatusV1;
  if (!value.material.has_value() ||
      (value.status != Status::available && value.status != Status::unavailable))
    return {};
  const bool available = value.status == Status::available;
  const auto &material = *value.material;
  if ((available && !ValidMaterialAvailable(value)) ||
      (!available && (!ValidUnavailable(value) ||
                      material.current_active_task_binding.has_value() ||
                      material.candidate_collection_complete ||
                      !material.candidates.empty()))) {
    return {};
  }

  std::string output;
  output.reserve(2'048 + material.candidates.size() * 384);
  output += "{\"schema_version\":1,\"contract_stage\":";
  AppendJsonString(output, ck3_12003::kDevelopMaterialStage);
  output += ",\"status\":";
  AppendJsonString(output, available ? "available" : "unavailable");
  output += ",\"unavailable_reason\":";
  if (available) output += "null";
  else AppendJsonString(output, WireUnavailableReason(value.unavailable_reason));
  output += ",\"snapshot_revision\":";
  output += Number(value.snapshot_revision);
  output += ",\"observed_date_raw\":";
  output += value.observed_date_raw.has_value()
                ? SignedNumber(*value.observed_date_raw) : "null";
  output += ",\"player_character_id\":";
  output += available ? SignedNumber(*value.player_character_id) : "null";
  output += ",\"steward_character_id\":";
  output += available ? SignedNumber(*value.steward_character_id) : "null";
  output += ",\"task_key\":\"task_develop_county\",\"shown\":";
  output += available ? (*value.shown ? "true" : "false") : "null";
  output += ",\"valid\":";
  output += available ? (*value.valid ? "true" : "false") : "null";
  output += ",\"task_failure_reason\":";
  if (value.task_failure_reason.has_value())
    AppendJsonString(output, *value.task_failure_reason);
  else
    output += "null";
  output += ",\"current_active_task_binding\":";
  if (available) AppendMaterialBinding(output, *material.current_active_task_binding);
  else output += "null";
  output += ",\"candidate_collection_scope\":\"player_realm\"";
  output += ",\"candidate_collection_complete\":";
  output += material.candidate_collection_complete ? "true" : "false";
  output += ",\"candidates\":[";
  for (std::size_t index = 0; index < material.candidates.size(); ++index) {
    if (index != 0) output.push_back(',');
    AppendMaterialCandidate(output, material.candidates[index]);
  }
  output += "],\"same_frame_stable\":";
  output += value.same_frame_stable ? "true" : "false";
  output += ",\"readiness\":";
  output += value.readiness.ready ? "true" : "false";
  output += ",\"provenance\":{\"game_version\":";
  AppendJsonString(output, version);
  output += ",\"executable_sha256\":";
  AppendJsonString(output, executable_sha256);
  output += ",\"backend_id\":";
  AppendJsonString(output, backend);
  output += ",\"reader_mode\":";
  AppendJsonString(output, ck3_12003::kDevelopMaterialReaderMode);
  output += ",\"next_reverse_engineering_entry\":";
  AppendJsonString(output, ck3_12003::kDevelopMaterialNextEntry);
  output += "}}";
  return output;
}

std::string SerializeStewardDevelopCountyQueryFrame(
    std::string_view request_id, std::uint64_t query_sequence,
    const game::StewardDevelopCountyCandidatesV1 &candidates,
    std::string_view payload) {
  if (payload.empty()) {
    return {};
  }
  const std::string_view status =
      candidates.status ==
              game::StewardDevelopCountyCandidatesStatusV1::available
          ? "available"
          : "unavailable";
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result +=
      ",\"ok\":true,\"result\":{\"step\":"
      "\"query-steward-develop-county-candidates-v1\","
      "\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(candidates.snapshot_revision);
  result += ",\"steward_develop_county_candidates\":";
  result += payload;
  result += ",\"backend_id\":\"native-headless\"}}";
  return result;
}

} // namespace

std::string SerializeStewardDevelopCountyCandidatesV1(
    const game::StewardDevelopCountyCandidatesV1 &value) {
  if (value.material.has_value())
    return ck3_12003::SerializeStewardDevelopCountyMaterial12003(value);
  const bool available =
      value.status ==
      game::StewardDevelopCountyCandidatesStatusV1::available;
  if ((available && !ValidAvailable(value)) ||
      (!available && !ValidUnavailable(value))) {
    return {};
  }

  std::string output;
  output.reserve(4'096 + value.candidates.size() * 512);
  output += "{\"schema_version\":1,\"contract_stage\":";
  AppendJsonString(output, kStewardDevelopCountyCandidatesV1ContractStage);
  output += ",\"status\":";
  AppendJsonString(output, available ? "available" : "unavailable");
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null";
  } else {
    AppendJsonString(output, WireUnavailableReason(value.unavailable_reason));
  }
  output += ",\"snapshot_revision\":";
  output += Number(value.snapshot_revision);
  output += ",\"observed_date_raw\":";
  if (value.observed_date_raw.has_value()) {
    output += SignedNumber(value.observed_date_raw.value());
  } else {
    output += "null";
  }
  output += ",\"player_character_id\":";
  output += available ? SignedNumber(value.player_character_id.value()) : "null";
  output += ",\"steward_character_id\":";
  output +=
      available ? SignedNumber(value.steward_character_id.value()) : "null";
  output += ",\"task_key\":\"task_develop_county\",\"shown\":";
  output += available ? (value.shown.value() ? "true" : "false") : "null";
  output += ",\"valid\":";
  output += available ? (value.valid.value() ? "true" : "false") : "null";
  output += ",\"task_failure_reason\":";
  if (!available || !value.task_failure_reason.has_value()) {
    output += "null";
  } else {
    AppendJsonString(output, value.task_failure_reason.value());
  }
  output += ",\"steward_increase_development_value_raw\":";
  output += available
                ? SignedNumber(
                      value.steward_increase_development_value_raw.value())
                : "null";
  output += ",\"current_gold_raw\":";
  output += available ? SignedNumber(value.current_gold_raw.value()) : "null";
  output += ",\"no_ai_increase_development\":";
  output += available
                ? (value.no_ai_increase_development.value() ? "true"
                                                            : "false")
                : "null";
  output += ",\"has_active_improve_development_directive\":";
  output += available
                ? (value.has_active_improve_development_directive.value()
                       ? "true"
                       : "false")
                : "null";
  output += ",\"target_selection_mode\":";
  AppendJsonString(output, kStewardDevelopCountyCandidatesV1TargetSelectionMode);
  output += ",\"candidates\":[";
  if (available) {
    for (std::size_t index = 0; index < value.candidates.size(); ++index) {
      if (index != 0) {
        output.push_back(',');
      }
      AppendCandidate(output, value.candidates[index]);
    }
  }
  output += "],\"same_frame_stable\":";
  output += available && value.same_frame_stable ? "true" : "false";
  output += ",\"readiness\":";
  output += available && value.readiness.ready ? "true" : "false";
  output += ",\"provenance\":";
  AppendProvenance(output);
  output.push_back('}');
  return output;
}

std::string SerializeStewardDevelopCountyQueryResultV1(
    std::string_view request_id, std::uint64_t query_sequence,
    const game::StewardDevelopCountyCandidatesV1 &candidates) {
  return SerializeStewardDevelopCountyQueryFrame(
      request_id, query_sequence, candidates,
      SerializeStewardDevelopCountyCandidatesV1(candidates));
}

} // namespace xar::ck3_11906

namespace xar::ck3_12003 {

std::string SerializeStewardDevelopCountyMaterial12003(
    const game::StewardDevelopCountyCandidatesV1 &value) {
  return ck3_11906::SerializeMaterialProfile(
      value, kGameVersion, kExecutableSha256, kDevelopMaterialBackend);
}

} // namespace xar::ck3_12003

namespace xar::ck3_12004 {

std::string SerializeStewardDevelopCountyMaterial12004(
    const StewardDevelopCountyEnvironment12004 &environment,
    const game::StewardDevelopCountyCandidatesV1 &value) {
  if (!IsStewardDevelopCountyEnvironment12004(environment)) return {};
  return ck3_11906::SerializeMaterialProfile(
      value, kGameVersion, kExecutableSha256, kDevelopMaterialBackend12004);
}

std::string SerializeStewardDevelopCountyQueryResult12004(
    const StewardDevelopCountyEnvironment12004 &environment,
    std::string_view request_id, std::uint64_t query_sequence,
    const game::StewardDevelopCountyCandidatesV1 &value) {
  return ck3_11906::SerializeStewardDevelopCountyQueryFrame(
      request_id, query_sequence, value,
      SerializeStewardDevelopCountyMaterial12004(environment, value));
}

} // namespace xar::ck3_12004
