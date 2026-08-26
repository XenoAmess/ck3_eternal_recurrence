#include "xar_bridge/event_window_context_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>

namespace xar::ck3_11906 {
namespace {

bool IsExecutingExactMailboxSlot(
    const EventWindowContextMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      query.expected_snapshot_revision == 0 ||
      query.expected_event_instance_id <= 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id) {
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
         mailbox.executor == &ExecuteEventWindowContextMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<EventWindowContextMailboxContextV1 *>(&query);
}

void MakeInternalUnavailable(EventWindowContextMailboxContextV1 &query,
                             const MainThreadExecutionStampV1 &stamp) {
  query.result = {};
  query.result.status = game::EventWindowContextStatusV1::unavailable;
  query.result.snapshot_revision = query.expected_snapshot_revision;
  query.result.date_raw = stamp.date_raw;
  query.result.current_event_instance_id =
      query.expected_event_instance_id;
  query.result.unavailable_reason = "internal_error";
  query.read_result = game::ReadEventWindowContextResultV1::unavailable;
  query.completion = EventWindowContextMailboxCompletionV1::completed;
}

} // namespace

bool ExecuteEventWindowContextMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query =
      static_cast<EventWindowContextMailboxContextV1 *>(opaque_context);
  if (query == nullptr || !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          EventWindowContextMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          EventWindowContextMailboxCompletionV1::infrastructure_rejected;
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
        !snapshot.has_active_event ||
        snapshot.active_event_instance_id !=
            query->expected_event_instance_id) {
      MakeInternalUnavailable(*query, stamp);
      query->result.unavailable_reason = "state_changed";
      return true;
    }
    query->read_result = ReadEventWindowContextV1(
        query->bindings, query->expected_snapshot_revision,
        query->expected_event_instance_id, query->result);
    const bool typed_available =
        query->read_result == game::ReadEventWindowContextResultV1::available &&
        query->result.status == game::EventWindowContextStatusV1::available &&
        query->result.window_match_count == 1 &&
        query->result.option_presentation_ready &&
        !query->result.effect_preview_ready &&
        !query->result.semantic_decision_ready;
    const bool typed_unavailable =
        query->read_result ==
            game::ReadEventWindowContextResultV1::unavailable &&
        query->result.status ==
            game::EventWindowContextStatusV1::unavailable &&
        !query->result.unavailable_reason.empty() &&
        !query->result.option_presentation_ready &&
        !query->result.effect_preview_ready &&
        !query->result.semantic_decision_ready;
    if ((typed_available || typed_unavailable) &&
        query->result.snapshot_revision ==
            query->expected_snapshot_revision &&
        query->result.current_event_instance_id ==
            query->expected_event_instance_id &&
        query->result.date_raw == stamp.date_raw) {
      query->completion = EventWindowContextMailboxCompletionV1::completed;
      return true;
    }
    MakeInternalUnavailable(*query, stamp);
    return true;
  } catch (...) {
    try {
      MakeInternalUnavailable(*query, stamp);
      return true;
    } catch (...) {
      query->completion =
          EventWindowContextMailboxCompletionV1::infrastructure_rejected;
      return false;
    }
  }
}

std::string_view EventWindowContextFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    EventWindowContextMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main event-window executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main event-window boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main event-window query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main event-window query timed out";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main event-window executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main event-window ticket mismatch";
    case MainThreadQueryWaitResultV1::completed:
      break;
    }
  }
  if (completion == EventWindowContextMailboxCompletionV1::completed) {
    return completion_snapshot_stable
               ? "application-main event-window result is inconsistent"
               : "event-window completion snapshot changed";
  }
  return "application-main event-window executor was rejected";
}

} // namespace xar::ck3_11906
