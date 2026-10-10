#pragma once

#include "xar_bridge/army_assault_group_release_observations_12004.hpp"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kArmyAssaultGroupReleaseRva12004 = 0x9D11F0;
inline constexpr std::size_t kArmyAssaultGroupReleasePatchBytes12004 = 14;
inline constexpr std::size_t kArmyAssaultGroupReleaseAbsoluteJumpBytes12004 = 14;
using ArmyAssaultGroupReleaseOriginal12004 = std::uint64_t(__fastcall *)(const void *);
using ArmyAssaultGroupReleaseReadMemory12004 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
using ArmyAssaultGroupReleaseReadParent12004 = bool (*)(void *, game::ArmyAssaultReleaseParent12004 &) noexcept;
using ArmyAssaultGroupReleaseNextClock12004 = ArmyNaturalPhaseEvent12004 (*)(void *) noexcept;
using ArmyAssaultGroupReleaseVirtualAlloc12004 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ArmyAssaultGroupReleaseVirtualFree12004 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ArmyAssaultGroupReleaseVirtualProtect12004 = bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ArmyAssaultGroupReleaseFlush12004 = bool (*)(void *, const void *, std::size_t) noexcept;

struct ArmyAssaultGroupReleaseBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ArmyAssaultGroupReleaseReadMemory12004 read_memory = nullptr;
  void *parent_context = nullptr;
  // Production wiring must copy37b's real active TLS extent and33b's real
  // phaseclock. No current-query input substitutes either callback.
  ArmyAssaultGroupReleaseReadParent12004 read_active_parent = nullptr;
  void *clock_context = nullptr;
  ArmyAssaultGroupReleaseNextClock12004 next_phase_clock = nullptr;
};

struct ArmyAssaultGroupReleaseInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ArmyAssaultGroupReleaseBindings12004 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ArmyAssaultGroupReleaseVirtualAlloc12004 virtual_alloc_override = nullptr;
  ArmyAssaultGroupReleaseVirtualFree12004 virtual_free_override = nullptr;
  ArmyAssaultGroupReleaseVirtualProtect12004 virtual_protect_override = nullptr;
  ArmyAssaultGroupReleaseFlush12004 flush_instruction_cache_override = nullptr;
};

struct ArmyAssaultGroupReleaseDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kArmyAssaultGroupReleasePatchBytes12004> original{};
  void *memory_context = nullptr;
  ArmyAssaultGroupReleaseVirtualFree12004 virtual_free = nullptr;
  ArmyAssaultGroupReleaseVirtualProtect12004 virtual_protect = nullptr;
  ArmyAssaultGroupReleaseFlush12004 flush_instruction_cache = nullptr;
};

enum ArmyAssaultGroupReleaseInstallFailure12004 : std::uint32_t {
  assault_release_install_none = 0,
  assault_release_install_exact_build = 1U << 0,
  assault_release_install_quiescence = 1U << 1,
  assault_release_install_already_installed = 1U << 2,
  assault_release_install_anchor = 1U << 3,
  assault_release_install_allocation = 1U << 4,
  assault_release_install_protection = 1U << 5,
  assault_release_install_flush = 1U << 6,
  assault_release_install_rollback = 1U << 7,
  assault_release_install_parent_clock_binding = 1U << 8,
};

ArmyAssaultGroupReleaseBindings12004 BindArmyAssaultGroupReleaseImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallArmyAssaultGroupReleaseObserver12004(
    ArmyAssaultGroupReleaseDetourState12004 &state,
    const ArmyAssaultGroupReleaseInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept;
std::optional<game::ArmyAssaultGroupReleaseObservations12004>
ReadArmyAssaultGroupReleaseObservations12004(std::uint32_t exact_native_carmy_full_id) noexcept;
extern "C" std::uint64_t __fastcall XarArmyAssaultGroupReleaseHook12004(const void *record_plus10) noexcept;

// Typed fixture invokes an owned original; never performs a native release,
// hook installation, query event injection or parent creation in production.
bool InitializeArmyAssaultGroupReleaseFixture12004(
    const ArmyAssaultGroupReleaseBindings12004 &bindings,
    ArmyAssaultGroupReleaseOriginal12004 original) noexcept;
std::uint64_t InvokeArmyAssaultGroupReleaseFixture12004(
    std::uint64_t caller_return_rva, const void *record_plus10) noexcept;
} // namespace xar::ck3_12004
