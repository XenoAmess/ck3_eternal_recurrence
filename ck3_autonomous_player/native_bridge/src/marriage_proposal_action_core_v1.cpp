#include "xar_bridge/marriage_proposal_action_core_v1.hpp"

#include <algorithm>
#include <string_view>
#include <utility>

namespace xar::bridge {
namespace {

bool ValidTextToken(std::string_view value, std::size_t maximum) noexcept {
  if (value.empty() || value.size() > maximum) return false;
  return std::all_of(value.begin(), value.end(), [](const char character) {
    const auto byte = static_cast<unsigned char>(character);
    return byte >= 0x21 && byte <= 0x7E && character != '"' &&
        character != '\\';
  });
}

std::string_view BoundedSnapshotId(
    const std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1>
        &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ValidDirectRoles(const MarriageMatchmakingPairRolesV1 &roles,
                      std::uint32_t subject_character_id,
                      std::uint32_t candidate_character_id) noexcept {
  return roles.actor_character_id == subject_character_id &&
      roles.recipient_character_id != 0 &&
      roles.secondary_actor_character_id == subject_character_id &&
      roles.secondary_recipient_character_id == candidate_character_id &&
      roles.actor_character_id != roles.recipient_character_id &&
      roles.secondary_actor_character_id !=
          roles.secondary_recipient_character_id;
}

bool ValidRequest(const MarriageProposalActionRequestV1 &request) noexcept {
  return ValidTextToken(request.request_id, 64) &&
      ValidTextToken(request.expected_snapshot_id,
                     kMarriageMatchmakingSnapshotIdCapacityV1 - 1) &&
      request.expected_public_revision != 0 &&
      request.expected_native_revision != 0 &&
      request.expected_proof_epoch != 0 && request.expected_date_raw > 0 &&
      request.subject_character_id != 0 &&
      request.candidate_character_id != 0 &&
      request.subject_character_id != request.candidate_character_id &&
      request.expected_native_rank > 0 &&
      request.expected_native_rank <=
          kMarriageMatchmakingMaximumCandidatesV1 &&
      request.expected_recipient_answer_status_raw != 0 &&
      request.expected_outcome != MarriagePredictedOutcomeV1::unavailable &&
      ValidDirectRoles(request.expected_roles,
                       request.subject_character_id,
                       request.candidate_character_id);
}

bool CompleteReadiness(
    const MarriageMatchmakingObserverReadinessV1 &readiness) noexcept {
  return readiness.ranked_candidates_ready &&
      readiness.pair_character_ids_ready && readiness.native_score_ready &&
      readiness.complete_can_send_ready &&
      readiness.recipient_ai_accept_ready &&
      readiness.recipient_answer_ready &&
      readiness.predicted_outcome_ready && readiness.same_frame_ready;
}

bool SameObservation(const MarriageMatchmakingObservationV1 &left,
                     const MarriageMatchmakingObservationV1 &right) noexcept {
  return left.status == right.status &&
      left.unavailable_reason == right.unavailable_reason &&
      left.snapshot_id == right.snapshot_id &&
      left.public_revision == right.public_revision &&
      left.native_revision == right.native_revision &&
      left.proof_epoch == right.proof_epoch &&
      left.date_raw == right.date_raw &&
      left.subject_character_id == right.subject_character_id &&
      left.matchmaker_character_id == right.matchmaker_character_id &&
      left.candidate_count == right.candidate_count &&
      left.candidates == right.candidates && left.readiness == right.readiness;
}

MarriageProposalActionAckStatusV1 Reject(
    const MarriageProposalActionRequestV1 &request,
    MarriageProposalActionFailureV1 failure, std::string_view reason,
    MarriageProposalActionAckV1 &ack) {
  ack = {};
  ack.status =
      MarriageProposalActionAckStatusV1::rejected_before_submit;
  ack.request_id = request.request_id;
  ack.failure = failure;
  ack.reason.assign(reason);
  return ack.status;
}

MarriageProposalActionFailureV1 ValidateObservation(
    const MarriageMatchmakingObservationV1 &observation,
    const MarriageProposalActionRequestV1 &request,
    const MarriageMatchmakingCandidateV1 *&selected) noexcept {
  selected = nullptr;
  if (observation.status != MarriageMatchmakingObserverStatusV1::available ||
      observation.unavailable_reason !=
          MarriageMatchmakingObserverFailureV1::none ||
      !CompleteReadiness(observation.readiness)) {
    return MarriageProposalActionFailureV1::
        semantic_observation_unavailable;
  }
  if (BoundedSnapshotId(observation.snapshot_id) !=
          request.expected_snapshot_id ||
      observation.public_revision != request.expected_public_revision ||
      observation.native_revision != request.expected_native_revision ||
      observation.proof_epoch != request.expected_proof_epoch ||
      observation.date_raw != request.expected_date_raw ||
      observation.subject_character_id != request.subject_character_id ||
      observation.matchmaker_character_id != request.subject_character_id ||
      observation.candidate_count >
          kMarriageMatchmakingMaximumCandidatesV1) {
    return MarriageProposalActionFailureV1::semantic_snapshot_mismatch;
  }
  for (std::uint32_t index = 0; index < observation.candidate_count; ++index) {
    const auto &candidate = observation.candidates[index];
    if (candidate.candidate_character_id == request.candidate_character_id) {
      if (selected != nullptr) {
        return MarriageProposalActionFailureV1::semantic_candidate_changed;
      }
      selected = &candidate;
    }
  }
  if (selected == nullptr) {
    return MarriageProposalActionFailureV1::semantic_candidate_missing;
  }
  const auto &evaluation = selected->evaluation;
  if (selected->rank != request.expected_native_rank ||
      selected->subject_character_id != request.subject_character_id ||
      selected->matchmaker_character_id != request.subject_character_id ||
      selected->native_candidate_score !=
          request.expected_native_candidate_score ||
      evaluation.roles != request.expected_roles ||
      !ValidDirectRoles(evaluation.roles, request.subject_character_id,
                        request.candidate_character_id) ||
      evaluation.recipient_ai_accept_raw !=
          request.expected_recipient_ai_accept_raw ||
      evaluation.recipient_answer_status_raw !=
          request.expected_recipient_answer_status_raw ||
      evaluation.predicted_outcome != request.expected_outcome) {
    return MarriageProposalActionFailureV1::semantic_candidate_changed;
  }
  if (selected->native_candidate_score <
      request.minimum_native_candidate_score) {
    return MarriageProposalActionFailureV1::candidate_below_score_floor;
  }
  if (!evaluation.complete_can_send ||
      evaluation.complete_can_send_status_raw == 0) {
    return MarriageProposalActionFailureV1::candidate_not_legal;
  }
  if (evaluation.recipient_ai_accept_raw <
      request.minimum_recipient_ai_accept_raw) {
    return MarriageProposalActionFailureV1::
        candidate_below_acceptance_floor;
  }
  if (!evaluation.recipient_answer_allows_send ||
      evaluation.recipient_answer_status_raw == 0) {
    return MarriageProposalActionFailureV1::candidate_not_accepted;
  }
  return MarriageProposalActionFailureV1::none;
}

MarriageProposalSubmissionV1 MakeSubmission(
    const MarriageMatchmakingCandidateV1 &candidate) noexcept {
  MarriageProposalSubmissionV1 output{};
  output.subject_character_id = candidate.subject_character_id;
  output.candidate_character_id = candidate.candidate_character_id;
  output.native_rank = candidate.rank;
  output.native_candidate_score = candidate.native_candidate_score;
  output.roles = candidate.evaluation.roles;
  output.recipient_ai_accept_raw =
      candidate.evaluation.recipient_ai_accept_raw;
  output.recipient_answer_status_raw =
      candidate.evaluation.recipient_answer_status_raw;
  output.predicted_outcome = candidate.evaluation.predicted_outcome;
  return output;
}

void FillPendingAck(const MarriageProposalActionRequestV1 &request,
                    const MarriageMatchmakingObservationV1 &observation,
                    const MarriageProposalSubmissionV1 &submission,
                    MarriageProposalActionAckV1 &ack) {
  ack = {};
  ack.status =
      MarriageProposalActionAckStatusV1::submitted_receipt_pending;
  ack.receipt_pending = true;
  ack.request_id = request.request_id;
  ack.pre_snapshot_id.assign(BoundedSnapshotId(observation.snapshot_id));
  ack.pre_public_revision = observation.public_revision;
  ack.pre_native_revision = observation.native_revision;
  ack.pre_proof_epoch = observation.proof_epoch;
  ack.pre_date_raw = observation.date_raw;
  ack.submission = submission;
  ack.failure = MarriageProposalActionFailureV1::none;
}

void CopyPostObservation(
    const MarriageProposalRelationshipObservationV1 &post,
    const MarriageProposalActionAckV1 &ack,
    MarriageProposalReceiptV1 &receipt) {
  receipt.request_id = ack.request_id;
  receipt.post_public_revision = post.public_revision;
  receipt.post_native_revision = post.native_revision;
  receipt.post_proof_epoch = post.proof_epoch;
  receipt.post_date_raw = post.date_raw;
  receipt.subject_character_id = post.subject_character_id;
  receipt.candidate_character_id = post.candidate_character_id;
  receipt.expected_outcome = ack.submission.predicted_outcome;
  receipt.native_resolution = post.native_resolution;
  receipt.marriage_observed =
      post.subject_has_candidate_as_spouse &&
      post.candidate_has_subject_as_spouse;
  receipt.betrothal_observed =
      post.subject_has_candidate_as_betrothed &&
      post.candidate_has_subject_as_betrothed;
  receipt.alliance_result_ready = post.alliance_state_ready;
  receipt.alliance_formed =
      post.subject_has_alliance_with_candidate &&
      post.candidate_has_alliance_with_subject;
}

MarriageProposalReceiptStatusV1 ReceiptFailure(
    MarriageProposalActionFailureV1 failure, std::string_view reason,
    MarriageProposalReceiptV1 &receipt) {
  receipt.status = MarriageProposalReceiptStatusV1::observation_failed;
  receipt.failure = failure;
  receipt.reason.assign(reason);
  receipt.terminal = false;
  receipt.postcondition_verified = false;
  return receipt.status;
}

MarriageProposalReceiptStatusV1 TerminalReceipt(
    MarriageProposalActionStateV1 &state,
    MarriageProposalReceiptStatusV1 status, std::string_view reason,
    MarriageProposalReceiptV1 &receipt) {
  receipt.status = status;
  receipt.reason.assign(reason);
  receipt.failure = MarriageProposalActionFailureV1::none;
  receipt.terminal = true;
  receipt.postcondition_verified = true;
  state.phase.store(
      static_cast<std::uint32_t>(MarriageProposalActionPhaseV1::terminal),
      std::memory_order_release);
  return status;
}

} // namespace

MarriageProposalActionEnvironmentV1 BindMarriageProposalActionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  MarriageProposalActionEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  output.admitted_executable_sha256 = admitted_executable_sha256;
  return output;
}

MarriageProposalActionAckStatusV1 ExecuteMarriageProposalActionV1(
    MarriageProposalActionStateV1 &state,
    const MarriageProposalActionEnvironmentV1 &environment,
    const MarriageProposalActionAccessV1 &access,
    const MarriageProposalActionRequestV1 &request,
    MarriageProposalActionAckV1 &ack) {
  if (!ValidRequest(request)) {
    return Reject(request, MarriageProposalActionFailureV1::invalid_request,
                  "invalid_request", ack);
  }
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kMarriageProposalActionCoreExecutableSha256V1) {
    return Reject(request,
                  MarriageProposalActionFailureV1::
                      exact_build_not_admitted,
                  "exact_build_not_admitted", ack);
  }
  if (ReadMarriageProposalActionPhaseV1(state) !=
      MarriageProposalActionPhaseV1::idle) {
    return Reject(request,
                  MarriageProposalActionFailureV1::
                      submission_already_claimed,
                  "submission_already_claimed", ack);
  }
  if (access.capture_observation == nullptr) {
    return Reject(request,
                  MarriageProposalActionFailureV1::
                      semantic_observation_unavailable,
                  "semantic_observation_unavailable", ack);
  }

  MarriageMatchmakingObservationV1 first{};
  if (!access.capture_observation(access.context, first)) {
    return Reject(request,
                  MarriageProposalActionFailureV1::
                      semantic_observation_unavailable,
                  "semantic_observation_unavailable", ack);
  }
  const MarriageMatchmakingCandidateV1 *selected = nullptr;
  auto failure = ValidateObservation(first, request, selected);
  if (failure != MarriageProposalActionFailureV1::none) {
    return Reject(request, failure, MarriageProposalActionFailureKeyV1(failure),
                  ack);
  }

  const bool production_certified = environment.module_base != 0 &&
      environment.native_submit_certified;
  const bool offline_certified = environment.module_base == 0 &&
      environment.offline_fixture_submit;
  if ((!production_certified && !offline_certified) ||
      access.submit_native == nullptr) {
    return Reject(request,
                  MarriageProposalActionFailureV1::
                      native_submit_not_certified,
                  "native_submit_not_certified", ack);
  }

  MarriageMatchmakingObservationV1 second{};
  if (!access.capture_observation(access.context, second)) {
    return Reject(request,
                  MarriageProposalActionFailureV1::
                      semantic_observation_unavailable,
                  "semantic_observation_unavailable", ack);
  }
  const MarriageMatchmakingCandidateV1 *selected_second = nullptr;
  failure = ValidateObservation(second, request, selected_second);
  if (failure != MarriageProposalActionFailureV1::none ||
      !SameObservation(first, second) || selected_second == nullptr) {
    return Reject(request,
                  failure == MarriageProposalActionFailureV1::none
                      ? MarriageProposalActionFailureV1::
                            semantic_candidate_changed
                      : failure,
                  "semantic_candidate_changed_before_submit", ack);
  }

  const auto submission = MakeSubmission(*selected_second);
  MarriageProposalActionAckV1 pending_ack{};
  FillPendingAck(request, second, submission, pending_ack);

  std::uint32_t expected_phase =
      static_cast<std::uint32_t>(MarriageProposalActionPhaseV1::idle);
  if (!state.phase.compare_exchange_strong(
          expected_phase,
          static_cast<std::uint32_t>(
              MarriageProposalActionPhaseV1::submit_claimed),
          std::memory_order_acq_rel, std::memory_order_acquire)) {
    return Reject(request,
                  MarriageProposalActionFailureV1::
                      submission_already_claimed,
                  "submission_already_claimed", ack);
  }

  const auto submit_result =
      access.submit_native(access.context, submission);
  if (submit_result != MarriageProposalNativeSubmitResultV1::submitted) {
    state.phase.store(
        static_cast<std::uint32_t>(MarriageProposalActionPhaseV1::terminal),
        std::memory_order_release);
    const auto submit_failure =
        submit_result == MarriageProposalNativeSubmitResultV1::rejected
            ? MarriageProposalActionFailureV1::native_submit_rejected
            : MarriageProposalActionFailureV1::native_submit_unavailable;
    return Reject(request, submit_failure,
                  MarriageProposalActionFailureKeyV1(submit_failure), ack);
  }

  state.phase.store(static_cast<std::uint32_t>(
                        MarriageProposalActionPhaseV1::receipt_pending),
                    std::memory_order_release);
  ack = std::move(pending_ack);
  return ack.status;
}

MarriageProposalReceiptStatusV1 VerifyMarriageProposalReceiptV1(
    MarriageProposalActionStateV1 &state,
    const MarriageProposalActionAckV1 &ack,
    const MarriageProposalRelationshipObservationV1 &post,
    MarriageProposalReceiptV1 &receipt) {
  receipt = {};
  CopyPostObservation(post, ack, receipt);
  if (ack.status ==
      MarriageProposalActionAckStatusV1::rejected_before_submit) {
    receipt.status =
        MarriageProposalReceiptStatusV1::rejected_before_submit;
    receipt.terminal = true;
    receipt.reason = ack.reason;
    receipt.failure = ack.failure;
    return receipt.status;
  }
  if (ack.status !=
          MarriageProposalActionAckStatusV1::submitted_receipt_pending ||
      !ack.receipt_pending || ack.request_id.empty() ||
      ack.submission.subject_character_id == 0 ||
      ack.submission.candidate_character_id == 0 ||
      ack.submission.predicted_outcome ==
          MarriagePredictedOutcomeV1::unavailable ||
      ReadMarriageProposalActionPhaseV1(state) !=
          MarriageProposalActionPhaseV1::receipt_pending) {
    return ReceiptFailure(MarriageProposalActionFailureV1::invalid_ack,
                          "invalid_ack", receipt);
  }
  if (!post.available || !post.paused ||
      !ValidTextToken(BoundedSnapshotId(post.snapshot_id),
                      kMarriageMatchmakingSnapshotIdCapacityV1 - 1)) {
    return ReceiptFailure(
        MarriageProposalActionFailureV1::receipt_observation_unavailable,
        "receipt_observation_unavailable", receipt);
  }
  if (post.public_revision <= ack.pre_public_revision ||
      post.native_revision <= ack.pre_native_revision ||
      post.proof_epoch <= ack.pre_proof_epoch ||
      post.date_raw < ack.pre_date_raw) {
    return ReceiptFailure(
        MarriageProposalActionFailureV1::receipt_observation_stale,
        "receipt_observation_stale", receipt);
  }
  if (post.subject_character_id !=
          ack.submission.subject_character_id ||
      post.candidate_character_id !=
          ack.submission.candidate_character_id ||
      !post.subject_identity_round_trip ||
      !post.candidate_identity_round_trip || !post.subject_alive ||
      !post.candidate_alive) {
    return TerminalReceipt(state,
                           MarriageProposalReceiptStatusV1::invalidated,
                           "party_identity_or_liveness_changed", receipt);
  }
  if (!post.relationship_state_ready || !post.alliance_state_ready) {
    return ReceiptFailure(
        MarriageProposalActionFailureV1::receipt_observation_unavailable,
        "relationship_or_alliance_observation_unavailable", receipt);
  }

  const bool marriage_symmetric =
      post.subject_has_candidate_as_spouse ==
      post.candidate_has_subject_as_spouse;
  const bool betrothal_symmetric =
      post.subject_has_candidate_as_betrothed ==
      post.candidate_has_subject_as_betrothed;
  const bool alliance_symmetric =
      post.subject_has_alliance_with_candidate ==
      post.candidate_has_alliance_with_subject;
  if (!marriage_symmetric || !betrothal_symmetric ||
      !alliance_symmetric ||
      (receipt.marriage_observed && receipt.betrothal_observed)) {
    return ReceiptFailure(
        MarriageProposalActionFailureV1::
            receipt_relationship_inconsistent,
        "receipt_relationship_inconsistent", receipt);
  }

  if (receipt.marriage_observed || receipt.betrothal_observed) {
    if (post.native_resolution ==
            MarriageProposalNativeResolutionV1::refused ||
        post.native_resolution ==
            MarriageProposalNativeResolutionV1::invalidated) {
      return ReceiptFailure(
          MarriageProposalActionFailureV1::
              receipt_relationship_inconsistent,
          "native_resolution_conflicts_with_relationship", receipt);
    }
    if (receipt.marriage_observed &&
        ack.submission.predicted_outcome ==
            MarriagePredictedOutcomeV1::marriage) {
      return TerminalReceipt(state,
                             MarriageProposalReceiptStatusV1::
                                 succeeded_marriage,
                             "marriage_observed", receipt);
    }
    if (receipt.betrothal_observed &&
        ack.submission.predicted_outcome ==
            MarriagePredictedOutcomeV1::betrothal) {
      return TerminalReceipt(state,
                             MarriageProposalReceiptStatusV1::
                                 succeeded_betrothal,
                             "betrothal_observed", receipt);
    }
    return TerminalReceipt(state,
                           MarriageProposalReceiptStatusV1::invalidated,
                           "predicted_outcome_changed", receipt);
  }

  switch (post.native_resolution) {
  case MarriageProposalNativeResolutionV1::pending:
    receipt.status = MarriageProposalReceiptStatusV1::verification_pending;
    receipt.reason = "native_resolution_pending";
    receipt.failure = MarriageProposalActionFailureV1::none;
    return receipt.status;
  case MarriageProposalNativeResolutionV1::accepted:
    return TerminalReceipt(state,
                           MarriageProposalReceiptStatusV1::invalidated,
                           "accepted_without_expected_relationship", receipt);
  case MarriageProposalNativeResolutionV1::refused:
    return TerminalReceipt(state, MarriageProposalReceiptStatusV1::refused,
                           "proposal_refused", receipt);
  case MarriageProposalNativeResolutionV1::invalidated:
    return TerminalReceipt(state,
                           MarriageProposalReceiptStatusV1::invalidated,
                           "proposal_invalidated", receipt);
  }
  return ReceiptFailure(
      MarriageProposalActionFailureV1::receipt_relationship_inconsistent,
      "unknown_native_resolution", receipt);
}

MarriageProposalActionPhaseV1 ReadMarriageProposalActionPhaseV1(
    const MarriageProposalActionStateV1 &state) noexcept {
  return static_cast<MarriageProposalActionPhaseV1>(
      state.phase.load(std::memory_order_acquire));
}

std::string_view MarriageProposalActionFailureKeyV1(
    MarriageProposalActionFailureV1 failure) noexcept {
  switch (failure) {
  case MarriageProposalActionFailureV1::none:
    return "none";
  case MarriageProposalActionFailureV1::invalid_request:
    return "invalid_request";
  case MarriageProposalActionFailureV1::exact_build_not_admitted:
    return "exact_build_not_admitted";
  case MarriageProposalActionFailureV1::semantic_observation_unavailable:
    return "semantic_observation_unavailable";
  case MarriageProposalActionFailureV1::semantic_snapshot_mismatch:
    return "semantic_snapshot_mismatch";
  case MarriageProposalActionFailureV1::semantic_candidate_missing:
    return "semantic_candidate_missing";
  case MarriageProposalActionFailureV1::semantic_candidate_changed:
    return "semantic_candidate_changed";
  case MarriageProposalActionFailureV1::candidate_not_legal:
    return "candidate_not_legal";
  case MarriageProposalActionFailureV1::candidate_not_accepted:
    return "candidate_not_accepted";
  case MarriageProposalActionFailureV1::candidate_below_score_floor:
    return "candidate_below_score_floor";
  case MarriageProposalActionFailureV1::candidate_below_acceptance_floor:
    return "candidate_below_acceptance_floor";
  case MarriageProposalActionFailureV1::native_submit_not_certified:
    return "native_submit_not_certified";
  case MarriageProposalActionFailureV1::submission_already_claimed:
    return "submission_already_claimed";
  case MarriageProposalActionFailureV1::native_submit_rejected:
    return "native_submit_rejected";
  case MarriageProposalActionFailureV1::native_submit_unavailable:
    return "native_submit_unavailable";
  case MarriageProposalActionFailureV1::invalid_ack:
    return "invalid_ack";
  case MarriageProposalActionFailureV1::receipt_observation_unavailable:
    return "receipt_observation_unavailable";
  case MarriageProposalActionFailureV1::receipt_observation_stale:
    return "receipt_observation_stale";
  case MarriageProposalActionFailureV1::
      receipt_relationship_inconsistent:
    return "receipt_relationship_inconsistent";
  }
  return "unknown";
}

std::string_view MarriageProposalReceiptStatusKeyV1(
    MarriageProposalReceiptStatusV1 status) noexcept {
  switch (status) {
  case MarriageProposalReceiptStatusV1::rejected_before_submit:
    return "rejected_before_submit";
  case MarriageProposalReceiptStatusV1::verification_pending:
    return "verification_pending";
  case MarriageProposalReceiptStatusV1::succeeded_marriage:
    return "succeeded_marriage";
  case MarriageProposalReceiptStatusV1::succeeded_betrothal:
    return "succeeded_betrothal";
  case MarriageProposalReceiptStatusV1::refused:
    return "refused";
  case MarriageProposalReceiptStatusV1::invalidated:
    return "invalidated";
  case MarriageProposalReceiptStatusV1::observation_failed:
    return "observation_failed";
  }
  return "observation_failed";
}

} // namespace xar::bridge
