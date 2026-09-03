#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

// Frozen for ck3.exe 1.19.0.6, SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
// The 2026-09-03 fifth-guard G2 dump binds null RBX/RCX at the single
// caller-local call 0x390A9ED. The 16-byte patch starts at 0x390A9E2, after
// the owning function's unwind prologue. Healthy input replays the store,
// argument setup and call exactly; null RBX skips only that call and both
// paths resume at 0x390A9F2.
inline constexpr std::uintptr_t kStartupRbxNullCallOwnerRvaV1 =
    0x390A700;
inline constexpr std::uintptr_t kStartupRbxNullCallPatchRvaV1 =
    0x390A9E2;
inline constexpr std::uintptr_t kStartupRbxNullCallContinueRvaV1 =
    0x390A9F2;
inline constexpr std::uintptr_t kStartupRbxNullCallTargetRvaV1 =
    0x3B67330;

inline constexpr std::size_t kStartupRbxNullCallPatchBytesV1 = 16;
inline constexpr std::size_t
    kStartupRbxNullCallProductionAnchorBytesV1 = 36;
inline constexpr std::size_t kStartupRbxNullCallStubBytesV1 = 58;
inline constexpr bool kStartupRbxNullCallGuardInstalledByDefaultV1 =
    false;

enum StartupRbxNullCallGuardFailureV1 : std::uint32_t {
  startup_rbx_null_call_guard_failure_none = 0,
  startup_rbx_null_call_guard_failure_exact_build = 1U << 0,
  startup_rbx_null_call_guard_failure_primary_thread_suspended =
      1U << 1,
  startup_rbx_null_call_guard_failure_unsupported_override =
      1U << 2,
  startup_rbx_null_call_guard_failure_already_installed = 1U << 3,
  startup_rbx_null_call_guard_failure_anchor = 1U << 4,
  startup_rbx_null_call_guard_failure_allocation = 1U << 5,
  startup_rbx_null_call_guard_failure_stub_protection = 1U << 6,
  startup_rbx_null_call_guard_failure_target_protection = 1U << 7,
  startup_rbx_null_call_guard_failure_target_identity = 1U << 8,
  startup_rbx_null_call_guard_failure_flush = 1U << 9,
  startup_rbx_null_call_guard_failure_rollback = 1U << 10,
};

using StartupRbxNullCallVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using StartupRbxNullCallVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using StartupRbxNullCallVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using StartupRbxNullCallFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

// Overrides are an offline executable-fixture seam only. Production must pass
// the admitted module base while its newly-created primary thread is suspended.
struct StartupRbxNullCallGuardV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;

  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t call_target_override = 0;

  void *memory_context = nullptr;
  StartupRbxNullCallVirtualAllocV1 virtual_alloc_override = nullptr;
  StartupRbxNullCallVirtualFreeV1 virtual_free_override = nullptr;
  StartupRbxNullCallVirtualProtectV1 virtual_protect_override =
      nullptr;
  StartupRbxNullCallFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

// The state address must remain stable through uninstall. The generated stub
// embeds the diagnostic atomic address.
struct StartupRbxNullCallGuardV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      startup_rbx_null_call_guard_failure_none};
  alignas(8) std::atomic<std::uint64_t> suppressed_count{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t call_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kStartupRbxNullCallPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kStartupRbxNullCallPatchBytesV1>
      installed_patch_bytes{};

  void *memory_context = nullptr;
  StartupRbxNullCallVirtualFreeV1 virtual_free = nullptr;
  StartupRbxNullCallVirtualProtectV1 virtual_protect = nullptr;
  StartupRbxNullCallFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct StartupRbxNullCallGuardV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags =
      startup_rbx_null_call_guard_failure_none;
  std::uint64_t suppressed_count = 0;
};

bool InstallStartupRbxNullCallGuardV1(
    StartupRbxNullCallGuardV1State &state,
    const StartupRbxNullCallGuardV1Environment &environment) noexcept;

// The caller must again prove quiescence externally before uninstalling. A
// failed restore retains the executable stub and reports rollback failure.
bool UninstallStartupRbxNullCallGuardV1(
    StartupRbxNullCallGuardV1State &state) noexcept;

StartupRbxNullCallGuardV1Diagnostics
ReadStartupRbxNullCallGuardV1Diagnostics(
    const StartupRbxNullCallGuardV1State &state) noexcept;

} // namespace xar::bridge
