#include "xar_bridge/player_epidemic_recovery_v1.hpp"

#include <windows.h>

#include <atomic>

namespace xar::ck3_11906 {

bool ExecutePlayerEpidemicRecoveryMailboxV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<PlayerEpidemicRecoveryMailboxContextV1 *>(opaque);
  if (query == nullptr || query->mailbox == nullptr ||
      query->ticket.sequence == 0 || query->expected_revision == 0 ||
      query->invocations != 0 || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id)
    return false;
  auto &mailbox = *query->mailbox;
  if (mailbox.state.load(std::memory_order_acquire) !=
          MainThreadQueryMailboxStateV1::executing ||
      mailbox.stop_requested.load(std::memory_order_acquire) ||
      mailbox.failure_flags.load(std::memory_order_acquire) != 0 ||
      mailbox.published_sequence.load(std::memory_order_acquire) !=
          query->ticket.sequence ||
      mailbox.owner_thread_id.load(std::memory_order_acquire) !=
          stamp.thread_id ||
      mailbox.paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire) <
          kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs ||
      mailbox.executor != &ExecutePlayerEpidemicRecoveryMailboxV1 ||
      mailbox.executor_context != query)
    return false;
  try {
    ++query->invocations;
    query->execution_stamp = stamp;
    game::Snapshot snapshot{};
    if (!ReadSnapshot(query->bindings, snapshot) ||
        snapshot != query->expected_snapshot || !snapshot.paused ||
        !snapshot.map_ready || !snapshot.has_played_character ||
        !snapshot.played_character_alive ||
        snapshot.date_raw != stamp.date_raw) {
      query->frame_changed = true;
      query->completed = true;
      return true;
    }
    query->result = ReadPlayerEpidemicRecoveryNativeV1(
        query->bindings, query->environment, query->expected_revision,
        snapshot.date_raw, snapshot.played_character_id,
        query->requested_title_id);
    query->completed = true;
    return true;
  } catch (...) {
    return false;
  }
}

} // namespace xar::ck3_11906
