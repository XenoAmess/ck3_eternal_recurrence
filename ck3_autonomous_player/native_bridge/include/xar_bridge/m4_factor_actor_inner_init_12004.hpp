#pragma once

#include "xar_bridge/m4_factor_actor_context_12004.hpp"

namespace xar::ck3_12004 {

// Source-equivalent actual8895D0 final fields, with explicit self-pointer
// operations for the final08c owned storage. No native initializer is called.
// Raw holes remain outside defined_bytes; raw alone is not a native witness.
bool ProjectM4FactorActorInnerInit12004(
    std::uintptr_t module_base, std::string_view executable_sha256,
    std::uint64_t frame_key, M4FactorActorInnerInit12004 &output) noexcept;

} // namespace xar::ck3_12004
