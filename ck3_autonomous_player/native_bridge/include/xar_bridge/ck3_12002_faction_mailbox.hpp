#pragma once

#include "xar_bridge/ck3_12002_faction_alerts.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12002 {

struct PlayerFactionAlertsMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  PlayerFactionAlertsNativeEnvironmentV1 environment{};
  game::PlayerFactionAlertsV1 result{};
  game::ReadPlayerFactionAlertsResultV1 read_result =
      game::ReadPlayerFactionAlertsResultV1::unavailable;
  bool completed = false;
};

bool ExecutePlayerFactionAlertsMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;

bool ReadPlayerFactionAlertsOnApplicationMain12002(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &published, std::uint64_t revision,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12002
