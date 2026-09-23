#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/combat_phase_event_trace_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>

namespace xar::ck3_11906 {

struct CombatPhaseEventTraceV1MailboxContext {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  std::int32_t combat_id = -1;
  std::uint64_t expected_revision = 0;
  game::Snapshot expected_snapshot{};
  game::ReadCombatPhaseEventTraceV1Result result =
      game::ReadCombatPhaseEventTraceV1Result::unavailable;
  game::CombatPhaseEventTraceV1 trace{};
  bool completed_on_same_frame = false;
};

bool ExecuteCombatPhaseEventTraceV1MailboxQuery(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept;

} // namespace xar::ck3_11906
