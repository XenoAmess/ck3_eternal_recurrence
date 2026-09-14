#pragma once

#include "xar_bridge/player_prisoner_management_snapshot_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kPlayerPrisonerManagementSourceAdapterV1PrivateKey =
        "player_prisoner_management_source_adapter_v1";
inline constexpr std::string_view
    kPlayerPrisonerManagementSourceAdapterV1EvidenceRevision =
        "player_prisoner_management_snapshot_v1@e9652edd";

// Every address below is a borrowed exact-build collector-memory lease. It is
// valid only during its callback sequence. The adapter re-resolves all leases
// for the second sample and publishes only the value-owned PRISONER2 snapshot.
struct PlayerPrisonerSourcePlayerLeaseV1 {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
  std::int32_t character_id = -1;
  bool alive = false;
};

struct PlayerPrisonerSourceCollectorLeaseV1 {
  bool identity_round_trip = false;
  std::uintptr_t native_address = 0;
  std::uint64_t identity = 0;
  std::uint64_t generation = 0;
  std::int32_t owner_character_id = -1;
  bool complete = false;
  std::uint32_t total_count = 0;
  std::uint32_t row_count = 0;
};

struct PlayerPrisonerSourceRowLeaseV1 {
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

struct PlayerPrisonerSourceNativeReasonsV1 {
  PlayerPrisonerOpaqueFinalBoolV1 has_imprisonment_reason{};
  PlayerPrisonerOpaqueFinalBoolV1 has_banish_reason{};
  PlayerPrisonerOpaqueFinalBoolV1 has_execute_reason{};
};

enum class PlayerPrisonerSourcePreviewKindV1 : std::uint8_t {
  release_unconditional,
  execute,
  move_to_dungeon,
  move_to_house_arrest,
  torture,
};

enum class PlayerPrisonerSourceAdapterFailureV1 : std::uint8_t {
  none,
  exact_build_mismatch,
  callbacks_unavailable,
  application_main_thread_required,
  frame_unavailable,
  not_paused,
  frame_invalid,
  player_unavailable,
  player_identity_drift,
  player_lifecycle_drift,
  collector_unavailable,
  collector_incomplete,
  collector_count_invalid,
  collector_identity_drift,
  collector_lifecycle_drift,
  prisoner_unavailable,
  prisoner_identity_invalid,
  prisoner_identity_drift,
  prisoner_lifecycle_drift,
  native_reason_unavailable,
  ransom_preview_unavailable,
  interaction_preview_unavailable,
  source_sample_drift,
  frame_drift,
  working_storage_unavailable,
  core_rejected,
};

using CapturePlayerPrisonerSourceFrameV1 = bool (*)(
    void *context, PlayerPrisonerFrameV1 &output) noexcept;
using ResolvePlayerPrisonerSourcePlayerV1 = bool (*)(
    void *context, std::int32_t expected_character_id,
    PlayerPrisonerSourcePlayerLeaseV1 &output) noexcept;
using ResolvePlayerPrisonerSourceCollectorV1 = bool (*)(
    void *context, const PlayerPrisonerSourcePlayerLeaseV1 &player,
    PlayerPrisonerSourceCollectorLeaseV1 &output) noexcept;
using ReadPlayerPrisonerSourceRowV1 = bool (*)(
    void *context, const PlayerPrisonerSourcePlayerLeaseV1 &player,
    const PlayerPrisonerSourceCollectorLeaseV1 &collector,
    std::size_t row_index,
    PlayerPrisonerSourceRowLeaseV1 &output) noexcept;
using ReadPlayerPrisonerSourceNativeReasonsV1 = bool (*)(
    void *context, const PlayerPrisonerSourcePlayerLeaseV1 &player,
    const PlayerPrisonerSourceRowLeaseV1 &prisoner,
    PlayerPrisonerSourceNativeReasonsV1 &output) noexcept;
using ReadPlayerPrisonerSourceRansomPreviewV1 = bool (*)(
    void *context, const PlayerPrisonerSourcePlayerLeaseV1 &player,
    const PlayerPrisonerSourceRowLeaseV1 &prisoner,
    PlayerPrisonerRansomPreviewV1 &output) noexcept;
using ReadPlayerPrisonerSourceInteractionPreviewV1 = bool (*)(
    void *context, const PlayerPrisonerSourcePlayerLeaseV1 &player,
    const PlayerPrisonerSourceRowLeaseV1 &prisoner,
    PlayerPrisonerSourcePreviewKindV1 kind,
    PlayerPrisonerInteractionPreviewV1 &output) noexcept;

struct PlayerPrisonerSourceAccessV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *context = nullptr;
  CapturePlayerPrisonerSourceFrameV1 capture_frame = nullptr;
  ResolvePlayerPrisonerSourcePlayerV1 resolve_player = nullptr;
  ResolvePlayerPrisonerSourceCollectorV1 resolve_collector = nullptr;
  ReadPlayerPrisonerSourceRowV1 read_prisoner = nullptr;
  ReadPlayerPrisonerSourceNativeReasonsV1 read_native_reasons = nullptr;
  ReadPlayerPrisonerSourceRansomPreviewV1 read_ransom_preview = nullptr;
  ReadPlayerPrisonerSourceInteractionPreviewV1 read_interaction_preview =
      nullptr;
};

struct PlayerPrisonerSourceResultV1 {
  PlayerPrisonerSourceAdapterFailureV1 failure =
      PlayerPrisonerSourceAdapterFailureV1::callbacks_unavailable;
  PlayerPrisonerSnapshotFailureV1 core_failure =
      PlayerPrisonerSnapshotFailureV1::source_adapter_unavailable;
  PlayerPrisonerManagementSnapshotV1 snapshot{};
};

// Runs one synchronous application-main transaction. The callbacks must read
// a complete exact-build prisoner collector and engine-final reason/preview
// results. Religious inputs remain opaque inside those native-final results.
// This adapter performs no command, effect or GUI action.
bool ObservePlayerPrisonerManagementSourceV1(
    const PlayerPrisonerSourceAccessV1 &access,
    PlayerPrisonerSourceResultV1 &output) noexcept;

std::string_view PlayerPrisonerSourceAdapterFailureNameV1(
    PlayerPrisonerSourceAdapterFailureV1 failure) noexcept;

} // namespace xar::bridge
