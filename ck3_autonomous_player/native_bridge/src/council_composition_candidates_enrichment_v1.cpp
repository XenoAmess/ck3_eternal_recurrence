#include "xar_bridge/council_composition_candidates_enrichment_v1.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

namespace xar::ck3_11906 {
namespace {

using Failure = game::CouncilCompositionCandidatesEnrichmentFailureV1;
using Result = game::ReadCouncilCompositionCandidatesEnrichmentResultV1;
using Frame = CouncilCompositionStewardCandidatesFrameV1;
using Private = game::CouncilCompositionStewardCandidatesV1;
using Output = CouncilCompositionCandidatesPublicEnrichmentV1;

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool PrivateReady(const Private &value) noexcept {
  return value.status ==
             game::CouncilCompositionStewardCandidatesStatusV1::available &&
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

bool FrameMatchesPrivate(const Frame &frame, const Private &value) noexcept {
  return frame.paused && frame.map_ready && frame.has_played_character &&
         frame.played_character_alive && frame.played_character != 0 &&
         frame.played_character_identity_round_trip &&
         frame.active_task_id != -1 && frame.active_task != 0 &&
         frame.active_task_identity_round_trip &&
         FixedString(frame.snapshot_id) == FixedString(value.snapshot_id) &&
         frame.public_revision == value.public_revision &&
         frame.native_revision == value.native_revision &&
         frame.date_raw == value.date_raw &&
         frame.played_character_id == value.owner_character_id &&
         FixedString(frame.position_key) == FixedString(value.position_key);
}

bool SameFrame(const Frame &before, const Frame &after) noexcept {
  return before == after;
}

template <typename Value>
bool ReadAt(const CouncilCompositionCandidatesEnrichmentAccessV1 &access,
            std::uintptr_t base, std::size_t offset, Value &output) noexcept {
  if (base == 0 || base >
          (std::numeric_limits<std::uintptr_t>::max)() - offset) {
    return false;
  }
  return access.read_memory(
      access.context, reinterpret_cast<const void *>(base + offset), &output,
      sizeof(output));
}

bool ResolveExact(
    const CouncilCompositionCandidatesEnrichmentAccessV1 &access,
    std::int32_t character_id, std::uintptr_t &character) noexcept {
  character = 0;
  std::int32_t observed_id = -1;
  return character_id != -1 && character_id != 0 &&
         access.resolve_character(access.context, character_id, character) &&
         character != 0 &&
         ReadAt(access, character, kCouncilCompositionCharacterIdentityOffsetV1,
                observed_id) &&
         observed_id == character_id;
}

Result Unavailable(Output &output, Failure &failure,
                   Failure reason) noexcept {
  output = {};
  failure = reason;
  return Result::unavailable;
}

} // namespace

game::ReadCouncilCompositionCandidatesEnrichmentResultV1
ReadCouncilCompositionCandidatesEnrichmentV1(
    const CouncilCompositionCandidatesEnrichmentEnvironmentV1 &environment,
    const CouncilCompositionCandidatesEnrichmentAccessV1 &access,
    const game::CouncilCompositionStewardCandidatesV1 &private_result,
    CouncilCompositionCandidatesPublicEnrichmentV1 &output,
    game::CouncilCompositionCandidatesEnrichmentFailureV1 &failure) noexcept {
  output = {};
  failure = Failure::none;
  if (!PrivateReady(private_result)) {
    return Unavailable(output, failure, Failure::invalid_private_result);
  }
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kCouncilCompositionCandidatesEnrichmentExecutableSha256V1) {
    return Unavailable(output, failure, Failure::exact_build_not_admitted);
  }
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      access.read_memory == nullptr || access.resolve_character == nullptr) {
    return Unavailable(output, failure, Failure::native_bindings_unavailable);
  }
  if (!access.is_main_thread(access.context)) {
    return Unavailable(output, failure,
                       Failure::application_main_thread_required);
  }

  Frame before{};
  if (!access.capture_frame(access.context, before)) {
    return Unavailable(output, failure, Failure::frame_capture_failed);
  }
  if (!FrameMatchesPrivate(before, private_result)) {
    return Unavailable(output, failure,
                       Failure::same_frame_binding_mismatch);
  }

  std::int32_t incumbent_id = 0;
  if (!ReadAt(access, before.active_task,
              kCouncilCompositionActiveTaskIncumbentIdOffsetV1,
              incumbent_id) ||
      incumbent_id == 0) {
    return Unavailable(output, failure, Failure::incumbent_unreadable);
  }

  std::int32_t incumbent_skill = -1;
  if (incumbent_id != -1) {
    std::uintptr_t incumbent = 0;
    if (!ResolveExact(access, incumbent_id, incumbent)) {
      return Unavailable(output, failure,
                         Failure::incumbent_generation_mismatch);
    }
    if (!ReadAt(access, incumbent,
                kCouncilCompositionCharacterStewardshipOffsetV1,
                incumbent_skill) ||
        incumbent_skill < 0) {
      return Unavailable(output, failure,
                         Failure::incumbent_main_skill_unreadable);
    }
  }

  Output pending{};
  pending.snapshot_id = private_result.snapshot_id;
  pending.public_revision = private_result.public_revision;
  pending.native_revision = private_result.native_revision;
  pending.date_raw = private_result.date_raw;
  pending.owner_character_id = private_result.owner_character_id;
  pending.position_key = private_result.position_key;
  pending.incumbent_character_id = incumbent_id;
  pending.incumbent_ready = true;
  pending.incumbent_main_skill = incumbent_skill;
  pending.incumbent_main_skill_ready = true;
  pending.candidate_count = private_result.candidate_count;

  for (std::uint32_t index = 0; index < private_result.candidate_count;
       ++index) {
    const auto &source = private_result.candidates[index];
    std::uintptr_t candidate = 0;
    if (!ResolveExact(access, source.character_id, candidate)) {
      return Unavailable(output, failure,
                         Failure::candidate_generation_mismatch);
    }
    std::int32_t stewardship = -1;
    if (!ReadAt(access, candidate,
                kCouncilCompositionCharacterStewardshipOffsetV1,
                stewardship) ||
        stewardship < 0) {
      return Unavailable(output, failure,
                         Failure::candidate_main_skill_unreadable);
    }
    pending.candidates[index].character_id = source.character_id;
    pending.candidates[index].native_collection_ordinal =
        source.native_collection_ordinal;
    pending.candidates[index].final_eligible = true;
    pending.candidates[index].eligibility_reason =
        game::CouncilCompositionCandidateEligibilityReasonV1::
            native_candidate_provider_accepted;
    pending.candidates[index].main_skill = stewardship;
  }

  if (!access.is_main_thread(access.context)) {
    return Unavailable(output, failure,
                       Failure::application_main_thread_required);
  }
  Frame after{};
  if (!access.capture_frame(access.context, after)) {
    return Unavailable(output, failure, Failure::frame_capture_failed);
  }
  if (!SameFrame(before, after)) {
    return Unavailable(output, failure, Failure::frame_drift);
  }

  pending.same_frame_stable = true;
  output = pending;
  failure = Failure::none;
  return Result::available;
}

std::string_view CouncilCompositionCandidatesEnrichmentFailureKeyV1(
    game::CouncilCompositionCandidatesEnrichmentFailureV1 failure) noexcept {
  using enum game::CouncilCompositionCandidatesEnrichmentFailureV1;
  switch (failure) {
  case none: return "none";
  case invalid_private_result: return "invalid_private_result";
  case exact_build_not_admitted: return "exact_build_not_admitted";
  case native_bindings_unavailable: return "native_bindings_unavailable";
  case application_main_thread_required:
    return "application_main_thread_required";
  case frame_capture_failed: return "frame_capture_failed";
  case same_frame_binding_mismatch: return "same_frame_binding_mismatch";
  case incumbent_unreadable: return "incumbent_unreadable";
  case incumbent_generation_mismatch:
    return "incumbent_generation_mismatch";
  case incumbent_main_skill_unreadable:
    return "incumbent_main_skill_unreadable";
  case candidate_generation_mismatch:
    return "candidate_generation_mismatch";
  case candidate_main_skill_unreadable:
    return "candidate_main_skill_unreadable";
  case frame_drift: return "frame_drift";
  }
  return "native_bindings_unavailable";
}

} // namespace xar::ck3_11906
