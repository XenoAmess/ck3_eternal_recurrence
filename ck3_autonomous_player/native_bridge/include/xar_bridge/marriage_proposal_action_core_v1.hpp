#pragma once

#include "xar_bridge/marriage_matchmaking_observer_v1.hpp"

#include <array>
#include <atomic>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kMarriageProposalActionCorePrivateKeyV1 =
    "marriage_proposal_action_core_v1";
inline constexpr std::string_view
    kMarriageProposalActionCoreExecutableSha256V1 =
        kMarriageMatchmakingObserverExecutableSha256V1;

enum class MarriageProposalActionPhaseV1 : std::uint32_t {
  idle = 0,
  submit_claimed = 1,
  receipt_pending = 2,
  terminal = 3,
};

enum class MarriageProposalActionFailureV1 : std::uint32_t {
  none = 0,
  invalid_request,
  exact_build_not_admitted,
  semantic_observation_unavailable,
  semantic_snapshot_mismatch,
  semantic_candidate_missing,
  semantic_candidate_changed,
  candidate_not_legal,
  candidate_not_accepted,
  candidate_below_score_floor,
  candidate_below_acceptance_floor,
  native_submit_not_certified,
  submission_already_claimed,
  native_submit_rejected,
  native_submit_unavailable,
  invalid_ack,
  receipt_observation_unavailable,
  receipt_observation_stale,
  receipt_relationship_inconsistent,
};

enum class MarriageProposalActionAckStatusV1 : std::uint32_t {
  rejected_before_submit = 0,
  submitted_receipt_pending = 1,
};

enum class MarriageProposalNativeSubmitResultV1 : std::uint32_t {
  submitted = 0,
  rejected = 1,
  unavailable = 2,
};

enum class MarriageProposalNativeResolutionV1 : std::uint32_t {
  pending = 0,
  accepted = 1,
  refused = 2,
  invalidated = 3,
};

enum class MarriageProposalReceiptStatusV1 : std::uint32_t {
  rejected_before_submit = 0,
  verification_pending = 1,
  succeeded_marriage = 2,
  succeeded_betrothal = 3,
  refused = 4,
  invalidated = 5,
  observation_failed = 6,
};

struct MarriageProposalActionRequestV1 {
  std::string request_id;
  std::string expected_snapshot_id;
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::uint64_t expected_proof_epoch = 0;
  std::int32_t expected_date_raw = 0;
  std::uint32_t subject_character_id = 0;
  std::uint32_t candidate_character_id = 0;
  std::uint32_t expected_native_rank = 0;
  std::int32_t expected_native_candidate_score = 0;
  std::int32_t minimum_native_candidate_score = 0;
  MarriageMatchmakingPairRolesV1 expected_roles{};
  std::int32_t expected_recipient_ai_accept_raw = 0;
  std::int32_t minimum_recipient_ai_accept_raw = 0;
  std::int32_t expected_recipient_answer_status_raw = 0;
  MarriagePredictedOutcomeV1 expected_outcome =
      MarriagePredictedOutcomeV1::unavailable;
};

struct MarriageProposalSubmissionV1 {
  std::uint32_t subject_character_id = 0;
  std::uint32_t candidate_character_id = 0;
  std::uint32_t native_rank = 0;
  std::int32_t native_candidate_score = 0;
  MarriageMatchmakingPairRolesV1 roles{};
  std::int64_t recipient_ai_accept_raw = 0;
  std::int32_t recipient_answer_status_raw = 0;
  MarriagePredictedOutcomeV1 predicted_outcome =
      MarriagePredictedOutcomeV1::unavailable;
  // Only the controlled observed-first-heir route may omit human-player AI
  // rank and outcome. The direct ranked action retains its original gates.
  bool rankless_observed_heir = false;

  friend bool operator==(const MarriageProposalSubmissionV1 &,
                         const MarriageProposalSubmissionV1 &) = default;
};

struct MarriageProposalActionAckV1 {
  MarriageProposalActionAckStatusV1 status =
      MarriageProposalActionAckStatusV1::rejected_before_submit;
  bool receipt_pending = false;
  std::string request_id;
  std::string pre_snapshot_id;
  std::uint64_t pre_public_revision = 0;
  std::uint64_t pre_native_revision = 0;
  std::uint64_t pre_proof_epoch = 0;
  std::int32_t pre_date_raw = 0;
  MarriageProposalSubmissionV1 submission{};
  MarriageProposalActionFailureV1 failure =
      MarriageProposalActionFailureV1::none;
  std::string reason;
};

struct MarriageProposalRelationshipObservationV1 {
  bool available = false;
  bool paused = false;
  std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t subject_character_id = 0;
  std::uint32_t candidate_character_id = 0;
  bool subject_identity_round_trip = false;
  bool candidate_identity_round_trip = false;
  bool subject_alive = false;
  bool candidate_alive = false;
  bool relationship_state_ready = false;
  bool subject_has_candidate_as_spouse = false;
  bool candidate_has_subject_as_spouse = false;
  bool subject_has_candidate_as_betrothed = false;
  bool candidate_has_subject_as_betrothed = false;
  bool alliance_state_ready = false;
  bool subject_has_alliance_with_candidate = false;
  bool candidate_has_alliance_with_subject = false;
  MarriageProposalNativeResolutionV1 native_resolution =
      MarriageProposalNativeResolutionV1::pending;

  friend bool operator==(const MarriageProposalRelationshipObservationV1 &,
                         const MarriageProposalRelationshipObservationV1 &) =
      default;
};

struct MarriageProposalReceiptV1 {
  MarriageProposalReceiptStatusV1 status =
      MarriageProposalReceiptStatusV1::observation_failed;
  bool terminal = false;
  bool postcondition_verified = false;
  std::string request_id;
  std::string reason;
  std::uint64_t post_public_revision = 0;
  std::uint64_t post_native_revision = 0;
  std::uint64_t post_proof_epoch = 0;
  std::int32_t post_date_raw = 0;
  std::uint32_t subject_character_id = 0;
  std::uint32_t candidate_character_id = 0;
  MarriagePredictedOutcomeV1 expected_outcome =
      MarriagePredictedOutcomeV1::unavailable;
  MarriageProposalNativeResolutionV1 native_resolution =
      MarriageProposalNativeResolutionV1::pending;
  bool marriage_observed = false;
  bool betrothal_observed = false;
  bool alliance_result_ready = false;
  bool alliance_formed = false;
  MarriageProposalActionFailureV1 failure =
      MarriageProposalActionFailureV1::none;
};

struct MarriageProposalActionEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  bool native_submit_certified = false;
  bool offline_fixture_submit = false;
};

using CaptureMarriageMatchmakingObservationV1 = bool (*)(
    void *context, MarriageMatchmakingObservationV1 &output) noexcept;
using SubmitMarriageProposalNativeV1 = MarriageProposalNativeSubmitResultV1 (*)(
    void *context, const MarriageProposalSubmissionV1 &submission) noexcept;

struct MarriageProposalActionAccessV1 {
  void *context = nullptr;
  CaptureMarriageMatchmakingObservationV1 capture_observation = nullptr;
  SubmitMarriageProposalNativeV1 submit_native = nullptr;
};

struct MarriageProposalActionStateV1 {
  std::atomic<std::uint32_t> phase{
      static_cast<std::uint32_t>(MarriageProposalActionPhaseV1::idle)};
};

MarriageProposalActionEnvironmentV1 BindMarriageProposalActionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept;

MarriageProposalActionAckStatusV1 ExecuteMarriageProposalActionV1(
    MarriageProposalActionStateV1 &state,
    const MarriageProposalActionEnvironmentV1 &environment,
    const MarriageProposalActionAccessV1 &access,
    const MarriageProposalActionRequestV1 &request,
    MarriageProposalActionAckV1 &ack);

MarriageProposalReceiptStatusV1 VerifyMarriageProposalReceiptV1(
    MarriageProposalActionStateV1 &state,
    const MarriageProposalActionAckV1 &ack,
    const MarriageProposalRelationshipObservationV1 &post_observation,
    MarriageProposalReceiptV1 &receipt);

MarriageProposalActionPhaseV1 ReadMarriageProposalActionPhaseV1(
    const MarriageProposalActionStateV1 &state) noexcept;
std::string_view MarriageProposalActionFailureKeyV1(
    MarriageProposalActionFailureV1 failure) noexcept;
std::string_view MarriageProposalReceiptStatusKeyV1(
    MarriageProposalReceiptStatusV1 status) noexcept;

} // namespace xar::bridge
