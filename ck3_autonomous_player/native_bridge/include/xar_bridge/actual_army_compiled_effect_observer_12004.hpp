#pragma once

#include "xar_bridge/actual_army_compiled_effect_observations_v1.hpp"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kActualArmyCompiledEffectRva12004 = 0x3765760;
inline constexpr std::size_t kActualArmyCompiledEffectPatchBytes12004 = 18;
inline constexpr std::size_t kActualArmyCompiledEffectAbsoluteJumpBytes12004 = 14;
// The native wrapper accepts RCX/RDX and leaves unspecified RAX bits. Preserve
// those bits exactly; they are not a semantic success result.
using ActualArmyCompiledEffectOriginalV1 = std::uint64_t(__fastcall *)(const void *, const void *);
using ActualArmyCompiledEffectReadMemoryV1 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
using ActualArmyCompiledEffectVirtualAllocV1 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ActualArmyCompiledEffectVirtualFreeV1 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ActualArmyCompiledEffectVirtualProtectV1 = bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ActualArmyCompiledEffectFlushV1 = bool (*)(void *, const void *, std::size_t) noexcept;
struct ActualArmyCompiledEffectBindingsV1 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ActualArmyCompiledEffectReadMemoryV1 read_memory = nullptr;
};
struct ActualArmyCompiledEffectInstallEnvironmentV1 {
  bool primary_thread_suspended_proven = false;
  ActualArmyCompiledEffectBindingsV1 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ActualArmyCompiledEffectVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualArmyCompiledEffectVirtualFreeV1 virtual_free_override = nullptr;
  ActualArmyCompiledEffectVirtualProtectV1 virtual_protect_override = nullptr;
  ActualArmyCompiledEffectFlushV1 flush_instruction_cache_override = nullptr;
};
// Static, pinned process lifetime. There is no live uninstall or unload API.
struct ActualArmyCompiledEffectDetourStateV1 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kActualArmyCompiledEffectPatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualArmyCompiledEffectVirtualFreeV1 virtual_free = nullptr;
  ActualArmyCompiledEffectVirtualProtectV1 virtual_protect = nullptr;
  ActualArmyCompiledEffectFlushV1 flush_instruction_cache = nullptr;
};
enum ActualArmyCompiledEffectInstallFailureV1 : std::uint32_t {
  actual_army_compiled_effect_install_none = 0,
  actual_army_compiled_effect_install_exact_build = 1U << 0,
  actual_army_compiled_effect_install_quiescence = 1U << 1,
  actual_army_compiled_effect_install_already_installed = 1U << 2,
  actual_army_compiled_effect_install_anchor = 1U << 3,
  actual_army_compiled_effect_install_allocation = 1U << 4,
  actual_army_compiled_effect_install_protection = 1U << 5,
  actual_army_compiled_effect_install_flush = 1U << 6,
  actual_army_compiled_effect_install_rollback = 1U << 7,
};
enum ActualArmyCompiledEffectCaptureFailureV1 : std::uint32_t {
  actual_army_compiled_effect_capture_before = 1U << 0,
  actual_army_compiled_effect_capture_receiver = 1U << 1,
  actual_army_compiled_effect_capture_after = 1U << 2,
  actual_army_compiled_effect_capture_identity_changed = 1U << 3,
  actual_army_compiled_effect_capture_flag = 1U << 4,
};
ActualArmyCompiledEffectBindingsV1 BindActualArmyCompiledEffectImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallActualArmyCompiledEffectObserver12004(
    ActualArmyCompiledEffectDetourStateV1 &state,
    const ActualArmyCompiledEffectInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept;
std::optional<game::ArmyActualCompiledEffectObservationsV1>
ReadActualArmyCompiledEffectObservations12004(std::int32_t native_carmy_id) noexcept;
// Army query adapter, implemented in the actual Army provider source.
std::optional<game::ArmyActualCompiledEffectObservationsV1>
ReadActualArmyCompiledEffectObservationsForArmy12004(std::int32_t native_carmy_id) noexcept;
extern "C" std::uint64_t __fastcall XarActualArmyCompiledEffectHook12004V1(
    const void *receiver, const void *incoming_context) noexcept;
// Typed owned fixture only: no effect execution, patch, query wire setter or
// native pointer resolution. Production uses the real hook and return address.
bool InitializeActualArmyCompiledEffectFixture12004(
    const ActualArmyCompiledEffectBindingsV1 &bindings,
    ActualArmyCompiledEffectOriginalV1 original) noexcept;
std::uint64_t InvokeActualArmyCompiledEffectFixture12004(
    std::uint64_t caller_return_rva, const void *receiver, const void *incoming_context) noexcept;
} // namespace xar::ck3_12004
