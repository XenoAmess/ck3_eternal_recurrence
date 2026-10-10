#pragma once
#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"

namespace xar::ck3_12004 {

// Actual2C0995E and2C09984 pass holder inRCX and a complete targetID inEDX.
// The Root-owned Access supplies guarded reads and a shared per-frame budget.
// No original native predicate/selector/getter is installed or invoked.
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition28B280012004(
    const ArmyRegularCoreReadonlyAccess12004 &access,
    std::uintptr_t holder, std::int32_t target_full_id) noexcept;

} // namespace xar::ck3_12004
