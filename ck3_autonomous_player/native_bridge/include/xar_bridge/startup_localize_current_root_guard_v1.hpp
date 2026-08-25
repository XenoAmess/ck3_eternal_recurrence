#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

// Frozen for ck3.exe 1.19.0.6, SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
// This guard owns only the Localize caller at 0x3A6A410. The 13-byte patch
// begins at 0x3A6A4D6, after the unwind prologue. A healthy call replays all
// three overwritten instructions and resumes at 0x3A6A4E3. If the published
// localization container has no current root, the stub preserves that null
// in RBX and enters the owner's native miss path at 0x3A6A51A.
inline constexpr std::uintptr_t kStartupLocalizeCurrentRootOwnerRvaV1 =
    0x3A6A410;
inline constexpr std::uintptr_t kStartupLocalizeCurrentRootPatchRvaV1 =
    0x3A6A4D6;
inline constexpr std::uintptr_t kStartupLocalizeCurrentRootContinueRvaV1 =
    0x3A6A4E3;
inline constexpr std::uintptr_t
    kStartupLocalizeCurrentRootGlobalContainerSlotRvaV1 = 0x57DFA28;
inline constexpr std::uintptr_t kStartupLocalizeCurrentRootNativeMissRvaV1 =
    0x3A6A51A;
inline constexpr std::uintptr_t
    kStartupLocalizeCurrentRootRawKeyFallbackRvaV1 = 0x3A6A67F;

inline constexpr std::size_t kStartupLocalizeCurrentRootPatchBytesV1 = 13;
inline constexpr std::size_t
    kStartupLocalizeCurrentRootProductionAnchorBytesV1 = 13;
inline constexpr std::size_t kStartupLocalizeCurrentRootStubBytesV1 = 64;
inline constexpr bool kStartupLocalizeCurrentRootGuardInstalledByDefaultV1 =
    false;

enum StartupLocalizeCurrentRootGuardFailureV1 : std::uint32_t {
  startup_localize_current_root_guard_failure_none = 0,
  startup_localize_current_root_guard_failure_exact_build = 1U << 0,
  startup_localize_current_root_guard_failure_primary_thread_suspended =
      1U << 1,
  startup_localize_current_root_guard_failure_unsupported_override = 1U << 2,
  startup_localize_current_root_guard_failure_already_installed = 1U << 3,
  startup_localize_current_root_guard_failure_anchor = 1U << 4,
  startup_localize_current_root_guard_failure_allocation = 1U << 5,
  startup_localize_current_root_guard_failure_stub_protection = 1U << 6,
  startup_localize_current_root_guard_failure_target_protection = 1U << 7,
  startup_localize_current_root_guard_failure_target_identity = 1U << 8,
  startup_localize_current_root_guard_failure_flush = 1U << 9,
  startup_localize_current_root_guard_failure_rollback = 1U << 10,
};

using StartupLocalizeCurrentRootVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using StartupLocalizeCurrentRootVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using StartupLocalizeCurrentRootVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using StartupLocalizeCurrentRootFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

// Overrides are an offline executable-fixture seam only. Production must pass
// the admitted module base while its newly-created primary thread is suspended.
struct StartupLocalizeCurrentRootGuardV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;

  std::uintptr_t patch_target_override = 0;
  std::uintptr_t global_container_slot_address_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t native_miss_target_override = 0;

  void *memory_context = nullptr;
  StartupLocalizeCurrentRootVirtualAllocV1 virtual_alloc_override = nullptr;
  StartupLocalizeCurrentRootVirtualFreeV1 virtual_free_override = nullptr;
  StartupLocalizeCurrentRootVirtualProtectV1 virtual_protect_override =
      nullptr;
  StartupLocalizeCurrentRootFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

// The state address must remain stable through uninstall because the leaf stub
// embeds the diagnostic counter address.
struct StartupLocalizeCurrentRootGuardV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      startup_localize_current_root_guard_failure_none};
  alignas(8) std::atomic<std::uint64_t> native_miss_count{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t global_container_slot_address = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t native_miss_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kStartupLocalizeCurrentRootPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kStartupLocalizeCurrentRootPatchBytesV1>
      installed_patch_bytes{};

  void *memory_context = nullptr;
  StartupLocalizeCurrentRootVirtualFreeV1 virtual_free = nullptr;
  StartupLocalizeCurrentRootVirtualProtectV1 virtual_protect = nullptr;
  StartupLocalizeCurrentRootFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct StartupLocalizeCurrentRootGuardV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags =
      startup_localize_current_root_guard_failure_none;
  std::uint64_t native_miss_count = 0;
};

bool InstallStartupLocalizeCurrentRootGuardV1(
    StartupLocalizeCurrentRootGuardV1State &state,
    const StartupLocalizeCurrentRootGuardV1Environment &environment) noexcept;

// The caller must again prove quiescence externally before uninstalling. A
// failed restore retains the executable stub and reports rollback failure.
bool UninstallStartupLocalizeCurrentRootGuardV1(
    StartupLocalizeCurrentRootGuardV1State &state) noexcept;

StartupLocalizeCurrentRootGuardV1Diagnostics
ReadStartupLocalizeCurrentRootGuardV1Diagnostics(
    const StartupLocalizeCurrentRootGuardV1State &state) noexcept;

} // namespace xar::bridge
