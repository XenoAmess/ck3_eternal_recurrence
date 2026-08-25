#pragma once

#include "xar_bridge/combat_phase_event_trace_ring_v1.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::ck3_11906 {

inline constexpr std::size_t kCombatPhaseEventTraceDetourPatchBytesV1 = 15;
inline constexpr std::size_t kCombatPhaseEventTraceAbsoluteJumpBytesV1 = 14;
inline constexpr std::size_t kCombatPhaseEventTraceTrampolineBytesV1 =
    kCombatPhaseEventTraceDetourPatchBytesV1 +
    kCombatPhaseEventTraceAbsoluteJumpBytesV1;

enum CombatPhaseEventTraceDetourFailureV1 : std::uint32_t {
  trace_detour_failure_none = 0,
  trace_detour_failure_exact_build = 1U << 0,
  trace_detour_failure_paused_quiescence = 1U << 1,
  trace_detour_failure_already_installed = 1U << 2,
  trace_detour_failure_anchor = 1U << 3,
  trace_detour_failure_allocation = 1U << 4,
  trace_detour_failure_trampoline_protection = 1U << 5,
  trace_detour_failure_target_protection = 1U << 6,
  trace_detour_failure_target_identity = 1U << 7,
  trace_detour_failure_flush = 1U << 8,
  trace_detour_failure_original_binding = 1U << 9,
  trace_detour_failure_rollback = 1U << 10,
  trace_detour_failure_capture_active = 1U << 11,
};

using CombatTraceVirtualAllocV1 = void *(*)(
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using CombatTraceVirtualFreeV1 = bool (*)(
    void *context, void *address, std::size_t size,
    DWORD free_type) noexcept;
using CombatTraceVirtualProtectV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using CombatTraceFlushInstructionCacheV1 = bool (*)(
    void *context, const void *address, std::size_t size) noexcept;

// Test overrides exist only so the patch/rollback state machine can be
// replayed without a CK3 process.  Production callers leave every override
// null, and exact addresses are derived from module_base plus the frozen RVAs.
struct CombatPhaseEventTraceDetourEnvironmentV1 {
  bool exact_build_admitted = false;
  bool managed_paused_quiescence_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;

  std::uintptr_t schedule_target_override = 0;
  std::uintptr_t fire_target_override = 0;
  std::uintptr_t schedule_side0_call_override = 0;
  std::uintptr_t schedule_side1_call_override = 0;
  std::uintptr_t fire_side0_call_override = 0;
  std::uintptr_t fire_side1_call_override = 0;
  std::uintptr_t fire_tail_jump_override = 0;

  void *memory_context = nullptr;
  CombatTraceVirtualAllocV1 virtual_alloc_override = nullptr;
  CombatTraceVirtualFreeV1 virtual_free_override = nullptr;
  CombatTraceVirtualProtectV1 virtual_protect_override = nullptr;
  CombatTraceFlushInstructionCacheV1 flush_instruction_cache_override =
      nullptr;
};

struct CombatPhaseEventTraceDetourStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{trace_detour_failure_none};
  std::uintptr_t module_base = 0;
  std::uintptr_t schedule_target = 0;
  std::uintptr_t fire_target = 0;
  void *schedule_trampoline = nullptr;
  void *fire_trampoline = nullptr;
  std::array<std::uint8_t, kCombatPhaseEventTraceDetourPatchBytesV1>
      schedule_original{};
  std::array<std::uint8_t, kCombatPhaseEventTraceDetourPatchBytesV1>
      fire_original{};
  void *memory_context = nullptr;
  CombatTraceVirtualFreeV1 virtual_free = nullptr;
  CombatTraceVirtualProtectV1 virtual_protect = nullptr;
  CombatTraceFlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

// Install/uninstall only patch the two frozen function entries.  The caller
// must invoke both operations from the verified application-main mailbox while
// CK3 is paused and the simulation tick is quiescent.  Installation never arms
// a capture ring and does not advertise a bridge capability.
bool InstallCombatPhaseEventTraceDetoursV1(
    CombatPhaseEventTraceDetourStateV1 &state,
    const CombatPhaseEventTraceDetourEnvironmentV1 &environment) noexcept;

bool UninstallCombatPhaseEventTraceDetoursV1(
    CombatPhaseEventTraceDetourStateV1 &state) noexcept;

} // namespace xar::ck3_11906
