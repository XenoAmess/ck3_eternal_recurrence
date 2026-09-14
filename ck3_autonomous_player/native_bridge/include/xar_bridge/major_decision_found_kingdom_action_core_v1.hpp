#pragma once

#include "xar_bridge/major_decision_found_kingdom_observer_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kMajorDecisionFoundKingdomActionCoreKeyV1 =
        "major_decision_found_kingdom_action_core_v1";
inline constexpr std::string_view
    kMajorDecisionFoundKingdomActionCoreStageV1 =
        "private-static-action-core-submit-abi-unbound";

enum class MajorDecisionFoundKingdomActionFailureClassV1 : std::uint8_t {
  none = 0,
  request_contract,
  exact_build,
  pending_action,
  observation,
  identity_binding,
  eligibility,
  resources,
  can_take,
  native_submit,
};

enum class MajorDecisionFoundKingdomActionAckStatusV1 : std::uint8_t {
  rejected_before_submit = 0,
  submitted_verification_pending,
};

enum class MajorDecisionFoundKingdomActionReceiptStatusV1 : std::uint8_t {
  rejected = 0,
  applied,
  postcondition_failed,
};

enum class MajorDecisionFoundKingdomTitleTierV1 : std::uint8_t {
  unknown = 0,
  barony,
  county,
  duchy,
  kingdom,
  empire,
};

struct MajorDecisionFoundKingdomActionBindingV1 {
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint64_t decision_database_identity = 0;
  std::uint64_t decision_database_generation = 0;
  std::uint64_t decision_definition_identity = 0;
  std::uint64_t decision_definition_generation = 0;
  std::int32_t primary_title_id = -1;
  std::uint64_t primary_title_identity = 0;
  std::uint64_t primary_title_generation = 0;
  std::uint64_t world_identity = 0;
  std::uint64_t world_generation = 0;
  std::uint64_t world_revision = 0;

  friend bool operator==(const MajorDecisionFoundKingdomActionBindingV1 &,
                         const MajorDecisionFoundKingdomActionBindingV1 &) =
      default;
};

// One callback capture must populate this pointer-free observation from a
// single paused transaction. The action core independently asks for two such
// captures immediately before submit.
struct MajorDecisionFoundKingdomActionPreconditionV1 {
  bool available = false;
  bool application_main_thread = false;
  bool paused = false;
  bool map_ready = false;
  bool played_character_alive = false;
  bool played_character_identity_round_trip = false;
  bool decision_database_identity_round_trip = false;
  bool decision_definition_identity_round_trip = false;
  bool decision_source_block_sha256_round_trip = false;
  std::string decision_id;
  MajorDecisionFoundKingdomActionBindingV1 binding{};
  MajorDecisionTypedBoolV1 is_shown{};
  MajorDecisionTypedBoolV1 is_valid{};
  MajorDecisionTypedBoolV1 is_valid_showing_failures_only{};
  MajorDecisionEvaluatedCostV1 evaluated_cost{};
  MajorDecisionTypedBoolV1 is_affordable{};
  MajorDecisionTypedBoolV1 can_take{};
  MajorDecisionEffectPreviewBoundaryV1 effect_preview{};

  friend bool operator==(
      const MajorDecisionFoundKingdomActionPreconditionV1 &,
      const MajorDecisionFoundKingdomActionPreconditionV1 &) = default;
};

struct MajorDecisionFoundKingdomActionRequestV1 {
  std::string request_id;
  std::string decision_id;
  MajorDecisionFoundKingdomActionBindingV1 expected_binding{};
  MajorDecisionEvaluatedCostV1 expected_evaluated_cost{};
};

struct MajorDecisionFoundKingdomActionEnvironmentV1 {
  bool action_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_game_version{};
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool submit_abi_certified = false;
  bool offline_fixture_submit = false;
};

using CaptureMajorDecisionFoundKingdomActionPreconditionV1 = bool (*)(
    void *context,
    MajorDecisionFoundKingdomActionPreconditionV1 &output) noexcept;

// A true return means that exactly one engine submission was accepted. It
// does not mean the decision effect ran or that any postcondition holds.
using SubmitMajorDecisionFoundKingdomActionV1 = bool (*)(
    void *context,
    const MajorDecisionFoundKingdomActionBindingV1 &binding,
    std::string_view decision_id) noexcept;

struct MajorDecisionFoundKingdomActionAccessV1 {
  void *context = nullptr;
  CaptureMajorDecisionFoundKingdomActionPreconditionV1 capture_precondition =
      nullptr;
  SubmitMajorDecisionFoundKingdomActionV1 submit = nullptr;
};

struct MajorDecisionFoundKingdomActionAckV1 {
  MajorDecisionFoundKingdomActionAckStatusV1 status =
      MajorDecisionFoundKingdomActionAckStatusV1::rejected_before_submit;
  bool verification_pending = false;
  bool effect_preview_available = false;
  bool exact_benefit_claimed = false;
  std::string request_id;
  std::string decision_id;
  std::uint64_t submission_sequence = 0;
  MajorDecisionFoundKingdomActionBindingV1 pre_binding{};
  MajorDecisionEvaluatedCostV1 submitted_evaluated_cost{};
  MajorDecisionFoundKingdomActionFailureClassV1 failure_class =
      MajorDecisionFoundKingdomActionFailureClassV1::none;
  std::string rejection_reason;
};

struct MajorDecisionFoundKingdomActionStateV1 {
  bool verification_pending = false;
  std::uint64_t next_submission_sequence = 1;
  std::uint64_t pending_submission_sequence = 0;
  std::string pending_request_id;
  std::string pending_decision_id;
  MajorDecisionFoundKingdomActionBindingV1 pending_binding{};
  MajorDecisionEvaluatedCostV1 pending_evaluated_cost{};
};

// The post observer reports only independently read state. In particular, it
// must not copy a requested title ID or an expected world result from the ACK.
struct MajorDecisionFoundKingdomActionPostconditionV1 {
  bool available = false;
  bool application_main_thread = false;
  bool paused = false;
  bool map_ready = false;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  std::int32_t played_character_id = -1;
  bool played_character_identity_round_trip = false;
  std::uint64_t decision_database_identity = 0;
  std::uint64_t decision_database_generation = 0;
  bool decision_database_identity_round_trip = false;

  bool decision_state_observed = false;
  bool decision_definition_present = false;
  std::uint64_t decision_definition_identity = 0;
  std::uint64_t decision_definition_generation = 0;
  bool decision_definition_identity_round_trip = false;
  bool decision_can_take_known = false;
  bool decision_can_take = false;

  bool primary_title_observed = false;
  std::int32_t primary_title_id = -1;
  std::uint64_t primary_title_identity = 0;
  std::uint64_t primary_title_generation = 0;
  MajorDecisionFoundKingdomTitleTierV1 primary_title_tier =
      MajorDecisionFoundKingdomTitleTierV1::unknown;
  std::int32_t primary_title_holder_character_id = -1;
  bool primary_title_identity_round_trip = false;
  bool primary_title_holder_identity_round_trip = false;
  bool player_primary_title_round_trip = false;
  bool dynamic_custom_kingdom_observed = false;

  bool world_outcome_observed = false;
  std::uint64_t world_identity = 0;
  std::uint64_t world_generation = 0;
  std::uint64_t world_revision = 0;
  bool world_identity_round_trip = false;
  bool new_title_registered = false;
  bool title_world_index_round_trip = false;
};

struct MajorDecisionFoundKingdomActionReceiptV1 {
  MajorDecisionFoundKingdomActionReceiptStatusV1 status =
      MajorDecisionFoundKingdomActionReceiptStatusV1::postcondition_failed;
  bool postcondition_verified = false;
  bool effect_preview_available = false;
  bool exact_benefit_claimed = false;
  std::string request_id;
  std::uint64_t submission_sequence = 0;
  std::string reason;
  std::uint64_t post_snapshot_revision = 0;
  std::uint64_t post_native_revision = 0;
  std::uint64_t post_world_identity = 0;
  std::uint64_t post_world_generation = 0;
  std::uint64_t post_world_revision = 0;
  std::int64_t post_date_raw = 0;
  std::int32_t played_character_id = -1;
  bool decision_no_longer_takeable = false;
  std::int32_t observed_primary_title_id = -1;
  std::uint64_t observed_primary_title_identity = 0;
  std::uint64_t observed_primary_title_generation = 0;
  bool new_kingdom_title_verified = false;
  bool world_outcome_verified = false;
};

MajorDecisionFoundKingdomActionAckStatusV1
ExecuteMajorDecisionFoundKingdomActionCoreV1(
    const MajorDecisionFoundKingdomActionEnvironmentV1 &environment,
    const MajorDecisionFoundKingdomActionAccessV1 &access,
    const MajorDecisionFoundKingdomActionRequestV1 &request,
    MajorDecisionFoundKingdomActionStateV1 &state,
    MajorDecisionFoundKingdomActionAckV1 &ack) noexcept;

MajorDecisionFoundKingdomActionReceiptStatusV1
VerifyMajorDecisionFoundKingdomActionReceiptV1(
    const MajorDecisionFoundKingdomActionAckV1 &ack,
    const MajorDecisionFoundKingdomActionPostconditionV1 &postcondition,
    MajorDecisionFoundKingdomActionStateV1 &state,
    MajorDecisionFoundKingdomActionReceiptV1 &receipt) noexcept;

std::string_view MajorDecisionFoundKingdomActionFailureClassNameV1(
    MajorDecisionFoundKingdomActionFailureClassV1 failure) noexcept;

} // namespace xar::bridge
