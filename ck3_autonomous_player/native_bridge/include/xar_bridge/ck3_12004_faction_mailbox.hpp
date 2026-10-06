#pragma once

#include "xar_bridge/ck3_12004_faction_alerts.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12004 {
struct PlayerFactionAlertsMailboxContext12004 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  PlayerFactionAlertsNativeEnvironmentV1 environment{};
  game::PlayerFactionAlertsV1 result{};
  bool completed = false;
};

bool ExecutePlayerFactionAlertsMailbox12004(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerFactionAlertsWhole12004(
    const game::PlayerFactionAlertsV1 &, std::uint64_t query_sequence,
    std::string_view request_id, const game::AdapterDescriptor &);
bool HandlePlayerFactionAlerts12004(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &published, std::uint64_t published_revision,
    std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure,
    const PlayerFactionAlertsNativeEnvironmentV1 *fixture_environment = nullptr) noexcept;
} // namespace xar::ck3_12004
