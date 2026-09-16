#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class PlayerLifestyleSnapshotStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class PlayerLifestyleSnapshotFailureV1 : std::uint32_t {
  none = 0,
  invalid_request,
  exact_build_not_admitted,
  native_bindings_unavailable,
  application_main_thread_required,
  frame_capture_failed,
  snapshot_identity_mismatch,
  revision_drift,
  date_drift,
  not_paused,
  player_unavailable,
  native_source_read_failed,
  stable_key_invalid,
  current_focus_invariant_failed,
  lifestyle_progress_invalid,
  owned_perk_collection_invalid,
  legal_focus_collection_invalid,
  legal_perk_collection_invalid,
  duplicate_stable_key,
  native_sample_drift,
  current_focus_getter_failed,
  focus_fallback_read_failed,
  current_focus_key_read_failed,
  current_lifestyle_getter_failed,
  current_lifestyle_key_read_failed,
  focus_lifestyle_binding_failed,
  lifestyle_xp_read_failed,
  lifestyle_xp_level_read_failed,
  owned_perk_span_getter_failed,
  owned_perk_span_layout_invalid,
  owned_perk_key_read_failed,
};

enum class PlayerLifestyleFocusPresenceV1 : std::uint32_t {
  unknown = 0,
  absent = 1,
  present = 2,
};

enum class PlayerLifestyleCandidateCollectionStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class PlayerLifestyleCandidateCollectionFailureV1 : std::uint32_t {
  none = 0,
  lifestyle_window_unavailable,
  native_enumerator_unavailable,
  final_legality_evaluator_unavailable,
  source_read_failed,
};

inline constexpr std::size_t kPlayerLifestyleStableKeyCapacityV1 = 128;
inline constexpr std::size_t kPlayerLifestyleSnapshotIdCapacityV1 = 48;
inline constexpr std::size_t kPlayerLifestyleMaximumOwnedPerksV1 = 512;
inline constexpr std::size_t kPlayerLifestyleMaximumLegalFocusCandidatesV1 =
    64;
inline constexpr std::size_t kPlayerLifestyleMaximumLegalPerkCandidatesV1 =
    512;

struct PlayerLifestyleStableKeyV1 {
  std::uint16_t size = 0;
  std::array<char, kPlayerLifestyleStableKeyCapacityV1> bytes{};

  friend bool operator==(const PlayerLifestyleStableKeyV1 &,
                         const PlayerLifestyleStableKeyV1 &) = default;
};

struct PlayerLifestyleProgressRowV1 {
  PlayerLifestyleStableKeyV1 lifestyle_key{};
  std::int64_t xp_total_raw = 0;
  std::int64_t xp_within_level_raw = 0;
  std::int32_t xp_per_level = 0;
  std::int32_t unspent_perk_points = 0;
  std::int32_t used_perk_points = 0;

  friend bool operator==(const PlayerLifestyleProgressRowV1 &,
                         const PlayerLifestyleProgressRowV1 &) = default;
};

struct PlayerLifestyleLegalCandidateV1 {
  PlayerLifestyleStableKeyV1 key{};
  PlayerLifestyleStableKeyV1 lifestyle_key{};

  friend bool operator==(const PlayerLifestyleLegalCandidateV1 &,
                         const PlayerLifestyleLegalCandidateV1 &) = default;
};

struct PlayerLifestyleStateV1 {
  PlayerLifestyleFocusPresenceV1 current_focus_presence =
      PlayerLifestyleFocusPresenceV1::unknown;
  PlayerLifestyleStableKeyV1 current_focus_key{};
  PlayerLifestyleStableKeyV1 current_lifestyle_key{};

  bool current_lifestyle_progress_present = false;
  PlayerLifestyleProgressRowV1 current_lifestyle_progress{};

  std::uint32_t owned_perk_count = 0;
  std::array<PlayerLifestyleStableKeyV1,
             kPlayerLifestyleMaximumOwnedPerksV1>
      owned_perk_keys{};

  PlayerLifestyleCandidateCollectionStatusV1 legal_focus_candidate_status =
      PlayerLifestyleCandidateCollectionStatusV1::unavailable;
  PlayerLifestyleCandidateCollectionFailureV1
      legal_focus_candidate_unavailable_reason =
          PlayerLifestyleCandidateCollectionFailureV1::
              lifestyle_window_unavailable;
  std::uint32_t legal_focus_candidate_count = 0;
  std::array<PlayerLifestyleLegalCandidateV1,
             kPlayerLifestyleMaximumLegalFocusCandidatesV1>
      legal_focus_candidates{};

  PlayerLifestyleCandidateCollectionStatusV1 legal_perk_candidate_status =
      PlayerLifestyleCandidateCollectionStatusV1::unavailable;
  PlayerLifestyleCandidateCollectionFailureV1
      legal_perk_candidate_unavailable_reason =
          PlayerLifestyleCandidateCollectionFailureV1::
              lifestyle_window_unavailable;
  std::uint32_t legal_perk_candidate_count = 0;
  std::array<PlayerLifestyleLegalCandidateV1,
             kPlayerLifestyleMaximumLegalPerkCandidatesV1>
      legal_perk_candidates{};

  friend bool operator==(const PlayerLifestyleStateV1 &,
                         const PlayerLifestyleStateV1 &) = default;
};

struct PlayerLifestyleSnapshotReadinessV1 {
  bool current_focus_ready = false;
  bool lifestyle_progress_ready = false;
  bool owned_perks_ready = false;
  bool legal_focus_candidates_ready = false;
  bool legal_perk_candidates_ready = false;
  bool same_frame_ready = false;

  friend bool operator==(const PlayerLifestyleSnapshotReadinessV1 &,
                         const PlayerLifestyleSnapshotReadinessV1 &) =
      default;
};

struct PlayerLifestyleSnapshotV1 {
  PlayerLifestyleSnapshotStatusV1 status =
      PlayerLifestyleSnapshotStatusV1::unavailable;
  PlayerLifestyleSnapshotFailureV1 unavailable_reason =
      PlayerLifestyleSnapshotFailureV1::none;
  std::array<char, kPlayerLifestyleSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t player_character_id = -1;
  PlayerLifestyleStateV1 state{};
  PlayerLifestyleSnapshotReadinessV1 readiness{};
};

enum class ReadPlayerLifestyleSnapshotResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kPlayerLifestyleSnapshotPrivateKeyV1 =
    "g2_player_lifestyle_snapshot_v1";
inline constexpr std::string_view kPlayerLifestyleSnapshotGameVersionV1 =
    "1.19.0.6";
inline constexpr std::string_view
    kPlayerLifestyleSnapshotExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::uintptr_t kPlayerLifestyleCurrentFocusGetterRvaV1 =
    0x26692F0;
inline constexpr std::uintptr_t kPlayerLifestyleCurrentLifestyleGetterRvaV1 =
    0x26691F0;
inline constexpr std::uintptr_t kPlayerLifestylePerkPointsGetterRvaV1 =
    0x2668A00;
inline constexpr std::uintptr_t kPlayerLifestylePerkPointsUsedGetterRvaV1 =
    0x2668A80;
inline constexpr std::uintptr_t kPlayerLifestyleXpGetterRvaV1 = 0x2668B80;
inline constexpr std::uintptr_t kPlayerLifestyleOwnedPerksGetterRvaV1 =
    0x2669170;
inline constexpr std::uintptr_t kPlayerLifestyleHasPerkGetterRvaV1 =
    0x2668EA0;
inline constexpr std::uintptr_t kPlayerLifestyleCharacterPerkDatabaseRvaV1 =
    0x88EC20;
inline constexpr std::uintptr_t kPlayerLifestyleCharacterStorageSlotRvaV1 =
    0x570C130;
inline constexpr std::uintptr_t
    kPlayerLifestyleCharacterFallbackSlotRvaV1 = 0x570C138;
inline constexpr std::uintptr_t kPlayerLifestyleFocusFallbackSlotRvaV1 =
    0x570CB90;
inline constexpr std::size_t kPlayerLifestyleDatabaseStableKeyOffsetV1 = 0x18;
inline constexpr std::size_t kPlayerLifestyleCharacterPerkStableKeyOffsetV1 =
    0x18;
inline constexpr std::size_t kPlayerLifestyleXpPerLevelOffsetV1 = 0x138;
inline constexpr std::size_t kPlayerLifestyleFocusLifestyleOffsetV1 = 0x880;
inline constexpr std::size_t kPlayerLifestylePerkLifestyleOffsetV1 = 0x468;
inline constexpr std::size_t kPlayerLifestyleUnlockedPerksCountOffsetV1 = 0x0C;
inline constexpr std::int64_t kPlayerLifestyleFixedPointScaleV1 = 100000;

struct PlayerLifestyleSnapshotFrameV1 {
  std::array<char, game::kPlayerLifestyleSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::int32_t played_character_id = -1;
  std::uintptr_t played_character = 0;
  bool played_character_identity_round_trip = false;

  friend bool operator==(const PlayerLifestyleSnapshotFrameV1 &,
                         const PlayerLifestyleSnapshotFrameV1 &) = default;
};

struct PlayerLifestyleSourceSampleV1 {
  std::int32_t player_character_id = -1;
  bool player_identity_round_trip = false;
  game::PlayerLifestyleStateV1 state{};

  friend bool operator==(const PlayerLifestyleSourceSampleV1 &,
                         const PlayerLifestyleSourceSampleV1 &) = default;
};

struct PlayerLifestyleSnapshotEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;

  using ObjectGetter = void *(*)(void *character);
  using Int32Getter = std::int32_t (*)(void *character, void *lifestyle);
  using XpGetter = std::int64_t *(*)(void *character, std::int64_t *output,
                                    void *lifestyle, bool within_level);
  using PerkSpanGetter = const void *(*)(void *character);

  ObjectGetter current_focus = nullptr;
  ObjectGetter current_lifestyle = nullptr;
  Int32Getter unspent_perk_points = nullptr;
  Int32Getter used_perk_points = nullptr;
  XpGetter lifestyle_xp = nullptr;
  PerkSpanGetter unlocked_perks = nullptr;
  std::uintptr_t focus_fallback_slot_address = 0;
};

using CapturePlayerLifestyleSnapshotFrameV1 = bool (*)(
    void *context, PlayerLifestyleSnapshotFrameV1 &output) noexcept;
using IsPlayerLifestyleSnapshotMainThreadV1 = bool (*)(void *context) noexcept;
using ReadPlayerLifestyleNativeSourceV1 = bool (*)(
    void *context, std::uintptr_t played_character,
    PlayerLifestyleSourceSampleV1 &output) noexcept;
using ReadPlayerLifestyleMemoryV1 = bool (*)(
    void *context, std::uintptr_t address, void *output,
    std::size_t size) noexcept;

struct PlayerLifestyleSnapshotAccessV1 {
  void *context = nullptr;
  CapturePlayerLifestyleSnapshotFrameV1 capture_frame = nullptr;
  IsPlayerLifestyleSnapshotMainThreadV1 is_main_thread = nullptr;
  ReadPlayerLifestyleMemoryV1 read_memory = nullptr;
  ReadPlayerLifestyleNativeSourceV1 read_offline_fixture_source = nullptr;
};

struct PlayerLifestyleSnapshotRequestV1 {
  std::string_view expected_snapshot_id{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::int32_t expected_player_character_id = -1;
};

bool AssignPlayerLifestyleStableKeyV1(
    std::string_view value, game::PlayerLifestyleStableKeyV1 &output) noexcept;

std::string_view PlayerLifestyleStableKeyViewV1(
    const game::PlayerLifestyleStableKeyV1 &value) noexcept;

bool ReadPlayerLifestyleMsvcStableKeyV1(
    void *context, ReadPlayerLifestyleMemoryV1 read_memory,
    std::uintptr_t native_string_address,
    game::PlayerLifestyleStableKeyV1 &output) noexcept;

PlayerLifestyleSnapshotEnvironmentV1 BindPlayerLifestyleSnapshotEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

game::ReadPlayerLifestyleSnapshotResultV1 ReadPlayerLifestyleSnapshotV1(
    const PlayerLifestyleSnapshotEnvironmentV1 &environment,
    const PlayerLifestyleSnapshotAccessV1 &access,
    const PlayerLifestyleSnapshotRequestV1 &request,
    game::PlayerLifestyleSnapshotV1 &output) noexcept;

std::string_view PlayerLifestyleSnapshotFailureKeyV1(
    game::PlayerLifestyleSnapshotFailureV1 reason) noexcept;

std::string_view PlayerLifestyleCandidateCollectionFailureKeyV1(
    game::PlayerLifestyleCandidateCollectionFailureV1 reason) noexcept;

std::string SerializePlayerLifestyleSnapshotV1(
    const game::PlayerLifestyleSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
