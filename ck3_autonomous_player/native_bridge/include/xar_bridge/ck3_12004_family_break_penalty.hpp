#pragma once

#include "xar_bridge/ck3_12002_family_obligations_break_penalty.hpp"

namespace xar::ck3_12004 {

// Only the identifier fields consumed by the existing family penalty reader.
// Other PhaseDefinitionBindings feature fields retain their empty defaults.
ck3_12002::PhaseDefinitionBindings BindFamilyBreakIdentifiersImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

ck3_12002::family_break_penalty::Bindings BindFamilyBreakPenaltyImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

} // namespace xar::ck3_12004
