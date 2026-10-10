#pragma once

#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"

namespace xar::ck3_12004 {
// Source direction: 2C09993 passes RCX=holder and RDX=actor.
// Reads the current conditional inputs of 2C3A0E0 and its sole 28BFCD0 leaf.
// It never calls either native function and grants no historical call credit.
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C3A0E012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t holder, std::uintptr_t actor) noexcept;
} // namespace xar::ck3_12004
