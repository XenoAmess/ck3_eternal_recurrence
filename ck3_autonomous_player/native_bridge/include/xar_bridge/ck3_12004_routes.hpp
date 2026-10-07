#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_routes.hpp"

namespace xar::ck3_12004 {

// Native prefix-duration source: paired logical 73+631B, including the
// nonempty-path continuation, in route-horizon-12004/duration-*/FAMILY-MAP.json.
inline constexpr std::uintptr_t kRouteTravelDurationRva12004 = 0x24AAD80;

// Supplies the existing horizon and committed-timeline software readers.
ck3_12002::RouteBindings BindRouteImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
