#pragma once

#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"

#include <cstdint>

namespace xar::ck3_12004 {

// Actual 2C090D0: RCX actor, RDX holder, R8 optional resolved War pointer.
// A null filter visits every War occurrence. Equal full Character IDs return
// false here; the enclosing position predicate owns its separate same-ID branch.
// This reads consumed operands through the parent's guarded read callback and
// never invokes a native getter or the original function.
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C090D012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t actor, std::uintptr_t holder,
    std::uintptr_t optional_war_identity = 0) noexcept;

} // namespace xar::ck3_12004
