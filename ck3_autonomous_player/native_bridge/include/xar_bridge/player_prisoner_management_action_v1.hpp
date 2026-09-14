#pragma once

#include "xar_bridge/player_prisoner_management_snapshot_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kPlayerPrisonerManagementActionV1PrivateKey =
        "player_prisoner_management_action_v1";
inline constexpr std::string_view
    kPlayerPrisonerManagementActionV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kPlayerPrisonerManagementActionV1ContractStage =
        "private_semantic_core_pending_exact_command_adapter";
inline constexpr bool
    kPlayerPrisonerManagementActionV1AdvertisedByDefault = false;

enum class PlayerPrisonerActionKindV1 : std::uint8_t {
  unknown,
  ransom,
  release_unconditional,
  punish_execute,
};

enum class PlayerPrisonerActionFailureClassV1 : std::uint8_t {
  none,
  request_contract,
  exact_build_binding,
  snapshot_binding,
  prisoner_binding,
  final_legality,
  native_command_dispatch,
  state_observation,
};

enum class PlayerPrisonerActionAckStatusV1 : std::uint8_t {
  rejected_before_submit,
  submitted_verification_pending,
};

enum class PlayerPrisonerActionReceiptStatusV1 : std::uint8_t {
  rejected,
  applied,
  postcondition_failed,
};

struct PlayerPrisonerActionRequestV1 {
  std::string_view request_id{};
  PlayerPrisonerActionKindV1 action = PlayerPrisonerActionKindV1::unknown;
  std::int32_t expected_player_character_id = -1;
  std::int32_t prisoner_character_id = -1;
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_proof_epoch = 0;
  std::int64_t expected_date_raw = 0;
};

// Value-only input for a later exact-build native adapter. Ransom terms are
// copied from the engine-final preview; callers cannot invent or replace them.
struct PlayerPrisonerActionSubmissionV1 {
  PlayerPrisonerActionKindV1 action = PlayerPrisonerActionKindV1::unknown;
  std::int32_t player_character_id = -1;
  std::int32_t prisoner_character_id = -1;
  std::int32_t payer_character_id = -1;
  PlayerPrisonerTypedKeyV1 selected_option_key{};
  PlayerPrisonerTypedKeyV1 resource_key{};
  std::int64_t resource_amount_raw = 0;
  std::uint64_t pre_public_revision = 0;
  std::uint64_t pre_native_revision = 0;
  std::uint64_t pre_proof_epoch = 0;
  std::int64_t pre_date_raw = 0;
};

struct PlayerPrisonerActionAckV1 {
  PlayerPrisonerActionAckStatusV1 status =
      PlayerPrisonerActionAckStatusV1::rejected_before_submit;
  bool verification_pending = false;
  std::string request_id;
  PlayerPrisonerActionKindV1 action = PlayerPrisonerActionKindV1::unknown;
  std::int32_t player_character_id = -1;
  std::int32_t prisoner_character_id = -1;
  PlayerPrisonerCustodyKindV1 pre_custody =
      PlayerPrisonerCustodyKindV1::unknown;
  std::int32_t payer_character_id = -1;
  PlayerPrisonerTypedKeyV1 selected_option_key{};
  PlayerPrisonerTypedKeyV1 resource_key{};
  std::int64_t resource_amount_raw = 0;
  bool native_execute_reason_known = false;
  bool native_execute_reason = false;
  std::uint64_t pre_public_revision = 0;
  std::uint64_t pre_native_revision = 0;
  std::uint64_t pre_proof_epoch = 0;
  std::int64_t pre_date_raw = 0;
  PlayerPrisonerActionFailureClassV1 failure_class =
      PlayerPrisonerActionFailureClassV1::none;
  std::string rejection_reason;
};

struct PlayerPrisonerActionReceiptV1 {
  PlayerPrisonerActionReceiptStatusV1 status =
      PlayerPrisonerActionReceiptStatusV1::postcondition_failed;
  std::string request_id;
  PlayerPrisonerActionKindV1 action = PlayerPrisonerActionKindV1::unknown;
  std::int32_t player_character_id = -1;
  std::int32_t prisoner_character_id = -1;
  std::uint64_t post_public_revision = 0;
  std::uint64_t post_native_revision = 0;
  std::uint64_t post_proof_epoch = 0;
  std::int64_t post_date_raw = 0;
  bool complete_prisoner_collection_reread = false;
  bool target_still_imprisoned = false;
  PlayerPrisonerCustodyKindV1 post_custody =
      PlayerPrisonerCustodyKindV1::unknown;
  bool target_state_changed = false;
  bool postcondition_verified = false;
  std::string reason;
};

struct PlayerPrisonerActionEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool command_abi_certified = false;
  bool offline_fixture_command = false;
};

using CapturePlayerPrisonerActionSnapshotV1 = bool (*)(
    void *context, PlayerPrisonerManagementSnapshotV1 &output) noexcept;
using IsPlayerPrisonerActionMainThreadV1 = bool (*)(void *context) noexcept;

// true means exactly one command was handed to a native submitter. It never
// means CK3 applied the action.
using SubmitPlayerPrisonerActionV1 = bool (*)(
    void *context, const PlayerPrisonerActionSubmissionV1 &submission) noexcept;

struct PlayerPrisonerActionAccessV1 {
  void *context = nullptr;
  CapturePlayerPrisonerActionSnapshotV1 capture_snapshot = nullptr;
  IsPlayerPrisonerActionMainThreadV1 is_application_main_thread = nullptr;
  SubmitPlayerPrisonerActionV1 submit_native = nullptr;
};

PlayerPrisonerActionEnvironmentV1 BindPlayerPrisonerActionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

PlayerPrisonerActionAckStatusV1 ExecutePlayerPrisonerActionV1(
    const PlayerPrisonerActionEnvironmentV1 &environment,
    const PlayerPrisonerActionAccessV1 &access,
    const PlayerPrisonerActionRequestV1 &request,
    PlayerPrisonerActionAckV1 &ack) noexcept;

// Captures a new PRISONER3 snapshot internally. A submitted ACK is applied
// only after the complete collection proves the same full prisoner ID absent.
PlayerPrisonerActionReceiptStatusV1 VerifyPlayerPrisonerActionReceiptV1(
    const PlayerPrisonerActionAccessV1 &access,
    const PlayerPrisonerActionAckV1 &ack,
    PlayerPrisonerActionReceiptV1 &receipt) noexcept;

std::string_view PlayerPrisonerActionFailureClassNameV1(
    PlayerPrisonerActionFailureClassV1 failure) noexcept;

} // namespace xar::bridge
