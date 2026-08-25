#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

// Frozen for ck3.exe 1.19.0.6, SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
// This guard contains the later, parameterless consumer at 0x1FCC100. The
// first 15 bytes are three complete nonvolatile-register saves. A suppressed
// call returns before any original instruction has executed; a healthy call
// replays all three saves and resumes at 0x1FCC10F.
inline constexpr std::uintptr_t kStartupParticle2ConsumerFunctionRvaV1 =
    0x1FCC100;
inline constexpr std::uintptr_t kStartupParticle2ConsumerContinueRvaV1 =
    0x1FCC10F;
inline constexpr std::uintptr_t kStartupParticle2ConsumerRootSlotRvaV1 =
    0x570F908;
inline constexpr std::size_t kStartupParticle2ConsumerSlotBaseOffsetV1 =
    0xA8;
inline constexpr std::size_t kStartupParticle2ConsumerSlotStrideV1 = 8;
inline constexpr std::uint32_t kStartupParticle2ConsumerSlotCountV1 = 8;
inline constexpr std::uint32_t kStartupParticle2ConsumerAllSlotsMaskV1 =
    0xFFU;

inline constexpr std::size_t kStartupParticle2ConsumerPatchBytesV1 = 15;
inline constexpr std::size_t kStartupParticle2ConsumerProductionAnchorBytesV1 =
    0x2A;
inline constexpr std::size_t kStartupParticle2ConsumerStubBytesV1 = 190;
inline constexpr bool kStartupParticle2ConsumerGuardInstalledByDefaultV1 =
    false;

enum StartupParticle2ConsumerGuardFailureV1 : std::uint32_t {
  startup_particle2_consumer_guard_failure_none = 0,
  startup_particle2_consumer_guard_failure_exact_build = 1U << 0,
  startup_particle2_consumer_guard_failure_primary_thread_suspended = 1U << 1,
  startup_particle2_consumer_guard_failure_unsupported_override = 1U << 2,
  startup_particle2_consumer_guard_failure_already_installed = 1U << 3,
  startup_particle2_consumer_guard_failure_anchor = 1U << 4,
  startup_particle2_consumer_guard_failure_allocation = 1U << 5,
  startup_particle2_consumer_guard_failure_stub_protection = 1U << 6,
  startup_particle2_consumer_guard_failure_target_protection = 1U << 7,
  startup_particle2_consumer_guard_failure_target_identity = 1U << 8,
  startup_particle2_consumer_guard_failure_flush = 1U << 9,
  startup_particle2_consumer_guard_failure_rollback = 1U << 10,
};

using StartupParticle2ConsumerVirtualAllocV1 = void *(*)(
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using StartupParticle2ConsumerVirtualFreeV1 = bool (*)(
    void *context, void *address, std::size_t size,
    DWORD free_type) noexcept;
using StartupParticle2ConsumerVirtualProtectV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using StartupParticle2ConsumerFlushInstructionCacheV1 = bool (*)(
    void *context, const void *address, std::size_t size) noexcept;

// Overrides are an offline executable-fixture seam only. Production must pass
// the admitted module base while its newly-created primary thread is suspended.
struct StartupParticle2ConsumerGuardV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;

  std::uintptr_t patch_target_override = 0;
  std::uintptr_t root_slot_address_override = 0;
  std::uintptr_t continue_target_override = 0;

  void *memory_context = nullptr;
  StartupParticle2ConsumerVirtualAllocV1 virtual_alloc_override = nullptr;
  StartupParticle2ConsumerVirtualFreeV1 virtual_free_override = nullptr;
  StartupParticle2ConsumerVirtualProtectV1 virtual_protect_override = nullptr;
  StartupParticle2ConsumerFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

// The state address must remain stable through uninstall. The generated stub
// embeds the two diagnostic atomic addresses.
struct StartupParticle2ConsumerGuardV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      startup_particle2_consumer_guard_failure_none};
  alignas(8) std::atomic<std::uint64_t> suppressed_count{0};
  alignas(4) std::atomic<std::uint32_t> missing_slot_mask{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t root_slot_address = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kStartupParticle2ConsumerPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kStartupParticle2ConsumerPatchBytesV1>
      installed_patch_bytes{};

  void *memory_context = nullptr;
  StartupParticle2ConsumerVirtualFreeV1 virtual_free = nullptr;
  StartupParticle2ConsumerVirtualProtectV1 virtual_protect = nullptr;
  StartupParticle2ConsumerFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct StartupParticle2ConsumerGuardV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags =
      startup_particle2_consumer_guard_failure_none;
  std::uint64_t suppressed_count = 0;
  std::uint32_t missing_slot_mask = 0;
};

bool InstallStartupParticle2ConsumerGuardV1(
    StartupParticle2ConsumerGuardV1State &state,
    const StartupParticle2ConsumerGuardV1Environment &environment) noexcept;

// The caller must again prove quiescence externally before uninstalling. A
// failed restore retains the executable stub and reports rollback failure.
bool UninstallStartupParticle2ConsumerGuardV1(
    StartupParticle2ConsumerGuardV1State &state) noexcept;

StartupParticle2ConsumerGuardV1Diagnostics
ReadStartupParticle2ConsumerGuardV1Diagnostics(
    const StartupParticle2ConsumerGuardV1State &state) noexcept;

} // namespace xar::bridge
