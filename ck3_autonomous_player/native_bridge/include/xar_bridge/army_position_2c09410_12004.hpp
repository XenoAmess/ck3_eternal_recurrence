#pragma once

#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"

namespace xar::ck3_12004 {

// Actual2C09410: preserves actor/holder direction. The third native argument is
// an optional record pointer whose complete ID at +8 filters the actor's list.
// Both reached calls in actual2C097F0 supply zero. No native getter is called.
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C0941012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t actor, std::uintptr_t holder,
    std::uintptr_t record_filter = 0) noexcept;

} // namespace xar::ck3_12004
