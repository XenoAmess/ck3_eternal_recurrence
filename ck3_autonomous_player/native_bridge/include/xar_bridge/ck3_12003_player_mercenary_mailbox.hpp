#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_province.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12003_player_mercenary_context.hpp"

namespace xar::ck3_12003 {

inline constexpr std::string_view kPlayerMercenaryContextCapabilityV1 =
    "game.command.query-player-mercenary-context-v1";

struct PlayerMercenaryMailboxContextV1 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  ck3_12002::CoreBindings core{};
  ck3_12002::ProvinceBindings provinces{};
  mercenary::ContextBindings bindings{};
  mercenary::Context observation{};
  bool completed = false;
};

// Calculates only reviewed image bindings. Actor/company/world reads occur
// exclusively in ExecutePlayerMercenaryMailboxV1 on application-main.
bool BindPlayerMercenaryMailboxImageV1(PlayerMercenaryMailboxContextV1 &,
    std::uintptr_t image_base, const game::AdapterDescriptor &) noexcept;
bool ExecutePlayerMercenaryMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
inline void RegisterPlayerMercenaryMailboxExecutorV1(
    ck3_11906::MainThreadQueryInstallEnvironmentV1 &environment) noexcept {
  environment.permitted_executor_player_mercenary_context12003 =
      &ExecutePlayerMercenaryMailboxV1;
}

} // namespace xar::ck3_12003
