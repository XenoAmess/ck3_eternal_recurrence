#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_family_obligations_break.hpp"
#include "xar_bridge/ck3_12002_family_obligations_lineage.hpp"

namespace xar::ck3_12004 {

// The existing reader structs are software contracts. Native function and
// loaded-slot addresses below are bound independently for the actual .4 image.
ck3_12002::ContextBindings BindFamilyContextImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

ck3_12002::FamilyObligationsBreakBindingsV1 BindFamilyObligationsBreakImageV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

ck3_12002::FamilyProjectionBindings BindFamilyProjectionImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

ck3_12002::family_value::Bindings BindFamilyValuesImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
ck3_12002::FamilyBindings BindFamilyImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

ck3_12002::family_obligations_lineage::Bindings BindFamilyLineageImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
#endif

} // namespace xar::ck3_12004
