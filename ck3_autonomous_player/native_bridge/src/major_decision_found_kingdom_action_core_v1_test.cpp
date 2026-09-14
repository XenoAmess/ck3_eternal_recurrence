#include "xar_bridge/major_decision_found_kingdom_action_core_v1.hpp"

#include <cassert>
#include <cstddef>
#include <string_view>
#include <vector>

namespace bridge = xar::bridge;

namespace {

using AckStatus = bridge::MajorDecisionFoundKingdomActionAckStatusV1;
using FailureClass = bridge::MajorDecisionFoundKingdomActionFailureClassV1;
using ReceiptStatus =
    bridge::MajorDecisionFoundKingdomActionReceiptStatusV1;

struct Fixture {
  std::vector<bridge::MajorDecisionFoundKingdomActionPreconditionV1>
      observations{};
  std::size_t capture_index = 0;
  int submit_calls = 0;
  bool submit_result = true;
  bridge::MajorDecisionFoundKingdomActionBindingV1 submitted_binding{};
  std::string submitted_decision_id;
};

bridge::MajorDecisionTypedBoolV1 Known(bool value) {
  return {bridge::MajorDecisionFieldStateV1::known, value,
          bridge::MajorDecisionUnknownReasonV1::none};
}

bridge::MajorDecisionEvaluatedCostV1 Cost() {
  bridge::MajorDecisionEvaluatedCostV1 output{};
  output.state = bridge::MajorDecisionFieldStateV1::known;
  output.source = bridge::MajorDecisionCostSourceV1::native_evaluated_cost;
  output.gold_q100000 = 30'000'000;
  output.treasury_q100000 = 0;
  output.prestige_q100000 = 50'000'000;
  output.piety_q100000 = 20'000'000;
  output.unknown_reason = bridge::MajorDecisionUnknownReasonV1::none;
  return output;
}

bridge::MajorDecisionFoundKingdomActionBindingV1 Binding() {
  bridge::MajorDecisionFoundKingdomActionBindingV1 output{};
  output.snapshot_revision = 100;
  output.native_revision = 70;
  output.proof_epoch = 40;
  output.date_raw = 1092;
  output.played_character_id = 0x0100002A;
  output.decision_database_identity = 0xDB001;
  output.decision_database_generation = 11;
  output.decision_definition_identity = 0xDE001;
  output.decision_definition_generation = 12;
  output.primary_title_id = 0x02000031;
  output.primary_title_identity = 0x71001;
  output.primary_title_generation = 13;
  output.world_identity = 0xA11001;
  output.world_generation = 14;
  output.world_revision = 60;
  return output;
}

bridge::MajorDecisionFoundKingdomActionPreconditionV1 Precondition() {
  bridge::MajorDecisionFoundKingdomActionPreconditionV1 output{};
  output.available = true;
  output.application_main_thread = true;
  output.paused = true;
  output.map_ready = true;
  output.played_character_alive = true;
  output.played_character_identity_round_trip = true;
  output.decision_database_identity_round_trip = true;
  output.decision_definition_identity_round_trip = true;
  output.decision_source_block_sha256_round_trip = true;
  output.decision_id.assign(
      bridge::kMajorDecisionFoundKingdomDecisionIdV1);
  output.binding = Binding();
  output.is_shown = Known(true);
  output.is_valid = Known(true);
  output.is_valid_showing_failures_only = Known(true);
  output.evaluated_cost = Cost();
  output.is_affordable = Known(true);
  output.can_take = Known(true);
  output.effect_preview.state = bridge::MajorDecisionFieldStateV1::unknown;
  output.effect_preview.unknown_reason =
      bridge::MajorDecisionUnknownReasonV1::effect_preview_not_provided;
  output.effect_preview.executable = false;
  return output;
}

bridge::MajorDecisionFoundKingdomActionRequestV1 Request() {
  bridge::MajorDecisionFoundKingdomActionRequestV1 output{};
  output.request_id = "decision5-fixture-1";
  output.decision_id.assign(
      bridge::kMajorDecisionFoundKingdomDecisionIdV1);
  output.expected_binding = Binding();
  output.expected_evaluated_cost = Cost();
  return output;
}

bridge::MajorDecisionFoundKingdomActionEnvironmentV1 Environment() {
  bridge::MajorDecisionFoundKingdomActionEnvironmentV1 output{};
  output.action_enabled = true;
  output.exact_build_admitted = true;
  output.admitted_game_version =
      bridge::kMajorDecisionFoundKingdomGameVersionV1;
  output.admitted_executable_sha256 =
      bridge::kMajorDecisionFoundKingdomExecutableSha256V1;
  output.offline_fixture_submit = true;
  return output;
}

bool Capture(void *context,
             bridge::MajorDecisionFoundKingdomActionPreconditionV1 &output)
    noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (fixture.capture_index >= fixture.observations.size()) return false;
  output = fixture.observations[fixture.capture_index++];
  return true;
}

bool Submit(
    void *context,
    const bridge::MajorDecisionFoundKingdomActionBindingV1 &binding,
    std::string_view decision_id) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.submit_calls;
  fixture.submitted_binding = binding;
  fixture.submitted_decision_id.assign(decision_id);
  return fixture.submit_result;
}

bridge::MajorDecisionFoundKingdomActionAccessV1 Access(Fixture &fixture) {
  return {&fixture, &Capture, &Submit};
}

bridge::MajorDecisionFoundKingdomActionPostconditionV1 Postcondition() {
  const auto pre = Binding();
  bridge::MajorDecisionFoundKingdomActionPostconditionV1 output{};
  output.available = true;
  output.application_main_thread = true;
  output.paused = true;
  output.map_ready = true;
  output.snapshot_revision = pre.snapshot_revision + 1;
  output.native_revision = pre.native_revision + 1;
  output.proof_epoch = pre.proof_epoch;
  output.date_raw = pre.date_raw;
  output.played_character_id = pre.played_character_id;
  output.played_character_identity_round_trip = true;
  output.decision_database_identity = pre.decision_database_identity;
  output.decision_database_generation = pre.decision_database_generation;
  output.decision_database_identity_round_trip = true;
  output.decision_state_observed = true;
  output.decision_definition_present = true;
  output.decision_definition_identity = pre.decision_definition_identity;
  output.decision_definition_generation =
      pre.decision_definition_generation;
  output.decision_definition_identity_round_trip = true;
  output.decision_can_take_known = true;
  output.decision_can_take = false;
  output.primary_title_observed = true;
  output.primary_title_id = 0x02000099;
  output.primary_title_identity = 0x99001;
  output.primary_title_generation = 21;
  output.primary_title_tier =
      bridge::MajorDecisionFoundKingdomTitleTierV1::kingdom;
  output.primary_title_holder_character_id = pre.played_character_id;
  output.primary_title_identity_round_trip = true;
  output.primary_title_holder_identity_round_trip = true;
  output.player_primary_title_round_trip = true;
  output.dynamic_custom_kingdom_observed = true;
  output.world_outcome_observed = true;
  output.world_identity = pre.world_identity;
  output.world_generation = pre.world_generation;
  output.world_revision = pre.world_revision + 1;
  output.world_identity_round_trip = true;
  output.new_title_registered = true;
  output.title_world_index_round_trip = true;
  return output;
}

bridge::MajorDecisionFoundKingdomActionAckV1 SubmitHappy(Fixture &fixture,
    bridge::MajorDecisionFoundKingdomActionStateV1 &state) {
  const auto pre = Precondition();
  fixture.observations = {pre, pre};
  auto environment = Environment();
  auto request = Request();
  auto access = Access(fixture);
  bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
  assert(bridge::ExecuteMajorDecisionFoundKingdomActionCoreV1(
             environment, access, request, state, ack) ==
         AckStatus::submitted_verification_pending);
  return ack;
}

void TestSubmitAndFreshReceipt() {
  Fixture fixture{};
  bridge::MajorDecisionFoundKingdomActionStateV1 state{};
  auto ack = SubmitHappy(fixture, state);
  assert(fixture.capture_index == 2);
  assert(fixture.submit_calls == 1);
  assert(fixture.submitted_binding == Binding());
  assert(fixture.submitted_decision_id ==
         bridge::kMajorDecisionFoundKingdomDecisionIdV1);
  assert(state.verification_pending);
  assert(ack.verification_pending);
  assert(!ack.effect_preview_available);
  assert(!ack.exact_benefit_claimed);
  assert(ack.submitted_evaluated_cost == Cost());

  // A pending action owns the single submit slot.
  auto environment = Environment();
  auto request = Request();
  auto access = Access(fixture);
  bridge::MajorDecisionFoundKingdomActionAckV1 duplicate{};
  assert(bridge::ExecuteMajorDecisionFoundKingdomActionCoreV1(
             environment, access, request, state, duplicate) ==
         AckStatus::rejected_before_submit);
  assert(duplicate.failure_class == FailureClass::pending_action);
  assert(fixture.submit_calls == 1);

  const auto post = Postcondition();
  bridge::MajorDecisionFoundKingdomActionReceiptV1 receipt{};
  assert(bridge::VerifyMajorDecisionFoundKingdomActionReceiptV1(
             ack, post, state, receipt) == ReceiptStatus::applied);
  assert(receipt.postcondition_verified);
  assert(receipt.decision_no_longer_takeable);
  assert(receipt.new_kingdom_title_verified);
  assert(receipt.world_outcome_verified);
  assert(!receipt.effect_preview_available);
  assert(!receipt.exact_benefit_claimed);
  assert(!state.verification_pending);
}

void TestPreconditionFailuresDoNotSubmit() {
  const auto run = [](auto mutate,
                      FailureClass expected_failure) {
    Fixture fixture{};
    auto first = Precondition();
    auto second = first;
    auto request = Request();
    auto environment = Environment();
    mutate(first, second, request, environment, fixture);
    fixture.observations = {first, second};
    auto access = Access(fixture);
    bridge::MajorDecisionFoundKingdomActionStateV1 state{};
    bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
    assert(bridge::ExecuteMajorDecisionFoundKingdomActionCoreV1(
               environment, access, request, state, ack) ==
           AckStatus::rejected_before_submit);
    assert(ack.failure_class == expected_failure);
    assert(fixture.submit_calls == 0);
    assert(!state.verification_pending);
  };

  run([](auto &first, auto &, auto &, auto &, auto &) {
        first.is_valid = Known(false);
      },
      FailureClass::eligibility);
  run([](auto &first, auto &, auto &, auto &, auto &) {
        first.is_affordable = Known(false);
      },
      FailureClass::resources);
  run([](auto &, auto &, auto &request, auto &, auto &) {
        ++request.expected_evaluated_cost.piety_q100000;
      },
      FailureClass::resources);
  run([](auto &first, auto &, auto &, auto &, auto &) {
        first.can_take = Known(false);
      },
      FailureClass::can_take);
  run([](auto &, auto &, auto &request, auto &, auto &) {
        ++request.expected_binding.proof_epoch;
      },
      FailureClass::identity_binding);
  run([](auto &, auto &second, auto &, auto &, auto &) {
        ++second.evaluated_cost.gold_q100000;
      },
      FailureClass::observation);
  run([](auto &, auto &, auto &, auto &environment, auto &) {
        environment.exact_build_admitted = false;
      },
      FailureClass::exact_build);
  run([](auto &, auto &, auto &, auto &environment, auto &) {
        environment.offline_fixture_submit = false;
      },
      FailureClass::native_submit);
}

void TestSubmitFailureIsOneAttempt() {
  Fixture fixture{};
  const auto pre = Precondition();
  fixture.observations = {pre, pre};
  fixture.submit_result = false;
  auto environment = Environment();
  auto request = Request();
  auto access = Access(fixture);
  bridge::MajorDecisionFoundKingdomActionStateV1 state{};
  bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
  assert(bridge::ExecuteMajorDecisionFoundKingdomActionCoreV1(
             environment, access, request, state, ack) ==
         AckStatus::rejected_before_submit);
  assert(ack.failure_class == FailureClass::native_submit);
  assert(fixture.submit_calls == 1);
  assert(!state.verification_pending);
}

void TestReceiptFailuresStayPendingForFreshRetry() {
  const auto run = [](auto mutate, std::string_view expected_reason) {
    Fixture fixture{};
    bridge::MajorDecisionFoundKingdomActionStateV1 state{};
    const auto ack = SubmitHappy(fixture, state);
    auto post = Postcondition();
    mutate(post);
    bridge::MajorDecisionFoundKingdomActionReceiptV1 receipt{};
    assert(bridge::VerifyMajorDecisionFoundKingdomActionReceiptV1(
               ack, post, state, receipt) ==
           ReceiptStatus::postcondition_failed);
    assert(receipt.reason == expected_reason);
    assert(!receipt.postcondition_verified);
    assert(state.verification_pending);

    // A later independently captured fresh state can close the same ACK.
    post = Postcondition();
    assert(bridge::VerifyMajorDecisionFoundKingdomActionReceiptV1(
               ack, post, state, receipt) == ReceiptStatus::applied);
    assert(!state.verification_pending);
  };

  run([](auto &post) { post.snapshot_revision = Binding().snapshot_revision; },
      "no_fresh_paused_observation");
  run([](auto &post) { ++post.date_raw; },
      "proof_or_date_binding_changed");
  run([](auto &post) { ++post.decision_database_generation; },
      "player_or_database_binding_changed");
  run([](auto &post) { post.decision_can_take = true; },
      "decision_still_takeable");
  run([](auto &post) { post.primary_title_id = Binding().primary_title_id; },
      "new_kingdom_title_not_observed");
  run([](auto &post) { post.title_world_index_round_trip = false; },
      "world_outcome_not_observed");
}

void TestMissingDefinitionCanBeObservedAsConsumed() {
  Fixture fixture{};
  bridge::MajorDecisionFoundKingdomActionStateV1 state{};
  const auto ack = SubmitHappy(fixture, state);
  auto post = Postcondition();
  post.decision_definition_present = false;
  post.decision_definition_identity = 0;
  post.decision_definition_generation = 0;
  post.decision_definition_identity_round_trip = false;
  post.decision_can_take_known = false;
  bridge::MajorDecisionFoundKingdomActionReceiptV1 receipt{};
  assert(bridge::VerifyMajorDecisionFoundKingdomActionReceiptV1(
             ack, post, state, receipt) == ReceiptStatus::applied);
  assert(receipt.decision_no_longer_takeable);
}

void TestMutatedAckCannotChangePendingBinding() {
  Fixture fixture{};
  bridge::MajorDecisionFoundKingdomActionStateV1 state{};
  auto ack = SubmitHappy(fixture, state);
  ++ack.pre_binding.decision_definition_generation;
  auto post = Postcondition();
  bridge::MajorDecisionFoundKingdomActionReceiptV1 receipt{};
  assert(bridge::VerifyMajorDecisionFoundKingdomActionReceiptV1(
             ack, post, state, receipt) ==
         ReceiptStatus::postcondition_failed);
  assert(receipt.reason == "invalid_pending_ack");
  assert(state.verification_pending);
}

} // namespace

int main() {
  TestSubmitAndFreshReceipt();
  TestPreconditionFailuresDoNotSubmit();
  TestSubmitFailureIsOneAttempt();
  TestReceiptFailuresStayPendingForFreshRetry();
  TestMissingDefinitionCanBeObservedAsConsumed();
  TestMutatedAckCannotChangePendingBinding();
  return 0;
}
