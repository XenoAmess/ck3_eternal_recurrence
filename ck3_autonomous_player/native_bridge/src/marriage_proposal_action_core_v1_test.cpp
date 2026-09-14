#include "xar_bridge/marriage_proposal_action_core_v1.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

namespace bridge = xar::bridge;

constexpr std::uint32_t kSubjectId = 0x01000002;
constexpr std::uint32_t kCandidateId = 0x01000003;
constexpr std::uint32_t kRecipientId = 0x01000004;

struct Harness {
  bridge::MarriageProposalActionStateV1 state{};
  bridge::MarriageMatchmakingObservationV1 first{};
  bridge::MarriageMatchmakingObservationV1 second{};
  bridge::MarriageProposalNativeSubmitResultV1 submit_result =
      bridge::MarriageProposalNativeSubmitResultV1::submitted;
  bridge::MarriageProposalSubmissionV1 submitted{};
  std::uint32_t capture_calls = 0;
  std::uint32_t submit_calls = 0;
};

void CopySnapshotId(
    std::array<char, bridge::kMarriageMatchmakingSnapshotIdCapacityV1> &output,
    const char *value) {
  const auto size = std::strlen(value);
  assert(size < output.size());
  std::memcpy(output.data(), value, size);
}

bridge::MarriageMatchmakingPairRolesV1 Roles() {
  bridge::MarriageMatchmakingPairRolesV1 output{};
  output.actor_character_id = kSubjectId;
  output.recipient_character_id = kRecipientId;
  output.secondary_actor_character_id = kSubjectId;
  output.secondary_recipient_character_id = kCandidateId;
  output.intermediary_character_id = 0;
  return output;
}

bridge::MarriageMatchmakingObservationV1 Observation(
    bridge::MarriagePredictedOutcomeV1 outcome =
        bridge::MarriagePredictedOutcomeV1::marriage) {
  bridge::MarriageMatchmakingObservationV1 output{};
  output.status = bridge::MarriageMatchmakingObserverStatusV1::available;
  output.unavailable_reason =
      bridge::MarriageMatchmakingObserverFailureV1::none;
  CopySnapshotId(output.snapshot_id, "marriage4-fixture-001");
  output.public_revision = 801;
  output.native_revision = 9801;
  output.proof_epoch = 31;
  output.date_raw = 54'700'000;
  output.subject_character_id = kSubjectId;
  output.matchmaker_character_id = kSubjectId;
  output.candidate_count = 1;
  auto &candidate = output.candidates[0];
  candidate.rank = 1;
  candidate.subject_character_id = kSubjectId;
  candidate.matchmaker_character_id = kSubjectId;
  candidate.candidate_character_id = kCandidateId;
  candidate.native_candidate_score = 187'500;
  candidate.evaluation.roles = Roles();
  candidate.evaluation.complete_can_send = true;
  candidate.evaluation.complete_can_send_status_raw = 1;
  candidate.evaluation.recipient_ai_accept_raw = 350'000;
  candidate.evaluation.recipient_answer_status_raw = 2;
  candidate.evaluation.recipient_answer_allows_send = true;
  candidate.evaluation.predicted_outcome = outcome;
  output.readiness.ranked_candidates_ready = true;
  output.readiness.pair_character_ids_ready = true;
  output.readiness.native_score_ready = true;
  output.readiness.complete_can_send_ready = true;
  output.readiness.recipient_ai_accept_ready = true;
  output.readiness.recipient_answer_ready = true;
  output.readiness.predicted_outcome_ready = true;
  output.readiness.same_frame_ready = true;
  return output;
}

void InitHarness(
    Harness &harness,
    bridge::MarriagePredictedOutcomeV1 outcome =
        bridge::MarriagePredictedOutcomeV1::marriage) {
  harness.first = Observation(outcome);
  harness.second = harness.first;
}

bridge::MarriageProposalActionRequestV1 Request(
    bridge::MarriagePredictedOutcomeV1 outcome =
        bridge::MarriagePredictedOutcomeV1::marriage) {
  bridge::MarriageProposalActionRequestV1 output{};
  output.request_id = "marriage4-request-001";
  output.expected_snapshot_id = "marriage4-fixture-001";
  output.expected_public_revision = 801;
  output.expected_native_revision = 9801;
  output.expected_proof_epoch = 31;
  output.expected_date_raw = 54'700'000;
  output.subject_character_id = kSubjectId;
  output.candidate_character_id = kCandidateId;
  output.expected_native_rank = 1;
  output.expected_native_candidate_score = 187'500;
  output.minimum_native_candidate_score = 100'000;
  output.expected_roles = Roles();
  output.expected_recipient_ai_accept_raw = 350'000;
  output.minimum_recipient_ai_accept_raw = 0;
  output.expected_recipient_answer_status_raw = 2;
  output.expected_outcome = outcome;
  return output;
}

bridge::MarriageProposalActionEnvironmentV1 Environment() {
  auto output = bridge::BindMarriageProposalActionEnvironmentV1(
      0, true, bridge::kMarriageProposalActionCoreExecutableSha256V1);
  output.offline_fixture_submit = true;
  return output;
}

bool Capture(void *context,
             bridge::MarriageMatchmakingObservationV1 &output) noexcept {
  auto &harness = *static_cast<Harness *>(context);
  output = harness.capture_calls++ == 0 ? harness.first : harness.second;
  return true;
}

bridge::MarriageProposalNativeSubmitResultV1 Submit(
    void *context,
    const bridge::MarriageProposalSubmissionV1 &submission) noexcept {
  auto &harness = *static_cast<Harness *>(context);
  ++harness.submit_calls;
  harness.submitted = submission;
  return harness.submit_result;
}

bridge::MarriageProposalActionAccessV1 Access(Harness &harness) {
  return {&harness, &Capture, &Submit};
}

bridge::MarriageProposalRelationshipObservationV1 PostObservation() {
  bridge::MarriageProposalRelationshipObservationV1 output{};
  output.available = true;
  output.paused = true;
  CopySnapshotId(output.snapshot_id, "marriage4-receipt-002");
  output.public_revision = 802;
  output.native_revision = 9802;
  output.proof_epoch = 32;
  output.date_raw = 54'700'001;
  output.subject_character_id = kSubjectId;
  output.candidate_character_id = kCandidateId;
  output.subject_identity_round_trip = true;
  output.candidate_identity_round_trip = true;
  output.subject_alive = true;
  output.candidate_alive = true;
  output.relationship_state_ready = true;
  output.alliance_state_ready = true;
  output.native_resolution =
      bridge::MarriageProposalNativeResolutionV1::pending;
  return output;
}

bridge::MarriageProposalActionAckV1 Execute(Harness &harness) {
  bridge::MarriageProposalActionAckV1 ack{};
  assert(bridge::ExecuteMarriageProposalActionV1(
             harness.state, Environment(), Access(harness), Request(), ack) ==
         bridge::MarriageProposalActionAckStatusV1::
             submitted_receipt_pending);
  return ack;
}

void TestSingleSubmitAndPendingAck() {
  Harness harness{};
  InitHarness(harness);
  auto ack = Execute(harness);
  const bridge::MarriageProposalSubmissionV1 expected{
      kSubjectId, kCandidateId, 1, 187'500, Roles(), 350'000, 2,
      bridge::MarriagePredictedOutcomeV1::marriage};
  assert(harness.capture_calls == 2 && harness.submit_calls == 1 &&
         harness.submitted == expected);
  assert(ack.receipt_pending &&
         ack.pre_snapshot_id == "marriage4-fixture-001" &&
         ack.pre_public_revision == 801 &&
         ack.pre_native_revision == 9801 && ack.pre_proof_epoch == 31 &&
         ack.pre_date_raw == 54'700'000 && ack.submission == expected &&
         ack.failure == bridge::MarriageProposalActionFailureV1::none);
  assert(bridge::ReadMarriageProposalActionPhaseV1(harness.state) ==
         bridge::MarriageProposalActionPhaseV1::receipt_pending);

  bridge::MarriageProposalActionAckV1 repeated{};
  assert(bridge::ExecuteMarriageProposalActionV1(
             harness.state, Environment(), Access(harness), Request(),
             repeated) == bridge::MarriageProposalActionAckStatusV1::
                              rejected_before_submit);
  assert(repeated.failure ==
             bridge::MarriageProposalActionFailureV1::
                 submission_already_claimed &&
         harness.capture_calls == 2 && harness.submit_calls == 1);
}

void TestSemanticCandidateGates() {
  Harness stale{};
  InitHarness(stale);
  stale.first.public_revision = 800;
  stale.second = stale.first;
  bridge::MarriageProposalActionAckV1 ack{};
  assert(bridge::ExecuteMarriageProposalActionV1(
             stale.state, Environment(), Access(stale), Request(), ack) ==
         bridge::MarriageProposalActionAckStatusV1::rejected_before_submit);
  assert(ack.failure == bridge::MarriageProposalActionFailureV1::
                            semantic_snapshot_mismatch &&
         stale.submit_calls == 0);

  Harness legal{};
  InitHarness(legal);
  legal.first.candidates[0].evaluation.complete_can_send = false;
  legal.second = legal.first;
  assert(bridge::ExecuteMarriageProposalActionV1(
             legal.state, Environment(), Access(legal), Request(), ack) ==
         bridge::MarriageProposalActionAckStatusV1::rejected_before_submit);
  assert(ack.failure ==
             bridge::MarriageProposalActionFailureV1::candidate_not_legal &&
         legal.submit_calls == 0);

  Harness acceptance{};
  InitHarness(acceptance);
  acceptance.first.candidates[0]
      .evaluation.recipient_answer_allows_send = false;
  acceptance.second = acceptance.first;
  assert(bridge::ExecuteMarriageProposalActionV1(
             acceptance.state, Environment(), Access(acceptance), Request(),
             ack) == bridge::MarriageProposalActionAckStatusV1::
                         rejected_before_submit);
  assert(ack.failure == bridge::MarriageProposalActionFailureV1::
                            candidate_not_accepted &&
         acceptance.submit_calls == 0);

  Harness drift{};
  InitHarness(drift);
  drift.second.candidates[0].native_candidate_score = 187'501;
  assert(bridge::ExecuteMarriageProposalActionV1(
             drift.state, Environment(), Access(drift), Request(), ack) ==
         bridge::MarriageProposalActionAckStatusV1::rejected_before_submit);
  assert(ack.failure == bridge::MarriageProposalActionFailureV1::
                            semantic_candidate_changed &&
         drift.capture_calls == 2 && drift.submit_calls == 0);

  Harness roles{};
  InitHarness(roles);
  roles.first.candidates[0].evaluation.roles.recipient_character_id =
      kCandidateId;
  roles.second = roles.first;
  assert(bridge::ExecuteMarriageProposalActionV1(
             roles.state, Environment(), Access(roles), Request(), ack) ==
         bridge::MarriageProposalActionAckStatusV1::rejected_before_submit);
  assert(ack.failure == bridge::MarriageProposalActionFailureV1::
                            semantic_candidate_changed &&
         roles.submit_calls == 0);

  Harness score{};
  InitHarness(score);
  auto score_request = Request();
  score_request.minimum_native_candidate_score = 200'000;
  assert(bridge::ExecuteMarriageProposalActionV1(
             score.state, Environment(), Access(score), score_request, ack) ==
         bridge::MarriageProposalActionAckStatusV1::rejected_before_submit);
  assert(ack.failure == bridge::MarriageProposalActionFailureV1::
                            candidate_below_score_floor &&
         score.submit_calls == 0);

  Harness acceptance_floor{};
  InitHarness(acceptance_floor);
  auto acceptance_request = Request();
  acceptance_request.minimum_recipient_ai_accept_raw = 400'000;
  assert(bridge::ExecuteMarriageProposalActionV1(
             acceptance_floor.state, Environment(), Access(acceptance_floor),
             acceptance_request, ack) ==
         bridge::MarriageProposalActionAckStatusV1::rejected_before_submit);
  assert(ack.failure == bridge::MarriageProposalActionFailureV1::
                            candidate_below_acceptance_floor &&
         acceptance_floor.submit_calls == 0);
}

void TestCertificationAndNativeSubmitRed() {
  Harness uncertified{};
  InitHarness(uncertified);
  auto environment = bridge::BindMarriageProposalActionEnvironmentV1(
      0, true, bridge::kMarriageProposalActionCoreExecutableSha256V1);
  bridge::MarriageProposalActionAckV1 ack{};
  assert(bridge::ExecuteMarriageProposalActionV1(
             uncertified.state, environment, Access(uncertified), Request(),
             ack) == bridge::MarriageProposalActionAckStatusV1::
                         rejected_before_submit);
  assert(ack.failure == bridge::MarriageProposalActionFailureV1::
                            native_submit_not_certified &&
         uncertified.capture_calls == 1 && uncertified.submit_calls == 0);

  Harness rejected{};
  InitHarness(rejected);
  rejected.submit_result =
      bridge::MarriageProposalNativeSubmitResultV1::rejected;
  assert(bridge::ExecuteMarriageProposalActionV1(
             rejected.state, Environment(), Access(rejected), Request(),
             ack) == bridge::MarriageProposalActionAckStatusV1::
                         rejected_before_submit);
  assert(ack.failure ==
             bridge::MarriageProposalActionFailureV1::native_submit_rejected &&
         rejected.submit_calls == 1 &&
         bridge::ReadMarriageProposalActionPhaseV1(rejected.state) ==
             bridge::MarriageProposalActionPhaseV1::terminal);
}

void TestMarriageReceiptAndAllianceResult() {
  Harness harness{};
  InitHarness(harness);
  const auto ack = Execute(harness);
  auto post = PostObservation();
  bridge::MarriageProposalReceiptV1 receipt{};
  assert(bridge::VerifyMarriageProposalReceiptV1(
             harness.state, ack, post, receipt) ==
         bridge::MarriageProposalReceiptStatusV1::verification_pending);
  assert(!receipt.terminal && !receipt.postcondition_verified &&
         bridge::ReadMarriageProposalActionPhaseV1(harness.state) ==
             bridge::MarriageProposalActionPhaseV1::receipt_pending);

  post.native_resolution =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  post.subject_has_candidate_as_spouse = true;
  post.candidate_has_subject_as_spouse = true;
  post.subject_has_alliance_with_candidate = true;
  post.candidate_has_alliance_with_subject = true;
  assert(bridge::VerifyMarriageProposalReceiptV1(
             harness.state, ack, post, receipt) ==
         bridge::MarriageProposalReceiptStatusV1::succeeded_marriage);
  assert(receipt.terminal && receipt.postcondition_verified &&
         receipt.marriage_observed && !receipt.betrothal_observed &&
         receipt.alliance_result_ready && receipt.alliance_formed &&
         bridge::ReadMarriageProposalActionPhaseV1(harness.state) ==
             bridge::MarriageProposalActionPhaseV1::terminal);
}

void TestBetrothalRefusalAndInvalidationReceipts() {
  Harness betrothal{};
  InitHarness(betrothal,
              bridge::MarriagePredictedOutcomeV1::betrothal);
  bridge::MarriageProposalActionAckV1 betrothal_ack{};
  assert(bridge::ExecuteMarriageProposalActionV1(
             betrothal.state, Environment(), Access(betrothal),
             Request(bridge::MarriagePredictedOutcomeV1::betrothal),
             betrothal_ack) ==
         bridge::MarriageProposalActionAckStatusV1::
             submitted_receipt_pending);
  auto post = PostObservation();
  post.native_resolution =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  post.subject_has_candidate_as_betrothed = true;
  post.candidate_has_subject_as_betrothed = true;
  bridge::MarriageProposalReceiptV1 receipt{};
  assert(bridge::VerifyMarriageProposalReceiptV1(
             betrothal.state, betrothal_ack, post, receipt) ==
         bridge::MarriageProposalReceiptStatusV1::succeeded_betrothal);
  assert(receipt.betrothal_observed && !receipt.alliance_formed);

  Harness refusal{};
  InitHarness(refusal);
  const auto refusal_ack = Execute(refusal);
  post = PostObservation();
  post.native_resolution =
      bridge::MarriageProposalNativeResolutionV1::refused;
  assert(bridge::VerifyMarriageProposalReceiptV1(
             refusal.state, refusal_ack, post, receipt) ==
         bridge::MarriageProposalReceiptStatusV1::refused);
  assert(receipt.terminal && receipt.postcondition_verified);

  Harness invalidated{};
  InitHarness(invalidated);
  const auto invalidated_ack = Execute(invalidated);
  post = PostObservation();
  post.native_resolution =
      bridge::MarriageProposalNativeResolutionV1::invalidated;
  assert(bridge::VerifyMarriageProposalReceiptV1(
             invalidated.state, invalidated_ack, post, receipt) ==
         bridge::MarriageProposalReceiptStatusV1::invalidated);
  assert(receipt.terminal && receipt.postcondition_verified);
}

void TestReceiptRequiresBothSidesAndFreshObservation() {
  Harness stale{};
  InitHarness(stale);
  const auto stale_ack = Execute(stale);
  auto post = PostObservation();
  post.native_revision = stale_ack.pre_native_revision;
  bridge::MarriageProposalReceiptV1 receipt{};
  assert(bridge::VerifyMarriageProposalReceiptV1(
             stale.state, stale_ack, post, receipt) ==
         bridge::MarriageProposalReceiptStatusV1::observation_failed);
  assert(receipt.failure == bridge::MarriageProposalActionFailureV1::
                                receipt_observation_stale &&
         bridge::ReadMarriageProposalActionPhaseV1(stale.state) ==
             bridge::MarriageProposalActionPhaseV1::receipt_pending);

  Harness asymmetric{};
  InitHarness(asymmetric);
  const auto asymmetric_ack = Execute(asymmetric);
  post = PostObservation();
  post.native_resolution =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  post.subject_has_candidate_as_spouse = true;
  assert(bridge::VerifyMarriageProposalReceiptV1(
             asymmetric.state, asymmetric_ack, post, receipt) ==
         bridge::MarriageProposalReceiptStatusV1::observation_failed);
  assert(receipt.failure == bridge::MarriageProposalActionFailureV1::
                                receipt_relationship_inconsistent &&
         bridge::ReadMarriageProposalActionPhaseV1(asymmetric.state) ==
             bridge::MarriageProposalActionPhaseV1::receipt_pending);

  Harness alliance{};
  InitHarness(alliance);
  const auto alliance_ack = Execute(alliance);
  post = PostObservation();
  post.native_resolution =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  post.subject_has_candidate_as_spouse = true;
  post.candidate_has_subject_as_spouse = true;
  post.subject_has_alliance_with_candidate = true;
  assert(bridge::VerifyMarriageProposalReceiptV1(
             alliance.state, alliance_ack, post, receipt) ==
         bridge::MarriageProposalReceiptStatusV1::observation_failed);
  assert(receipt.failure == bridge::MarriageProposalActionFailureV1::
                                receipt_relationship_inconsistent);
}

} // namespace

int main() {
  TestSingleSubmitAndPendingAck();
  TestSemanticCandidateGates();
  TestCertificationAndNativeSubmitRed();
  TestMarriageReceiptAndAllianceResult();
  TestBetrothalRefusalAndInvalidationReceipts();
  TestReceiptRequiresBothSidesAndFreshObservation();
  std::cout << "GREEN: marriage-proposal-action-core-v1 fixture\n";
  return 0;
}
