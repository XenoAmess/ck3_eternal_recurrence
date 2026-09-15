#pragma once

#include "xar_bridge/council_composition_candidates_public_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class CouncilAssignCouncillorRouteV1 : std::uint8_t {
  none = 0,
  assign_vacant,
  replace_incumbent,
};

enum class CouncilAssignCouncillorFailureV1 : std::uint8_t {
  none = 0,
  request_contract_invalid,
  exact_build_mismatch,
  private_candidate_not_admitted,
  application_main_thread_required,
  callbacks_unavailable,
  observation_unavailable,
  not_paused,
  snapshot_binding_mismatch,
  position_outside_coverage,
  active_task_identity_unavailable,
  incumbent_identity_unavailable,
  candidate_equals_incumbent,
  final_legality_unavailable,
  candidate_not_in_exact_collection,
  candidate_identity_mismatch,
  candidate_already_councillor,
  candidate_is_guest,
  pending_character_interaction,
  incumbent_cannot_be_replaced,
  state_changed_before_submit,
  native_helper_not_invoked,
};

enum class CouncilAssignCouncillorAckStatusV1 : std::uint8_t {
  rejected_before_submit = 0,
  native_helper_invoked_verification_pending,
};

enum class CouncilAssignCouncillorReceiptStatusV1 : std::uint8_t {
  rejected = 0,
  postcondition_failed,
  applied,
};

struct CouncilAssignCouncillorActionRequestV1 {
  std::string request_id;
  std::string position_key;
  std::string expected_snapshot_id;
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::int32_t expected_owner_character_id = -1;
  std::int32_t candidate_character_id = -1;
  bool expected_has_incumbent = false;
  std::int32_t expected_incumbent_character_id = -1;
};

// One copied, pointer-free paused frame. The production adapter must source
// owner/incumbent/task identities from their exact-build stores and perform
// generation round-trips before setting the corresponding flags.
struct CouncilAssignCouncillorFrameV1 {
  bool available = false;
  bool paused = false;
  bool map_ready = false;
  std::string snapshot_id;
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t owner_character_id = -1;
  bool owner_identity_round_trip = false;
  std::string position_key;
  std::int32_t active_task_id = -1;
  bool active_task_identity_round_trip = false;
  bool has_incumbent = false;
  std::int32_t incumbent_character_id = -1;
  bool incumbent_identity_round_trip = false;

  friend bool operator==(const CouncilAssignCouncillorFrameV1 &,
                         const CouncilAssignCouncillorFrameV1 &) = default;
};

// This is the result of re-running the exact producer and the native final
// gates immediately before dispatch. A row copied from an older snapshot is
// insufficient. Replacement also requires the incumbent fireability result
// used by CFireFromCouncilConfirmation::CanConfirm.
struct CouncilAssignCouncillorFinalLegalityV1 {
  bool available = false;
  std::int32_t owner_character_id = -1;
  std::int32_t active_task_id = -1;
  std::string position_key;
  std::int32_t candidate_character_id = -1;
  std::uint32_t candidate_match_count = 0;
  bool candidate_identity_round_trip = false;
  bool candidate_already_councillor = false;
  bool candidate_is_guest = false;
  bool pending_character_interaction = false;
  bool incumbent_fireability_evaluated = false;
  bool incumbent_can_be_fired = false;
  std::string native_reason_key;
};

struct CouncilAssignCouncillorNativeSubmissionV1 {
  CouncilAssignCouncillorRouteV1 route =
      CouncilAssignCouncillorRouteV1::none;
  std::int32_t owner_character_id = -1;
  std::int32_t active_task_id = -1;
  std::int32_t candidate_character_id = -1;
  bool had_incumbent = false;
  std::int32_t previous_incumbent_character_id = -1;
};

struct CouncilAssignCouncillorActionAckV1 {
  CouncilAssignCouncillorAckStatusV1 status =
      CouncilAssignCouncillorAckStatusV1::rejected_before_submit;
  CouncilAssignCouncillorFailureV1 failure =
      CouncilAssignCouncillorFailureV1::callbacks_unavailable;
  std::string request_id;
  std::string pre_snapshot_id;
  std::uint64_t pre_public_revision = 0;
  std::uint64_t pre_native_revision = 0;
  std::int32_t pre_date_raw = 0;
  std::int32_t owner_character_id = -1;
  std::string position_key;
  std::int32_t active_task_id = -1;
  std::int32_t candidate_character_id = -1;
  bool had_incumbent = false;
  std::int32_t previous_incumbent_character_id = -1;
  CouncilAssignCouncillorRouteV1 route =
      CouncilAssignCouncillorRouteV1::none;
  bool native_helper_invoked = false;
  bool queue_acceptance_observed = false;
  bool verification_pending = false;
  std::string native_reason_key;
};

struct CouncilAssignCouncillorActionReceiptV1 {
  CouncilAssignCouncillorReceiptStatusV1 status =
      CouncilAssignCouncillorReceiptStatusV1::postcondition_failed;
  CouncilAssignCouncillorFailureV1 rejected_action_failure =
      CouncilAssignCouncillorFailureV1::none;
  std::string request_id;
  std::string post_snapshot_id;
  std::uint64_t post_public_revision = 0;
  std::uint64_t post_native_revision = 0;
  std::int32_t post_date_raw = 0;
  std::int32_t owner_character_id = -1;
  std::string position_key;
  std::int32_t incumbent_character_id = -1;
  bool incumbent_identity_round_trip = false;
  bool postcondition_verified = false;
  std::string reason;
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kCouncilAssignCouncillorActionTargetCapabilityV1 =
        "game.action.assign-councillor-v1";
inline constexpr std::string_view
    kCouncilAssignCouncillorActionPrivateKeyV1 =
        "g2_council_assign_councillor_action_v1_private";
inline constexpr std::string_view kCouncilAssignCouncillorPositionKeyV1 =
    "councillor_steward";
inline constexpr std::string_view kCouncilAssignCouncillorGameVersionV1 =
    "1.19.0.6";
inline constexpr std::string_view
    kCouncilAssignCouncillorExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::uintptr_t kCouncilAssignCouncillorSetPositionRvaV1 =
    0x10573C0;
inline constexpr std::uintptr_t
    kCouncilAssignCouncillorConfirmationCanConfirmRvaV1 = 0x105C770;
inline constexpr std::uintptr_t
    kCouncilAssignCouncillorConfirmationConfirmRvaV1 = 0x105C940;
inline constexpr std::uintptr_t
    kCouncilAssignCouncillorSendInteractionHelperRvaV1 = 0x1056C00;
inline constexpr std::uintptr_t
    kCouncilAssignCouncillorSendInteractionValidatorRvaV1 = 0x2C43F00;
inline constexpr bool kCouncilAssignCouncillorAdvertisedByDefaultV1 = false;
inline constexpr std::size_t kCouncilAssignCouncillorRequestIdCapacityV1 = 64;
inline constexpr std::size_t kCouncilAssignCouncillorSnapshotIdCapacityV1 = 64;

struct CouncilAssignCouncillorNativeEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool native_command_abi_certified = false;
  bool private_candidate_admitted = false;
  bool offline_fixture = false;
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
};

using CaptureCouncilAssignCouncillorFrameV1 = bool (*)(
    void *context, game::CouncilAssignCouncillorFrameV1 &output) noexcept;
using RecheckCouncilAssignCouncillorFinalLegalityV1 = bool (*)(
    void *context, const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept;
// The exact 1.19.0.6 helper is void. true therefore means only that the
// adapter invoked it; it must never be described as queue acceptance.
using InvokeCouncilAssignCouncillorNativeHelperV1 = bool (*)(
    void *context,
    const game::CouncilAssignCouncillorNativeSubmissionV1 &submission) noexcept;

struct CouncilAssignCouncillorActionAccessV1 {
  void *context = nullptr;
  CaptureCouncilAssignCouncillorFrameV1 capture_frame = nullptr;
  RecheckCouncilAssignCouncillorFinalLegalityV1 recheck_final_legality =
      nullptr;
  InvokeCouncilAssignCouncillorNativeHelperV1 invoke_native_helper = nullptr;
};

bool PrepareCouncilAssignCouncillorActionRequestV1(
    const game::CouncilCompositionCandidatesPublicV1 &candidates,
    std::int32_t candidate_character_id, std::string_view request_id,
    game::CouncilAssignCouncillorActionRequestV1 &request) noexcept;

using CouncilAssignCouncillorNativeHelperOverrideV1 = void (*)(
    void *context, std::int32_t candidate_character_id,
    std::int32_t active_task_id) noexcept;

// Narrow production adapter for the only submit seam proven by this package.
// It intentionally does not manufacture the frame or final-legality result.
struct CouncilAssignCouncillorNativeSubmitAdapterV1 {
  CouncilAssignCouncillorNativeEnvironmentV1 environment{};
  void *override_context = nullptr;
  CouncilAssignCouncillorNativeHelperOverrideV1 helper_override = nullptr;
  std::uint64_t invocation_count = 0;
};

bool InvokeCouncilAssignCouncillorNativeSubmitAdapterV1(
    void *context,
    const game::CouncilAssignCouncillorNativeSubmissionV1 &submission) noexcept;

game::CouncilAssignCouncillorAckStatusV1 ExecuteCouncilAssignCouncillorActionV1(
    const CouncilAssignCouncillorNativeEnvironmentV1 &environment,
    const CouncilAssignCouncillorActionAccessV1 &access,
    const game::CouncilAssignCouncillorActionRequestV1 &request,
    game::CouncilAssignCouncillorActionAckV1 &ack) noexcept;

game::CouncilAssignCouncillorReceiptStatusV1
VerifyCouncilAssignCouncillorActionReceiptV1(
    const game::CouncilAssignCouncillorActionAckV1 &ack,
    const game::CouncilAssignCouncillorFrameV1 &post,
    game::CouncilAssignCouncillorActionReceiptV1 &receipt) noexcept;

std::string_view CouncilAssignCouncillorFailureKeyV1(
    game::CouncilAssignCouncillorFailureV1 failure) noexcept;
std::string_view CouncilAssignCouncillorRouteKeyV1(
    game::CouncilAssignCouncillorRouteV1 route) noexcept;

} // namespace xar::ck3_11906
