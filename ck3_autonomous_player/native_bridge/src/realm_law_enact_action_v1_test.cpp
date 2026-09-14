#include "xar_bridge/realm_law_enact_action_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <memory>
#include <string_view>
#include <type_traits>

namespace {

namespace bridge = xar::bridge;
using AckStatus = bridge::RealmLawEnactActionAckStatusV1;
using ActionFailure = bridge::RealmLawEnactActionFailureV1;
using Observation = bridge::RealmLawEnactActionObservationV1;
using Presence = bridge::RealmLawGovernancePresenceV1;
using ReceiptFailure = bridge::RealmLawEnactActionReceiptFailureV1;
using ReceiptStatus = bridge::RealmLawEnactActionReceiptStatusV1;

bridge::RealmLawGovernanceKeyV1 Key(std::string_view value) {
  bridge::RealmLawGovernanceKeyV1 output{};
  assert(bridge::AssignRealmLawGovernanceKeyV1(value, output));
  return output;
}

bridge::RealmLawGovernanceReasonV1 Reason(std::string_view value) {
  bridge::RealmLawGovernanceReasonV1 output{};
  assert(bridge::AssignRealmLawGovernanceReasonV1(value, output));
  return output;
}

bridge::RealmLawGovernanceReasonV1 NoReason() {
  bridge::RealmLawGovernanceReasonV1 output{};
  output.presence = Presence::absent;
  return output;
}

bridge::RealmLawGovernanceOptionalKeyV1 OptionalKey(
    std::string_view value) {
  return {Presence::present, Key(value)};
}

bridge::RealmLawGovernanceSuccessionShapeV1 SuccessionShape(
    std::int64_t share = 50'000) {
  bridge::RealmLawGovernanceSuccessionShapeV1 output{};
  output.presence = Presence::present;
  output.order_of_succession = Key("inheritance");
  output.title_division = OptionalKey("partition");
  output.traversal_order = OptionalKey("children");
  output.rank = OptionalKey("oldest");
  output.primary_heir_minimum_share = {Presence::present, share};
  return output;
}

bridge::RealmLawGovernanceCandidateV1 Candidate(
    std::string_view key, bool active, bool can_enact,
    std::int64_t cost = 100) {
  bridge::RealmLawGovernanceCandidateV1 output{};
  output.law_key = Key(key);
  output.is_active = active;
  output.evaluation_complete = true;
  output.can_have = true;
  output.can_pass = true;
  output.can_enact = can_enact;
  output.blocked_reason = can_enact ? NoReason() : Reason("already_enacted");
  output.costs_complete = true;
  output.cost_count = 1;
  output.costs[0] = {Key("prestige"), cost};
  output.succession = SuccessionShape();
  return output;
}

void PopulatePreObservation(Observation &output) {
  static_assert(std::is_trivially_copyable_v<Observation>);
  std::memset(&output, 0, sizeof(output));
  output.available = true;
  output.paused = true;
  auto &snapshot = output.law_snapshot;
  snapshot.status = bridge::RealmLawGovernanceSnapshotV1Status::available;
  snapshot.unavailable_reason =
      bridge::RealmLawGovernanceSnapshotV1Failure::none;
  snapshot.public_revision = 901;
  snapshot.native_revision = 19'006;
  snapshot.proof_epoch = 33;
  snapshot.date_raw = 56'000'000;
  snapshot.played_character_id = 32'904;
  snapshot.group_count = 1;
  snapshot.readiness = {true, true, true, true, true, true};
  auto &group = snapshot.groups[0];
  group.group_key = Key("succession_order_laws");
  group.active_law_key = Key("partition_succession_law");
  group.can_change_evaluated = true;
  group.can_change = true;
  group.candidates_complete = true;
  group.candidate_count = 2;
  group.candidates[0] =
      Candidate("partition_succession_law", true, false);
  group.candidates[1] =
      Candidate("high_partition_succession_law", false, true);

  auto &titles = snapshot.title_baseline;
  titles.primary_title_presence = Presence::present;
  titles.primary_title_id = 101;
  titles.primary_title_successor_count = 2;
  titles.primary_title_successor_character_ids[0] = 201;
  titles.primary_title_successor_character_ids[1] = 301;
  titles.held_title_count = 1;
  titles.held_titles[0].title_id = 101;
  titles.held_titles[0].primary = true;
  titles.held_titles[0].successor_count = 2;
  titles.held_titles[0].successor_character_ids[0] = 201;
  titles.held_titles[0].successor_character_ids[1] = 301;

  output.resources_complete = true;
  output.resource_count = 1;
  output.resources[0] = {Key("prestige"), 500};
}

bridge::RealmLawEnactActionRequestV1 Request() {
  bridge::RealmLawEnactActionRequestV1 output{};
  output.request_id = "law4-test-1";
  output.group_key = Key("succession_order_laws");
  output.law_key = Key("high_partition_succession_law");
  output.expected_public_revision = 901;
  output.expected_native_revision = 19'006;
  output.expected_proof_epoch = 33;
  output.expected_date_raw = 56'000'000;
  output.expected_player_character_id = 32'904;
  output.budget_count = 1;
  output.budgets[0] = {Key("prestige"), 100};
  return output;
}

struct Fixture {
  std::array<Observation, 2> observations{};
  std::size_t capture_calls = 0;
  std::size_t submit_calls = 0;
  std::size_t fail_capture_call = 0;
  bool submit_result = true;
  bridge::RealmLawEnactSubmissionV1 submitted{};

  Fixture() {
    PopulatePreObservation(observations[0]);
    observations[1] = observations[0];
  }
};

bool Capture(void *context, Observation &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.capture_calls;
  if (fixture.capture_calls == fixture.fail_capture_call) return false;
  output = fixture.observations[fixture.capture_calls > 1 ? 1 : 0];
  return true;
}

bool Submit(void *context,
            const bridge::RealmLawEnactSubmissionV1 &submission) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.submit_calls;
  fixture.submitted = submission;
  return fixture.submit_result;
}

bridge::RealmLawEnactActionAccessV1 Access(Fixture &fixture) {
  bridge::RealmLawEnactActionAccessV1 output{};
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      bridge::kRealmLawGovernanceSnapshotV1ExecutableSha256;
  output.current_thread_id = 77;
  output.application_main_thread_id = 77;
  output.context = &fixture;
  output.capture_observation = &Capture;
  output.submit = &Submit;
  return output;
}

ActionFailure ExecuteFailure(
    Fixture &fixture, bridge::RealmLawEnactActionRequestV1 request,
    bridge::RealmLawEnactActionAccessV1 access) {
  bridge::RealmLawEnactActionAckV1 ack{};
  assert(bridge::ExecuteRealmLawEnactActionV1(access, request, ack) ==
         AckStatus::rejected_before_submit);
  assert(!ack.verification_pending);
  assert(fixture.submit_calls == 0);
  return ack.failure;
}

bridge::RealmLawEnactActionAckV1 SubmittedAck(Fixture &fixture) {
  bridge::RealmLawEnactActionAckV1 ack{};
  assert(bridge::ExecuteRealmLawEnactActionV1(
             Access(fixture), Request(), ack) ==
         AckStatus::submitted_verification_pending);
  assert(ack.verification_pending);
  assert(ack.failure == ActionFailure::none);
  assert(fixture.capture_calls == 2);
  assert(fixture.submit_calls == 1);
  return ack;
}

void PopulatePostObservation(Observation &output) {
  PopulatePreObservation(output);
  ++output.law_snapshot.public_revision;
  ++output.law_snapshot.native_revision;
  auto &group = output.law_snapshot.groups[0];
  group.active_law_key = Key("high_partition_succession_law");
  group.candidates[0] =
      Candidate("partition_succession_law", false, true);
  group.candidates[1] =
      Candidate("high_partition_succession_law", true, false);
  output.resources[0].amount_raw = 400;
}

void TestStableCandidateSubmitsExactlyOnceAndReturnsPendingAck() {
  auto fixture = std::make_unique<Fixture>();
  const auto ack = SubmittedAck(*fixture);
  assert(ack.pre_public_revision == 901);
  assert(ack.previous_effective_law_key ==
         Key("partition_succession_law"));
  assert(ack.requested_law_key == Key("high_partition_succession_law"));
  assert(ack.charge_count == 1);
  assert(ack.charges[0].cost_raw == 100);
  assert(ack.charges[0].pre_balance_raw == 500);
  assert(ack.expected_succession == SuccessionShape());
  assert(ack.pre_title_successors.primary_title_id == 101);
  assert(fixture->submitted.requested_law_key == ack.requested_law_key);
  assert(fixture->submitted.charge_count == 1);
}

void TestRequestBuildThreadAndCallbackGates() {
  auto fixture = std::make_unique<Fixture>();
  auto request = Request();
  request.request_id = "bad id";
  assert(ExecuteFailure(*fixture, request, Access(*fixture)) ==
         ActionFailure::request_contract_invalid);
  assert(fixture->capture_calls == 0);

  fixture = std::make_unique<Fixture>();
  auto access = Access(*fixture);
  access.admitted_executable_sha256 = "wrong";
  assert(ExecuteFailure(*fixture, Request(), access) ==
         ActionFailure::exact_build_mismatch);

  fixture = std::make_unique<Fixture>();
  access = Access(*fixture);
  access.current_thread_id = 78;
  assert(ExecuteFailure(*fixture, Request(), access) ==
         ActionFailure::application_main_thread_required);

  fixture = std::make_unique<Fixture>();
  access = Access(*fixture);
  access.submit = nullptr;
  assert(ExecuteFailure(*fixture, Request(), access) ==
         ActionFailure::callbacks_unavailable);
}

void TestPausedSnapshotAndFrameBindingGates() {
  auto fixture = std::make_unique<Fixture>();
  fixture->observations[0].available = false;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::observation_unavailable);

  fixture = std::make_unique<Fixture>();
  fixture->observations[0].paused = false;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::not_paused);

  fixture = std::make_unique<Fixture>();
  fixture->observations[0].law_snapshot.readiness.same_frame_ready = false;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::snapshot_unavailable);

  fixture = std::make_unique<Fixture>();
  auto request = Request();
  ++request.expected_proof_epoch;
  assert(ExecuteFailure(*fixture, request, Access(*fixture)) ==
         ActionFailure::stale_snapshot);
}

void TestAuthorityAndEngineFinalLegalityGates() {
  auto fixture = std::make_unique<Fixture>();
  fixture->observations[0].law_snapshot.groups[0].can_change = false;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::authority_denied);

  fixture = std::make_unique<Fixture>();
  auto &candidate =
      fixture->observations[0].law_snapshot.groups[0].candidates[1];
  candidate.can_enact = false;
  candidate.blocked_reason = Reason("cooldown_active");
  bridge::RealmLawEnactActionAckV1 ack{};
  assert(bridge::ExecuteRealmLawEnactActionV1(
             Access(*fixture), Request(), ack) ==
         AckStatus::rejected_before_submit);
  assert(ack.failure == ActionFailure::final_legality_denied);
  assert(bridge::RealmLawGovernanceReasonViewV1(ack.blocked_reason) ==
         "cooldown_active");
  assert(fixture->submit_calls == 0);
}

void TestBudgetAndResourceGates() {
  auto fixture = std::make_unique<Fixture>();
  auto request = Request();
  request.budgets[0].maximum_spend_raw = 99;
  assert(ExecuteFailure(*fixture, request, Access(*fixture)) ==
         ActionFailure::budget_not_authorized);

  fixture = std::make_unique<Fixture>();
  fixture->observations[0].resources[0].amount_raw = 99;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::insufficient_resources);

  fixture = std::make_unique<Fixture>();
  request = Request();
  request.budget_count = 0;
  assert(ExecuteFailure(*fixture, request, Access(*fixture)) ==
         ActionFailure::budget_not_authorized);

  fixture = std::make_unique<Fixture>();
  fixture->observations[0].resources_complete = false;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::resource_observation_invalid);
}

void TestAllSelectedSemanticsMustStayStable() {
  auto fixture = std::make_unique<Fixture>();
  fixture->observations[1].law_snapshot.groups[0].can_change = false;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::state_changed_before_submit);
  assert(fixture->capture_calls == 2);

  fixture = std::make_unique<Fixture>();
  ++fixture->observations[1]
        .law_snapshot.groups[0].candidates[1].costs[0].amount_raw;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::state_changed_before_submit);

  fixture = std::make_unique<Fixture>();
  ++fixture->observations[1]
        .law_snapshot.groups[0].candidates[1]
        .succession.primary_heir_minimum_share.value_raw;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::state_changed_before_submit);

  fixture = std::make_unique<Fixture>();
  --fixture->observations[1].resources[0].amount_raw;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::state_changed_before_submit);

  fixture = std::make_unique<Fixture>();
  fixture->observations[1].law_snapshot.title_baseline
      .primary_title_successor_character_ids[1] = 302;
  assert(ExecuteFailure(*fixture, Request(), Access(*fixture)) ==
         ActionFailure::state_changed_before_submit);
}

void TestSubmitRejectionIsTypedAndNeverRetried() {
  auto fixture = std::make_unique<Fixture>();
  fixture->submit_result = false;
  bridge::RealmLawEnactActionAckV1 ack{};
  assert(bridge::ExecuteRealmLawEnactActionV1(
             Access(*fixture), Request(), ack) ==
         AckStatus::rejected_before_submit);
  assert(ack.failure == ActionFailure::native_submit_rejected);
  assert(fixture->submit_calls == 1);
  assert(fixture->capture_calls == 2);
}

void TestReceiptDistinguishesEnactedRejectedAndFailed() {
  auto fixture = std::make_unique<Fixture>();
  const auto ack = SubmittedAck(*fixture);
  auto post = std::make_unique<Observation>();
  PopulatePostObservation(*post);
  bridge::RealmLawEnactActionReceiptV1 receipt{};
  assert(bridge::VerifyRealmLawEnactActionReceiptV1(ack, *post, receipt) ==
         ReceiptStatus::enacted);
  assert(receipt.failure == ReceiptFailure::none);
  assert(receipt.effective_law_verified);
  assert(receipt.resources_verified);
  assert(receipt.succession_verified);
  assert(receipt.charges[0].post_balance_raw == 400);
  assert(receipt.post_title_successors.primary_title_id == 101);

  auto rejected_fixture = std::make_unique<Fixture>();
  auto rejected_request = Request();
  rejected_request.budget_count = 0;
  bridge::RealmLawEnactActionAckV1 rejected_ack{};
  bridge::ExecuteRealmLawEnactActionV1(
      Access(*rejected_fixture), rejected_request, rejected_ack);
  assert(bridge::VerifyRealmLawEnactActionReceiptV1(
             rejected_ack, *post, receipt) == ReceiptStatus::rejected);
  assert(receipt.failure == ReceiptFailure::action_rejected);
  assert(receipt.rejected_action_failure ==
         ActionFailure::budget_not_authorized);

  auto stale = std::make_unique<Observation>();
  PopulatePreObservation(*stale);
  assert(bridge::VerifyRealmLawEnactActionReceiptV1(ack, *stale, receipt) ==
         ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::no_new_paused_snapshot);

  auto wrong_law = std::make_unique<Observation>();
  PopulatePostObservation(*wrong_law);
  wrong_law->law_snapshot.groups[0].active_law_key =
      Key("partition_succession_law");
  assert(bridge::VerifyRealmLawEnactActionReceiptV1(
             ack, *wrong_law, receipt) == ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::effective_law_not_enacted);

  auto wrong_resource = std::make_unique<Observation>();
  PopulatePostObservation(*wrong_resource);
  wrong_resource->resources[0].amount_raw = 401;
  assert(bridge::VerifyRealmLawEnactActionReceiptV1(
             ack, *wrong_resource, receipt) == ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::resource_recheck_failed);

  auto wrong_shape = std::make_unique<Observation>();
  PopulatePostObservation(*wrong_shape);
  ++wrong_shape->law_snapshot.groups[0].candidates[1]
        .succession.primary_heir_minimum_share.value_raw;
  assert(bridge::VerifyRealmLawEnactActionReceiptV1(
             ack, *wrong_shape, receipt) == ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::succession_shape_changed);

  auto wrong_player = std::make_unique<Observation>();
  PopulatePostObservation(*wrong_player);
  ++wrong_player->law_snapshot.played_character_id;
  assert(bridge::VerifyRealmLawEnactActionReceiptV1(
             ack, *wrong_player, receipt) == ReceiptStatus::failed);
  assert(receipt.failure == ReceiptFailure::player_identity_changed);
}

} // namespace

int main() {
  static_assert(bridge::kRealmLawGovernanceSnapshotV1ExecutableSha256.size() ==
                64);
  TestStableCandidateSubmitsExactlyOnceAndReturnsPendingAck();
  TestRequestBuildThreadAndCallbackGates();
  TestPausedSnapshotAndFrameBindingGates();
  TestAuthorityAndEngineFinalLegalityGates();
  TestBudgetAndResourceGates();
  TestAllSelectedSemanticsMustStayStable();
  TestSubmitRejectionIsTypedAndNeverRetried();
  TestReceiptDistinguishesEnactedRejectedAndFailed();
  assert(bridge::RealmLawEnactActionFailureNameV1(
             ActionFailure::state_changed_before_submit) ==
         "state_changed_before_submit");
  assert(bridge::RealmLawEnactActionReceiptFailureNameV1(
             ReceiptFailure::resource_recheck_failed) ==
         "resource_recheck_failed");
  std::cout << "realm_law_enact_action_v1_test: 8/8 GREEN\n";
  return 0;
}
