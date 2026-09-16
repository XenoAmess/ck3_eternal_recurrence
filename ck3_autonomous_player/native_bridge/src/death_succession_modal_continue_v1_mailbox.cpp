#include "xar_bridge/death_succession_modal_continue_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>

namespace xar::ck3_11906 {
namespace {

bool IsExecutingExactMailboxSlot(
    const DeathSuccessionModalContinueMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.request.expected_snapshot_revision == 0 ||
      query.request.expected_played_character_id <= 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecuteDeathSuccessionModalContinueMailboxV1 &&
         mailbox.executor_context ==
             const_cast<DeathSuccessionModalContinueMailboxContextV1 *>(&query);
}

void SetUnavailable(DeathSuccessionModalContinueMailboxContextV1 &query,
                    std::string_view reason) {
  query.receipt = {};
  query.receipt.status =
      game::DeathSuccessionModalContinueStatusV1::unavailable;
  query.receipt.snapshot_revision =
      query.request.expected_snapshot_revision;
  query.receipt.date_raw = query.request.expected_date_raw;
  query.receipt.played_character_id =
      query.request.expected_played_character_id;
  query.receipt.unavailable_reason.assign(reason);
}

} // namespace

bool ExecuteDeathSuccessionModalContinueMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<DeathSuccessionModalContinueMailboxContextV1 *>(
      opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          DeathSuccessionModalContinueMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion = DeathSuccessionModalContinueMailboxCompletionV1::
          infrastructure_rejected;
      SetUnavailable(*query, "owning_thread_boundary_rejected");
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    game::Snapshot snapshot{};
    if (!ReadSnapshot(query->bindings, snapshot) ||
        snapshot != query->expected_snapshot || !snapshot.paused ||
        !snapshot.map_ready || !snapshot.has_played_character ||
        !snapshot.played_character_alive ||
        snapshot.played_character_id !=
            query->request.expected_played_character_id ||
        snapshot.date_raw != query->request.expected_date_raw ||
        snapshot.date_raw != stamp.date_raw) {
      SetUnavailable(*query, "state_changed");
      query->completion =
          DeathSuccessionModalContinueMailboxCompletionV1::frame_changed;
      return true;
    }

    CurrentTimelineBlockerReadRequestV1 read_request{};
    read_request.snapshot_revision =
        query->request.expected_snapshot_revision;
    read_request.date_raw = query->request.expected_date_raw;
    read_request.played_character_id =
        query->request.expected_played_character_id;
    read_request.paused = true;
    game::CurrentTimelineBlockerContextV1 timeline{};
    if (ReadCurrentTimelineBlockerContextNativeV1(
            query->bindings, query->environment, query->access, read_request,
            timeline) !=
        game::ReadCurrentTimelineBlockerContextResultV1::available) {
      SetUnavailable(*query, timeline.unavailable_reason.empty()
                                 ? "timeline_query_unavailable"
                                 : timeline.unavailable_reason);
      query->completion =
          DeathSuccessionModalContinueMailboxCompletionV1::completed;
      return true;
    }
    (void)ExecuteDeathSuccessionModalContinueNativeV1(
        query->environment, query->request, timeline, query->receipt);
    query->completion =
        DeathSuccessionModalContinueMailboxCompletionV1::completed;
    return true;
  } catch (...) {
    SetUnavailable(*query, "internal_error");
    query->completion =
        DeathSuccessionModalContinueMailboxCompletionV1::
            infrastructure_rejected;
    return false;
  }
}

std::string_view DeathSuccessionModalContinueFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    DeathSuccessionModalContinueMailboxCompletionV1 completion,
    std::string_view typed_reason) noexcept {
  if (!typed_reason.empty()) return typed_reason;
  if (wait ==
      MainThreadQueryWaitResultV1::timeout_cancelled_before_execution)
    return "owning_thread_executor_timeout_before_execution";
  if (wait == MainThreadQueryWaitResultV1::executor_failed ||
      completion == DeathSuccessionModalContinueMailboxCompletionV1::
                        infrastructure_rejected)
    return "owning_thread_executor_failed";
  if (completion ==
      DeathSuccessionModalContinueMailboxCompletionV1::frame_changed)
    return "state_changed";
  return "death_succession_modal_continue_unavailable";
}

} // namespace xar::ck3_11906
