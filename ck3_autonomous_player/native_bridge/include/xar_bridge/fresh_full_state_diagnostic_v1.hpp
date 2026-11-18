#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <optional>
#include <string>

namespace xar::ck3_12002 {
enum class FreshFullSnapshotStageV1 {
  not_started, worker_guard_rejected, submit_rejected, wait_terminal,
  reclaim_rejected, raw_read_unavailable, complete, exception
};

// Worker-thread diagnostic only. No field grants snapshot or action authority.
struct FreshFullSnapshotDiagnosticV1 {
  FreshFullSnapshotStageV1 stage = FreshFullSnapshotStageV1::not_started;
  std::optional<ck3_11906::MainThreadQuerySubmitResultV1> submit_result;
  std::optional<ck3_11906::MainThreadQueryWaitResultV1> wait_result;
  std::optional<ck3_11906::MainThreadQueryReclaimResultV1> reclaim_result;
  std::uint32_t wait_running_timeouts = 0;
  std::uint64_t query_sequence = 0;
  std::uint64_t elapsed_ms = 0;
  ck3_11906::MainThreadQueryQueuedWakeTraceV1 wake{};
  bool fresh_available = false;
};

// Same worker thread, immediately after ReadFreshFullSnapshot12002. A failed
// adapter cast also replaces the diagnostic; an older request is never reused.
FreshFullSnapshotDiagnosticV1 ReadLastFreshFullSnapshotDiagnosticV1() noexcept;
std::string SerializeFreshFullSnapshotDiagnosticV1(
    const FreshFullSnapshotDiagnosticV1 &diagnostic);
} // namespace xar::ck3_12002
