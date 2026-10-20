#pragma once
#include <cstddef>
#include <cstdint>
#include <span>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kKnightStatContextSourceRva12004=0x28C3AC0;
inline constexpr std::size_t kKnightStatContextSourceBytes12004=220;
// Original full220, or this DLL's complete owned installed pair plus original
// trampolines, exact return jumps, untouched tail and stable bookends. Readonly;
// no patch/unpatch, function invocation, public override or gameplay action.
bool KnightStatContextSourceStillBound12004(std::uintptr_t image_base,
    std::span<const std::uint8_t,kKnightStatContextSourceBytes12004> original,
    const char *&failure) noexcept;
} // namespace xar::ck3_12004
