#pragma once

#include "xar_bridge/active_scheme_state_v1_private_native_binder.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kActiveSchemeSemanticActionV1PrivateGameVersion = "1.19.0.6";
inline constexpr std::string_view
    kActiveSchemeSemanticActionV1PrivateExecutableSha256 =
        kActiveSchemeStateV1PrivateObserverExecutableSha256;
inline constexpr std::string_view
    kActiveSchemeSemanticActionV1PrivateContractStage =
        "private_action_core_shared_glue_and_live_pending";
inline constexpr std::size_t
    kActiveSchemeSemanticActionV1PrivateMaximumPriorIdentities =
        kActiveSchemeStateV1PrivateMaximumRows;

enum class ActiveSchemeSemanticActionV1PrivateFailure : std::uint8_t {
  none,
  request_contract,
  exact_build_mismatch,
  action_route_unavailable,
  observation_unavailable,
  snapshot_mismatch,
  actor_or_target_mismatch,
  interaction_not_allowed,
  matching_scheme_already_active,
  precondition_unavailable,
  interaction_not_shown,
  interaction_not_valid,
  can_start_scheme_denied,
  starter_package_invalid,
  preview_unresolved,
  preview_invalid,
  state_changed_before_submit,
  submit_rejected,
  post_observation_unavailable,
  post_observation_not_fresh,
  post_actor_changed,
  postcondition_missing,
  postcondition_ambiguous,
};

enum class ActiveSchemeSemanticActionV1PrivateAckStatus : std::uint8_t {
  rejected_before_submit,
  submitted_verification_pending,
};

enum class ActiveSchemeSemanticActionV1PrivateReceiptStatus : std::uint8_t {
  rejected,
  applied,
  red,
};

enum class ActiveSchemeSemanticActionV1PrivatePreviewStatus : std::uint8_t {
  unresolved,
  available,
  explicitly_unavailable,
};

struct ActiveSchemeSemanticActionV1PrivatePreviewValue {
  ActiveSchemeSemanticActionV1PrivatePreviewStatus status =
      ActiveSchemeSemanticActionV1PrivatePreviewStatus::unresolved;
  std::int32_t value = 0;

  friend bool operator==(
      const ActiveSchemeSemanticActionV1PrivatePreviewValue &,
      const ActiveSchemeSemanticActionV1PrivatePreviewValue &) = default;
};

// A copied result from the exact-build character-interaction validator.  The
// producer must evaluate all fields in one paused application-main frame and
// must not retain or publish engine pointers.
struct ActiveSchemeSemanticActionV1PrivatePrecondition {
  bool available = false;
  bool paused = false;
  std::uint64_t capture_epoch = 0;
  std::int64_t date_raw = 0;
  std::int64_t actor_character_id = 0;
  ActiveSchemeStateV1PrivateTargetKind target_kind =
      ActiveSchemeStateV1PrivateTargetKind::unavailable;
  std::int64_t target_id = 0;
  std::string interaction_key;
  std::string scheme_type_key;

  bool shown_evaluated = false;
  bool shown = false;
  bool validity_evaluated = false;
  bool valid = false;
  bool can_start_scheme_evaluated = false;
  bool can_start_scheme = false;
  std::string native_reason_key;

  bool starter_options_evaluated = false;
  bool starter_options_exclusive = false;
  std::uint32_t starter_option_count = 0;
  std::string selected_starter_package;

  ActiveSchemeSemanticActionV1PrivatePreviewValue success_chance{};
  ActiveSchemeSemanticActionV1PrivatePreviewValue maximum_success_chance{};
  ActiveSchemeSemanticActionV1PrivatePreviewValue secrecy{};

  friend bool operator==(
      const ActiveSchemeSemanticActionV1PrivatePrecondition &,
      const ActiveSchemeSemanticActionV1PrivatePrecondition &) = default;
};

struct ActiveSchemeSemanticActionV1PrivateRequest {
  std::string request_id;
  std::string interaction_key;
  std::int64_t actor_character_id = 0;
  ActiveSchemeStateV1PrivateTargetKind target_kind =
      ActiveSchemeStateV1PrivateTargetKind::unavailable;
  std::int64_t target_id = 0;
  std::uint64_t expected_capture_epoch = 0;
  std::uint64_t expected_container_generation = 0;
  std::int64_t expected_date_raw = 0;
  std::string selected_starter_package;
};

struct ActiveSchemeSemanticActionV1PrivateCommand {
  std::string request_id;
  std::string interaction_key;
  std::string scheme_type_key;
  std::int64_t actor_character_id = 0;
  ActiveSchemeStateV1PrivateTargetKind target_kind =
      ActiveSchemeStateV1PrivateTargetKind::unavailable;
  std::int64_t target_id = 0;
  std::string selected_starter_package;
};

struct ActiveSchemeSemanticActionV1PrivateIdentity {
  std::uint64_t instance_id = 0;
  std::uint32_t generation = 0;
};

struct ActiveSchemeSemanticActionV1PrivateAck {
  ActiveSchemeSemanticActionV1PrivateAckStatus status =
      ActiveSchemeSemanticActionV1PrivateAckStatus::rejected_before_submit;
  ActiveSchemeSemanticActionV1PrivateFailure failure =
      ActiveSchemeSemanticActionV1PrivateFailure::none;
  std::string reason;
  std::string native_reason_key;
  std::string request_id;
  std::string interaction_key;
  std::string scheme_type_key;
  std::int64_t actor_character_id = 0;
  ActiveSchemeStateV1PrivateTargetKind target_kind =
      ActiveSchemeStateV1PrivateTargetKind::unavailable;
  std::int64_t target_id = 0;
  std::uint64_t pre_capture_epoch = 0;
  std::uint64_t pre_container_generation = 0;
  std::int64_t pre_date_raw = 0;
  bool submit_attempted = false;
  std::uint32_t submit_call_count = 0;
  bool verification_pending = false;
  std::size_t prior_identity_count = 0;
  std::array<ActiveSchemeSemanticActionV1PrivateIdentity,
             kActiveSchemeSemanticActionV1PrivateMaximumPriorIdentities>
      prior_identities{};
};

struct ActiveSchemeSemanticActionV1PrivateReceipt {
  ActiveSchemeSemanticActionV1PrivateReceiptStatus status =
      ActiveSchemeSemanticActionV1PrivateReceiptStatus::red;
  ActiveSchemeSemanticActionV1PrivateFailure failure =
      ActiveSchemeSemanticActionV1PrivateFailure::postcondition_missing;
  std::string reason;
  std::string request_id;
  std::uint64_t post_capture_epoch = 0;
  std::uint64_t post_container_generation = 0;
  std::int64_t post_date_raw = 0;
  std::uint64_t scheme_instance_id = 0;
  std::uint32_t scheme_instance_generation = 0;
  bool postcondition_verified = false;
};

using CaptureActiveSchemeSemanticActionObservationV1Private = bool (*)(
    void *context,
    ActiveSchemeStateV1PrivateObservation &output) noexcept;
using CaptureActiveSchemeSemanticActionPreconditionV1Private = bool (*)(
    void *context,
    ActiveSchemeSemanticActionV1PrivatePrecondition &output) noexcept;

// True means one command was handed to the existing character-interaction
// send-command route. False must mean it was definitely not handed off.
using SubmitActiveSchemeSemanticActionV1Private = bool (*)(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateCommand &command) noexcept;

struct ActiveSchemeSemanticActionV1PrivateAccess {
  void *context = nullptr;
  CaptureActiveSchemeSemanticActionObservationV1Private capture_observation =
      nullptr;
  CaptureActiveSchemeSemanticActionPreconditionV1Private
      capture_precondition = nullptr;
  SubmitActiveSchemeSemanticActionV1Private submit = nullptr;
};

struct ActiveSchemeSemanticActionV1PrivateEnvironment {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool character_interaction_route_bound = false;
  bool offline_fixture = false;
};

ActiveSchemeSemanticActionV1PrivateAckStatus
ExecuteActiveSchemeSemanticActionV1Private(
    const ActiveSchemeSemanticActionV1PrivateEnvironment &environment,
    const ActiveSchemeSemanticActionV1PrivateAccess &access,
    const ActiveSchemeSemanticActionV1PrivateRequest &request,
    ActiveSchemeSemanticActionV1PrivateAck &ack) noexcept;

// Performs the required fresh SCHEME4-backed reread itself. The submit ACK is
// never accepted as the gameplay postcondition.
ActiveSchemeSemanticActionV1PrivateReceiptStatus
VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
    const ActiveSchemeSemanticActionV1PrivateAccess &access,
    const ActiveSchemeSemanticActionV1PrivateAck &ack,
    ActiveSchemeSemanticActionV1PrivateReceipt &receipt) noexcept;

std::string_view ActiveSchemeSemanticActionV1PrivateFailureName(
    ActiveSchemeSemanticActionV1PrivateFailure failure) noexcept;

} // namespace xar::bridge
