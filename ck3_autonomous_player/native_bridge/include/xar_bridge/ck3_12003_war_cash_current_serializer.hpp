#pragma once

#include "xar_bridge/ck3_12003_war_cash_current_reader.hpp"
#include "xar_bridge/game_contract.hpp"

#include <string>

namespace xar::ck3_12003::war_cash_current {

inline constexpr std::string_view kCurrentStepV1 =
    "query-war-cash-current-resources-v1";

// Serializes the actual reader output with the owning-thread paused frame.
// No future war estimate, per-war duplication, or null-to-zero conversion.
std::string SerializeCurrentResourcesV1(
    const ActorResources &resources, const game::Snapshot &snapshot,
    std::uint64_t snapshot_revision, bool same_frame_ready);

} // namespace xar::ck3_12003::war_cash_current
