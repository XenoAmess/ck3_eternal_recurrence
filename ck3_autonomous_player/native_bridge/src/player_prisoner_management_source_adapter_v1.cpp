#include "xar_bridge/player_prisoner_management_source_adapter_v1.hpp"

#include <algorithm>
#include <array>
#include <memory>
#include <new>
#include <type_traits>

namespace xar::bridge {
namespace {

using CoreFailure = PlayerPrisonerSnapshotFailureV1;
using Failure = PlayerPrisonerSourceAdapterFailureV1;
using Result = PlayerPrisonerSourceResultV1;

struct ResolvedSourceV1 {
  PlayerPrisonerSourcePlayerLeaseV1 player{};
  PlayerPrisonerSourceCollectorLeaseV1 collector{};
};

struct RowFingerprintV1 {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
  std::int32_t prisoner_character_id = -1;
  std::int32_t jailer_character_id = -1;
  bool alive = false;
  PlayerPrisonerCustodyKindV1 custody =
      PlayerPrisonerCustodyKindV1::unknown;
  std::int64_t time_imprisoned_days = -1;
};

void Fail(Result &output, Failure failure,
          CoreFailure core_failure =
              CoreFailure::source_adapter_unavailable) noexcept {
  output = {};
  output.failure = failure;
  output.core_failure = core_failure;
  output.snapshot.status = PlayerPrisonerSnapshotStatusV1::unavailable;
  output.snapshot.unavailable_reason = core_failure;
  output.snapshot.played_character_id = -1;
}

bool CallbacksComplete(const PlayerPrisonerSourceAccessV1 &access) noexcept {
  return access.capture_frame != nullptr && access.resolve_player != nullptr &&
         access.resolve_collector != nullptr &&
         access.read_prisoner != nullptr &&
         access.read_native_reasons != nullptr &&
         access.read_ransom_preview != nullptr &&
         access.read_interaction_preview != nullptr;
}

bool ValidFrame(const PlayerPrisonerFrameV1 &frame) noexcept {
  return frame.public_revision != 0 && frame.native_revision != 0 &&
         frame.proof_epoch != 0 && frame.paused && frame.map_ready &&
         frame.played_character_id > 0 && frame.played_character_alive &&
         frame.played_character_identity_round_trip;
}

bool ValidPlayer(const PlayerPrisonerSourcePlayerLeaseV1 &player,
                 std::int32_t expected_character_id) noexcept {
  return player.identity_round_trip && player.native_address != 0 &&
         player.identity != 0 && player.generation != 0 && player.alive &&
         player.character_id == expected_character_id;
}

Failure ComparePlayer(const PlayerPrisonerSourcePlayerLeaseV1 &first,
                      const PlayerPrisonerSourcePlayerLeaseV1 &second) noexcept {
  if (first.identity_round_trip != second.identity_round_trip ||
      first.native_address != second.native_address ||
      first.identity != second.identity ||
      first.character_id != second.character_id) {
    return Failure::player_identity_drift;
  }
  if (first.generation != second.generation) {
    return Failure::player_lifecycle_drift;
  }
  return first.alive == second.alive ? Failure::none
                                    : Failure::source_sample_drift;
}

Failure ValidateCollector(
    const PlayerPrisonerSourceCollectorLeaseV1 &collector,
    std::int32_t expected_owner) noexcept {
  if (!collector.identity_round_trip || collector.native_address == 0 ||
      collector.identity == 0 || collector.generation == 0 ||
      collector.owner_character_id != expected_owner) {
    return Failure::collector_unavailable;
  }
  if (!collector.complete) return Failure::collector_incomplete;
  if (collector.row_count > kPlayerPrisonerMaximumRowsV1 ||
      collector.total_count != collector.row_count) {
    return Failure::collector_count_invalid;
  }
  return Failure::none;
}

Failure CompareCollector(
    const PlayerPrisonerSourceCollectorLeaseV1 &first,
    const PlayerPrisonerSourceCollectorLeaseV1 &second) noexcept {
  if (first.identity_round_trip != second.identity_round_trip ||
      first.native_address != second.native_address ||
      first.identity != second.identity ||
      first.owner_character_id != second.owner_character_id) {
    return Failure::collector_identity_drift;
  }
  if (first.generation != second.generation) {
    return Failure::collector_lifecycle_drift;
  }
  return first.complete == second.complete &&
                 first.total_count == second.total_count &&
                 first.row_count == second.row_count
             ? Failure::none
             : Failure::source_sample_drift;
}

bool ValidRow(const PlayerPrisonerSourceRowLeaseV1 &row,
              std::int32_t expected_jailer) noexcept {
  return row.identity_round_trip && row.native_address != 0 &&
         row.identity != 0 && row.generation != 0 &&
         row.prisoner_character_id > 0 &&
         row.prisoner_character_id != expected_jailer &&
         row.jailer_character_id == expected_jailer && row.alive &&
         row.custody != PlayerPrisonerCustodyKindV1::unknown &&
         row.time_imprisoned_days >= 0;
}

RowFingerprintV1 Fingerprint(
    const PlayerPrisonerSourceRowLeaseV1 &row) noexcept {
  return {row.identity_round_trip,
          row.native_address,
          row.identity,
          row.generation,
          row.prisoner_character_id,
          row.jailer_character_id,
          row.alive,
          row.custody,
          row.time_imprisoned_days};
}

Failure CompareRow(const RowFingerprintV1 &first,
                   const RowFingerprintV1 &second) noexcept {
  if (first.identity_round_trip != second.identity_round_trip ||
      first.native_address != second.native_address ||
      first.identity != second.identity ||
      first.prisoner_character_id != second.prisoner_character_id ||
      first.jailer_character_id != second.jailer_character_id) {
    return Failure::prisoner_identity_drift;
  }
  if (first.generation != second.generation) {
    return Failure::prisoner_lifecycle_drift;
  }
  return first.alive == second.alive && first.custody == second.custody &&
                 first.time_imprisoned_days == second.time_imprisoned_days
             ? Failure::none
             : Failure::source_sample_drift;
}

Failure ResolveSource(const PlayerPrisonerSourceAccessV1 &access,
                      std::int32_t played_character_id,
                      ResolvedSourceV1 &output) noexcept {
  output = {};
  if (!access.resolve_player(access.context, played_character_id,
                             output.player) ||
      !ValidPlayer(output.player, played_character_id)) {
    return Failure::player_unavailable;
  }
  if (!access.resolve_collector(access.context, output.player,
                                output.collector)) {
    return Failure::collector_unavailable;
  }
  return ValidateCollector(output.collector, played_character_id);
}

PlayerPrisonerInteractionPreviewV1 *PreviewDestination(
    PlayerPrisonerRowV1 &row,
    PlayerPrisonerSourcePreviewKindV1 kind) noexcept {
  switch (kind) {
  case PlayerPrisonerSourcePreviewKindV1::release_unconditional:
    return &row.release_unconditional;
  case PlayerPrisonerSourcePreviewKindV1::execute:
    return &row.execute;
  case PlayerPrisonerSourcePreviewKindV1::move_to_dungeon:
    return &row.move_to_dungeon;
  case PlayerPrisonerSourcePreviewKindV1::move_to_house_arrest:
    return &row.move_to_house_arrest;
  case PlayerPrisonerSourcePreviewKindV1::torture:
    return &row.torture;
  }
  return nullptr;
}

Failure ReadSample(
    const PlayerPrisonerSourceAccessV1 &access,
    const ResolvedSourceV1 &source, PlayerPrisonerSourceSampleV1 &sample,
    std::array<RowFingerprintV1, kPlayerPrisonerMaximumRowsV1> &fingerprints,
    bool require_matching_fingerprints) noexcept {
  sample = {};
  sample.played_character_id = source.player.character_id;
  sample.played_character_identity_round_trip =
      source.player.identity_round_trip;
  sample.total_prisoner_count = source.collector.total_count;
  sample.prisoner_count = source.collector.row_count;

  constexpr std::array<PlayerPrisonerSourcePreviewKindV1, 5> kinds{
      PlayerPrisonerSourcePreviewKindV1::release_unconditional,
      PlayerPrisonerSourcePreviewKindV1::execute,
      PlayerPrisonerSourcePreviewKindV1::move_to_dungeon,
      PlayerPrisonerSourcePreviewKindV1::move_to_house_arrest,
      PlayerPrisonerSourcePreviewKindV1::torture};

  for (std::size_t index = 0; index < source.collector.row_count; ++index) {
    PlayerPrisonerSourceRowLeaseV1 lease{};
    if (!access.read_prisoner(access.context, source.player,
                              source.collector, index, lease)) {
      return Failure::prisoner_unavailable;
    }
    if (!ValidRow(lease, source.player.character_id)) {
      return Failure::prisoner_identity_invalid;
    }
    const auto fingerprint = Fingerprint(lease);
    if (require_matching_fingerprints) {
      const auto failure = CompareRow(fingerprints[index], fingerprint);
      if (failure != Failure::none) return failure;
    } else {
      fingerprints[index] = fingerprint;
    }

    auto &row = sample.prisoners[index];
    row.prisoner_character_id = lease.prisoner_character_id;
    row.jailer_character_id = lease.jailer_character_id;
    row.prisoner_identity_round_trip = lease.identity_round_trip;
    row.prisoner_alive = lease.alive;
    row.custody = lease.custody;
    row.time_imprisoned_days = lease.time_imprisoned_days;

    PlayerPrisonerSourceNativeReasonsV1 reasons{};
    if (!access.read_native_reasons(access.context, source.player, lease,
                                    reasons)) {
      return Failure::native_reason_unavailable;
    }
    row.has_imprisonment_reason = reasons.has_imprisonment_reason;
    row.has_banish_reason = reasons.has_banish_reason;
    row.has_execute_reason = reasons.has_execute_reason;

    if (!access.read_ransom_preview(access.context, source.player, lease,
                                    row.ransom)) {
      return Failure::ransom_preview_unavailable;
    }
    for (const auto kind : kinds) {
      auto *const preview = PreviewDestination(row, kind);
      if (preview == nullptr ||
          !access.read_interaction_preview(access.context, source.player,
                                           lease, kind, *preview)) {
        return Failure::interaction_preview_unavailable;
      }
    }
  }
  sample.prisoner_collection_complete = true;
  sample.source_read_complete = true;
  return Failure::none;
}

CoreFailure CoreFailureForAdapterFailure(Failure failure) noexcept {
  switch (failure) {
  case Failure::exact_build_mismatch:
    return CoreFailure::exact_build_mismatch;
  case Failure::application_main_thread_required:
    return CoreFailure::application_main_thread_required;
  case Failure::not_paused:
    return CoreFailure::not_paused;
  case Failure::frame_invalid:
  case Failure::player_unavailable:
    return CoreFailure::played_character_unavailable;
  case Failure::collector_incomplete:
    return CoreFailure::prisoner_collection_incomplete;
  case Failure::collector_count_invalid:
    return CoreFailure::prisoner_count_invalid;
  case Failure::prisoner_identity_invalid:
    return CoreFailure::prisoner_identity_invalid;
  case Failure::player_identity_drift:
  case Failure::player_lifecycle_drift:
    return CoreFailure::player_identity_mismatch;
  case Failure::collector_identity_drift:
  case Failure::collector_lifecycle_drift:
  case Failure::prisoner_identity_drift:
  case Failure::prisoner_lifecycle_drift:
  case Failure::source_sample_drift:
    return CoreFailure::source_sample_drift;
  case Failure::frame_drift:
    return CoreFailure::frame_drift;
  default:
    return CoreFailure::source_adapter_unavailable;
  }
}

} // namespace

static_assert(std::is_trivially_copyable_v<PlayerPrisonerSourcePlayerLeaseV1>);
static_assert(
    std::is_trivially_copyable_v<PlayerPrisonerSourceCollectorLeaseV1>);
static_assert(std::is_trivially_copyable_v<PlayerPrisonerSourceRowLeaseV1>);

bool ObservePlayerPrisonerManagementSourceV1(
    const PlayerPrisonerSourceAccessV1 &access,
    PlayerPrisonerSourceResultV1 &output) noexcept {
  Fail(output, Failure::callbacks_unavailable);
  if (!access.exact_build_admitted ||
      access.admitted_executable_sha256 !=
          kPlayerPrisonerManagementSnapshotV1ExecutableSha256) {
    Fail(output, Failure::exact_build_mismatch,
         CoreFailure::exact_build_mismatch);
    return false;
  }
  if (!CallbacksComplete(access)) return false;
  if (access.current_thread_id == 0 ||
      access.current_thread_id != access.application_main_thread_id) {
    Fail(output, Failure::application_main_thread_required,
         CoreFailure::application_main_thread_required);
    return false;
  }

  std::unique_ptr<PlayerPrisonerCaptureV1> capture{
      new (std::nothrow) PlayerPrisonerCaptureV1{}};
  if (!capture) {
    Fail(output, Failure::working_storage_unavailable);
    return false;
  }
  if (!access.capture_frame(access.context, capture->frame_before)) {
    Fail(output, Failure::frame_unavailable);
    return false;
  }
  if (!capture->frame_before.paused) {
    Fail(output, Failure::not_paused, CoreFailure::not_paused);
    return false;
  }
  if (!ValidFrame(capture->frame_before)) {
    Fail(output, Failure::frame_invalid,
         CoreFailure::played_character_unavailable);
    return false;
  }

  ResolvedSourceV1 first_source{};
  auto failure = ResolveSource(access,
                               capture->frame_before.played_character_id,
                               first_source);
  if (failure != Failure::none) {
    Fail(output, failure, CoreFailureForAdapterFailure(failure));
    return false;
  }
  std::array<RowFingerprintV1, kPlayerPrisonerMaximumRowsV1>
      fingerprints{};
  failure = ReadSample(access, first_source, capture->first_sample,
                       fingerprints, false);
  if (failure != Failure::none) {
    Fail(output, failure, CoreFailureForAdapterFailure(failure));
    return false;
  }

  // Re-resolve every borrowed lease. No first-pass native address is reused
  // to locate or evaluate the second collector sample.
  ResolvedSourceV1 second_source{};
  failure = ResolveSource(access,
                          capture->frame_before.played_character_id,
                          second_source);
  if (failure != Failure::none) {
    Fail(output, failure, CoreFailureForAdapterFailure(failure));
    return false;
  }
  failure = ComparePlayer(first_source.player, second_source.player);
  if (failure != Failure::none) {
    Fail(output, failure, CoreFailureForAdapterFailure(failure));
    return false;
  }
  failure = CompareCollector(first_source.collector,
                             second_source.collector);
  if (failure != Failure::none) {
    Fail(output, failure, CoreFailureForAdapterFailure(failure));
    return false;
  }
  failure = ReadSample(access, second_source, capture->second_sample,
                       fingerprints, true);
  if (failure != Failure::none) {
    Fail(output, failure, CoreFailureForAdapterFailure(failure));
    return false;
  }

  if (!access.capture_frame(access.context, capture->frame_after)) {
    Fail(output, Failure::frame_unavailable);
    return false;
  }
  if (!capture->frame_after.paused) {
    Fail(output, Failure::not_paused, CoreFailure::not_paused);
    return false;
  }
  if (capture->frame_before != capture->frame_after) {
    Fail(output, Failure::frame_drift, CoreFailure::frame_drift);
    return false;
  }

  capture->exact_build_admitted = true;
  std::copy(access.admitted_executable_sha256.begin(),
            access.admitted_executable_sha256.end(),
            capture->admitted_executable_sha256.begin());
  capture->source_adapter_bound = true;
  capture->application_main_thread = true;

  std::unique_ptr<PlayerPrisonerManagementSnapshotV1> snapshot{
      new (std::nothrow) PlayerPrisonerManagementSnapshotV1{}};
  if (!snapshot) {
    Fail(output, Failure::working_storage_unavailable);
    return false;
  }
  if (!ObservePlayerPrisonerManagementSnapshotV1(*capture, *snapshot)) {
    const auto core_failure = snapshot->unavailable_reason;
    Fail(output,
         core_failure == CoreFailure::source_sample_drift
             ? Failure::source_sample_drift
             : Failure::core_rejected,
         core_failure);
    return false;
  }

  output = {};
  output.failure = Failure::none;
  output.core_failure = CoreFailure::none;
  output.snapshot = *snapshot;
  return true;
}

std::string_view PlayerPrisonerSourceAdapterFailureNameV1(
    PlayerPrisonerSourceAdapterFailureV1 failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::callbacks_unavailable: return "callbacks_unavailable";
  case Failure::application_main_thread_required:
    return "application_main_thread_required";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::not_paused: return "not_paused";
  case Failure::frame_invalid: return "frame_invalid";
  case Failure::player_unavailable: return "player_unavailable";
  case Failure::player_identity_drift: return "player_identity_drift";
  case Failure::player_lifecycle_drift: return "player_lifecycle_drift";
  case Failure::collector_unavailable: return "collector_unavailable";
  case Failure::collector_incomplete: return "collector_incomplete";
  case Failure::collector_count_invalid: return "collector_count_invalid";
  case Failure::collector_identity_drift:
    return "collector_identity_drift";
  case Failure::collector_lifecycle_drift:
    return "collector_lifecycle_drift";
  case Failure::prisoner_unavailable: return "prisoner_unavailable";
  case Failure::prisoner_identity_invalid:
    return "prisoner_identity_invalid";
  case Failure::prisoner_identity_drift:
    return "prisoner_identity_drift";
  case Failure::prisoner_lifecycle_drift:
    return "prisoner_lifecycle_drift";
  case Failure::native_reason_unavailable:
    return "native_reason_unavailable";
  case Failure::ransom_preview_unavailable:
    return "ransom_preview_unavailable";
  case Failure::interaction_preview_unavailable:
    return "interaction_preview_unavailable";
  case Failure::source_sample_drift: return "source_sample_drift";
  case Failure::frame_drift: return "frame_drift";
  case Failure::working_storage_unavailable:
    return "working_storage_unavailable";
  case Failure::core_rejected: return "core_rejected";
  }
  return "unknown";
}

} // namespace xar::bridge
