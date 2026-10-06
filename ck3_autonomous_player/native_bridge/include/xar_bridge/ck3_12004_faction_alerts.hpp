#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_faction_alerts.hpp"

namespace xar::ck3_12004 {

inline constexpr std::string_view kPlayerFactionAlertsBackendId12004 =
    "ck3-1.20.0.4-native-player-faction-alerts-v1";

// Shared caller-owned DTO/access algorithms; executable binding is independent.
using PlayerFactionAlertsNativeEnvironmentV1 =
    ck3_12002::PlayerFactionAlertsNativeEnvironmentV1;
using PlayerFactionAlertsAccessV1 = ck3_12002::PlayerFactionAlertsAccessV1;
using ReadFactionEntityResult12004 = ck3_12002::ReadFactionEntityResult12002;

PlayerFactionAlertsNativeEnvironmentV1 BindPlayerFactionAlertsImage12004(
    std::uintptr_t, std::string_view actual_executable_sha256) noexcept;
game::ReadPlayerFactionAlertsResultV1 ReadPlayerFactionAlerts12004(
    const PlayerFactionAlertsNativeEnvironmentV1 &,
    const PlayerFactionAlertsAccessV1 &,
    const ck3_12002::PlayerFactionAlertsRequestV1 &,
    game::PlayerFactionAlertsV1 &) noexcept;
ReadFactionEntityResult12004 ReadFactionEntity12004(
    const PlayerFactionAlertsNativeEnvironmentV1 &,
    const PlayerFactionAlertsAccessV1 &, std::int32_t,
    game::PlayerTargetingFactionV1 &) noexcept;
std::string SerializePlayerFactionAlerts12004(
    const game::PlayerFactionAlertsV1 &);

} // namespace xar::ck3_12004
