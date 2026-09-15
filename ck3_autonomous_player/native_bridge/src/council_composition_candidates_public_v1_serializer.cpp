#include "xar_bridge/council_composition_candidates_public_v1.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

void AppendString(std::string &output, std::string_view value) {
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

template <typename Number>
void AppendNumber(std::string &output, Number value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec == std::errc{}) output.append(buffer.data(), result.ptr);
}

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

bool ValidAvailable(
    const game::CouncilCompositionCandidatesPublicV1 &value) noexcept {
  if (value.status !=
          game::CouncilCompositionCandidatesPublicStatusV1::available ||
      value.unavailable_reason !=
          game::CouncilCompositionCandidatesPublicFailureV1::none ||
      value.source_unavailable_reason !=
          game::CouncilCompositionStewardCandidatesFailureV1::none ||
      FixedString(value.snapshot_id).empty() || value.public_revision == 0 ||
      value.native_revision == 0 || !value.paused ||
      value.owner_character_id == -1 ||
      FixedString(value.position_key) !=
          kCouncilCompositionCandidatesPublicPositionKeyV1 ||
      value.vacant != (value.incumbent_character_id == -1) ||
      value.action_route !=
          (value.vacant
               ? game::CouncilCompositionCandidateActionRouteV1::assign
               : game::CouncilCompositionCandidateActionRouteV1::replace) ||
      !value.candidate_collection_complete ||
      value.candidate_count >
          game::kCouncilCompositionStewardCandidatesMaximumRowsV1 ||
      !value.readiness.identity_ready ||
      !value.readiness.candidate_collection_ready ||
      !value.readiness.incumbent_ready ||
      !value.readiness.candidate_legality_ready ||
      !value.readiness.main_skill_ready ||
      !value.readiness.action_route_ready ||
      !value.readiness.same_frame_ready || !value.readiness.ready) {
    return false;
  }
  for (std::uint32_t index = 0; index < value.candidate_count; ++index) {
    const auto &candidate = value.candidates[index];
    if (candidate.character_id == -1 || !candidate.eligible ||
        CouncilCompositionCandidateEligibilityReasonKeyV1(
            candidate.eligibility_reason)
            .empty() ||
        FixedString(candidate.main_skill.key) !=
            kCouncilCompositionCandidatesPublicMainSkillKeyV1 ||
        candidate.main_skill.value < 0 ||
        candidate.action_route != value.action_route) {
      return false;
    }
  }
  return true;
}

std::string_view SourceFailureKey(
    game::CouncilCompositionStewardCandidatesFailureV1 reason) noexcept {
  using enum game::CouncilCompositionStewardCandidatesFailureV1;
  switch (reason) {
  case none: return "none";
  case invalid_request: return "invalid_request";
  case exact_build_not_admitted: return "exact_build_not_admitted";
  case native_bindings_unavailable: return "native_bindings_unavailable";
  case application_main_thread_required:
    return "application_main_thread_required";
  case frame_capture_failed: return "frame_capture_failed";
  case snapshot_identity_mismatch: return "snapshot_identity_mismatch";
  case revision_drift: return "revision_drift";
  case date_drift: return "date_drift";
  case not_paused: return "not_paused";
  case player_unavailable: return "player_unavailable";
  case active_steward_task_unavailable:
    return "active_steward_task_unavailable";
  case position_outside_coverage: return "position_outside_coverage";
  case candidate_collection_unavailable:
    return "candidate_collection_unavailable";
  case candidate_span_invalid: return "candidate_span_invalid";
  case candidate_row_unreadable: return "candidate_row_unreadable";
  case candidate_generation_mismatch:
    return "candidate_generation_mismatch";
  case duplicate_candidate_id: return "duplicate_candidate_id";
  case temporary_vector_release_failed:
    return "temporary_vector_release_failed";
  }
  return "native_bindings_unavailable";
}

void AppendReadiness(
    std::string &output,
    const game::CouncilCompositionCandidatesPublicReadinessV1 &readiness) {
  output += "{\"identity_ready\":";
  AppendBool(output, readiness.identity_ready);
  output += ",\"candidate_collection_ready\":";
  AppendBool(output, readiness.candidate_collection_ready);
  output += ",\"incumbent_ready\":";
  AppendBool(output, readiness.incumbent_ready);
  output += ",\"candidate_legality_ready\":";
  AppendBool(output, readiness.candidate_legality_ready);
  output += ",\"main_skill_ready\":";
  AppendBool(output, readiness.main_skill_ready);
  output += ",\"action_route_ready\":";
  AppendBool(output, readiness.action_route_ready);
  output += ",\"same_frame_ready\":";
  AppendBool(output, readiness.same_frame_ready);
  output += ",\"ready\":";
  AppendBool(output, readiness.ready);
  output.push_back('}');
}

} // namespace

std::string SerializeCouncilCompositionCandidatesPublicV1(
    const game::CouncilCompositionCandidatesPublicV1 &value) {
  const bool available =
      value.status == game::CouncilCompositionCandidatesPublicStatusV1::available;
  if (available && !ValidAvailable(value)) return {};
  if (!available &&
      value.unavailable_reason ==
          game::CouncilCompositionCandidatesPublicFailureV1::none) {
    return {};
  }

  std::string output;
  output.reserve(2'048 + static_cast<std::size_t>(value.candidate_count) * 256);
  output += "{\"schema\":";
  AppendString(output, kCouncilCompositionCandidatesPublicSchemaV1);
  output += ",\"schema_version\":1,\"capability\":";
  AppendString(output, kCouncilCompositionCandidatesPublicCapabilityV1);
  output += ",\"exact_build\":{\"game_version\":";
  AppendString(output, kCouncilCompositionCandidatesPublicGameVersionV1);
  output += ",\"executable_sha256\":";
  AppendString(output, kCouncilCompositionCandidatesPublicExecutableSha256V1);
  output += "},\"status\":";
  AppendString(output, available ? "available" : "unavailable");
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null";
  } else {
    AppendString(output, CouncilCompositionCandidatesPublicFailureKeyV1(
                             value.unavailable_reason));
  }
  output += ",\"source_unavailable_reason\":";
  if (value.source_unavailable_reason ==
      game::CouncilCompositionStewardCandidatesFailureV1::none) {
    output += "null";
  } else {
    AppendString(output, SourceFailureKey(value.source_unavailable_reason));
  }
  if (!available) {
    output.push_back('}');
    return output;
  }

  output += ",\"snapshot\":{\"snapshot_id\":";
  AppendString(output, FixedString(value.snapshot_id));
  output += ",\"public_revision\":";
  AppendNumber(output, value.public_revision);
  output += ",\"native_revision\":";
  AppendNumber(output, value.native_revision);
  output += ",\"date_raw\":";
  AppendNumber(output, value.date_raw);
  output += ",\"paused\":";
  AppendBool(output, value.paused);
  output += "},\"owner_character_id\":";
  AppendNumber(output, value.owner_character_id);
  output += ",\"position\":{\"position_key\":";
  AppendString(output, FixedString(value.position_key));
  output += ",\"incumbent_character_id\":";
  if (value.vacant) {
    output += "null";
  } else {
    AppendNumber(output, value.incumbent_character_id);
  }
  output += ",\"vacant\":";
  AppendBool(output, value.vacant);
  output += ",\"action_route\":";
  AppendString(output,
               CouncilCompositionCandidateActionRouteKeyV1(value.action_route));
  output += "},\"candidate_collection_complete\":";
  AppendBool(output, value.candidate_collection_complete);
  output += ",\"candidates\":[";
  for (std::uint32_t index = 0; index < value.candidate_count; ++index) {
    if (index != 0) output.push_back(',');
    const auto &candidate = value.candidates[index];
    output += "{\"character_id\":";
    AppendNumber(output, candidate.character_id);
    output += ",\"native_collection_ordinal\":";
    AppendNumber(output, candidate.native_collection_ordinal);
    output += ",\"eligible\":";
    AppendBool(output, candidate.eligible);
    output += ",\"eligibility_reason\":";
    AppendString(output, CouncilCompositionCandidateEligibilityReasonKeyV1(
                             candidate.eligibility_reason));
    output += ",\"main_skill\":{\"key\":";
    AppendString(output, FixedString(candidate.main_skill.key));
    output += ",\"value\":";
    AppendNumber(output, candidate.main_skill.value);
    output += "},\"action_route\":";
    AppendString(output, CouncilCompositionCandidateActionRouteKeyV1(
                             candidate.action_route));
    output.push_back('}');
  }
  output += "],\"readiness\":";
  AppendReadiness(output, value.readiness);
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
