#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_sway_state.hpp"
#include "xar_bridge/ck3_12002_sway_command.hpp"
#include "xar_bridge/ck3_12002_sway_outcome.hpp"

// These are reused caller-owned software bindings. Only the actual4 profile
// below selects native image addresses; no legacy image binder is invoked.
namespace xar::ck3_12004 {
ck3_12002::SwayStateBindings12002 BindSwayStateImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12002::SwayCommandBindingsV1 BindSwayCommandImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
ck3_12002::SwayOutcomeBindings BindSwayOutcomeOpinionImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
} // namespace xar::ck3_12004
