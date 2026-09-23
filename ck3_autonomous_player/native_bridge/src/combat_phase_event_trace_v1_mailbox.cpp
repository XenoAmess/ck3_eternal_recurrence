#include "xar_bridge/combat_phase_event_trace_v1_mailbox.hpp"

#include <windows.h>

#include <atomic>

namespace xar::ck3_11906 {

bool ExecuteCombatPhaseEventTraceV1MailboxQuery(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *const query =
      static_cast<CombatPhaseEventTraceV1MailboxContext *>(opaque_context);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->combat_id <= 0 ||
      query->expected_revision == 0 || stamp.thread_id == 0 ||
      !stamp.paused || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) !=
          stamp.thread_id ||
      mailbox.executor != &ExecuteCombatPhaseEventTraceV1MailboxQuery ||
      mailbox.executor_context != query) {
    return false;
  }
  try {
    game::Snapshot before{};
    if (!ReadSnapshot(query->bindings, before) || !before.paused ||
        before != query->expected_snapshot || before.date_raw != stamp.date_raw) {
      return true;
    }
    query->result = ReadCombatPhaseEventTraceV1Probe(
        query->bindings, query->combat_id, query->trace);
    game::Snapshot after{};
    if (!ReadSnapshot(query->bindings, after) || after != before) {
      query->trace = {};
      query->result = game::ReadCombatPhaseEventTraceV1Result::atomicity_failed;
      return true;
    }
    query->completed_on_same_frame = true;
    return true;
  } catch (...) {
    query->trace = {};
    query->result = game::ReadCombatPhaseEventTraceV1Result::unavailable;
    return true;
  }
}

} // namespace xar::ck3_11906
