#include "xar_bridge/current_timeline_blocker_context_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>

namespace xar::ck3_11906 {
namespace {

bool IsExecutingExactMailboxSlot(
    const CurrentTimelineBlockerContextMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.request.snapshot_revision == 0 || !query.request.paused ||
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
         mailbox.executor ==
             &ExecuteCurrentTimelineBlockerContextMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<CurrentTimelineBlockerContextMailboxContextV1 *>(
                 &query);
}

void MakeInternalUnavailable(
    CurrentTimelineBlockerContextMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp, std::string_view reason) {
  query.result = {};
  query.result.status = game::CurrentTimelineBlockerStatusV1::unavailable;
  query.result.snapshot_revision = query.request.snapshot_revision;
  query.result.date_raw = stamp.date_raw;
  query.result.unavailable_reason.assign(reason);
  query.result.blocks_simulation.available = false;
  query.result.blocks_simulation.unavailable_reason.assign(reason);
  query.result.can_continue.available = false;
  query.result.can_continue.unavailable_reason.assign(reason);
  query.read_result =
      game::ReadCurrentTimelineBlockerContextResultV1::unavailable;
  query.completion =
      CurrentTimelineBlockerContextMailboxCompletionV1::completed;
}

bool ValidTypedResult(
    const CurrentTimelineBlockerContextMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  const auto &result = query.result;
  if (result.snapshot_revision != query.request.snapshot_revision ||
      result.date_raw != stamp.date_raw) {
    return false;
  }
  if (result.status == game::CurrentTimelineBlockerStatusV1::unavailable) {
    return query.read_result ==
               game::ReadCurrentTimelineBlockerContextResultV1::unavailable &&
           !result.unavailable_reason.empty() &&
           !result.blocks_simulation.available &&
           !result.blocks_simulation.unavailable_reason.empty() &&
           !result.can_continue.available &&
           !result.can_continue.unavailable_reason.empty();
  }
  if (query.read_result !=
          game::ReadCurrentTimelineBlockerContextResultV1::available ||
      !result.unavailable_reason.empty() ||
      result.blocks_simulation.available ||
      result.blocks_simulation.unavailable_reason.empty() ||
      result.evidence.source_kind.empty() || result.evidence.source_path.empty()) {
    return false;
  }
  if (result.identity == game::CurrentTimelineBlockerIdentityV1::none) {
    return !result.can_continue.available &&
           !result.can_continue.unavailable_reason.empty();
  }
  return result.can_continue.available &&
         result.can_continue.unavailable_reason.empty();
}

} // namespace

bool ExecuteCurrentTimelineBlockerContextMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<CurrentTimelineBlockerContextMailboxContextV1 *>(
      opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          CurrentTimelineBlockerContextMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion = CurrentTimelineBlockerContextMailboxCompletionV1::
          infrastructure_rejected;
    }
    return false;
  }
  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;
    game::Snapshot snapshot{};
    if (!ReadSnapshot(query->bindings, snapshot) ||
        snapshot != query->expected_snapshot || !snapshot.paused ||
        snapshot.date_raw != stamp.date_raw ||
        query->request.date_raw != stamp.date_raw) {
      MakeInternalUnavailable(*query, stamp, "state_changed");
      query->completion =
          CurrentTimelineBlockerContextMailboxCompletionV1::frame_changed;
      return true;
    }
    query->read_result = ReadCurrentTimelineBlockerContextNativeV1(
        query->environment, query->access, query->request, query->result);
    if (ValidTypedResult(*query, stamp)) {
      query->completion =
          CurrentTimelineBlockerContextMailboxCompletionV1::completed;
    } else {
      MakeInternalUnavailable(*query, stamp, "internal_error");
    }
    return true;
  } catch (...) {
    try {
      MakeInternalUnavailable(*query, stamp, "internal_error");
      return true;
    } catch (...) {
      query->completion = CurrentTimelineBlockerContextMailboxCompletionV1::
          infrastructure_rejected;
      return false;
    }
  }
}

std::string_view CurrentTimelineBlockerContextFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    CurrentTimelineBlockerContextMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (!completion_snapshot_stable ||
      completion ==
          CurrentTimelineBlockerContextMailboxCompletionV1::frame_changed) {
    return "timeline-blocker context crossed its paused revision";
  }
  switch (wait) {
  case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
    return "application-main timeline-blocker query timed out";
  case MainThreadQueryWaitResultV1::timeout_executor_already_running:
    return "application-main timeline-blocker executor is still running";
  case MainThreadQueryWaitResultV1::completed:
    break;
  default:
    return "application-main timeline-blocker query failed";
  }
  return "application-main timeline-blocker executor rejected query";
}

} // namespace xar::ck3_11906
