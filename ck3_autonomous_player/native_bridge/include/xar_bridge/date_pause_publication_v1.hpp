#pragma once
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

namespace xar::bridge {
// This only admits an attempt to publish the existing complete semantic frame.
// PublishSnapshot/WorkerAdapter keep their original current-owner read guards.
inline bool DatePausePublicationDueV1(
    bool previous_present, std::int32_t previous_date_raw, bool previous_paused,
    const ck3_11906::MainThreadQueryMailboxDiagnosticsV1 &stamp) noexcept {
  return previous_present && previous_date_raw > 0 &&
      !stamp.stop_requested && stamp.observed_stamp_read_success &&
      stamp.pump_epochs != 0 && stamp.owner_verified_pump_epochs != 0 &&
      stamp.owner_thread_id != 0 &&
      stamp.observed_current_thread_id == stamp.owner_thread_id &&
      stamp.observed_tls_initialized == 1 &&
      stamp.observed_tls_main_thread_marker == 1 &&
      stamp.observed_tls_context != 0 && stamp.observed_jomini_state != 0 &&
      stamp.observed_game_state != 0 && stamp.observed_date_raw > 0 &&
      (stamp.observed_date_raw != previous_date_raw ||
       stamp.observed_paused != previous_paused);
}
} // namespace xar::bridge
