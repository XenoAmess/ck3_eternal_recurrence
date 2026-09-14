#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kPlayerPrisonerManagementSnapshotV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kPlayerPrisonerManagementSnapshotV1EvidenceRevision =
        "g2-m6-nonreligious-prisoner-management-native-tree-v1@eec90244";
inline constexpr bool
    kPlayerPrisonerManagementSnapshotV1AdvertisedByDefault = false;

inline constexpr std::size_t kPlayerPrisonerKeyCapacityV1 = 96;
inline constexpr std::size_t kPlayerPrisonerSha256CapacityV1 = 65;
inline constexpr std::size_t kPlayerPrisonerMaximumRowsV1 = 64;
inline constexpr std::int64_t kPlayerPrisonerFixedPointOneV1 = 100'000;

enum class PlayerPrisonerSnapshotStatusV1 : std::uint8_t {
  unavailable,
  available,
};

enum class PlayerPrisonerSnapshotFailureV1 : std::uint8_t {
  none,
  exact_build_mismatch,
  source_adapter_unavailable,
  application_main_thread_required,
  not_paused,
  frame_drift,
  played_character_unavailable,
  source_sample_incomplete,
  player_identity_mismatch,
  prisoner_collection_incomplete,
  prisoner_count_invalid,
  source_sample_drift,
  prisoner_identity_invalid,
  duplicate_prisoner_identity,
  prisoner_not_alive,
  jailer_identity_mismatch,
  custody_invalid,
  imprisonment_duration_invalid,
  typed_value_invalid,
  native_reason_source_invalid,
  native_preview_source_invalid,
  preview_invariant_failed,
  ransom_terms_invalid,
};

enum class PlayerPrisonerFieldStateV1 : std::uint8_t {
  unknown,
  known,
};

enum class PlayerPrisonerUnknownReasonV1 : std::uint8_t {
  none,
  not_observed,
  not_applicable,
  native_final_evaluator_unresolved,
  native_role_binding_unresolved,
  native_option_unresolved,
  native_resource_term_unresolved,
  provider_unavailable,
};

enum class PlayerPrisonerNativeReasonSourceV1 : std::uint8_t {
  unknown,
  native_opaque_final,
};

enum class PlayerPrisonerPreviewSourceV1 : std::uint8_t {
  unknown,
  native_finalized_character_interaction,
};

enum class PlayerPrisonerCustodyKindV1 : std::uint8_t {
  unknown,
  house_arrest,
  dungeon,
  other,
};

struct PlayerPrisonerKeyV1 {
  std::uint16_t size = 0;
  std::array<char, kPlayerPrisonerKeyCapacityV1> bytes{};

  friend bool operator==(const PlayerPrisonerKeyV1 &,
                         const PlayerPrisonerKeyV1 &) = default;
};

struct PlayerPrisonerTypedKeyV1 {
  PlayerPrisonerFieldStateV1 state = PlayerPrisonerFieldStateV1::unknown;
  PlayerPrisonerKeyV1 value{};
  PlayerPrisonerUnknownReasonV1 unknown_reason =
      PlayerPrisonerUnknownReasonV1::not_observed;

  friend bool operator==(const PlayerPrisonerTypedKeyV1 &,
                         const PlayerPrisonerTypedKeyV1 &) = default;
};

// Crime and punishment inputs may include faith-derived stock logic. The
// adapter supplies only the engine-final boolean; the core never receives
// faith, doctrine, tenet or conversion fields.
struct PlayerPrisonerOpaqueFinalBoolV1 {
  PlayerPrisonerFieldStateV1 state = PlayerPrisonerFieldStateV1::unknown;
  bool value = false;
  PlayerPrisonerUnknownReasonV1 unknown_reason =
      PlayerPrisonerUnknownReasonV1::not_observed;
  PlayerPrisonerNativeReasonSourceV1 source =
      PlayerPrisonerNativeReasonSourceV1::unknown;

  friend bool operator==(const PlayerPrisonerOpaqueFinalBoolV1 &,
                         const PlayerPrisonerOpaqueFinalBoolV1 &) = default;
};

struct PlayerPrisonerInteractionPreviewV1 {
  PlayerPrisonerFieldStateV1 state = PlayerPrisonerFieldStateV1::unknown;
  PlayerPrisonerUnknownReasonV1 unknown_reason =
      PlayerPrisonerUnknownReasonV1::not_observed;
  PlayerPrisonerPreviewSourceV1 source =
      PlayerPrisonerPreviewSourceV1::unknown;
  bool shown = false;
  bool valid = false;
  bool can_send = false;
  PlayerPrisonerTypedKeyV1 failure_reason_key{};

  friend bool operator==(const PlayerPrisonerInteractionPreviewV1 &,
                         const PlayerPrisonerInteractionPreviewV1 &) = default;
};

struct PlayerPrisonerRansomPreviewV1 {
  PlayerPrisonerInteractionPreviewV1 interaction{};
  std::int32_t payer_character_id = -1;
  PlayerPrisonerTypedKeyV1 selected_option_key{};
  PlayerPrisonerTypedKeyV1 resource_key{};
  std::int64_t resource_amount_raw = 0;
  bool acceptance_required = false;
  PlayerPrisonerOpaqueFinalBoolV1 would_accept_now{};

  friend bool operator==(const PlayerPrisonerRansomPreviewV1 &,
                         const PlayerPrisonerRansomPreviewV1 &) = default;
};

struct PlayerPrisonerRowV1 {
  std::int32_t prisoner_character_id = -1;
  std::int32_t jailer_character_id = -1;
  bool prisoner_identity_round_trip = false;
  bool prisoner_alive = false;
  PlayerPrisonerCustodyKindV1 custody =
      PlayerPrisonerCustodyKindV1::unknown;
  std::int64_t time_imprisoned_days = -1;

  PlayerPrisonerOpaqueFinalBoolV1 has_imprisonment_reason{};
  PlayerPrisonerOpaqueFinalBoolV1 has_banish_reason{};
  PlayerPrisonerOpaqueFinalBoolV1 has_execute_reason{};

  PlayerPrisonerRansomPreviewV1 ransom{};
  PlayerPrisonerInteractionPreviewV1 release_unconditional{};
  PlayerPrisonerInteractionPreviewV1 execute{};
  PlayerPrisonerInteractionPreviewV1 move_to_dungeon{};
  PlayerPrisonerInteractionPreviewV1 move_to_house_arrest{};
  PlayerPrisonerInteractionPreviewV1 torture{};

  friend bool operator==(const PlayerPrisonerRowV1 &,
                         const PlayerPrisonerRowV1 &) = default;
};

// This is the value-only handoff from a future exact-build reader. It owns all
// IDs, booleans and fixed strings; no native pointer or borrowed lifetime is
// present.
struct PlayerPrisonerSourceSampleV1 {
  bool source_read_complete = false;
  std::int32_t played_character_id = -1;
  bool played_character_identity_round_trip = false;
  bool prisoner_collection_complete = false;
  std::uint32_t total_prisoner_count = 0;
  std::uint32_t prisoner_count = 0;
  std::array<PlayerPrisonerRowV1, kPlayerPrisonerMaximumRowsV1> prisoners{};

  friend bool operator==(const PlayerPrisonerSourceSampleV1 &,
                         const PlayerPrisonerSourceSampleV1 &) = default;
};

struct PlayerPrisonerFrameV1 {
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  std::int32_t played_character_id = -1;
  bool played_character_alive = false;
  bool played_character_identity_round_trip = false;

  friend bool operator==(const PlayerPrisonerFrameV1 &,
                         const PlayerPrisonerFrameV1 &) = default;
};

// Both source samples must come from the same paused application-main turn.
// The semantic core publishes neither one unless the complete value copies
// agree.
struct PlayerPrisonerCaptureV1 {
  bool exact_build_admitted = false;
  std::array<char, kPlayerPrisonerSha256CapacityV1>
      admitted_executable_sha256{};
  bool source_adapter_bound = false;
  bool application_main_thread = false;
  PlayerPrisonerFrameV1 frame_before{};
  PlayerPrisonerSourceSampleV1 first_sample{};
  PlayerPrisonerSourceSampleV1 second_sample{};
  PlayerPrisonerFrameV1 frame_after{};
};

struct PlayerPrisonerReadinessV1 {
  bool collection_ready = false;
  bool crime_reasons_ready = false;
  bool ransom_previews_ready = false;
  bool ransom_candidate_available = false;
  bool release_previews_ready = false;
  bool punishment_legality_ready = false;
  bool same_frame_ready = false;
  bool semantic_ready = false;

  friend bool operator==(const PlayerPrisonerReadinessV1 &,
                         const PlayerPrisonerReadinessV1 &) = default;
};

struct PlayerPrisonerManagementSnapshotV1 {
  PlayerPrisonerSnapshotStatusV1 status =
      PlayerPrisonerSnapshotStatusV1::unavailable;
  PlayerPrisonerSnapshotFailureV1 unavailable_reason =
      PlayerPrisonerSnapshotFailureV1::source_adapter_unavailable;
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t total_prisoner_count = 0;
  std::uint32_t prisoner_count = 0;
  std::array<PlayerPrisonerRowV1, kPlayerPrisonerMaximumRowsV1> prisoners{};
  bool religious_details_exposed = false;
  PlayerPrisonerReadinessV1 readiness{};
};

bool AssignPlayerPrisonerKeyV1(
    std::string_view value, PlayerPrisonerKeyV1 &output) noexcept;

std::string_view PlayerPrisonerKeyViewV1(
    const PlayerPrisonerKeyV1 &value) noexcept;

PlayerPrisonerTypedKeyV1 PlayerPrisonerKnownKeyV1(
    std::string_view value) noexcept;

PlayerPrisonerTypedKeyV1 PlayerPrisonerUnknownKeyV1(
    PlayerPrisonerUnknownReasonV1 reason) noexcept;

bool ObservePlayerPrisonerManagementSnapshotV1(
    const PlayerPrisonerCaptureV1 &capture,
    PlayerPrisonerManagementSnapshotV1 &output) noexcept;

std::string_view PlayerPrisonerSnapshotFailureNameV1(
    PlayerPrisonerSnapshotFailureV1 failure) noexcept;

std::string_view PlayerPrisonerUnknownReasonNameV1(
    PlayerPrisonerUnknownReasonV1 reason) noexcept;

} // namespace xar::bridge
