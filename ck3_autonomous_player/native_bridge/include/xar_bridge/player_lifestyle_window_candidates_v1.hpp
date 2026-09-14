#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::game {

enum class PlayerLifestyleWindowCandidatesStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class PlayerLifestyleWindowCollectionStatusV1 : std::uint32_t {
  unavailable = 0,
  known_empty = 1,
  available = 2,
};

enum class PlayerLifestyleWindowCandidatesFailureV1 : std::uint32_t {
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
  owner_path_unavailable,
  owner_path_invalid,
  lifestyle_window_unbound_or_stale,
  invalid_container,
  materialization_unavailable,
  final_legality_evaluator_unavailable,
  candidate_provenance_invalid,
  stable_key_invalid,
  duplicate_stable_key,
  root_reacquisition_not_proven,
  native_sample_drift,
  native_source_read_failed,
};

inline constexpr std::size_t kPlayerLifestyleWindowStableKeyCapacityV1 =
    128;
inline constexpr std::size_t kPlayerLifestyleWindowSnapshotIdCapacityV1 =
    48;
inline constexpr std::size_t kPlayerLifestyleWindowMaximumFocusesV1 = 64;
inline constexpr std::size_t kPlayerLifestyleWindowMaximumPerksV1 = 512;

struct PlayerLifestyleWindowStableKeyV1 {
  std::uint16_t size = 0;
  std::array<char, kPlayerLifestyleWindowStableKeyCapacityV1> bytes{};

  friend bool operator==(const PlayerLifestyleWindowStableKeyV1 &,
                         const PlayerLifestyleWindowStableKeyV1 &) = default;
};

struct PlayerLifestyleWindowFocusCandidateV1 {
  PlayerLifestyleWindowStableKeyV1 key{};
  PlayerLifestyleWindowStableKeyV1 lifestyle_key{};
  bool can_select = false;

  friend bool operator==(const PlayerLifestyleWindowFocusCandidateV1 &,
                         const PlayerLifestyleWindowFocusCandidateV1 &) =
      default;
};

struct PlayerLifestyleWindowPerkCandidateV1 {
  PlayerLifestyleWindowStableKeyV1 key{};
  PlayerLifestyleWindowStableKeyV1 lifestyle_key{};
  bool can_select = false;
  // Explanatory frontier state only. It never authorizes an action.
  bool can_select_ignore_cost = false;

  friend bool operator==(const PlayerLifestyleWindowPerkCandidateV1 &,
                         const PlayerLifestyleWindowPerkCandidateV1 &) =
      default;
};

struct PlayerLifestyleWindowCandidatesReadinessV1 {
  bool owner_path_ready = false;
  bool bound_player_ready = false;
  bool containers_ready = false;
  bool focus_candidates_ready = false;
  bool perk_candidates_ready = false;
  bool final_legality_ready = false;
  bool same_frame_ready = false;

  friend bool operator==(const PlayerLifestyleWindowCandidatesReadinessV1 &,
                         const PlayerLifestyleWindowCandidatesReadinessV1 &) =
      default;
};

struct PlayerLifestyleWindowCandidatesV1 {
  PlayerLifestyleWindowCandidatesStatusV1 status =
      PlayerLifestyleWindowCandidatesStatusV1::unavailable;
  PlayerLifestyleWindowCandidatesFailureV1 unavailable_reason =
      PlayerLifestyleWindowCandidatesFailureV1::none;
  std::array<char, kPlayerLifestyleWindowSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t player_character_id = 0xFFFFFFFFU;

  PlayerLifestyleWindowCollectionStatusV1 focus_status =
      PlayerLifestyleWindowCollectionStatusV1::unavailable;
  std::uint32_t focus_count = 0;
  std::array<PlayerLifestyleWindowFocusCandidateV1,
             kPlayerLifestyleWindowMaximumFocusesV1>
      focuses{};

  PlayerLifestyleWindowCollectionStatusV1 perk_status =
      PlayerLifestyleWindowCollectionStatusV1::unavailable;
  std::uint32_t perk_count = 0;
  std::array<PlayerLifestyleWindowPerkCandidateV1,
             kPlayerLifestyleWindowMaximumPerksV1>
      perks{};
  PlayerLifestyleWindowCandidatesReadinessV1 readiness{};
};

enum class ReadPlayerLifestyleWindowCandidatesResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kPlayerLifestyleWindowCandidatesPrivateKeyV1 =
        "g2_player_lifestyle_window_candidates_v1";
inline constexpr std::string_view
    kPlayerLifestyleWindowCandidatesGameVersionV1 = "1.19.0.6";
inline constexpr std::string_view
    kPlayerLifestyleWindowCandidatesExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr bool kPlayerLifestyleWindowCandidatesAdvertisedByDefaultV1 =
    false;
inline constexpr bool kPlayerLifestyleWindowCandidatesReadOnlyV1 = true;

// Exact-build owner and evaluator anchors frozen by LIFE3.
inline constexpr std::uintptr_t kLifestyleWindowGlobalRootPointerRvaV1 =
    0x570F7B8;
inline constexpr std::size_t kLifestyleWindowRootIdlerOffsetV1 = 0x10;
inline constexpr std::size_t kLifestyleWindowIdlerHandlerOffsetV1 = 0x88;
inline constexpr std::size_t kLifestyleWindowHandlerOwnerSlotOffsetV1 =
    0x1A8;
inline constexpr std::uintptr_t kLifestyleWindowHandlerVtableRvaV1 =
    0x40AF630;
inline constexpr std::uintptr_t kLifestyleWindowPrimaryVtableRvaV1 =
    0x4148BE8;
inline constexpr std::uintptr_t kLifestyleWindowSecondaryVtableRvaV1 =
    0x4148BC0;
inline constexpr std::size_t kLifestyleWindowSecondaryVtableOffsetV1 = 0x10;
inline constexpr std::size_t kLifestyleWindowOwnerRoundTripOffsetV1 = 0xD0;
inline constexpr std::size_t kLifestyleWindowBoundCharacterIdOffsetV1 = 0xF8;
inline constexpr std::size_t kLifestyleWindowLifestylesSpanOffsetV1 = 0x100;
inline constexpr std::size_t kLifestyleWindowPerkTreeSpanOffsetV1 = 0x118;
inline constexpr std::size_t kLifestyleWindowFocusSpanOffsetV1 = 0x130;
inline constexpr std::size_t kLifestyleWindowPointerSpanElementBytesV1 = 8;
inline constexpr std::size_t kLifestyleWindowPerkTreeRowBytesV1 = 0x78;
inline constexpr std::uintptr_t kLifestyleWindowCanSelectFocusRvaV1 =
    0x132D4A0;
inline constexpr std::uintptr_t kLifestyleWindowCanSelectPerkRvaV1 =
    0x132D640;
inline constexpr std::uintptr_t kLifestyleWindowCanSelectPerkIgnoreCostRvaV1 =
    0x132D700;

// These mutation entry points are deliberately metadata only. The observer
// access surface exposes no function capable of calling them.
inline constexpr std::uintptr_t kLifestyleWindowForbiddenBinderRvaV1 =
    0xF48780;
inline constexpr std::uintptr_t kLifestyleWindowForbiddenRefreshRvaV1 =
    0x132C970;

struct PlayerLifestyleWindowFrameV1 {
  std::array<char, game::kPlayerLifestyleWindowSnapshotIdCapacityV1>
      snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::uintptr_t played_character = 0;
  bool played_character_identity_round_trip = false;

  friend bool operator==(const PlayerLifestyleWindowFrameV1 &,
                         const PlayerLifestyleWindowFrameV1 &) = default;
};

struct PlayerLifestyleWindowSpanV1 {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  std::size_t element_bytes = 0;
  bool complete_range_readable = false;

  friend bool operator==(const PlayerLifestyleWindowSpanV1 &,
                         const PlayerLifestyleWindowSpanV1 &) = default;
};

struct PlayerLifestyleWindowFocusSourceRowV1 {
  std::uintptr_t definition = 0;
  game::PlayerLifestyleWindowStableKeyV1 key{};
  game::PlayerLifestyleWindowStableKeyV1 lifestyle_key{};
  bool pointer_in_captured_focus_span = false;
  bool stable_key_round_trip = false;
  bool final_evaluator_invoked = false;
  bool can_select = false;

  friend bool operator==(const PlayerLifestyleWindowFocusSourceRowV1 &,
                         const PlayerLifestyleWindowFocusSourceRowV1 &) =
      default;
};

struct PlayerLifestyleWindowPerkSourceRowV1 {
  std::uintptr_t definition = 0;
  game::PlayerLifestyleWindowStableKeyV1 key{};
  game::PlayerLifestyleWindowStableKeyV1 lifestyle_key{};
  bool pointer_in_exact_perk_database = false;
  bool stable_key_round_trip = false;
  bool final_evaluator_invoked = false;
  bool ignore_cost_evaluator_invoked = false;
  bool can_select = false;
  bool can_select_ignore_cost = false;

  friend bool operator==(const PlayerLifestyleWindowPerkSourceRowV1 &,
                         const PlayerLifestyleWindowPerkSourceRowV1 &) =
      default;
};

struct PlayerLifestyleWindowSourceSampleV1 {
  // A monotonic adapter-owned serial proving that this sample performed a new
  // complete root -> idler -> handler -> window acquisition.
  std::uint64_t root_acquisition_serial = 0;
  std::uintptr_t root = 0;
  std::uintptr_t idler_base = 0;
  std::uintptr_t idler_gfx = 0;
  bool idler_exact_rtti_cast = false;
  std::uintptr_t handler = 0;
  std::uintptr_t handler_vtable = 0;
  std::uintptr_t window = 0;
  std::uintptr_t window_primary_vtable = 0;
  std::uintptr_t window_secondary_vtable = 0;
  std::uintptr_t window_owner_round_trip = 0;
  std::uint32_t bound_character_id = 0xFFFFFFFFU;
  bool character_storage_round_trip = false;

  PlayerLifestyleWindowSpanV1 lifestyles{};
  PlayerLifestyleWindowSpanV1 perk_trees{};
  PlayerLifestyleWindowSpanV1 focuses{};

  bool perk_database_fully_materialized = false;
  std::uint32_t focus_count = 0;
  std::array<PlayerLifestyleWindowFocusSourceRowV1,
             game::kPlayerLifestyleWindowMaximumFocusesV1>
      focus_rows{};
  std::uint32_t perk_count = 0;
  std::array<PlayerLifestyleWindowPerkSourceRowV1,
             game::kPlayerLifestyleWindowMaximumPerksV1>
      perk_rows{};
};

enum class PlayerLifestyleWindowSourceReadResultV1 : std::uint32_t {
  success = 0,
  owner_path_unavailable,
  invalid_container,
  materialization_unavailable,
  final_legality_evaluator_unavailable,
  source_read_failed,
};

struct PlayerLifestyleWindowCandidatesEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
};

using CapturePlayerLifestyleWindowFrameV1 = bool (*)(
    void *context, PlayerLifestyleWindowFrameV1 &output) noexcept;
using IsPlayerLifestyleWindowMainThreadV1 = bool (*)(void *context) noexcept;
using ReadPlayerLifestyleWindowSourceV1 =
    PlayerLifestyleWindowSourceReadResultV1 (*)(
        void *context, std::uintptr_t module_base,
        std::uint32_t played_character_id,
        PlayerLifestyleWindowSourceSampleV1 &output) noexcept;

struct PlayerLifestyleWindowCandidatesAccessV1 {
  void *context = nullptr;
  CapturePlayerLifestyleWindowFrameV1 capture_frame = nullptr;
  IsPlayerLifestyleWindowMainThreadV1 is_main_thread = nullptr;
  ReadPlayerLifestyleWindowSourceV1 read_source = nullptr;
};

struct PlayerLifestyleWindowCandidatesRequestV1 {
  std::string_view expected_snapshot_id{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::uint32_t expected_player_character_id = 0xFFFFFFFFU;
};

bool AssignPlayerLifestyleWindowStableKeyV1(
    std::string_view value,
    game::PlayerLifestyleWindowStableKeyV1 &output) noexcept;

std::string_view PlayerLifestyleWindowStableKeyViewV1(
    const game::PlayerLifestyleWindowStableKeyV1 &value) noexcept;

game::ReadPlayerLifestyleWindowCandidatesResultV1
ReadPlayerLifestyleWindowCandidatesV1(
    const PlayerLifestyleWindowCandidatesEnvironmentV1 &environment,
    const PlayerLifestyleWindowCandidatesAccessV1 &access,
    const PlayerLifestyleWindowCandidatesRequestV1 &request,
    game::PlayerLifestyleWindowCandidatesV1 &output) noexcept;

std::string_view PlayerLifestyleWindowCandidatesFailureKeyV1(
    game::PlayerLifestyleWindowCandidatesFailureV1 reason) noexcept;

} // namespace xar::ck3_11906
