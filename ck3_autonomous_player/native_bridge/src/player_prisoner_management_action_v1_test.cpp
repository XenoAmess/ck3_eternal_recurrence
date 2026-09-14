#include "xar_bridge/player_prisoner_management_action_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string_view>

namespace {

namespace bridge = xar::bridge;

using AckStatus = bridge::PlayerPrisonerActionAckStatusV1;
using Action = bridge::PlayerPrisonerActionKindV1;
using Failure = bridge::PlayerPrisonerActionFailureClassV1;
using ReceiptStatus = bridge::PlayerPrisonerActionReceiptStatusV1;

constexpr std::int32_t kPlayer = 0x11000011;
constexpr std::int32_t kPrisoner = 0x1200002A;
constexpr std::int32_t kPrisonerOtherGeneration = 0x1300002A;
constexpr std::int32_t kPayer = 0x14000031;
constexpr std::uint64_t kPublicRevision = 710;
constexpr std::uint64_t kNativeRevision = 9001;
constexpr std::uint64_t kProofEpoch = 51;
constexpr std::int64_t kDate = 54'336'000;

bridge::PlayerPrisonerOpaqueFinalBoolV1 Opaque(bool value) {
  return {bridge::PlayerPrisonerFieldStateV1::known, value,
          bridge::PlayerPrisonerUnknownReasonV1::none,
          bridge::PlayerPrisonerNativeReasonSourceV1::native_opaque_final};
}

bridge::PlayerPrisonerInteractionPreviewV1 Preview(bool can_send = true) {
  bridge::PlayerPrisonerInteractionPreviewV1 output{};
  output.state = bridge::PlayerPrisonerFieldStateV1::known;
  output.unknown_reason = bridge::PlayerPrisonerUnknownReasonV1::none;
  output.source =
      bridge::PlayerPrisonerPreviewSourceV1::
          native_finalized_character_interaction;
  output.shown = true;
  output.valid = true;
  output.can_send = can_send;
  output.failure_reason_key = bridge::PlayerPrisonerUnknownKeyV1(
      bridge::PlayerPrisonerUnknownReasonV1::not_applicable);
  return output;
}

bridge::PlayerPrisonerManagementSnapshotV1 Snapshot() {
  bridge::PlayerPrisonerManagementSnapshotV1 output{};
  output.status = bridge::PlayerPrisonerSnapshotStatusV1::available;
  output.unavailable_reason = bridge::PlayerPrisonerSnapshotFailureV1::none;
  output.public_revision = kPublicRevision;
  output.native_revision = kNativeRevision;
  output.proof_epoch = kProofEpoch;
  output.date_raw = kDate;
  output.played_character_id = kPlayer;
  output.total_prisoner_count = 1;
  output.prisoner_count = 1;
  auto &row = output.prisoners[0];
  row.prisoner_character_id = kPrisoner;
  row.jailer_character_id = kPlayer;
  row.prisoner_identity_round_trip = true;
  row.prisoner_alive = true;
  row.custody = bridge::PlayerPrisonerCustodyKindV1::dungeon;
  row.time_imprisoned_days = 180;
  row.has_imprisonment_reason = Opaque(true);
  row.has_banish_reason = Opaque(false);
  row.has_execute_reason = Opaque(false);
  row.ransom.interaction = Preview();
  row.ransom.payer_character_id = kPayer;
  row.ransom.selected_option_key =
      bridge::PlayerPrisonerKnownKeyV1("gold");
  row.ransom.resource_key =
      bridge::PlayerPrisonerKnownKeyV1("gold");
  row.ransom.resource_amount_raw = 100 *
      bridge::kPlayerPrisonerFixedPointOneV1;
  row.ransom.acceptance_required = true;
  row.ransom.would_accept_now = Opaque(true);
  row.release_unconditional = Preview();
  row.execute = Preview();
  row.move_to_dungeon = Preview();
  row.move_to_house_arrest = Preview();
  row.torture = Preview();
  output.religious_details_exposed = false;
  output.readiness = {true, true, true, true, true, true, true, true};
  return output;
}

struct Fixture {
  bridge::PlayerPrisonerManagementSnapshotV1 pre = Snapshot();
  bridge::PlayerPrisonerManagementSnapshotV1 post = Snapshot();
  std::uint32_t captures = 0;
  std::uint32_t submits = 0;
  bool main_thread = true;
  bool capture_result = true;
  bool submit_result = true;
  bool drift_second_precondition = false;
  bridge::PlayerPrisonerActionSubmissionV1 submission{};
};

std::unique_ptr<Fixture> Base() {
  auto fixture = std::make_unique<Fixture>();
  fixture->post.public_revision = kPublicRevision + 1;
  fixture->post.native_revision = kNativeRevision + 1;
  fixture->post.proof_epoch = kProofEpoch + 1;
  fixture->post.total_prisoner_count = 0;
  fixture->post.prisoner_count = 0;
  fixture->post.readiness = {};
  fixture->post.readiness.collection_ready = true;
  fixture->post.readiness.same_frame_ready = true;
  return fixture;
}

bool Capture(void *context,
             bridge::PlayerPrisonerManagementSnapshotV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.captures;
  if (!fixture.capture_result) return false;
  output = fixture.captures <= 2 ? fixture.pre : fixture.post;
  if (fixture.drift_second_precondition && fixture.captures == 2) {
    ++output.native_revision;
  }
  return true;
}

bool IsMain(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool Submit(
    void *context,
    const bridge::PlayerPrisonerActionSubmissionV1 &submission) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.submits;
  fixture.submission = submission;
  return fixture.submit_result;
}

bridge::PlayerPrisonerActionEnvironmentV1 Environment() {
  return {true, bridge::kPlayerPrisonerManagementActionV1ExecutableSha256,
          0, false, true};
}

bridge::PlayerPrisonerActionAccessV1 Access(Fixture &fixture) {
  return {&fixture, &Capture, &IsMain, &Submit};
}

bridge::PlayerPrisonerActionRequestV1 Request(Action action) {
  return {"prisoner-action-fixture-1", action, kPlayer, kPrisoner,
          kPublicRevision, kNativeRevision, kProofEpoch, kDate};
}

bridge::PlayerPrisonerActionAckV1 Execute(Fixture &fixture, Action action) {
  bridge::PlayerPrisonerActionAckV1 ack{};
  bridge::ExecutePlayerPrisonerActionV1(
      Environment(), Access(fixture), Request(action), ack);
  return ack;
}

void RequirePending(const bridge::PlayerPrisonerActionAckV1 &ack,
                    Fixture &fixture, Action action) {
  assert(ack.status == AckStatus::submitted_verification_pending);
  assert(ack.verification_pending);
  assert(ack.action == action);
  assert(ack.player_character_id == kPlayer);
  assert(ack.prisoner_character_id == kPrisoner);
  assert(ack.pre_public_revision == kPublicRevision);
  assert(ack.pre_native_revision == kNativeRevision);
  assert(ack.pre_proof_epoch == kProofEpoch);
  assert(ack.pre_date_raw == kDate);
  assert(fixture.captures == 2);
  assert(fixture.submits == 1);
  assert(fixture.submission.action == action);
  assert(fixture.submission.player_character_id == kPlayer);
  assert(fixture.submission.prisoner_character_id == kPrisoner);
}

void TestAllThreeActionsSubmitOnceAndRemainPending() {
  {
    auto fixture = Base();
    const auto ack = Execute(*fixture, Action::ransom);
    RequirePending(ack, *fixture, Action::ransom);
    assert(fixture->submission.payer_character_id == kPayer);
    assert(bridge::PlayerPrisonerKeyViewV1(
               fixture->submission.selected_option_key.value) == "gold");
    assert(fixture->submission.resource_amount_raw ==
           100 * bridge::kPlayerPrisonerFixedPointOneV1);
  }
  {
    auto fixture = Base();
    const auto ack = Execute(*fixture, Action::release_unconditional);
    RequirePending(ack, *fixture, Action::release_unconditional);
    assert(fixture->submission.payer_character_id == -1);
  }
  {
    auto fixture = Base();
    // The opaque engine-final reason is false, but the exact finalized Can
    // Send result is true. The core does not reconstruct religious logic.
    const auto ack = Execute(*fixture, Action::punish_execute);
    RequirePending(ack, *fixture, Action::punish_execute);
    assert(ack.native_execute_reason_known);
    assert(!ack.native_execute_reason);
  }
}

void TestDoubleSampleAndFullGenerationBinding() {
  {
    auto fixture = Base();
    fixture->drift_second_precondition = true;
    const auto ack = Execute(*fixture, Action::ransom);
    assert(ack.status == AckStatus::rejected_before_submit);
    assert(ack.failure_class == Failure::snapshot_binding);
    assert(fixture->captures == 2 && fixture->submits == 0);
  }
  {
    auto fixture = Base();
    fixture->pre.prisoners[0].prisoner_character_id =
        kPrisonerOtherGeneration;
    const auto ack = Execute(*fixture, Action::release_unconditional);
    assert(ack.status == AckStatus::rejected_before_submit);
    assert(ack.failure_class == Failure::prisoner_binding);
    assert(fixture->submits == 0);
  }
  {
    auto fixture = Base();
    auto request = Request(Action::ransom);
    ++request.expected_proof_epoch;
    bridge::PlayerPrisonerActionAckV1 ack{};
    assert(bridge::ExecutePlayerPrisonerActionV1(
               Environment(), Access(*fixture), request, ack) ==
           AckStatus::rejected_before_submit);
    assert(ack.failure_class == Failure::snapshot_binding);
    assert(fixture->submits == 0);
  }
}

void TestNativeFinalGatesRejectBeforeSubmit() {
  {
    auto fixture = Base();
    fixture->pre.prisoners[0].ransom.would_accept_now = Opaque(false);
    const auto ack = Execute(*fixture, Action::ransom);
    assert(ack.failure_class == Failure::final_legality);
    assert(fixture->submits == 0);
  }
  {
    auto fixture = Base();
    fixture->pre.prisoners[0].release_unconditional.can_send = false;
    const auto ack = Execute(*fixture, Action::release_unconditional);
    assert(ack.failure_class == Failure::final_legality);
    assert(fixture->submits == 0);
  }
  {
    auto fixture = Base();
    fixture->pre.prisoners[0].execute.can_send = false;
    const auto ack = Execute(*fixture, Action::punish_execute);
    assert(ack.failure_class == Failure::final_legality);
    assert(fixture->submits == 0);
  }
}

void TestSubmitFailureIsNeverRetried() {
  auto fixture = Base();
  fixture->submit_result = false;
  const auto ack = Execute(*fixture, Action::ransom);
  assert(ack.status == AckStatus::rejected_before_submit);
  assert(ack.failure_class == Failure::native_command_dispatch);
  assert(fixture->submits == 1);
  bridge::PlayerPrisonerActionReceiptV1 receipt{};
  assert(bridge::VerifyPlayerPrisonerActionReceiptV1(
             Access(*fixture), ack, receipt) == ReceiptStatus::rejected);
}

void TestFreshReceiptMustProveTargetAbsent() {
  {
    auto fixture = Base();
    const auto ack = Execute(*fixture, Action::release_unconditional);
    bridge::PlayerPrisonerActionReceiptV1 receipt{};
    assert(bridge::VerifyPlayerPrisonerActionReceiptV1(
               Access(*fixture), ack, receipt) == ReceiptStatus::applied);
    assert(receipt.complete_prisoner_collection_reread);
    assert(!receipt.target_still_imprisoned);
    assert(receipt.target_state_changed);
    assert(receipt.postcondition_verified);
  }
  {
    auto fixture = Base();
    fixture->post.total_prisoner_count = 1;
    fixture->post.prisoner_count = 1;
    const auto ack = Execute(*fixture, Action::punish_execute);
    bridge::PlayerPrisonerActionReceiptV1 receipt{};
    assert(bridge::VerifyPlayerPrisonerActionReceiptV1(
               Access(*fixture), ack, receipt) ==
           ReceiptStatus::postcondition_failed);
    assert(receipt.target_still_imprisoned);
    assert(!receipt.postcondition_verified);
  }
  {
    auto fixture = Base();
    fixture->post.proof_epoch = kProofEpoch;
    const auto ack = Execute(*fixture, Action::ransom);
    bridge::PlayerPrisonerActionReceiptV1 receipt{};
    assert(bridge::VerifyPlayerPrisonerActionReceiptV1(
               Access(*fixture), ack, receipt) ==
           ReceiptStatus::postcondition_failed);
    assert(receipt.reason == "no_fresh_paused_receipt");
  }
}

void TestEnvironmentAndThreadFailClosed() {
  {
    auto fixture = Base();
    auto environment = bridge::BindPlayerPrisonerActionEnvironmentV1(
        0x140000000ULL, true,
        bridge::kPlayerPrisonerManagementActionV1ExecutableSha256);
    bridge::PlayerPrisonerActionAckV1 ack{};
    assert(bridge::ExecutePlayerPrisonerActionV1(
               environment, Access(*fixture), Request(Action::ransom), ack) ==
           AckStatus::rejected_before_submit);
    assert(ack.failure_class == Failure::exact_build_binding);
  }
  {
    auto fixture = Base();
    fixture->main_thread = false;
    const auto ack = Execute(*fixture, Action::ransom);
    assert(ack.failure_class == Failure::snapshot_binding);
    assert(fixture->captures == 0 && fixture->submits == 0);
  }
  assert(bridge::PlayerPrisonerActionFailureClassNameV1(
             Failure::final_legality) == "final_legality");
}

} // namespace

int main() {
  TestAllThreeActionsSubmitOnceAndRemainPending();
  TestDoubleSampleAndFullGenerationBinding();
  TestNativeFinalGatesRejectBeforeSubmit();
  TestSubmitFailureIsNeverRetried();
  TestFreshReceiptMustProveTargetAbsent();
  TestEnvironmentAndThreadFailClosed();
  std::cout << "player prisoner management action v1: 6/6 green\n";
  return 0;
}
