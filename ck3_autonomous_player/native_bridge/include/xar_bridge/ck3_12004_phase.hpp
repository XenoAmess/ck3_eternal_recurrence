#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_phase.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12004 {

// Reuse the adopted phase DTO and reader ABI. This factory selects actual .4
// entries directly and never invokes a legacy image binder or hash alias.
ck3_12002::PhaseBindings BindPhaseImage12004(
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
