#pragma once

#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/ck3_12003_holy_war_defender_join_inputs.hpp"

namespace xar::ck3_12004::religion::holy_war_defender_join {

// Root's finite actual4 source map: complete1479B collector plus75B caller.
// Caller reaches this exact collector and allocator, and retains CB+1548
// bit15, the24B Character* vector and all four native argument registers.
inline constexpr std::uintptr_t kCollectorRva12004 = 0x2C0AA90;
inline constexpr std::uintptr_t kEngineAllocatorRva12004 = 0x54DEDE0;
using Bindings = ck3_12002::religion::holy_war_defender_join::Bindings;

// Software DTO/readers are reused. Every callable/image pointer is supplied
// by the actual4 factory; the original exact3 factory remains independent.
Bindings BindHolyWarDefenderJoinInputsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ContextBindings &actual_existing_faith) noexcept;

} // namespace xar::ck3_12004::religion::holy_war_defender_join
