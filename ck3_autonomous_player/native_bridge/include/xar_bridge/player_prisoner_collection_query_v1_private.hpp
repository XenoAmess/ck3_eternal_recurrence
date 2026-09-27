#pragma once

#include "xar_bridge/player_prisoner_management_snapshot_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

// Private collection and same-frame lineage probe. Reverse jailer identity is
// checked, but this does not claim final interaction legality or the complete
// player_prisoner_management_snapshot_v1 readiness.
inline constexpr std::string_view kPlayerPrisonerCollectionQueryV1PrivateKey =
    "player_prisoner_collection_query_v1_private";
inline constexpr std::uintptr_t kPlayerPrisonerCharacterStorageSlotRvaV1 =
    0x570C130;
inline constexpr std::uintptr_t kPlayerPrisonerCharacterFallbackSlotRvaV1 =
    0x570C138;
// Exact 1.19.0.6 `is_child_of` production predicate; see the frozen ABI
// verifier before enabling its private row projection.
inline constexpr std::uintptr_t kPlayerPrisonerChildOfPredicateRvaV1 =
    0x26085E0;

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
  lineage_unavailable,
  child_relation_unavailable,
  sample_drift,
  frame_drift,
};

struct PlayerPrisonerCollectionRowV1 {
  std::uint32_t source_ordinal = 0;
  std::uint32_t full_character_id = 0;
  std::uint32_t jailer_character_id = 0;
  std::int32_t house_id = -1;
  std::int32_t dynasty_id = -1;
  bool child_of_played_character = false;

  friend bool operator==(const PlayerPrisonerCollectionRowV1 &,
                         const PlayerPrisonerCollectionRowV1 &) = default;
};

struct PlayerPrisonerCollectionSnapshotV1 {
  bool available = false;
  PlayerPrisonerCollectionFailureV1 failure =
      PlayerPrisonerCollectionFailureV1::callbacks_unavailable;
  PlayerPrisonerFrameV1 frame{};
  std::int32_t played_house_id = -1;
  std::int32_t played_dynasty_id = -1;
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
using IsPlayerPrisonerChildOfV1 = bool (*)(void *child_character,
                                           void *parent_character);

struct PlayerPrisonerCollectionAccessV1 {
  bool exact_build_admitted = false;
  bool read_lineage = false;
  bool read_child_relation = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *context = nullptr;
  CapturePlayerPrisonerCollectionFrameV1 capture_frame = nullptr;
  ReadPlayerPrisonerCollectionMemoryV1 read_memory = nullptr;
  IsPlayerPrisonerChildOfV1 is_child_of = nullptr;
};

// One synchronous paused application-main transaction. All borrowed addresses
// are discarded before return; only copied full generation-bearing IDs escape.
bool ReadPlayerPrisonerCollectionV1Private(
    const PlayerPrisonerCollectionAccessV1 &access,
    PlayerPrisonerCollectionSnapshotV1 &output) noexcept;

std::string_view PlayerPrisonerCollectionFailureNameV1(
    PlayerPrisonerCollectionFailureV1 failure) noexcept;

} // namespace xar::bridge
