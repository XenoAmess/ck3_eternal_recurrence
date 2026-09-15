#include "xar_bridge/marriage_application_main_receipt_v1.hpp"

#include <cassert>
#include <cstring>
#include <iostream>

namespace bridge = xar::bridge;
namespace native = xar::ck3_11906;

namespace {

native::MainThreadExecutionStampV1 PrepareExecutingMailbox(
    native::MainThreadQueryMailboxV1 &mailbox) {
  const auto thread_id = GetCurrentThreadId();
  native::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 9;
  stamp.thread_id = thread_id;
  stamp.tls_initialized = 1;
  stamp.tls_main_thread_marker = 1;
  stamp.tls_context = 0x1111;
  stamp.jomini_state = 0x2222;
  stamp.game_state = 0x3333;
  stamp.date_raw = 12345;
  stamp.paused = true;

  mailbox.module_base = 1;
  mailbox.state.store(native::MainThreadQueryMailboxStateV1::executing);
  mailbox.owner_thread_id.store(thread_id);
  mailbox.observed_current_thread_id.store(thread_id);
  mailbox.observed_tls_initialized.store(1);
  mailbox.observed_tls_main_thread_marker.store(1);
  mailbox.observed_tls_context.store(stamp.tls_context);
  mailbox.observed_jomini_state.store(stamp.jomini_state);
  mailbox.observed_game_state.store(stamp.game_state);
  mailbox.observed_date_raw.store(stamp.date_raw);
  mailbox.observed_paused.store(true);
  mailbox.observed_stamp_read_success.store(true);
  mailbox.pump_epochs.store(stamp.pump_epoch);
  mailbox.executor_started_pump_epoch.store(stamp.pump_epoch);
  mailbox.paused_owner_verified_pump_epochs.store(
      native::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  return stamp;
}

void PrepareSharedGlue(bridge::MarriageSharedGlueStateV1 &glue) {
  glue.installed.store(1);
  glue.receipt_frames.enabled.store(1);
  glue.binder.environment.module_base = 1;
}

void TestCanonicalApplicationMainReceipt() {
  bridge::MarriageSharedGlueStateV1 glue{};
  PrepareSharedGlue(glue);
  native::MainThreadQueryMailboxV1 mailbox{};
  const auto stamp = PrepareExecutingMailbox(mailbox);
  bridge::MarriageApplicationMainReceiptStateV1 state{};
  assert(bridge::ConfigureMarriageApplicationMainReceiptV1(
      state, glue, mailbox));
  assert(bridge::PublishMarriageApplicationMainReceiptV1(state, stamp, 17));

  bridge::MarriageProposalReceiptFrameV1 frame{};
  assert(bridge::CaptureMarriageSharedReceiptFrameV1(
      &glue.receipt_frames, frame));
  assert(frame.available);
  assert(frame.paused);
  assert(std::strcmp(frame.snapshot_id.data(), "native:17") == 0);
  assert(frame.public_revision == 17);
  assert(frame.native_revision == 17);
  assert(frame.proof_epoch == stamp.pump_epoch);
  assert(frame.date_raw == stamp.date_raw);
  assert(bridge::ReadMarriageApplicationMainReceiptFailureV1(state) ==
         bridge::MarriageApplicationMainReceiptFailureV1::none);
}

void TestOnlyExecutingPausedOwnerCanPublish() {
  bridge::MarriageSharedGlueStateV1 glue{};
  PrepareSharedGlue(glue);
  native::MainThreadQueryMailboxV1 mailbox{};
  auto stamp = PrepareExecutingMailbox(mailbox);
  bridge::MarriageApplicationMainReceiptStateV1 state{};
  assert(bridge::ConfigureMarriageApplicationMainReceiptV1(
      state, glue, mailbox));

  mailbox.state.store(native::MainThreadQueryMailboxStateV1::completed);
  assert(!bridge::PublishMarriageApplicationMainReceiptV1(state, stamp, 18));
  assert(bridge::ReadMarriageApplicationMainReceiptFailureV1(state) ==
         bridge::MarriageApplicationMainReceiptFailureV1::
             mailbox_not_executing);

  mailbox.state.store(native::MainThreadQueryMailboxStateV1::executing);
  mailbox.observed_tls_main_thread_marker.store(0);
  assert(!bridge::PublishMarriageApplicationMainReceiptV1(state, stamp, 18));
  assert(bridge::ReadMarriageApplicationMainReceiptFailureV1(state) ==
         bridge::MarriageApplicationMainReceiptFailureV1::
             application_main_identity_unproven);

  mailbox.observed_tls_main_thread_marker.store(1);
  stamp.paused = false;
  assert(!bridge::PublishMarriageApplicationMainReceiptV1(state, stamp, 18));
  assert(bridge::ReadMarriageApplicationMainReceiptFailureV1(state) ==
         bridge::MarriageApplicationMainReceiptFailureV1::
             paused_frame_unproven);
}

void TestAckCannotCreateReceiptAndTypedFailuresPersist() {
  bridge::MarriageSharedGlueStateV1 glue{};
  PrepareSharedGlue(glue);
  native::MainThreadQueryMailboxV1 mailbox{};
  auto stamp = PrepareExecutingMailbox(mailbox);
  bridge::MarriageApplicationMainReceiptStateV1 state{};
  assert(bridge::ConfigureMarriageApplicationMainReceiptV1(
      state, glue, mailbox));

  // Arm/ACK paths can only invalidate the source. No receipt exists until a
  // later application-main executor explicitly publishes a proven frame.
  bridge::InvalidateMarriageSharedReceiptFrameV1(glue);
  bridge::MarriageProposalReceiptFrameV1 frame{};
  assert(!bridge::CaptureMarriageSharedReceiptFrameV1(
      &glue.receipt_frames, frame));

  assert(!bridge::PublishMarriageApplicationMainReceiptV1(state, stamp, 0));
  assert(bridge::ReadMarriageApplicationMainReceiptFailureV1(state) ==
         bridge::MarriageApplicationMainReceiptFailureV1::
             revision_unavailable);
  assert(!bridge::CaptureMarriageSharedReceiptFrameV1(
      &glue.receipt_frames, frame));

  bridge::MarriageApplicationMainReceiptStateV1 unconfigured{};
  assert(!bridge::PublishMarriageApplicationMainReceiptV1(
      unconfigured, stamp, 1));
  assert(bridge::ReadMarriageApplicationMainReceiptFailureV1(unconfigured) ==
         bridge::MarriageApplicationMainReceiptFailureV1::
             shared_glue_unavailable);
}

void TestMailboxMustShareTheInstalledModule() {
  bridge::MarriageSharedGlueStateV1 glue{};
  PrepareSharedGlue(glue);
  native::MainThreadQueryMailboxV1 mailbox{};
  PrepareExecutingMailbox(mailbox);
  mailbox.module_base = 2;
  bridge::MarriageApplicationMainReceiptStateV1 state{};
  assert(!bridge::ConfigureMarriageApplicationMainReceiptV1(
      state, glue, mailbox));
  assert(bridge::ReadMarriageApplicationMainReceiptFailureV1(state) ==
         bridge::MarriageApplicationMainReceiptFailureV1::
             invalid_environment);
}

} // namespace

int main() {
  TestCanonicalApplicationMainReceipt();
  TestOnlyExecutingPausedOwnerCanPublish();
  TestAckCannotCreateReceiptAndTypedFailuresPersist();
  TestMailboxMustShareTheInstalledModule();
  std::cout << "marriage_application_main_receipt_v1 tests passed\n";
  return 0;
}
