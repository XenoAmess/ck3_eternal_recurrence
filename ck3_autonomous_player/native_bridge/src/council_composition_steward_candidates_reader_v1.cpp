#include "xar_bridge/council_composition_steward_candidates_reader_v1.hpp"

#include <algorithm>
#include <array>
#include <limits>

namespace xar::ck3_11906 {
namespace {

using Failure = game::CouncilCompositionStewardCandidatesFailureV1;
using Result = game::ReadCouncilCompositionStewardCandidatesResultV1;
using Output = game::CouncilCompositionStewardCandidatesV1;
using Frame = CouncilCompositionStewardCandidatesFrameV1;

static_assert(sizeof(void *) == 8,
              "council composition steward reader is x64-only");

constexpr std::int32_t kMaximumNativeCapacity = 65'536;

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ValidRequest(
    const CouncilCompositionStewardCandidatesRequestV1 &request) noexcept {
  return !request.expected_snapshot_id.empty() &&
      request.expected_snapshot_id.size() <
          game::kCouncilCompositionStewardSnapshotIdCapacityV1 &&
      request.expected_owner_character_id != -1;
}

Failure ValidateInitialFrame(
    const Frame &frame,
    const CouncilCompositionStewardCandidatesRequestV1 &request) noexcept {
  if (FixedString(frame.snapshot_id) != request.expected_snapshot_id) {
    return Failure::snapshot_identity_mismatch;
  }
  if (frame.public_revision != request.expected_public_revision ||
      frame.native_revision != request.expected_native_revision) {
    return Failure::revision_drift;
  }
  if (frame.date_raw != request.expected_date_raw) {
    return Failure::date_drift;
  }
  if (!frame.paused) return Failure::not_paused;
  if (!frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive || frame.played_character == 0 ||
      frame.played_character_id == -1 ||
      !frame.played_character_identity_round_trip ||
      frame.played_character_id != request.expected_owner_character_id) {
    return Failure::player_unavailable;
  }
  if (frame.active_task_id == -1 || frame.active_task == 0 ||
      !frame.active_task_identity_round_trip) {
    return Failure::active_steward_task_unavailable;
  }
  if (FixedString(frame.position_key) !=
      kCouncilCompositionStewardCandidatesReaderPositionKeyV1) {
    return Failure::position_outside_coverage;
  }
  return Failure::none;
}

Failure ClassifyFrameDrift(const Frame &before,
                           const Frame &after) noexcept {
  if (FixedString(before.snapshot_id) != FixedString(after.snapshot_id)) {
    return Failure::snapshot_identity_mismatch;
  }
  if (before.public_revision != after.public_revision ||
      before.native_revision != after.native_revision) {
    return Failure::revision_drift;
  }
  if (before.date_raw != after.date_raw) return Failure::date_drift;
  if (!after.paused) return Failure::not_paused;
  if (before.map_ready != after.map_ready ||
      before.has_played_character != after.has_played_character ||
      before.played_character_alive != after.played_character_alive ||
      before.played_character_id != after.played_character_id ||
      before.played_character != after.played_character ||
      before.played_character_identity_round_trip !=
          after.played_character_identity_round_trip) {
    return Failure::player_unavailable;
  }
  if (before.active_task_id != after.active_task_id ||
      before.active_task != after.active_task ||
      before.active_task_identity_round_trip !=
          after.active_task_identity_round_trip) {
    return Failure::active_steward_task_unavailable;
  }
  if (FixedString(before.position_key) != FixedString(after.position_key)) {
    return Failure::position_outside_coverage;
  }
  return Failure::none;
}

Failure ValidateSpan(
    const CouncilCompositionStewardNativeCandidateVectorV1 &vector,
    const CouncilCompositionStewardCandidatesAccessV1 &access) noexcept {
  if (vector.capacity < 0 || vector.count < 0 ||
      vector.capacity < vector.count ||
      vector.capacity > kMaximumNativeCapacity ||
      vector.count > static_cast<std::int32_t>(
                         game::kCouncilCompositionStewardCandidatesMaximumRowsV1)) {
    return Failure::candidate_span_invalid;
  }
  if (vector.count == 0) return Failure::none;
  constexpr auto stride = sizeof(std::uintptr_t);
  const auto count = static_cast<std::size_t>(vector.count);
  if (vector.data_address == 0 ||
      count > (std::numeric_limits<std::size_t>::max)() / stride) {
    return Failure::candidate_span_invalid;
  }
  const auto size = count * stride;
  if (vector.data_address >
      (std::numeric_limits<std::uintptr_t>::max)() - size ||
      !access.is_readable_span(access.context, vector.data_address, size)) {
    return Failure::candidate_span_invalid;
  }
  return Failure::none;
}

void ClearUnavailable(Output &output, Failure reason,
                      bool temporary_vector_released) noexcept {
  output = {};
  output.status =
      game::CouncilCompositionStewardCandidatesStatusV1::unavailable;
  output.unavailable_reason = reason;
  output.temporary_vector_released = temporary_vector_released;
}

void Publish(
    const Frame &frame,
    const std::array<game::CouncilCompositionStewardCandidateV1,
                     game::kCouncilCompositionStewardCandidatesMaximumRowsV1>
        &candidates,
    std::uint32_t candidate_count, Output &output) noexcept {
  output = {};
  output.status = game::CouncilCompositionStewardCandidatesStatusV1::available;
  output.unavailable_reason = Failure::none;
  output.snapshot_id = frame.snapshot_id;
  output.public_revision = frame.public_revision;
  output.native_revision = frame.native_revision;
  output.date_raw = frame.date_raw;
  output.paused = frame.paused;
  output.owner_character_id = frame.played_character_id;
  output.position_key = frame.position_key;
  output.candidate_collection_complete = true;
  output.candidate_count = candidate_count;
  output.candidates = candidates;
  output.temporary_vector_released = true;
  output.readiness.identity_ready = true;
  output.readiness.candidate_collection_ready = true;
}

} // namespace

game::ReadCouncilCompositionStewardCandidatesResultV1
ReadCouncilCompositionStewardCandidatesV1(
    const CouncilCompositionStewardCandidatesEnvironmentV1 &environment,
    const CouncilCompositionStewardCandidatesAccessV1 &access,
    const CouncilCompositionStewardCandidatesRequestV1 &request,
    game::CouncilCompositionStewardCandidatesV1 &output) noexcept {
  ClearUnavailable(output, Failure::invalid_request, false);
  if (!ValidRequest(request)) return Result::unavailable;
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kCouncilCompositionStewardCandidatesReaderExecutableSha256V1) {
    ClearUnavailable(output, Failure::exact_build_not_admitted, false);
    return Result::unavailable;
  }
  if (environment.module_base == 0 || environment.producer_address == 0 ||
      access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      access.produce == nullptr || access.release == nullptr ||
      access.is_readable_span == nullptr ||
      access.read_candidate_pointer == nullptr ||
      access.read_candidate_id == nullptr ||
      access.resolve_candidate == nullptr) {
    ClearUnavailable(output, Failure::native_bindings_unavailable, false);
    return Result::unavailable;
  }
  if (environment.producer_address < environment.module_base ||
      environment.producer_address - environment.module_base !=
      kCouncilCompositionStewardCandidatesProducerRvaV1) {
    ClearUnavailable(output, Failure::native_bindings_unavailable, false);
    return Result::unavailable;
  }
  if (!access.is_main_thread(access.context)) {
    ClearUnavailable(output, Failure::application_main_thread_required, false);
    return Result::unavailable;
  }

  Frame before{};
  if (!access.capture_frame(access.context, before)) {
    ClearUnavailable(output, Failure::frame_capture_failed, false);
    return Result::unavailable;
  }
  const auto initial_failure = ValidateInitialFrame(before, request);
  if (initial_failure != Failure::none) {
    ClearUnavailable(output, initial_failure, false);
    return Result::unavailable;
  }

  CouncilCompositionStewardNativeCandidateVectorV1 vector{};
  const bool produced = access.produce(
      access.context, before.played_character, before.active_task,
      true, vector);
  Failure pending_failure = produced
      ? ValidateSpan(vector, access)
      : Failure::candidate_collection_unavailable;

  std::array<game::CouncilCompositionStewardCandidateV1,
             game::kCouncilCompositionStewardCandidatesMaximumRowsV1>
      candidates{};
  std::uint32_t candidate_count = 0;
  if (pending_failure == Failure::none) {
    candidate_count = static_cast<std::uint32_t>(vector.count);
    for (std::uint32_t ordinal = 0; ordinal < candidate_count; ++ordinal) {
      std::uintptr_t candidate = 0;
      std::int32_t character_id = -1;
      std::uintptr_t resolved = 0;
      const auto address = vector.data_address +
          static_cast<std::uintptr_t>(ordinal) * sizeof(std::uintptr_t);
      if (!access.read_candidate_pointer(access.context, address, candidate) ||
          candidate == 0 ||
          !access.read_candidate_id(access.context, candidate, character_id)) {
        pending_failure = Failure::candidate_row_unreadable;
        break;
      }
      if (character_id == -1 ||
          !access.resolve_candidate(access.context, character_id, resolved) ||
          resolved != candidate) {
        pending_failure = Failure::candidate_generation_mismatch;
        break;
      }
      for (std::uint32_t prior = 0; prior < ordinal; ++prior) {
        if (candidates[prior].character_id == character_id) {
          pending_failure = Failure::duplicate_candidate_id;
          break;
        }
      }
      if (pending_failure != Failure::none) break;
      candidates[ordinal].character_id = character_id;
      candidates[ordinal].native_collection_ordinal = ordinal;
    }
  }

  const bool released = access.release(access.context, vector);
  if (!released) {
    ClearUnavailable(output, Failure::temporary_vector_release_failed, false);
    return Result::unavailable;
  }

  Frame after{};
  if (!access.capture_frame(access.context, after)) {
    ClearUnavailable(output, Failure::frame_capture_failed, true);
    return Result::unavailable;
  }
  const auto drift = ClassifyFrameDrift(before, after);
  if (drift != Failure::none) {
    ClearUnavailable(output, drift, true);
    return Result::unavailable;
  }
  if (pending_failure != Failure::none) {
    ClearUnavailable(output, pending_failure, true);
    return Result::unavailable;
  }

  std::sort(candidates.begin(), candidates.begin() + candidate_count,
            [](const auto &left, const auto &right) {
              return static_cast<std::uint32_t>(left.character_id) <
                  static_cast<std::uint32_t>(right.character_id);
            });
  Publish(before, candidates, candidate_count, output);
  return Result::available;
}

std::string_view CouncilCompositionStewardCandidatesFailureKeyV1(
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

} // namespace xar::ck3_11906
