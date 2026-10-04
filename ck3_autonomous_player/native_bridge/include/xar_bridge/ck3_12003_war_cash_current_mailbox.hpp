#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_war_cash_current_serializer.hpp"

namespace xar::ck3_12003::war_cash_current {

struct CurrentResourcesMailboxContextV1 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  ActorResources observation{};
  bool completed = false;
};

bool ExecuteCurrentResourcesMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

} // namespace xar::ck3_12003::war_cash_current
