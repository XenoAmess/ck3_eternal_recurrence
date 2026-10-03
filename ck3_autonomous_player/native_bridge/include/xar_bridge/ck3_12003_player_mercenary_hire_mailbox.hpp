#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_mercenary_hire_action.hpp"
#include "xar_bridge/ck3_12003_mercenary_hire_wire.hpp"

namespace xar::ck3_12003 {

struct PlayerMercenaryHireMailboxContextV1 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  ck3_12002::CoreBindings core{};
  mercenary::HireActionBindings bindings{};
  std::uint32_t company_id = UINT32_MAX;
  mercenary::HireActionResult observation{};
  bool completed = false;
};

bool BindPlayerMercenaryHireMailboxImageV1(PlayerMercenaryHireMailboxContextV1 &,
    std::uintptr_t image_base, const game::AdapterDescriptor &) noexcept;
bool ExecutePlayerMercenaryHireMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
inline void RegisterPlayerMercenaryHireMailboxExecutorV1(
    ck3_11906::MainThreadQueryInstallEnvironmentV1 &environment) noexcept {
  environment.permitted_executor_player_mercenary_hire12003 =
      &ExecutePlayerMercenaryHireMailboxV1;
}

} // namespace xar::ck3_12003
