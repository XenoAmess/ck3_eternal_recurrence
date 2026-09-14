#include "xar_bridge/player_lifestyle_window_candidates_v1.hpp"

#include <algorithm>
#include <limits>

namespace xar::ck3_11906 {
namespace {

using Failure = game::PlayerLifestyleWindowCandidatesFailureV1;
using Result = game::ReadPlayerLifestyleWindowCandidatesResultV1;
using SourceResult = PlayerLifestyleWindowSourceReadResultV1;

static_assert(sizeof(void *) == 8,
              "player lifestyle window observer is x64-only");

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
      value.size() >= game::kPlayerLifestyleWindowSnapshotIdCapacityV1) {
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

bool ValidStableKey(
    const game::PlayerLifestyleWindowStableKeyV1 &value) noexcept {
  if (value.size == 0 ||
      value.size >= game::kPlayerLifestyleWindowStableKeyCapacityV1 ||
      value.bytes[value.size] != '\0') {
    return false;
  }
  const auto view = PlayerLifestyleWindowStableKeyViewV1(value);
  if (view.size() != value.size) return false;
  for (const char character : view) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

bool StableKeyLess(
    const game::PlayerLifestyleWindowStableKeyV1 &left,
    const game::PlayerLifestyleWindowStableKeyV1 &right) noexcept {
  const auto left_view = PlayerLifestyleWindowStableKeyViewV1(left);
  const auto right_view = PlayerLifestyleWindowStableKeyViewV1(right);
  return std::lexicographical_compare(
      left_view.begin(), left_view.end(), right_view.begin(), right_view.end(),
      [](char left_byte, char right_byte) {
        return static_cast<unsigned char>(left_byte) <
            static_cast<unsigned char>(right_byte);
      });
}

bool ValidRequest(
    const PlayerLifestyleWindowCandidatesRequestV1 &request) noexcept {
  return ValidSnapshotId(request.expected_snapshot_id) &&
      request.expected_public_revision != 0 &&
      request.expected_native_revision != 0 &&
      request.expected_player_character_id != 0xFFFFFFFFU;
}

Failure ValidateInitialFrame(
    const PlayerLifestyleWindowFrameV1 &frame,
    const PlayerLifestyleWindowCandidatesRequestV1 &request) noexcept {
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
      !frame.played_character_alive ||
      frame.played_character_id == 0xFFFFFFFFU ||
      frame.played_character == 0 ||
      !frame.played_character_identity_round_trip ||
      frame.played_character_id != request.expected_player_character_id) {
    return Failure::player_unavailable;
  }
  return Failure::none;
}

Failure ClassifyFrameDrift(const PlayerLifestyleWindowFrameV1 &before,
                           const PlayerLifestyleWindowFrameV1 &after) noexcept {
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

bool AddRva(std::uintptr_t module_base, std::uintptr_t rva,
            std::uintptr_t &output) noexcept {
  if (module_base == 0 ||
      module_base > std::numeric_limits<std::uintptr_t>::max() - rva) {
    output = 0;
    return false;
  }
  output = module_base + rva;
  return true;
}

bool ValidSpan(const PlayerLifestyleWindowSpanV1 &span,
               std::size_t expected_element_bytes) noexcept {
  if (span.capacity < 0 || span.count < 0 || span.count > span.capacity ||
      span.element_bytes != expected_element_bytes) {
    return false;
  }
  if (span.count == 0) return true;
  if (span.data == 0 || !span.complete_range_readable) return false;
  const auto count = static_cast<std::uintptr_t>(span.count);
  const auto element = static_cast<std::uintptr_t>(span.element_bytes);
  return count <= std::numeric_limits<std::uintptr_t>::max() / element &&
      span.data <= std::numeric_limits<std::uintptr_t>::max() -
                       count * element;
}

Failure ValidateOwner(
    const PlayerLifestyleWindowSourceSampleV1 &sample,
    const PlayerLifestyleWindowCandidatesEnvironmentV1 &environment,
    std::uint32_t current_player) noexcept {
  std::uintptr_t handler_vtable = 0;
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
  if (!AddRva(environment.module_base, kLifestyleWindowHandlerVtableRvaV1,
              handler_vtable) ||
      !AddRva(environment.module_base, kLifestyleWindowPrimaryVtableRvaV1,
              primary_vtable) ||
      !AddRva(environment.module_base, kLifestyleWindowSecondaryVtableRvaV1,
              secondary_vtable)) {
    return Failure::native_bindings_unavailable;
  }
  if (sample.root_acquisition_serial == 0 || sample.root == 0 ||
      sample.idler_base == 0 || sample.idler_gfx == 0 ||
      !sample.idler_exact_rtti_cast || sample.handler == 0 ||
      sample.window == 0 || sample.handler_vtable != handler_vtable ||
      sample.window_primary_vtable != primary_vtable ||
      sample.window_secondary_vtable != secondary_vtable ||
      sample.window_owner_round_trip != sample.handler) {
    return Failure::owner_path_invalid;
  }
  if (sample.bound_character_id != current_player ||
      !sample.character_storage_round_trip) {
    return Failure::lifestyle_window_unbound_or_stale;
  }
  return Failure::none;
}

Failure ValidateContainers(
    const PlayerLifestyleWindowSourceSampleV1 &sample) noexcept {
  if (!ValidSpan(sample.lifestyles,
                 kLifestyleWindowPointerSpanElementBytesV1) ||
      !ValidSpan(sample.perk_trees, kLifestyleWindowPerkTreeRowBytesV1) ||
      !ValidSpan(sample.focuses, kLifestyleWindowPointerSpanElementBytesV1) ||
      sample.focus_count > game::kPlayerLifestyleWindowMaximumFocusesV1 ||
      sample.perk_count > game::kPlayerLifestyleWindowMaximumPerksV1 ||
      sample.focus_count != static_cast<std::uint32_t>(sample.focuses.count)) {
    return Failure::invalid_container;
  }
  if (!sample.perk_database_fully_materialized) {
    return Failure::materialization_unavailable;
  }
  return Failure::none;
}

Failure ValidateCandidates(
    const PlayerLifestyleWindowSourceSampleV1 &sample) noexcept {
  for (std::uint32_t index = 0; index < sample.focus_count; ++index) {
    const auto &row = sample.focus_rows[index];
    if (row.definition == 0 || !row.pointer_in_captured_focus_span ||
        !row.stable_key_round_trip) {
      return Failure::candidate_provenance_invalid;
    }
    if (!ValidStableKey(row.key) || !ValidStableKey(row.lifestyle_key)) {
      return Failure::stable_key_invalid;
    }
    if (!row.final_evaluator_invoked) {
      return Failure::final_legality_evaluator_unavailable;
    }
    for (std::uint32_t previous = 0; previous < index; ++previous) {
      if (sample.focus_rows[previous].key == row.key) {
        return Failure::duplicate_stable_key;
      }
    }
  }
  for (std::uint32_t index = 0; index < sample.perk_count; ++index) {
    const auto &row = sample.perk_rows[index];
    if (row.definition == 0 || !row.pointer_in_exact_perk_database ||
        !row.stable_key_round_trip) {
      return Failure::candidate_provenance_invalid;
    }
    if (!ValidStableKey(row.key) || !ValidStableKey(row.lifestyle_key)) {
      return Failure::stable_key_invalid;
    }
    if (!row.final_evaluator_invoked ||
        !row.ignore_cost_evaluator_invoked) {
      return Failure::final_legality_evaluator_unavailable;
    }
    for (std::uint32_t previous = 0; previous < index; ++previous) {
      if (sample.perk_rows[previous].key == row.key) {
        return Failure::duplicate_stable_key;
      }
    }
  }
  return Failure::none;
}

Failure MapSourceResult(SourceResult result) noexcept {
  switch (result) {
  case SourceResult::success: return Failure::none;
  case SourceResult::owner_path_unavailable:
    return Failure::owner_path_unavailable;
  case SourceResult::invalid_container: return Failure::invalid_container;
  case SourceResult::materialization_unavailable:
    return Failure::materialization_unavailable;
  case SourceResult::final_legality_evaluator_unavailable:
    return Failure::final_legality_evaluator_unavailable;
  case SourceResult::source_read_failed:
    return Failure::native_source_read_failed;
  }
  return Failure::native_source_read_failed;
}

bool EquivalentSamples(const PlayerLifestyleWindowSourceSampleV1 &left,
                       const PlayerLifestyleWindowSourceSampleV1 &right) noexcept {
  if (left.root != right.root || left.idler_base != right.idler_base ||
      left.idler_gfx != right.idler_gfx ||
      left.idler_exact_rtti_cast != right.idler_exact_rtti_cast ||
      left.handler != right.handler ||
      left.handler_vtable != right.handler_vtable ||
      left.window != right.window ||
      left.window_primary_vtable != right.window_primary_vtable ||
      left.window_secondary_vtable != right.window_secondary_vtable ||
      left.window_owner_round_trip != right.window_owner_round_trip ||
      left.bound_character_id != right.bound_character_id ||
      left.character_storage_round_trip !=
          right.character_storage_round_trip ||
      left.lifestyles != right.lifestyles ||
      left.perk_trees != right.perk_trees || left.focuses != right.focuses ||
      left.perk_database_fully_materialized !=
          right.perk_database_fully_materialized ||
      left.focus_count != right.focus_count ||
      left.perk_count != right.perk_count) {
    return false;
  }
  for (std::uint32_t index = 0; index < left.focus_count; ++index) {
    if (left.focus_rows[index] != right.focus_rows[index]) return false;
  }
  for (std::uint32_t index = 0; index < left.perk_count; ++index) {
    if (left.perk_rows[index] != right.perk_rows[index]) return false;
  }
  return true;
}

void ClearUnavailable(game::PlayerLifestyleWindowCandidatesV1 &output,
                      Failure reason) noexcept {
  output = {};
  output.status = game::PlayerLifestyleWindowCandidatesStatusV1::unavailable;
  output.unavailable_reason = reason;
  output.focus_status =
      game::PlayerLifestyleWindowCollectionStatusV1::unavailable;
  output.perk_status =
      game::PlayerLifestyleWindowCollectionStatusV1::unavailable;
}

void Publish(const PlayerLifestyleWindowFrameV1 &frame,
             const PlayerLifestyleWindowSourceSampleV1 &sample,
             game::PlayerLifestyleWindowCandidatesV1 &output) noexcept {
  output = {};
  output.status = game::PlayerLifestyleWindowCandidatesStatusV1::available;
  output.unavailable_reason = Failure::none;
  (void)AssignFixed(FixedString(frame.snapshot_id), output.snapshot_id);
  output.public_revision = frame.public_revision;
  output.native_revision = frame.native_revision;
  output.proof_epoch = frame.proof_epoch;
  output.date_raw = frame.date_raw;
  output.player_character_id = frame.played_character_id;

  output.focus_count = sample.focus_count;
  for (std::uint32_t index = 0; index < sample.focus_count; ++index) {
    output.focuses[index] = {
        sample.focus_rows[index].key,
        sample.focus_rows[index].lifestyle_key,
        sample.focus_rows[index].can_select};
  }
  std::sort(output.focuses.begin(),
            output.focuses.begin() + output.focus_count,
            [](const auto &left, const auto &right) {
              return StableKeyLess(left.key, right.key);
            });
  output.focus_status = output.focus_count == 0
      ? game::PlayerLifestyleWindowCollectionStatusV1::known_empty
      : game::PlayerLifestyleWindowCollectionStatusV1::available;

  output.perk_count = sample.perk_count;
  for (std::uint32_t index = 0; index < sample.perk_count; ++index) {
    output.perks[index] = {
        sample.perk_rows[index].key,
        sample.perk_rows[index].lifestyle_key,
        sample.perk_rows[index].can_select,
        sample.perk_rows[index].can_select_ignore_cost};
  }
  std::sort(output.perks.begin(), output.perks.begin() + output.perk_count,
            [](const auto &left, const auto &right) {
              return StableKeyLess(left.key, right.key);
            });
  output.perk_status = output.perk_count == 0
      ? game::PlayerLifestyleWindowCollectionStatusV1::known_empty
      : game::PlayerLifestyleWindowCollectionStatusV1::available;

  output.readiness.owner_path_ready = true;
  output.readiness.bound_player_ready = true;
  output.readiness.containers_ready = true;
  output.readiness.focus_candidates_ready = true;
  output.readiness.perk_candidates_ready = true;
  output.readiness.final_legality_ready = true;
  output.readiness.same_frame_ready = true;
}

} // namespace

bool AssignPlayerLifestyleWindowStableKeyV1(
    std::string_view value,
    game::PlayerLifestyleWindowStableKeyV1 &output) noexcept {
  output = {};
  if (value.empty() ||
      value.size() >= game::kPlayerLifestyleWindowStableKeyCapacityV1) {
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

std::string_view PlayerLifestyleWindowStableKeyViewV1(
    const game::PlayerLifestyleWindowStableKeyV1 &value) noexcept {
  if (value.size == 0 || value.size >= value.bytes.size() ||
      value.bytes[value.size] != '\0') {
    return {};
  }
  return {value.bytes.data(), value.size};
}

game::ReadPlayerLifestyleWindowCandidatesResultV1
ReadPlayerLifestyleWindowCandidatesV1(
    const PlayerLifestyleWindowCandidatesEnvironmentV1 &environment,
    const PlayerLifestyleWindowCandidatesAccessV1 &access,
    const PlayerLifestyleWindowCandidatesRequestV1 &request,
    game::PlayerLifestyleWindowCandidatesV1 &output) noexcept {
  ClearUnavailable(output, Failure::invalid_request);
  if (!ValidRequest(request)) return Result::unavailable;
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kPlayerLifestyleWindowCandidatesExecutableSha256V1) {
    ClearUnavailable(output, Failure::exact_build_not_admitted);
    return Result::unavailable;
  }
  if (environment.module_base == 0 || access.capture_frame == nullptr ||
      access.is_main_thread == nullptr || access.read_source == nullptr) {
    ClearUnavailable(output, Failure::native_bindings_unavailable);
    return Result::unavailable;
  }
  if (!access.is_main_thread(access.context)) {
    ClearUnavailable(output, Failure::application_main_thread_required);
    return Result::unavailable;
  }

  try {
    PlayerLifestyleWindowFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      ClearUnavailable(output, Failure::frame_capture_failed);
      return Result::unavailable;
    }
    const auto initial_failure = ValidateInitialFrame(before, request);
    if (initial_failure != Failure::none) {
      ClearUnavailable(output, initial_failure);
      return Result::unavailable;
    }

    PlayerLifestyleWindowSourceSampleV1 first{};
    PlayerLifestyleWindowSourceSampleV1 second{};
    const auto first_read = access.read_source(
        access.context, environment.module_base, before.played_character_id,
        first);
    if (const auto failure = MapSourceResult(first_read);
        failure != Failure::none) {
      ClearUnavailable(output, failure);
      return Result::unavailable;
    }
    const auto first_owner =
        ValidateOwner(first, environment, before.played_character_id);
    if (first_owner != Failure::none) {
      ClearUnavailable(output, first_owner);
      return Result::unavailable;
    }
    if (const auto failure = ValidateContainers(first);
        failure != Failure::none) {
      ClearUnavailable(output, failure);
      return Result::unavailable;
    }
    if (const auto failure = ValidateCandidates(first);
        failure != Failure::none) {
      ClearUnavailable(output, failure);
      return Result::unavailable;
    }

    const auto second_read = access.read_source(
        access.context, environment.module_base, before.played_character_id,
        second);
    if (const auto failure = MapSourceResult(second_read);
        failure != Failure::none) {
      ClearUnavailable(output, failure);
      return Result::unavailable;
    }
    const auto second_owner =
        ValidateOwner(second, environment, before.played_character_id);
    if (second_owner != Failure::none) {
      ClearUnavailable(output, second_owner);
      return Result::unavailable;
    }
    if (const auto failure = ValidateContainers(second);
        failure != Failure::none) {
      ClearUnavailable(output, failure);
      return Result::unavailable;
    }
    if (const auto failure = ValidateCandidates(second);
        failure != Failure::none) {
      ClearUnavailable(output, failure);
      return Result::unavailable;
    }
    if (second.root_acquisition_serial <= first.root_acquisition_serial) {
      ClearUnavailable(output, Failure::root_reacquisition_not_proven);
      return Result::unavailable;
    }
    if (!EquivalentSamples(first, second)) {
      ClearUnavailable(output, Failure::native_sample_drift);
      return Result::unavailable;
    }

    PlayerLifestyleWindowFrameV1 after{};
    if (!access.capture_frame(access.context, after)) {
      ClearUnavailable(output, Failure::frame_capture_failed);
      return Result::unavailable;
    }
    const auto frame_failure = ClassifyFrameDrift(before, after);
    if (frame_failure != Failure::none) {
      ClearUnavailable(output, frame_failure);
      return Result::unavailable;
    }
    Publish(before, first, output);
    return Result::available;
  } catch (...) {
    ClearUnavailable(output, Failure::native_source_read_failed);
    return Result::unavailable;
  }
}

std::string_view PlayerLifestyleWindowCandidatesFailureKeyV1(
    game::PlayerLifestyleWindowCandidatesFailureV1 reason) noexcept {
  using enum game::PlayerLifestyleWindowCandidatesFailureV1;
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
  case owner_path_unavailable: return "owner_path_unavailable";
  case owner_path_invalid: return "owner_path_invalid";
  case lifestyle_window_unbound_or_stale:
    return "lifestyle_window_unbound_or_stale";
  case invalid_container: return "invalid_container";
  case materialization_unavailable: return "materialization_unavailable";
  case final_legality_evaluator_unavailable:
    return "final_legality_evaluator_unavailable";
  case candidate_provenance_invalid:
    return "candidate_provenance_invalid";
  case stable_key_invalid: return "stable_key_invalid";
  case duplicate_stable_key: return "duplicate_stable_key";
  case root_reacquisition_not_proven:
    return "root_reacquisition_not_proven";
  case native_sample_drift: return "native_sample_drift";
  case native_source_read_failed: return "native_source_read_failed";
  }
  return "unknown";
}

} // namespace xar::ck3_11906
