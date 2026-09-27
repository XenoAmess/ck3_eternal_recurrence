#pragma once

#include "xar_bridge/combat_phase_event_trace_detour_v1.hpp"

#include <array>
#include <atomic>
#include <cstdint>

namespace xar::ck3_11906 {

inline constexpr std::size_t kCombatCounterOutputPatchBytesV1 = 14;
inline constexpr std::size_t kCombatCounterOutputTrampolineBytesV1 = 128;

// Optional exact-build, paused-only patch at 0x23CAF25. The trampoline copies
// the output after the original helper returns, then replays all four original
// instructions. The default managed trace never installs it.
struct CombatCounterOutputDetourV1 {
  std::atomic<std::uint32_t> installed{0};
  std::uint32_t failure_flags = 0;
  std::uintptr_t target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kCombatCounterOutputPatchBytesV1> original{};
};

bool InstallCombatCounterOutputDetourV1(
    CombatCounterOutputDetourV1 &state, std::uintptr_t module_base,
    bool exact_build_admitted, bool paused_quiescence_proven,
    std::uintptr_t offline_target_override = 0) noexcept;
bool UninstallCombatCounterOutputDetourV1(
    CombatCounterOutputDetourV1 &state) noexcept;

} // namespace xar::ck3_11906
