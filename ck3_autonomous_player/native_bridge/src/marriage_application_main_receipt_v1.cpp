#include "xar_bridge/marriage_application_main_receipt_v1.hpp"

#include <charconv>
#include <cstring>

namespace xar::bridge {
namespace {

void SetFailure(MarriageApplicationMainReceiptStateV1 &state,
                MarriageApplicationMainReceiptFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

bool CanonicalSnapshotId(
    std::uint64_t revision,
    std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1> &output)
    noexcept {
  output = {};
  constexpr char prefix[] = "native:";
  constexpr auto prefix_size = sizeof(prefix) - 1;
  static_assert(prefix_size < kMarriageMatchmakingSnapshotIdCapacityV1);
  std::memcpy(output.data(), prefix, prefix_size);
  const auto converted = std::to_chars(
      output.data() + prefix_size, output.data() + output.size() - 1,
      revision);
  return converted.ec == std::errc{} && converted.ptr != output.data() &&
         converted.ptr < output.data() + output.size();
}

} // namespace

bool ConfigureMarriageApplicationMainReceiptV1(
    MarriageApplicationMainReceiptStateV1 &state,
    MarriageSharedGlueStateV1 &shared_glue,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept {
  if (shared_glue.installed.load(std::memory_order_acquire) == 0 ||
      mailbox.module_base == 0 ||
      shared_glue.binder.environment.module_base != mailbox.module_base) {
    state.shared_glue = nullptr;
    state.mailbox = nullptr;
    SetFailure(state,
               MarriageApplicationMainReceiptFailureV1::invalid_environment);
    return false;
  }
  state.shared_glue = &shared_glue;
  state.mailbox = &mailbox;
  SetFailure(state, MarriageApplicationMainReceiptFailureV1::none);
  return true;
}

bool PublishMarriageApplicationMainReceiptV1(
    MarriageApplicationMainReceiptStateV1 &state,
    const xar::ck3_11906::MainThreadExecutionStampV1 &execution_stamp,
    std::uint64_t snapshot_revision) noexcept {
  auto fail = [&state](MarriageApplicationMainReceiptFailureV1 failure) {
    SetFailure(state, failure);
    return false;
  };
  if (state.shared_glue == nullptr || state.mailbox == nullptr ||
      state.shared_glue->installed.load(std::memory_order_acquire) == 0) {
    return fail(
        MarriageApplicationMainReceiptFailureV1::shared_glue_unavailable);
  }
  auto &mailbox = *state.mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing) {
    return fail(
        MarriageApplicationMainReceiptFailureV1::mailbox_not_executing);
  }
  const auto current_thread_id = GetCurrentThreadId();
  const auto owner_thread_id =
      mailbox.owner_thread_id.load(std::memory_order_acquire);
  if (!mailbox.observed_stamp_read_success.load(std::memory_order_acquire) ||
      current_thread_id == 0 || current_thread_id != owner_thread_id ||
      current_thread_id != execution_stamp.thread_id ||
      mailbox.observed_current_thread_id.load(std::memory_order_acquire) !=
          execution_stamp.thread_id ||
      mailbox.observed_tls_initialized.load(std::memory_order_acquire) != 1 ||
      mailbox.observed_tls_main_thread_marker.load(std::memory_order_acquire) !=
          1 ||
      execution_stamp.tls_initialized != 1 ||
      execution_stamp.tls_main_thread_marker != 1 ||
      execution_stamp.tls_context == 0 ||
      mailbox.observed_tls_context.load(std::memory_order_acquire) !=
          execution_stamp.tls_context ||
      mailbox.executor_started_pump_epoch.load(std::memory_order_acquire) !=
          execution_stamp.pump_epoch ||
      mailbox.pump_epochs.load(std::memory_order_acquire) !=
          execution_stamp.pump_epoch) {
    return fail(MarriageApplicationMainReceiptFailureV1::
                    application_main_identity_unproven);
  }
  if (!execution_stamp.paused || execution_stamp.pump_epoch == 0 ||
      execution_stamp.date_raw <= 0 || execution_stamp.jomini_state == 0 ||
      execution_stamp.game_state == 0 ||
      !mailbox.observed_paused.load(std::memory_order_acquire) ||
      mailbox.observed_jomini_state.load(std::memory_order_acquire) !=
          execution_stamp.jomini_state ||
      mailbox.observed_game_state.load(std::memory_order_acquire) !=
          execution_stamp.game_state ||
      mailbox.observed_date_raw.load(std::memory_order_acquire) !=
          execution_stamp.date_raw ||
      mailbox.paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire) <
          xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs) {
    return fail(
        MarriageApplicationMainReceiptFailureV1::paused_frame_unproven);
  }
  if (snapshot_revision == 0) {
    return fail(
        MarriageApplicationMainReceiptFailureV1::revision_unavailable);
  }

  MarriageProposalReceiptFrameV1 frame{};
  frame.available = true;
  frame.paused = true;
  frame.public_revision = snapshot_revision;
  frame.native_revision = snapshot_revision;
  frame.proof_epoch = execution_stamp.pump_epoch;
  frame.date_raw = execution_stamp.date_raw;
  if (!CanonicalSnapshotId(snapshot_revision, frame.snapshot_id)) {
    return fail(
        MarriageApplicationMainReceiptFailureV1::revision_unavailable);
  }
  if (!PublishMarriageSharedReceiptFrameV1(*state.shared_glue, frame)) {
    return fail(
        MarriageApplicationMainReceiptFailureV1::frame_publish_failed);
  }
  SetFailure(state, MarriageApplicationMainReceiptFailureV1::none);
  return true;
}

MarriageApplicationMainReceiptFailureV1
ReadMarriageApplicationMainReceiptFailureV1(
    const MarriageApplicationMainReceiptStateV1 &state) noexcept {
  return static_cast<MarriageApplicationMainReceiptFailureV1>(
      state.last_failure.load(std::memory_order_acquire));
}

} // namespace xar::bridge
