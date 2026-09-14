#pragma once

#include "xar_bridge/player_lifestyle_window_candidates_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class PlayerLifestyleSelectionKindV1 : std::uint32_t {
  unknown = 0,
  focus = 1,
  perk = 2,
};

enum class PlayerLifestyleSelectionActionFailureClassV1 : std::uint32_t {
  none = 0,
  request_contract,
  exact_build_binding,
  snapshot_binding,
  final_legality,
  state_observation,
  native_command_dispatch,
};

enum class PlayerLifestyleSelectionActionAckStatusV1 : std::uint32_t {
  rejected_before_submit = 0,
  submitted_verification_pending = 1,
};

enum class PlayerLifestyleSelectionActionReceiptStatusV1 : std::uint32_t {
  rejected = 0,
  applied = 1,
  postcondition_failed = 2,
};

struct PlayerLifestyleSelectionProgressRowV1 {
  PlayerLifestyleWindowStableKeyV1 lifestyle_key{};
  std::int64_t experience_raw = 0;
  std::int32_t perk_points = 0;

  friend bool operator==(const PlayerLifestyleSelectionProgressRowV1 &,
                         const PlayerLifestyleSelectionProgressRowV1 &) =
      default;
};

inline constexpr std::size_t kPlayerLifestyleSelectionMaximumProgressRowsV1 =
    64;

// Produced from one paused native transaction. All four observation groups
// are mandatory: current focus, the complete owned-perk set, lifestyle XP,
// and lifestyle perk points.
struct PlayerLifestyleSelectionStateObservationV1 {
  bool available = false;
  bool paused = false;
  std::array<char, kPlayerLifestyleWindowSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t player_character_id = 0xFFFFFFFFU;

  bool current_focus_known = false;
  bool has_current_focus = false;
  PlayerLifestyleWindowStableKeyV1 current_focus_key{};

  bool owned_perks_fully_materialized = false;
  std::uint32_t owned_perk_count = 0;
  std::array<PlayerLifestyleWindowStableKeyV1,
             kPlayerLifestyleWindowMaximumPerksV1>
      owned_perk_keys{};

  bool lifestyle_progress_fully_materialized = false;
  std::uint32_t lifestyle_progress_count = 0;
  std::array<PlayerLifestyleSelectionProgressRowV1,
             kPlayerLifestyleSelectionMaximumProgressRowsV1>
      lifestyle_progress{};

  friend bool operator==(const PlayerLifestyleSelectionStateObservationV1 &,
                         const PlayerLifestyleSelectionStateObservationV1 &) =
      default;
};

// The producer must capture candidates and state inside the same paused
// transaction. The action core checks their identity and revision fields.
struct PlayerLifestyleSelectionPreconditionV1 {
  PlayerLifestyleWindowCandidatesV1 candidates{};
  PlayerLifestyleSelectionStateObservationV1 state{};
};

struct PlayerLifestyleSelectionActionRequestV1 {
  std::string_view request_id{};
  PlayerLifestyleSelectionKindV1 kind =
      PlayerLifestyleSelectionKindV1::unknown;
  std::string_view target_key{};
  std::string_view expected_snapshot_id{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_proof_epoch = 0;
  std::int32_t expected_date_raw = 0;
  std::uint32_t expected_player_character_id = 0xFFFFFFFFU;
};

struct PlayerLifestyleSelectionActionAckV1 {
  PlayerLifestyleSelectionActionAckStatusV1 status =
      PlayerLifestyleSelectionActionAckStatusV1::rejected_before_submit;
  bool verification_pending = false;
  std::string request_id;
  PlayerLifestyleSelectionKindV1 kind =
      PlayerLifestyleSelectionKindV1::unknown;
  PlayerLifestyleWindowStableKeyV1 target_key{};
  PlayerLifestyleWindowStableKeyV1 target_lifestyle_key{};
  std::array<char, kPlayerLifestyleWindowSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t pre_public_revision = 0;
  std::uint64_t pre_native_revision = 0;
  std::uint64_t pre_proof_epoch = 0;
  std::int32_t pre_date_raw = 0;
  std::uint32_t player_character_id = 0xFFFFFFFFU;
  bool pre_has_current_focus = false;
  PlayerLifestyleWindowStableKeyV1 pre_current_focus_key{};
  std::uint32_t pre_owned_perk_count = 0;
  bool pre_target_perk_owned = false;
  std::int64_t pre_target_lifestyle_experience_raw = 0;
  std::int32_t pre_target_lifestyle_perk_points = 0;
  PlayerLifestyleSelectionActionFailureClassV1 failure_class =
      PlayerLifestyleSelectionActionFailureClassV1::none;
  std::string rejection_reason;
};

struct PlayerLifestyleSelectionActionReceiptV1 {
  PlayerLifestyleSelectionActionReceiptStatusV1 status =
      PlayerLifestyleSelectionActionReceiptStatusV1::postcondition_failed;
  std::string request_id;
  PlayerLifestyleSelectionKindV1 kind =
      PlayerLifestyleSelectionKindV1::unknown;
  PlayerLifestyleWindowStableKeyV1 target_key{};
  std::string reason;
  std::uint64_t post_public_revision = 0;
  std::uint64_t post_native_revision = 0;
  std::uint64_t post_proof_epoch = 0;
  std::int32_t post_date_raw = 0;
  std::uint32_t player_character_id = 0xFFFFFFFFU;
  bool post_has_current_focus = false;
  PlayerLifestyleWindowStableKeyV1 post_current_focus_key{};
  std::uint32_t post_owned_perk_count = 0;
  bool post_target_perk_owned = false;
  std::int64_t post_target_lifestyle_experience_raw = 0;
  std::int32_t post_target_lifestyle_perk_points = 0;
  bool current_focus_reread = false;
  bool owned_perks_reread = false;
  bool experience_reread = false;
  bool perk_points_reread = false;
  bool target_state_changed = false;
  bool postcondition_verified = false;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kPlayerLifestyleSelectionActionPrivateKeyV1 =
    "g2_player_lifestyle_selection_action_v1";
inline constexpr std::string_view kPlayerLifestyleSelectionActionGameVersionV1 =
    "1.19.0.6";
inline constexpr std::string_view
    kPlayerLifestyleSelectionActionExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kPlayerLifestyleSelectionActionContractStageV1 =
        "private_semantic_core_pending_exact_command_adapter";
inline constexpr bool kPlayerLifestyleSelectionActionAdvertisedByDefaultV1 =
    false;

struct PlayerLifestyleSelectionActionEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool command_abi_certified = false;
  bool offline_fixture_command = false;
};

using CapturePlayerLifestyleSelectionPreconditionV1 = bool (*)(
    void *context,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept;
using CapturePlayerLifestyleSelectionReceiptStateV1 = bool (*)(
    void *context,
    game::PlayerLifestyleSelectionStateObservationV1 &output) noexcept;
using IsPlayerLifestyleSelectionMainThreadV1 = bool (*)(
    void *context) noexcept;

// A true return means exactly one command was handed to the engine submitter.
// It never means that CK3 applied the selection.
using SubmitPlayerLifestyleSelectionCommandV1 = bool (*)(
    void *context, game::PlayerLifestyleSelectionKindV1 kind,
    const game::PlayerLifestyleWindowStableKeyV1 &target_key) noexcept;

struct PlayerLifestyleSelectionActionAccessV1 {
  void *context = nullptr;
  CapturePlayerLifestyleSelectionPreconditionV1 capture_precondition = nullptr;
  CapturePlayerLifestyleSelectionReceiptStateV1 capture_receipt_state = nullptr;
  IsPlayerLifestyleSelectionMainThreadV1 is_main_thread = nullptr;
  SubmitPlayerLifestyleSelectionCommandV1 submit_native = nullptr;
};

PlayerLifestyleSelectionActionEnvironmentV1
BindPlayerLifestyleSelectionActionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

game::PlayerLifestyleSelectionActionAckStatusV1
ExecutePlayerLifestyleSelectionActionV1(
    const PlayerLifestyleSelectionActionEnvironmentV1 &environment,
    const PlayerLifestyleSelectionActionAccessV1 &access,
    const game::PlayerLifestyleSelectionActionRequestV1 &request,
    game::PlayerLifestyleSelectionActionAckV1 &ack) noexcept;

// A pending ACK is resolved only by this function's fresh state capture.
game::PlayerLifestyleSelectionActionReceiptStatusV1
VerifyPlayerLifestyleSelectionActionReceiptV1(
    const PlayerLifestyleSelectionActionAccessV1 &access,
    const game::PlayerLifestyleSelectionActionAckV1 &ack,
    game::PlayerLifestyleSelectionActionReceiptV1 &receipt) noexcept;

std::string_view PlayerLifestyleSelectionActionFailureClassKeyV1(
    game::PlayerLifestyleSelectionActionFailureClassV1 value) noexcept;

} // namespace xar::ck3_11906
