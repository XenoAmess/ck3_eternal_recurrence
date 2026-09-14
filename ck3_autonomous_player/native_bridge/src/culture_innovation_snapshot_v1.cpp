#include "xar_bridge/culture_innovation_snapshot_v1.hpp"

#include <algorithm>

namespace xar::ck3_11906 {
namespace {

using Failure = game::CultureInnovationSnapshotFailureV1;
using Presence = game::CultureInnovationPresenceV1;
using Result = game::ReadCultureInnovationSnapshotResultV1;
using Snapshot = game::CultureInnovationSnapshotV1;
using State = game::CultureInnovationStateV1;

static_assert(sizeof(void *) == 8,
              "culture innovation snapshot is x64-only");
static_assert(kCultureEraStateCountOffsetV1 -
                  kCultureEraStateVectorOffsetV1 ==
              0x0C);
static_assert(kCultureInnovationStateCountOffsetV1 -
                  kCultureInnovationStateVectorOffsetV1 ==
              0x0C);
static_assert(kCultureInnovationDefinitionCountOffsetV1 -
                  kCultureInnovationDefinitionVectorOffsetV1 ==
              0x0C);

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

template <std::size_t Size>
bool AssignFixed(std::string_view value,
                 std::array<char, Size> &output) noexcept {
  output.fill('\0');
  if (value.empty() || value.size() >= Size) return false;
  std::copy(value.begin(), value.end(), output.begin());
  return true;
}

bool ValidSnapshotId(std::string_view value) noexcept {
  if (value.empty() ||
      value.size() >= game::kCultureInnovationSnapshotIdCapacityV1) {
    return false;
  }
  for (const char character : value) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= 'A' && character <= 'Z') ||
          (character >= '0' && character <= '9') || character == '_' ||
          character == '-' || character == '.')) {
      return false;
    }
  }
  return true;
}

bool EmptyStableKey(
    const game::CultureInnovationStableKeyV1 &value) noexcept {
  return value.size == 0 && value.bytes[0] == '\0';
}

bool ValidStableKey(
    const game::CultureInnovationStableKeyV1 &value) noexcept {
  if (value.size == 0 ||
      value.size >= game::kCultureInnovationStableKeyCapacityV1 ||
      value.bytes[value.size] != '\0') {
    return false;
  }
  const auto view = CultureInnovationStableKeyViewV1(value);
  if (view.size() != value.size) return false;
  for (const char character : view) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

bool NormalizeStableKey(
    game::CultureInnovationStableKeyV1 &value) noexcept {
  if (!ValidStableKey(value)) return false;
  game::CultureInnovationStableKeyV1 normalized{};
  if (!AssignCultureInnovationStableKeyV1(
          CultureInnovationStableKeyViewV1(value), normalized)) {
    return false;
  }
  value = normalized;
  return true;
}

bool StableKeyLess(const game::CultureInnovationStableKeyV1 &left,
                   const game::CultureInnovationStableKeyV1 &right) noexcept {
  const auto left_view = CultureInnovationStableKeyViewV1(left);
  const auto right_view = CultureInnovationStableKeyViewV1(right);
  return std::lexicographical_compare(
      left_view.begin(), left_view.end(), right_view.begin(), right_view.end(),
      [](char left_byte, char right_byte) {
        return static_cast<unsigned char>(left_byte) <
            static_cast<unsigned char>(right_byte);
      });
}

bool EraExists(const State &state,
               const game::CultureInnovationStableKeyV1 &key) noexcept {
  for (std::uint32_t index = 0; index < state.era_count; ++index) {
    if (state.eras[index].key == key) return true;
  }
  return false;
}

Failure ValidateAndNormalizeState(State &state,
                                  std::int32_t player_character_id) noexcept {
  if (state.culture_id == -1) return Failure::culture_identity_invalid;

  if (state.culture_head_presence == Presence::unknown) {
    return Failure::culture_head_invariant_failed;
  }
  if (state.culture_head_presence == Presence::absent) {
    if (state.culture_head_character_id != -1 ||
        state.is_player_culture_head) {
      return Failure::culture_head_invariant_failed;
    }
  } else if (state.culture_head_presence == Presence::present) {
    if (state.culture_head_character_id == -1 ||
        state.is_player_culture_head !=
            (state.culture_head_character_id == player_character_id)) {
      return Failure::culture_head_invariant_failed;
    }
  } else {
    return Failure::culture_head_invariant_failed;
  }

  if (state.fascination_presence == Presence::unknown) {
    return Failure::fascination_invariant_failed;
  }
  if (state.fascination_presence == Presence::absent) {
    if (!EmptyStableKey(state.current_fascination_key)) {
      return Failure::fascination_invariant_failed;
    }
    state.current_fascination_key = {};
  } else if (state.fascination_presence == Presence::present) {
    if (!NormalizeStableKey(state.current_fascination_key)) {
      return Failure::fascination_invariant_failed;
    }
  } else {
    return Failure::fascination_invariant_failed;
  }

  if (state.era_count == 0 ||
      state.era_count > game::kCultureInnovationMaximumErasV1) {
    return Failure::era_collection_invalid;
  }
  for (std::uint32_t index = 0; index < state.era_count; ++index) {
    auto &era = state.eras[index];
    if (!NormalizeStableKey(era.key)) return Failure::stable_key_invalid;
    if (era.progress_raw < 0) return Failure::progress_invalid;
  }
  std::sort(state.eras.begin(), state.eras.begin() + state.era_count,
            [](const auto &left, const auto &right) {
              return StableKeyLess(left.key, right.key);
            });
  for (std::uint32_t index = 1; index < state.era_count; ++index) {
    if (state.eras[index - 1].key == state.eras[index].key) {
      return Failure::duplicate_stable_key;
    }
  }
  std::fill(state.eras.begin() + state.era_count, state.eras.end(),
            game::CultureInnovationEraV1{});

  if (state.innovation_count == 0 ||
      state.innovation_count >
          game::kCultureInnovationMaximumInnovationsV1) {
    return Failure::innovation_collection_invalid;
  }
  std::uint32_t fascination_count = 0;
  std::uint32_t spread_marker_count = 0;
  for (std::uint32_t index = 0; index < state.innovation_count; ++index) {
    auto &innovation = state.innovations[index];
    if (!NormalizeStableKey(innovation.key) ||
        !NormalizeStableKey(innovation.era_key) ||
        !NormalizeStableKey(innovation.group_key) ||
        !NormalizeStableKey(innovation.skill_key)) {
      return Failure::stable_key_invalid;
    }
    if (!EraExists(state, innovation.era_key)) {
      return Failure::innovation_collection_invalid;
    }
    if (innovation.progress_raw < 0 ||
        innovation.progress_raw >
            kCultureInnovationCompleteFixedPointV1) {
      return Failure::progress_invalid;
    }
    if (innovation.is_fascination) ++fascination_count;
    if (innovation.has_spread_marker) ++spread_marker_count;
  }
  std::sort(state.innovations.begin(),
            state.innovations.begin() + state.innovation_count,
            [](const auto &left, const auto &right) {
              return StableKeyLess(left.key, right.key);
            });
  for (std::uint32_t index = 1; index < state.innovation_count; ++index) {
    if (state.innovations[index - 1].key == state.innovations[index].key) {
      return Failure::duplicate_stable_key;
    }
  }
  std::fill(state.innovations.begin() + state.innovation_count,
            state.innovations.end(), game::CultureInnovationRowV1{});
  if (spread_marker_count > 1) {
    return Failure::innovation_collection_invalid;
  }
  if (state.fascination_presence == Presence::absent) {
    if (fascination_count != 0) {
      return Failure::fascination_invariant_failed;
    }
  } else {
    if (fascination_count != 1) {
      return Failure::fascination_invariant_failed;
    }
    bool matched = false;
    for (std::uint32_t index = 0; index < state.innovation_count; ++index) {
      const auto &innovation = state.innovations[index];
      if (innovation.is_fascination &&
          innovation.key == state.current_fascination_key) {
        matched = true;
        break;
      }
    }
    if (!matched) return Failure::fascination_invariant_failed;
  }
  return Failure::none;
}

bool ValidRequest(
    const CultureInnovationSnapshotRequestV1 &request) noexcept {
  return ValidSnapshotId(request.expected_snapshot_id) &&
      request.expected_public_revision != 0 &&
      request.expected_native_revision != 0 &&
      request.expected_player_character_id != -1;
}

Failure ValidateInitialFrame(
    const CultureInnovationSnapshotFrameV1 &frame,
    const CultureInnovationSnapshotRequestV1 &request) noexcept {
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
      !frame.played_character_alive || frame.played_character_id == -1 ||
      frame.played_character == 0 ||
      !frame.played_character_identity_round_trip ||
      frame.played_character_id != request.expected_player_character_id) {
    return Failure::player_unavailable;
  }
  return Failure::none;
}

Failure ClassifyFrameDrift(const CultureInnovationSnapshotFrameV1 &before,
                           const CultureInnovationSnapshotFrameV1 &after) noexcept {
  if (FixedString(before.snapshot_id) != FixedString(after.snapshot_id)) {
    return Failure::snapshot_identity_mismatch;
  }
  if (before.public_revision != after.public_revision ||
      before.native_revision != after.native_revision ||
      before.proof_epoch != after.proof_epoch) {
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
  return Failure::none;
}

void ClearUnavailable(Snapshot &output, Failure reason) noexcept {
  output = {};
  output.status = game::CultureInnovationSnapshotStatusV1::unavailable;
  output.unavailable_reason = reason;
}

void Publish(const CultureInnovationSnapshotFrameV1 &frame,
             const CultureInnovationSourceSampleV1 &sample,
             Snapshot &output) noexcept {
  output = {};
  output.status = game::CultureInnovationSnapshotStatusV1::available;
  output.unavailable_reason = Failure::none;
  (void)AssignFixed(FixedString(frame.snapshot_id), output.snapshot_id);
  (void)AssignFixed(kCultureInnovationSnapshotGameVersionV1,
                    output.game_build);
  (void)AssignFixed(kCultureInnovationSnapshotExecutableSha256V1,
                    output.executable_sha256);
  output.public_revision = frame.public_revision;
  output.native_revision = frame.native_revision;
  output.proof_epoch = frame.proof_epoch;
  output.date_raw = frame.date_raw;
  output.player_character_id = frame.played_character_id;
  output.state = sample.state;
  output.readiness.culture_identity_ready = true;
  output.readiness.culture_head_ready = true;
  output.readiness.fascination_ready = true;
  output.readiness.era_collection_ready = true;
  output.readiness.innovation_collection_ready = true;
  output.readiness.same_frame_ready = true;
}

} // namespace

bool AssignCultureInnovationStableKeyV1(
    std::string_view value,
    game::CultureInnovationStableKeyV1 &output) noexcept {
  output = {};
  if (value.empty() ||
      value.size() >= game::kCultureInnovationStableKeyCapacityV1) {
    return false;
  }
  for (const char character : value) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  output.size = static_cast<std::uint16_t>(value.size());
  std::copy(value.begin(), value.end(), output.bytes.begin());
  return true;
}

std::string_view CultureInnovationStableKeyViewV1(
    const game::CultureInnovationStableKeyV1 &value) noexcept {
  if (value.size >= value.bytes.size() || value.bytes[value.size] != '\0') {
    return {};
  }
  return {value.bytes.data(), value.size};
}

game::ReadCultureInnovationSnapshotResultV1 ReadCultureInnovationSnapshotV1(
    const CultureInnovationSnapshotEnvironmentV1 &environment,
    const CultureInnovationSnapshotAccessV1 &access,
    const CultureInnovationSnapshotRequestV1 &request,
    game::CultureInnovationSnapshotV1 &output) noexcept {
  ClearUnavailable(output, Failure::invalid_request);
  if (!ValidRequest(request)) return Result::unavailable;
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kCultureInnovationSnapshotExecutableSha256V1) {
    ClearUnavailable(output, Failure::exact_build_not_admitted);
    return Result::unavailable;
  }
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      access.read_source == nullptr ||
      (environment.offline_fixture ? environment.module_base != 0
                                   : environment.module_base == 0)) {
    ClearUnavailable(output, Failure::native_bindings_unavailable);
    return Result::unavailable;
  }
  if (!access.is_main_thread(access.context)) {
    ClearUnavailable(output, Failure::application_main_thread_required);
    return Result::unavailable;
  }

  try {
    CultureInnovationSnapshotFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      ClearUnavailable(output, Failure::frame_capture_failed);
      return Result::unavailable;
    }
    const auto initial_failure = ValidateInitialFrame(before, request);
    if (initial_failure != Failure::none) {
      ClearUnavailable(output, initial_failure);
      return Result::unavailable;
    }

    CultureInnovationSourceSampleV1 first{};
    CultureInnovationSourceSampleV1 second{};
    if (!access.read_source(access.context, before.played_character, first) ||
        !access.read_source(access.context, before.played_character, second)) {
      ClearUnavailable(output, Failure::native_source_read_failed);
      return Result::unavailable;
    }
    if (first.player_character_id != before.played_character_id ||
        second.player_character_id != before.played_character_id ||
        !first.player_identity_round_trip ||
        !second.player_identity_round_trip) {
      ClearUnavailable(output, Failure::player_unavailable);
      return Result::unavailable;
    }
    const auto first_failure =
        ValidateAndNormalizeState(first.state, before.played_character_id);
    if (first_failure != Failure::none) {
      ClearUnavailable(output, first_failure);
      return Result::unavailable;
    }
    const auto second_failure =
        ValidateAndNormalizeState(second.state, before.played_character_id);
    if (second_failure != Failure::none) {
      ClearUnavailable(output, second_failure);
      return Result::unavailable;
    }
    if (first != second) {
      ClearUnavailable(output, Failure::native_sample_drift);
      return Result::unavailable;
    }

    CultureInnovationSnapshotFrameV1 after{};
    if (!access.capture_frame(access.context, after)) {
      ClearUnavailable(output, Failure::frame_capture_failed);
      return Result::unavailable;
    }
    const auto drift = ClassifyFrameDrift(before, after);
    if (drift != Failure::none) {
      ClearUnavailable(output, drift);
      return Result::unavailable;
    }
    Publish(before, first, output);
    return Result::available;
  } catch (...) {
    ClearUnavailable(output, Failure::native_source_read_failed);
    return Result::unavailable;
  }
}

std::string_view CultureInnovationSnapshotFailureKeyV1(
    game::CultureInnovationSnapshotFailureV1 reason) noexcept {
  using enum game::CultureInnovationSnapshotFailureV1;
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
  case native_source_read_failed: return "native_source_read_failed";
  case culture_identity_invalid: return "culture_identity_invalid";
  case culture_head_invariant_failed:
    return "culture_head_invariant_failed";
  case fascination_invariant_failed:
    return "fascination_invariant_failed";
  case era_collection_invalid: return "era_collection_invalid";
  case innovation_collection_invalid:
    return "innovation_collection_invalid";
  case stable_key_invalid: return "stable_key_invalid";
  case progress_invalid: return "progress_invalid";
  case duplicate_stable_key: return "duplicate_stable_key";
  case native_sample_drift: return "native_sample_drift";
  }
  return "unknown";
}

} // namespace xar::ck3_11906
