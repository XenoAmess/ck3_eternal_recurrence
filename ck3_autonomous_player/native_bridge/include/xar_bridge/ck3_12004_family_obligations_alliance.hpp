#pragma once

#include "xar_bridge/ck3_12002_family_obligations_alliance.hpp"
#include "xar_bridge/ck3_12004_family.hpp"

namespace xar::ck3_12004 {

// Existing reader types are software contracts; native addresses are bound
// independently for the exact actual 1.20.0.4 image.
ck3_12002::family_obligations_alliance::Bindings
BindFamilyObligationsAllianceImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
