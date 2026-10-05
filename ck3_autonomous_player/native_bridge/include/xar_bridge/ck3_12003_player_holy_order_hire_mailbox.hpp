#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_holy_order_hire_action.hpp"
#include "xar_bridge/ck3_12003_holy_order_hire_wire.hpp"

namespace xar::ck3_12003 {

struct PlayerHolyOrderHireMailboxContextV1 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  ck3_12002::CoreBindings core{};
  religion::holy_order::HireActionBindings bindings{};
  std::uint32_t holy_order_id = UINT32_MAX;
  religion::holy_order::HireActionResult observation{};
  bool completed = false;
};

bool BindPlayerHolyOrderHireMailboxImageV1(PlayerHolyOrderHireMailboxContextV1 &,
    std::uintptr_t image_base, const game::AdapterDescriptor &) noexcept;
bool ExecutePlayerHolyOrderHireMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
inline void RegisterPlayerHolyOrderHireMailboxExecutorV1(
    ck3_11906::MainThreadQueryInstallEnvironmentV1 &environment) noexcept {
  environment.permitted_executor_player_holy_order_hire12003 =
      &ExecutePlayerHolyOrderHireMailboxV1;
}

} // namespace xar::ck3_12003
