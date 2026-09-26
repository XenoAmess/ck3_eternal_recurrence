#pragma once

#include "xar_bridge/player_prisoner_management_snapshot_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

// Private collection-only probe. This does not claim custody, final interaction
// legality, or player_prisoner_management_snapshot_v1 readiness.
inline constexpr std::string_view kPlayerPrisonerCollectionQueryV1PrivateKey =
    "player_prisoner_collection_query_v1_private";
inline constexpr std::uintptr_t kPlayerPrisonerCharacterStorageSlotRvaV1 =
    0x570C130;
inline constexpr std::uintptr_t kPlayerPrisonerCharacterFallbackSlotRvaV1 =
    0x570C138;

enum class PlayerPrisonerCollectionFailureV1 : std::uint8_t {
  none,
  exact_build_mismatch,
  callbacks_unavailable,
  application_main_thread_required,
  frame_unavailable,
  not_paused,
  player_unavailable,
  memory_unavailable,
  collection_invalid,
  collection_truncated,
  prisoner_identity_invalid,
  custody_relation_invalid,
  sample_drift,
  frame_drift,
};

struct PlayerPrisonerCollectionRowV1 {
  std::uint32_t source_ordinal = 0;
  std::uint32_t full_character_id = 0;
  std::uint32_t jailer_character_id = 0;

  friend bool operator==(const PlayerPrisonerCollectionRowV1 &,
                         const PlayerPrisonerCollectionRowV1 &) = default;
};

struct PlayerPrisonerCollectionSnapshotV1 {
  bool available = false;
  PlayerPrisonerCollectionFailureV1 failure =
      PlayerPrisonerCollectionFailureV1::callbacks_unavailable;
  PlayerPrisonerFrameV1 frame{};
  std::uint32_t total_count = 0;
  std::uint32_t returned_count = 0;
  bool collection_complete = false;
  std::array<PlayerPrisonerCollectionRowV1, kPlayerPrisonerMaximumRowsV1>
      rows{};
};

using CapturePlayerPrisonerCollectionFrameV1 = bool (*)(
    void *context, PlayerPrisonerFrameV1 &output) noexcept;
using ReadPlayerPrisonerCollectionMemoryV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;

struct PlayerPrisonerCollectionAccessV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *context = nullptr;
  CapturePlayerPrisonerCollectionFrameV1 capture_frame = nullptr;
  ReadPlayerPrisonerCollectionMemoryV1 read_memory = nullptr;
};

// One synchronous paused application-main transaction. All borrowed addresses
// are discarded before return; only copied full generation-bearing IDs escape.
bool ReadPlayerPrisonerCollectionV1Private(
    const PlayerPrisonerCollectionAccessV1 &access,
    PlayerPrisonerCollectionSnapshotV1 &output) noexcept;

std::string_view PlayerPrisonerCollectionFailureNameV1(
    PlayerPrisonerCollectionFailureV1 failure) noexcept;

} // namespace xar::bridge
