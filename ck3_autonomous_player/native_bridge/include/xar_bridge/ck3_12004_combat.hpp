#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_combat.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12004 {

// Existing GeneralCombat readers consume this adopted software type.
// Executable addresses and enabled extensions are bound independently to .4.
ck3_12002::CombatBindings BindCombatImage12004(
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
