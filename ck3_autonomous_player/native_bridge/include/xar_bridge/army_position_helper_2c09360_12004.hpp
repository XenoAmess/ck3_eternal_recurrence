#pragma once

#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"
#include <cstdint>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kArmyPositionHelperRva12004 = 0x2C09360;
inline constexpr std::uintptr_t kArmyPositionHelperParentCallRva12004 = 0x2C092AA;
inline constexpr std::uintptr_t kArmyPositionHelperParentReturnRva12004 = 0x2C092AF;

// Literal helper arguments are native RCX=&{holder, optional_war_identity},
// native RDX=actor. In 2C09280 these are original RDX, R8 and RCX respectively.
// Only guarded reads and conditional projections run; no native code is called.
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C0936012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t holder, std::uintptr_t actor,
    std::uintptr_t optional_war_identity = 0) noexcept;

} // namespace xar::ck3_12004
