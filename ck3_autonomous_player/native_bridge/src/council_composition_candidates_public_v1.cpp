#include "xar_bridge/council_composition_candidates_public_v1.hpp"

#include <algorithm>

namespace xar::ck3_11906 {
namespace {

using Failure = game::CouncilCompositionCandidatesPublicFailureV1;
using Output = game::CouncilCompositionCandidatesPublicV1;
using Result = ProjectCouncilCompositionCandidatesPublicResultV1;
using PrivateStatus = game::CouncilCompositionStewardCandidatesStatusV1;

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

template <std::size_t Size>
bool SetFixed(std::array<char, Size> &output, std::string_view value) noexcept {
  if (value.empty() || value.size() >= output.size()) return false;
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
  return true;
}

void Unavailable(Output &output, Failure reason,
                 game::CouncilCompositionStewardCandidatesFailureV1
                     source_reason = game::
                         CouncilCompositionStewardCandidatesFailureV1::none)
    noexcept {
  output = {};
  output.status = game::CouncilCompositionCandidatesPublicStatusV1::unavailable;
  output.unavailable_reason = reason;
  output.source_unavailable_reason = source_reason;
}

bool PrivateAvailableInvariant(
    const game::CouncilCompositionStewardCandidatesV1 &value) noexcept {
  return value.status == PrivateStatus::available &&
         value.unavailable_reason ==
             game::CouncilCompositionStewardCandidatesFailureV1::none &&
         !FixedString(value.snapshot_id).empty() && value.public_revision != 0 &&
         value.native_revision != 0 && value.paused &&
         value.owner_character_id != -1 &&
         FixedString(value.position_key) ==
             kCouncilCompositionCandidatesPublicPositionKeyV1 &&
         value.candidate_collection_complete &&
         value.candidate_count <=
             game::kCouncilCompositionStewardCandidatesMaximumRowsV1 &&
         value.temporary_vector_released && value.readiness.identity_ready &&
         value.readiness.candidate_collection_ready;
}

bool SameFrame(
    const game::CouncilCompositionStewardCandidatesV1 &private_result,
    const CouncilCompositionCandidatesPublicEnrichmentV1 &enrichment) noexcept {
  return enrichment.same_frame_stable &&
         FixedString(enrichment.snapshot_id) ==
             FixedString(private_result.snapshot_id) &&
         enrichment.public_revision == private_result.public_revision &&
         enrichment.native_revision == private_result.native_revision &&
         enrichment.date_raw == private_result.date_raw &&
         enrichment.owner_character_id == private_result.owner_character_id &&
         FixedString(enrichment.position_key) ==
             FixedString(private_result.position_key);
}

} // namespace

ProjectCouncilCompositionCandidatesPublicResultV1
ProjectCouncilCompositionCandidatesPublicV1(
    const game::CouncilCompositionStewardCandidatesV1 &private_result,
    const CouncilCompositionCandidatesPublicEnrichmentV1 &enrichment,
    game::CouncilCompositionCandidatesPublicV1 &output) noexcept {
  if (private_result.status != PrivateStatus::available) {
    Unavailable(output, Failure::private_reader_unavailable,
                private_result.unavailable_reason);
    return Result::unavailable;
  }
  if (!PrivateAvailableInvariant(private_result)) {
    Unavailable(output, Failure::schema_invariant_failed);
    return Result::unavailable;
  }
  if (!enrichment.incumbent_ready) {
    Unavailable(output, Failure::enrichment_unavailable);
    return Result::unavailable;
  }
  if (!SameFrame(private_result, enrichment)) {
    Unavailable(output, Failure::same_frame_binding_mismatch);
    return Result::unavailable;
  }
  if (enrichment.incumbent_character_id == 0) {
    Unavailable(output, Failure::incumbent_invalid);
    return Result::unavailable;
  }
  if (enrichment.candidate_count != private_result.candidate_count ||
      enrichment.candidate_count >
          game::kCouncilCompositionStewardCandidatesMaximumRowsV1) {
    Unavailable(output, Failure::candidate_set_mismatch);
    return Result::unavailable;
  }

  for (std::uint32_t index = 0; index < enrichment.candidate_count; ++index) {
    const auto &native = private_result.candidates[index];
    const auto &fact = enrichment.candidates[index];
    if (fact.character_id != native.character_id ||
        fact.native_collection_ordinal != native.native_collection_ordinal) {
      Unavailable(output, Failure::candidate_set_mismatch);
      return Result::unavailable;
    }
    if (!fact.final_eligible ||
        fact.eligibility_reason !=
            game::CouncilCompositionCandidateEligibilityReasonV1::
                native_candidate_provider_accepted) {
      Unavailable(output, Failure::candidate_eligibility_unready);
      return Result::unavailable;
    }
    if (fact.main_skill < 0) {
      Unavailable(output, Failure::candidate_main_skill_unready);
      return Result::unavailable;
    }
  }

  const bool vacant = enrichment.incumbent_character_id == -1;
  const auto action_route =
      vacant ? game::CouncilCompositionCandidateActionRouteV1::assign
             : game::CouncilCompositionCandidateActionRouteV1::replace;
  output = {};
  output.status = game::CouncilCompositionCandidatesPublicStatusV1::available;
  output.unavailable_reason = Failure::none;
  output.source_unavailable_reason =
      game::CouncilCompositionStewardCandidatesFailureV1::none;
  output.snapshot_id = private_result.snapshot_id;
  output.public_revision = private_result.public_revision;
  output.native_revision = private_result.native_revision;
  output.date_raw = private_result.date_raw;
  output.paused = private_result.paused;
  output.owner_character_id = private_result.owner_character_id;
  output.position_key = private_result.position_key;
  output.incumbent_character_id = enrichment.incumbent_character_id;
  output.vacant = vacant;
  output.action_route = action_route;
  output.candidate_collection_complete = true;
  output.candidate_count = private_result.candidate_count;
  for (std::uint32_t index = 0; index < output.candidate_count; ++index) {
    const auto &native = private_result.candidates[index];
    const auto &fact = enrichment.candidates[index];
    auto &candidate = output.candidates[index];
    candidate.character_id = native.character_id;
    candidate.native_collection_ordinal = native.native_collection_ordinal;
    candidate.eligible = true;
    candidate.eligibility_reason = fact.eligibility_reason;
    if (!SetFixed(candidate.main_skill.key,
                  kCouncilCompositionCandidatesPublicMainSkillKeyV1)) {
      Unavailable(output, Failure::schema_invariant_failed);
      return Result::unavailable;
    }
    candidate.main_skill.value = fact.main_skill;
    candidate.action_route = action_route;
  }
  output.readiness.identity_ready = true;
  output.readiness.candidate_collection_ready = true;
  output.readiness.incumbent_ready = true;
  output.readiness.candidate_legality_ready = true;
  output.readiness.main_skill_ready = true;
  output.readiness.action_route_ready = true;
  output.readiness.same_frame_ready = true;
  output.readiness.ready = true;
  return Result::available;
}

std::string_view CouncilCompositionCandidatesPublicFailureKeyV1(
    game::CouncilCompositionCandidatesPublicFailureV1 reason) noexcept {
  using enum game::CouncilCompositionCandidatesPublicFailureV1;
  switch (reason) {
  case none: return "none";
  case private_reader_unavailable: return "private_reader_unavailable";
  case enrichment_unavailable: return "enrichment_unavailable";
  case same_frame_binding_mismatch: return "same_frame_binding_mismatch";
  case incumbent_invalid: return "incumbent_invalid";
  case candidate_set_mismatch: return "candidate_set_mismatch";
  case candidate_eligibility_unready: return "candidate_eligibility_unready";
  case candidate_main_skill_unready: return "candidate_main_skill_unready";
  case schema_invariant_failed: return "schema_invariant_failed";
  }
  return "schema_invariant_failed";
}

std::string_view CouncilCompositionCandidateEligibilityReasonKeyV1(
    game::CouncilCompositionCandidateEligibilityReasonV1 reason) noexcept {
  switch (reason) {
  case game::CouncilCompositionCandidateEligibilityReasonV1::
      native_candidate_provider_accepted:
    return "native_candidate_provider_accepted";
  }
  return {};
}

std::string_view CouncilCompositionCandidateActionRouteKeyV1(
    game::CouncilCompositionCandidateActionRouteV1 route) noexcept {
  switch (route) {
  case game::CouncilCompositionCandidateActionRouteV1::assign:
    return "assign";
  case game::CouncilCompositionCandidateActionRouteV1::replace:
    return "replace";
  }
  return {};
}

} // namespace xar::ck3_11906
