#pragma once

#include "xar_bridge/current_actor_stress_adjustment_v1.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12003 {

struct CurrentActorStressAdjustmentMailboxContextV1 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  std::uintptr_t image_base = 0;
  CurrentActorStressAdjustmentRequestV1 request{};
  CurrentActorStressAdjustmentObservationV1 observation{};
  bool completed = false;
};

bool ExecuteCurrentActorStressAdjustmentMailboxV1(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

} // namespace xar::ck3_12003
