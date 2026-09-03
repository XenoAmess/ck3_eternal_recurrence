#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

// Frozen for ck3.exe 1.19.0.6, SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
// The 2026-09-03 guarded G2 dump binds null RDI at the single caller-local
// widget flag call 0xAF4EE8. The 13-byte patch starts at 0xAF4EE0, after the
// owning function's unwind prologue. Healthy input replays the call exactly;
// null RDI skips only that call and both paths resume at 0xAF4EED.
inline constexpr std::uintptr_t kStartupWidgetNullFlagCallOwnerRvaV1 =
    0xAF4C90;
inline constexpr std::uintptr_t kStartupWidgetNullFlagCallPatchRvaV1 =
    0xAF4EE0;
inline constexpr std::uintptr_t kStartupWidgetNullFlagCallContinueRvaV1 =
    0xAF4EED;
inline constexpr std::uintptr_t kStartupWidgetNullFlagCallTargetRvaV1 =
    0x369CB30;

inline constexpr std::size_t kStartupWidgetNullFlagCallPatchBytesV1 = 13;
inline constexpr std::size_t
    kStartupWidgetNullFlagCallProductionAnchorBytesV1 = 29;
inline constexpr std::size_t kStartupWidgetNullFlagCallStubBytesV1 = 55;
inline constexpr bool kStartupWidgetNullFlagCallGuardInstalledByDefaultV1 =
    false;

enum StartupWidgetNullFlagCallGuardFailureV1 : std::uint32_t {
  startup_widget_null_flag_call_guard_failure_none = 0,
  startup_widget_null_flag_call_guard_failure_exact_build = 1U << 0,
  startup_widget_null_flag_call_guard_failure_primary_thread_suspended =
      1U << 1,
  startup_widget_null_flag_call_guard_failure_unsupported_override =
      1U << 2,
  startup_widget_null_flag_call_guard_failure_already_installed = 1U << 3,
  startup_widget_null_flag_call_guard_failure_anchor = 1U << 4,
  startup_widget_null_flag_call_guard_failure_allocation = 1U << 5,
  startup_widget_null_flag_call_guard_failure_stub_protection = 1U << 6,
  startup_widget_null_flag_call_guard_failure_target_protection = 1U << 7,
  startup_widget_null_flag_call_guard_failure_target_identity = 1U << 8,
  startup_widget_null_flag_call_guard_failure_flush = 1U << 9,
  startup_widget_null_flag_call_guard_failure_rollback = 1U << 10,
};

using StartupWidgetNullFlagCallVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using StartupWidgetNullFlagCallVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using StartupWidgetNullFlagCallVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using StartupWidgetNullFlagCallFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

// Overrides are an offline executable-fixture seam only. Production must pass
// the admitted module base while its newly-created primary thread is suspended.
struct StartupWidgetNullFlagCallGuardV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;

  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t call_target_override = 0;

  void *memory_context = nullptr;
  StartupWidgetNullFlagCallVirtualAllocV1 virtual_alloc_override = nullptr;
  StartupWidgetNullFlagCallVirtualFreeV1 virtual_free_override = nullptr;
  StartupWidgetNullFlagCallVirtualProtectV1 virtual_protect_override =
      nullptr;
  StartupWidgetNullFlagCallFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

// The state address must remain stable through uninstall. The generated stub
// embeds the diagnostic atomic address.
struct StartupWidgetNullFlagCallGuardV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      startup_widget_null_flag_call_guard_failure_none};
  alignas(8) std::atomic<std::uint64_t> suppressed_count{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t call_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kStartupWidgetNullFlagCallPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kStartupWidgetNullFlagCallPatchBytesV1>
      installed_patch_bytes{};

  void *memory_context = nullptr;
  StartupWidgetNullFlagCallVirtualFreeV1 virtual_free = nullptr;
  StartupWidgetNullFlagCallVirtualProtectV1 virtual_protect = nullptr;
  StartupWidgetNullFlagCallFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct StartupWidgetNullFlagCallGuardV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags =
      startup_widget_null_flag_call_guard_failure_none;
  std::uint64_t suppressed_count = 0;
};

bool InstallStartupWidgetNullFlagCallGuardV1(
    StartupWidgetNullFlagCallGuardV1State &state,
    const StartupWidgetNullFlagCallGuardV1Environment &environment) noexcept;

// The caller must again prove quiescence externally before uninstalling. A
// failed restore retains the executable stub and reports rollback failure.
bool UninstallStartupWidgetNullFlagCallGuardV1(
    StartupWidgetNullFlagCallGuardV1State &state) noexcept;

StartupWidgetNullFlagCallGuardV1Diagnostics
ReadStartupWidgetNullFlagCallGuardV1Diagnostics(
    const StartupWidgetNullFlagCallGuardV1State &state) noexcept;

} // namespace xar::bridge
