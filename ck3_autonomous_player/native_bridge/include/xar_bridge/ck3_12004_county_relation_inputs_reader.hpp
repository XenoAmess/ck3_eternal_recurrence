#pragma once
#include "xar_bridge/army_county_predicate_trace_v1.hpp"
#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"

namespace xar::ck3_12004 {
std::optional<std::uint32_t> ReadCountyRelationFullId12004(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t identity) noexcept;
game::ArmyCountyRelationInputsV1 ReadCountyRelationInputs12004(
    const ArmyRegularCoreReadonlyAccess12004 &, std::uintptr_t receiver,
    std::uintptr_t actor, std::uintptr_t auxiliary) noexcept;
}
