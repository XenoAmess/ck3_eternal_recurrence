#pragma once

#include "xar_bridge/ck3_12002_declarations.hpp"

namespace xar::ck3_12004 {

// Readonly context fields are supplied by the actual .4 holy-war profile.
// The owning adapter supplies its separately mapped actual .4 command bundle.
ck3_12002::DeclarationsBindings BindDeclarationsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::CommandBindings &actual_commands = {}) noexcept;

} // namespace xar::ck3_12004
