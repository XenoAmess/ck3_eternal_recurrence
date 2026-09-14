#include "xar_bridge/war_entry_assessments_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>
#include <cstddef>

namespace xar::ck3_11906 {
namespace {

struct WarEntryMailboxAccessProxyV1 {
  WarEntryAssessmentMailboxContextV1 *query = nullptr;
  const MainThreadExecutionStampV1 *stamp = nullptr;
};

bool IsExecutingExactMailboxSlot(
    const WarEntryAssessmentMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
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
         mailbox.executor == &ExecuteWarEntryAssessmentMailboxQueryV1 &&
         mailbox.executor_context ==
             const_cast<WarEntryAssessmentMailboxContextV1 *>(&query);
}

bool ProxyIsMainThread(void *opaque) noexcept {
  const auto *const proxy =
      static_cast<const WarEntryMailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp);
}

bool ProxyCaptureFrame(
    void *opaque, game::WarEntryAssessmentFrameV1 &output) noexcept {
  const auto *const proxy =
      static_cast<const WarEntryMailboxAccessProxyV1 *>(opaque);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      proxy->query->access.capture_frame == nullptr ||
      !IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) ||
      !proxy->query->access.capture_frame(proxy->query->access.context,
                                          output)) {
    return false;
  }
  return output.paused && output.date_raw == proxy->stamp->date_raw;
}

bool ProxyReadMemory(void *opaque, const void *address, void *output,
                     std::size_t size) noexcept {
  const auto *const proxy =
      static_cast<const WarEntryMailboxAccessProxyV1 *>(opaque);
  return proxy != nullptr && proxy->query != nullptr &&
         proxy->stamp != nullptr &&
         proxy->query->access.read_memory != nullptr &&
         IsExecutingExactMailboxSlot(*proxy->query, *proxy->stamp) &&
         proxy->query->access.read_memory(proxy->query->access.context,
                                          address, output, size);
}

void MarkQueryUnavailable(WarEntryAssessmentMailboxContextV1 &query,
                          std::string_view fallback_stage) {
  query.completion =
      WarEntryAssessmentMailboxCompletionV1::query_unavailable;
  if (query.result.available) {
    query.result = {};
  }
  if (query.result.unavailable_stage.empty()) {
    query.result.unavailable_stage.assign(fallback_stage);
  }
}

} // namespace

bool ExecuteWarEntryAssessmentMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<WarEntryAssessmentMailboxContextV1 *>(opaque_context);
  if (query == nullptr ||
      !IsExecutingExactMailboxSlot(*query, stamp) ||
      query->completion !=
          WarEntryAssessmentMailboxCompletionV1::not_executed ||
      query->executor_invocations != 0) {
    if (query != nullptr) {
      query->completion =
          WarEntryAssessmentMailboxCompletionV1::infrastructure_rejected;
    }
    return false;
  }

  try {
    ++query->executor_invocations;
    query->execution_stamp = stamp;

    WarEntryMailboxAccessProxyV1 proxy{query, &stamp};
    WarEntryAssessmentAccessV1 access{};
    access.context = &proxy;
    access.capture_frame = &ProxyCaptureFrame;
    access.is_main_thread = &ProxyIsMainThread;
    access.read_memory = query->access.read_memory == nullptr
                             ? nullptr
                             : &ProxyReadMemory;

    // The reader constructs its zeroed native State16 on this proven
    // application-main execution boundary; no actor AI-context pointer is
    // captured or carried through the worker-owned mailbox context.
    query->read_result = ReadWarEntryAssessmentsV1(
        query->environment, access, query->request, query->result);
    if (query->read_result ==
            game::ReadWarEntryAssessmentsV1Result::available &&
        query->result.available && query->result.readiness.ready) {
      query->completion = WarEntryAssessmentMailboxCompletionV1::available;
      return true;
    }

    MarkQueryUnavailable(*query, "mailbox_reader_unavailable");
    return true;
  } catch (...) {
    try {
      query->read_result = game::ReadWarEntryAssessmentsV1Result::unavailable;
      query->result = {};
      MarkQueryUnavailable(*query, "mailbox_adapter_exception");
      return true;
    } catch (...) {
      query->completion =
          WarEntryAssessmentMailboxCompletionV1::infrastructure_rejected;
      return false;
    }
  }
}

std::string WarEntryAssessmentFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    WarEntryAssessmentMailboxCompletionV1 completion,
    std::string_view unavailable_stage) {
  if (wait != MainThreadQueryWaitResultV1::completed) {
    switch (wait) {
    case MainThreadQueryWaitResultV1::executor_failed:
      return "application-main war-entry executor failed";
    case MainThreadQueryWaitResultV1::infrastructure_failed:
      return "application-main war-entry boundary drifted";
    case MainThreadQueryWaitResultV1::cancelled:
      return "application-main war-entry query was cancelled";
    case MainThreadQueryWaitResultV1::timeout_cancelled_before_execution:
      return "application-main war-entry query timed out before execution";
    case MainThreadQueryWaitResultV1::timeout_executor_already_running:
      return "application-main war-entry executor is still running";
    case MainThreadQueryWaitResultV1::ticket_mismatch:
      return "application-main war-entry ticket mismatch";
    case MainThreadQueryWaitResultV1::completed:
      break;
    }
  }
  if (completion == WarEntryAssessmentMailboxCompletionV1::query_unavailable) {
    std::string error = "application-main war-entry query failed:";
    error.append(unavailable_stage.empty() ? "mailbox_reader_unavailable"
                                           : unavailable_stage);
    return error;
  }
  if (completion == WarEntryAssessmentMailboxCompletionV1::available) {
    return "application-main war-entry result is inconsistent";
  }
  if (completion ==
      WarEntryAssessmentMailboxCompletionV1::infrastructure_rejected) {
    return "application-main war-entry executor rejected request";
  }
  return "application-main war-entry executor produced no completion";
}

} // namespace xar::ck3_11906
