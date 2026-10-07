#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_routes.hpp"

namespace xar::ck3_12004 {

// Existing actual/projected contact readers retain their software RouteBindings
// and DTOs. This image factory consumes only the actual .4 identity and composes
// the independently closed route, Core, Army and readonly contact profiles.
ck3_12002::RouteBindings BindContactImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
