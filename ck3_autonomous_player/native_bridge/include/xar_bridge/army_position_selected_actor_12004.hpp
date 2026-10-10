#pragma once

#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004 {

struct ArmyPositionSelectedActor12004 {
  std::optional<std::uintptr_t> selected_actor_identity;
  std::size_t path_occurrences = 0;
  std::string unavailable_reason;
};

// Actual2C092BB ->2C0FEC0 supplies original actor and the pair(holder,R8).
// This memory-only current projection preserves that actual R8 pointer; the
// parent16b caller supplies literal null. No native getter is invoked.
ArmyPositionSelectedActor12004 ReadArmyPositionSelectedActor2C0FEC012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t original_actor, std::uintptr_t holder,
    std::uintptr_t optional_war_identity = 0) noexcept;

} // namespace xar::ck3_12004
