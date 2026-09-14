#include "xar_bridge/character_interaction_proposal_action_core_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

namespace game = xar::game;
namespace ck3 = xar::ck3_11906;

using AckStatus = game::CharacterInteractionProposalActionAckStatusV1;
using AcceptanceKind = game::CharacterInteractionAcceptanceKindV1;
using Failure = game::CharacterInteractionProposalActionFailureV1;
using Postcondition = game::CharacterInteractionProposalPostconditionKindV1;
using ReceiptStatus = game::CharacterInteractionProposalReceiptStatusV1;

constexpr std::int32_t kActorId = 0x01000002;
constexpr std::int32_t kRecipientId = 0x02000003;
constexpr std::int32_t kWardId = 0x03000004;
constexpr std::int32_t kGuardianId = 0x04000005;
constexpr std::int32_t kVassalId = 0x05000006;
constexpr std::int32_t kPrisonerId = 0x06000007;

constexpr std::array<std::string_view, 11> kAllowlist{
    "gift_interaction",
    "recruit_guest_interaction",
    "invite_to_court_interaction",
    "offer_vassalization_interaction",
    "demand_payment_interaction",
    "educate_child_interaction",
    "offer_ward_interaction",
    "offer_guardianship_interaction",
    "grant_titles_interaction",
    "grant_vassal_interaction",
    "ransom_interaction",
};

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "character interaction proposal action fixture failed at line " +
        std::to_string(location.line()));
  }
}

void AssignSnapshotId(
    std::array<char, game::kCharacterInteractionPreviewSnapshotIdCapacityV1>
        &output,
    std::string_view value) {
  Require(value.size() < output.size());
  std::copy(value.begin(), value.end(), output.begin());
}

struct Fixture {
  game::CharacterInteractionProposalPreviewEnvelopeV1 envelope{};
  std::int32_t captures = 0;
  std::int32_t submits = 0;
  bool submit_acknowledged = true;
  bool drift_cost = false;
  bool drift_acceptance = false;
  bool drift_frame = false;
};

void SetPayloadShape(Fixture &fixture, std::string_view key) {
  auto &payload = fixture.envelope.payload;
  payload.complete = true;
  payload.fingerprint = "payload:v1";
  payload.semantic_subject_character_id = kRecipientId;
  payload.semantic_object_character_id = kActorId;
  if (key == "offer_vassalization_interaction") {
    payload.ordinary_feudal_or_clan_vassalization = true;
  } else if (key == "educate_child_interaction" ||
             key == "offer_ward_interaction" ||
             key == "offer_guardianship_interaction") {
    payload.semantic_subject_character_id = kWardId;
    payload.semantic_object_character_id = kGuardianId;
  } else if (key == "grant_titles_interaction") {
    payload.selected_title_count = 2;
  } else if (key == "grant_vassal_interaction") {
    payload.semantic_subject_character_id = kVassalId;
    payload.semantic_object_character_id = kRecipientId;
  } else if (key == "ransom_interaction") {
    payload.semantic_subject_character_id = kPrisonerId;
  }
}

Fixture BaseFixture(std::string_view key = "gift_interaction") {
  Fixture fixture{};
  auto &preview = fixture.envelope.preview;
  preview.status = game::CharacterInteractionPreviewStatusV1::available;
  preview.unavailable_reason =
      game::CharacterInteractionPreviewFailureV1::none;
  AssignSnapshotId(preview.snapshot_id, "diplomatic-frame-31");
  preview.public_revision = 51;
  preview.native_revision = 91;
  preview.proof_epoch = 121;
  preview.date_raw = 10'001;
  preview.definition.canonical_key.assign(key);
  preview.definition.deterministic_key_hash = 0xD15EA5EDU;
  preview.definition.runtime_ordinal = 87;
  preview.roles.actor_character_id = kActorId;
  preview.roles.recipient_character_id = kRecipientId;
  preview.can_send = true;
  preview.costs.raw[0] = 2'500'000;
  preview.costs.raw[3] = -100'000;
  preview.acceptance.kind = AcceptanceKind::auto_accept;
  preview.acceptance.recipient_is_ai = true;
  preview.acceptance.auto_accept = true;
  preview.acceptance.would_accept_now_present = true;
  preview.acceptance.would_accept_now = true;
  preview.readiness = {true, true, true, true, true, true, true, true};
  SetPayloadShape(fixture, key);
  return fixture;
}

game::CharacterInteractionProposalActionRequestV1 Request(
    const Fixture &fixture) {
  const auto &preview = fixture.envelope.preview;
  const auto &payload = fixture.envelope.payload;
  game::CharacterInteractionProposalActionRequestV1 request{};
  request.request_id = "proposal-action-31";
  request.expected_snapshot_id = "diplomatic-frame-31";
  request.expected_public_revision = preview.public_revision;
  request.expected_native_revision = preview.native_revision;
  request.expected_proof_epoch = preview.proof_epoch;
  request.expected_date_raw = preview.date_raw;
  request.interaction_key = preview.definition.canonical_key;
  request.actor_character_id = preview.roles.actor_character_id;
  request.recipient_character_id = preview.roles.recipient_character_id;
  request.semantic_subject_character_id =
      payload.semantic_subject_character_id;
  request.semantic_object_character_id = payload.semantic_object_character_id;
  request.selected_title_count = payload.selected_title_count;
  request.payload_fingerprint = payload.fingerprint;
  request.budget.maximum_actor_spend_raw.fill(10'000'000);
  return request;
}

bool Capture(void *context,
             game::CharacterInteractionProposalPreviewEnvelopeV1
                 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.envelope;
  ++fixture.captures;
  if (fixture.captures == 2) {
    if (fixture.drift_cost) ++output.preview.costs.raw[0];
    if (fixture.drift_acceptance) {
      output.preview.acceptance.kind = AcceptanceKind::ai_final;
      output.preview.acceptance.auto_accept = false;
      output.preview.acceptance.recipient_raw_present = true;
      output.preview.acceptance.recipient_raw = 1'000'000;
      output.preview.acceptance.final_status_present = true;
      output.preview.acceptance.final_status_raw = 0;
    }
    if (fixture.drift_frame) ++output.preview.proof_epoch;
  }
  return true;
}

bool SubmitOnce(
    void *context,
    const game::CharacterInteractionProposalActionRequestV1 &request,
    const game::CharacterInteractionProposalPreviewEnvelopeV1
        &bound_preview) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.submits;
  return fixture.submit_acknowledged &&
         request.interaction_key ==
             bound_preview.preview.definition.canonical_key &&
         request.payload_fingerprint == bound_preview.payload.fingerprint;
}

ck3::CharacterInteractionProposalActionEnvironmentV1 Environment() {
  return {true, false, true};
}

ck3::CharacterInteractionProposalActionAccessV1 Access(Fixture &fixture) {
  return {&fixture, &Capture, &SubmitOnce};
}

game::CharacterInteractionProposalPostconditionObservationV1 AppliedPost(
    const game::CharacterInteractionProposalActionAckV1 &ack) {
  game::CharacterInteractionProposalPostconditionObservationV1 post{};
  post.available = true;
  post.paused = true;
  post.snapshot_id = "diplomatic-frame-32";
  post.public_revision = ack.pre_public_revision + 1;
  post.native_revision = ack.pre_native_revision + 1;
  post.date_raw = ack.pre_date_raw;
  post.interaction_key = ack.interaction_key;
  post.actor_character_id = ack.actor_character_id;
  post.recipient_character_id = ack.recipient_character_id;
  post.semantic_subject_character_id = ack.semantic_subject_character_id;
  post.semantic_object_character_id = ack.semantic_object_character_id;
  post.selected_title_count = ack.selected_title_count;
  post.payload_fingerprint = ack.payload_fingerprint;
  post.terms_reconciled = true;
  switch (ack.postcondition_kind) {
  case Postcondition::gift_opinion_and_payment:
    post.recipient_has_gift_opinion_toward_actor = true;
    post.actor_gold_spent_raw = ack.costs.raw[0];
    break;
  case Postcondition::recruit_to_court:
    post.recipient_court_owner_character_id = ack.actor_character_id;
    break;
  case Postcondition::invite_to_court_and_cooldown:
    post.recipient_court_owner_character_id = ack.actor_character_id;
    post.invite_cooldown_present = true;
    break;
  case Postcondition::ordinary_vassalization:
    post.recipient_immediate_liege_character_id = ack.actor_character_id;
    post.obligation_state_matches = true;
    break;
  case Postcondition::demand_payment_and_hook:
    post.actor_hook_to_recipient_consumed = true;
    post.actor_gold_received_raw = 5'000'000;
    break;
  case Postcondition::educate_child_relation:
  case Postcondition::offer_ward_relation:
  case Postcondition::offer_guardianship_relation:
    post.observed_guardian_character_id =
        ack.semantic_object_character_id;
    post.observed_ward_character_id = ack.semantic_subject_character_id;
    post.education_relation_present = true;
    break;
  case Postcondition::grant_selected_titles:
    post.selected_titles_held_by_subject_count = ack.selected_title_count;
    post.title_transfer_graph_consistent = true;
    break;
  case Postcondition::grant_vassal_transfer:
    post.transferred_vassal_immediate_liege_character_id =
        ack.semantic_object_character_id;
    post.title_transfer_graph_consistent = true;
    break;
  case Postcondition::ransom_prisoner_release:
    post.prisoner_imprisoned_by_character_id = -1;
    break;
  case Postcondition::unavailable:
    break;
  }
  return post;
}

game::CharacterInteractionProposalActionAckV1 ExecuteAvailable(
    Fixture &fixture, ck3::CharacterInteractionProposalActionStateV1 &state) {
  game::CharacterInteractionProposalActionAckV1 ack{};
  Require(ck3::ExecuteCharacterInteractionProposalActionCoreV1(
              Environment(), Access(fixture), state, Request(fixture), ack) ==
          AckStatus::submitted_verification_pending);
  Require(ack.verification_pending && ack.failure == Failure::none);
  Require(fixture.captures == 2 && fixture.submits == 1);
  Require(state.submission_in_flight &&
          state.in_flight_request_id == ack.request_id &&
          state.acknowledged_submission_count == 1);
  return ack;
}

void TestAllElevenAllowlistedReceipts() {
  for (const auto key : kAllowlist) {
    auto fixture = BaseFixture(key);
    ck3::CharacterInteractionProposalActionStateV1 state{};
    const auto ack = ExecuteAvailable(fixture, state);
    Require(ack.postcondition_kind != Postcondition::unavailable);
    Require(ck3::CharacterInteractionProposalPostconditionKeyV1(
                ack.postcondition_kind) != "unavailable");
    game::CharacterInteractionProposalReceiptV1 receipt{};
    Require(ck3::VerifyCharacterInteractionProposalReceiptV1(
                state, ack, AppliedPost(ack), receipt) ==
            ReceiptStatus::applied);
    Require(receipt.interaction_specific_postcondition_verified);
    Require(!state.submission_in_flight &&
            state.acknowledged_submission_count == 1);
  }
}

void TestPreviewAndAllowlistGates() {
  {
    auto fixture = BaseFixture();
    auto request = Request(fixture);
    request.interaction_key = "imprison_interaction";
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    Require(ck3::ExecuteCharacterInteractionProposalActionCoreV1(
                Environment(), Access(fixture), state, request, ack) ==
            AckStatus::rejected_before_submit);
    Require(ack.failure == Failure::interaction_not_allowlisted &&
            fixture.captures == 0 && fixture.submits == 0);
  }
  {
    auto fixture = BaseFixture("educate_child_interaction");
    fixture.envelope.payload.religious_option_selected = true;
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalActionCoreV1(
        Environment(), Access(fixture), state, Request(fixture), ack);
    Require(ack.failure == Failure::religious_option_deferred &&
            fixture.submits == 0);
  }
  {
    auto fixture = BaseFixture("offer_vassalization_interaction");
    fixture.envelope.payload.ordinary_feudal_or_clan_vassalization = false;
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalActionCoreV1(
        Environment(), Access(fixture), state, Request(fixture), ack);
    Require(ack.failure == Failure::proposal_payload_mismatch &&
            fixture.submits == 0);
  }
  {
    auto fixture = BaseFixture();
    fixture.envelope.preview.readiness.same_frame_ready = false;
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalActionCoreV1(
        Environment(), Access(fixture), state, Request(fixture), ack);
    Require(ack.failure == Failure::proposal_preview_unavailable &&
            fixture.submits == 0);
  }
}

void TestCanSendAcceptanceAndBudgetGates() {
  {
    auto fixture = BaseFixture();
    fixture.envelope.preview.can_send = false;
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalActionCoreV1(
        Environment(), Access(fixture), state, Request(fixture), ack);
    Require(ack.failure == Failure::can_send_rejected &&
            fixture.submits == 0);
  }
  {
    auto fixture = BaseFixture();
    auto &acceptance = fixture.envelope.preview.acceptance;
    acceptance = {};
    acceptance.kind = AcceptanceKind::ai_final;
    acceptance.recipient_is_ai = true;
    acceptance.recipient_raw_present = true;
    acceptance.recipient_raw = -3'000'000;
    acceptance.final_status_present = true;
    acceptance.final_status_raw = 2;
    acceptance.would_accept_now_present = true;
    acceptance.would_accept_now = false;
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalActionCoreV1(
        Environment(), Access(fixture), state, Request(fixture), ack);
    Require(ack.failure == Failure::acceptance_not_actionable &&
            fixture.submits == 0);
  }
  {
    auto fixture = BaseFixture();
    auto &acceptance = fixture.envelope.preview.acceptance;
    acceptance = {};
    acceptance.kind = AcceptanceKind::human_pending;
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalActionCoreV1(
        Environment(), Access(fixture), state, Request(fixture), ack);
    Require(ack.failure == Failure::acceptance_not_actionable &&
            fixture.submits == 0);
  }
  {
    auto fixture = BaseFixture();
    auto request = Request(fixture);
    request.budget.maximum_actor_spend_raw[0] = 2'499'999;
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalActionCoreV1(
        Environment(), Access(fixture), state, request, ack);
    Require(ack.failure == Failure::budget_exceeded &&
            fixture.submits == 0);
  }
}

void TestEnvironmentAndSubmitSeamGates() {
  auto fixture = BaseFixture();
  ck3::CharacterInteractionProposalActionStateV1 state{};
  game::CharacterInteractionProposalActionAckV1 ack{};
  auto environment = Environment();
  environment.exact_build_admitted = false;
  ck3::ExecuteCharacterInteractionProposalActionCoreV1(
      environment, Access(fixture), state, Request(fixture), ack);
  Require(ack.failure == Failure::exact_build_not_admitted &&
          fixture.captures == 0 && fixture.submits == 0);

  fixture = BaseFixture();
  environment = Environment();
  environment.offline_fixture_submit = false;
  ck3::ExecuteCharacterInteractionProposalActionCoreV1(
      environment, Access(fixture), state, Request(fixture), ack);
  Require(ack.failure == Failure::submit_seam_unavailable &&
          fixture.captures == 1 && fixture.submits == 0);
}

void TestDoubleCaptureAndSingleSubmit() {
  for (std::int32_t drift_kind = 0; drift_kind != 3; ++drift_kind) {
    auto fixture = BaseFixture();
    fixture.drift_cost = drift_kind == 0;
    fixture.drift_acceptance = drift_kind == 1;
    fixture.drift_frame = drift_kind == 2;
    ck3::CharacterInteractionProposalActionStateV1 state{};
    game::CharacterInteractionProposalActionAckV1 ack{};
    ck3::ExecuteCharacterInteractionProposalActionCoreV1(
        Environment(), Access(fixture), state, Request(fixture), ack);
    Require(ack.failure == Failure::proposal_changed_before_submit &&
            fixture.captures == 2 && fixture.submits == 0);
  }

  auto fixture = BaseFixture();
  ck3::CharacterInteractionProposalActionStateV1 state{};
  const auto ack = ExecuteAvailable(fixture, state);
  game::CharacterInteractionProposalActionAckV1 duplicate{};
  Require(ck3::ExecuteCharacterInteractionProposalActionCoreV1(
              Environment(), Access(fixture), state, Request(fixture),
              duplicate) == AckStatus::rejected_before_submit);
  Require(duplicate.failure == Failure::submission_already_in_flight);
  Require(fixture.submits == 1 &&
          state.acknowledged_submission_count == 1);

  auto failed_submit = BaseFixture();
  failed_submit.submit_acknowledged = false;
  state = {};
  game::CharacterInteractionProposalActionAckV1 failed_ack{};
  ck3::ExecuteCharacterInteractionProposalActionCoreV1(
      Environment(), Access(failed_submit), state, Request(failed_submit),
      failed_ack);
  Require(failed_ack.failure == Failure::submit_not_acknowledged &&
          failed_submit.submits == 1 && !state.submission_in_flight &&
          state.acknowledged_submission_count == 0);
  (void)ack;
}

void TestAckRemainsPendingUntilSpecificReadback() {
  auto fixture = BaseFixture("invite_to_court_interaction");
  ck3::CharacterInteractionProposalActionStateV1 state{};
  const auto ack = ExecuteAvailable(fixture, state);
  Require(ack.status == AckStatus::submitted_verification_pending &&
          ack.verification_pending);

  game::CharacterInteractionProposalReceiptV1 receipt{};
  game::CharacterInteractionProposalPostconditionObservationV1 missing{};
  Require(ck3::VerifyCharacterInteractionProposalReceiptV1(
              state, ack, missing, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "new_paused_observation_unavailable" &&
          !receipt.interaction_specific_postcondition_verified &&
          state.submission_in_flight);

  auto pending = AppliedPost(ack);
  pending.recipient_court_owner_character_id = -1;
  pending.invite_cooldown_present = false;
  pending.matching_pending_proposal = true;
  Require(ck3::VerifyCharacterInteractionProposalReceiptV1(
              state, ack, pending, receipt) == ReceiptStatus::response_pending);
  Require(!receipt.interaction_specific_postcondition_verified &&
          state.submission_in_flight);

  auto applied = AppliedPost(ack);
  Require(ck3::VerifyCharacterInteractionProposalReceiptV1(
              state, ack, applied, receipt) == ReceiptStatus::applied);
  Require(receipt.interaction_specific_postcondition_verified &&
          !state.submission_in_flight);

  auto mismatch_fixture = BaseFixture("gift_interaction");
  state = {};
  const auto mismatch_ack = ExecuteAvailable(mismatch_fixture, state);
  auto wrong_specific_state = AppliedPost(mismatch_ack);
  wrong_specific_state.recipient_has_gift_opinion_toward_actor = false;
  Require(ck3::VerifyCharacterInteractionProposalReceiptV1(
              state, mismatch_ack, wrong_specific_state, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason ==
              "interaction_specific_postcondition_failed" &&
          !state.submission_in_flight);
}

} // namespace

int main() {
  try {
    Require(kAllowlist.size() == 11);
    Require(ck3::kCharacterInteractionProposalActionCoreExecutableSha256V1
                .size() == 64);
    TestAllElevenAllowlistedReceipts();
    TestPreviewAndAllowlistGates();
    TestCanSendAcceptanceAndBudgetGates();
    TestEnvironmentAndSubmitSeamGates();
    TestDoubleCaptureAndSingleSubmit();
    TestAckRemainsPendingUntilSpecificReadback();
    std::cout << "character interaction proposal action core passed\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
