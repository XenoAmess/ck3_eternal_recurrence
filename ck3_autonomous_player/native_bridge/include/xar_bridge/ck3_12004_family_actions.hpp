#pragma once

#include "xar_bridge/ck3_12004_family.hpp"
#include "xar_bridge/ck3_12002_family_outbound.hpp"

namespace xar::ck3_12004 {

// Native constructor/table inputs are independently mapped for actual .4.
// The caller supplies the shared actual4 command binding; no old image binder
// or readonly context is used as a replacement for the command queue.
// The existing default arrange-marriage choices/action use this same context
// contract independently of the private Family query compile flag.
ck3_12002::ContextBindings BindArrangeMarriageImage(
    std::uintptr_t module_base, std::string_view executable_sha256,
    const ck3_12002::CommandBindings &actual_commands) noexcept;

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
ck3_12002::FamilyBindings BindFamilyActionImage(
    std::uintptr_t module_base, std::string_view executable_sha256,
    const ck3_12002::CommandBindings &actual_commands) noexcept;
#endif

// Uses the existing cold scanner and DTO with actual .4 loaded slots/vtables.
ck3_12002::FamilyOutboundBindings BindFamilyOutboundImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
