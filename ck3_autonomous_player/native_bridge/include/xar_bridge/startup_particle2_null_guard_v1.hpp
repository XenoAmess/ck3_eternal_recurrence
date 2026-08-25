#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

// Frozen for ck3.exe 1.19.0.6, SHA-256
// 2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86.
// The patch begins only after the complete 0x1d-byte UNWIND_INFO prologue.
inline constexpr std::uintptr_t kStartupParticle2RegistrationFunctionRvaV1 =
    0x1DABD50;
inline constexpr std::size_t kStartupParticle2RegistrationPrologueBytesV1 =
    0x1D;
inline constexpr std::uintptr_t kStartupParticle2NullGuardPatchRvaV1 =
    0x1DABD6D;
inline constexpr std::uintptr_t kStartupParticle2NullGuardContinueRvaV1 =
    0x1DABD82;
inline constexpr std::uintptr_t kStartupParticle2NullGuardSkipRvaV1 =
    0x1DABEA0;
inline constexpr std::uintptr_t kStartupParticle2RootSlotRvaV1 = 0x570F908;
inline constexpr std::size_t kStartupParticle2SlotBaseOffsetV1 = 0xA8;
inline constexpr std::size_t kStartupParticle2SlotStrideV1 = 8;
inline constexpr std::uint32_t kStartupParticle2SlotCountV1 = 8;
inline constexpr std::uint32_t kStartupParticle2NoSuppressedIndexV1 =
    0xFFFFFFFFU;

inline constexpr std::size_t kStartupParticle2NullGuardPatchBytesV1 = 13;
inline constexpr std::size_t kStartupParticle2NullGuardPatchAnchorBytesV1 = 21;
inline constexpr std::size_t kStartupParticle2NullGuardStubBytesV1 = 130;
inline constexpr bool kStartupParticle2NullGuardInstalledByDefaultV1 = false;

enum StartupParticle2NullGuardFailureV1 : std::uint32_t {
  startup_particle2_null_guard_failure_none = 0,
  startup_particle2_null_guard_failure_exact_build = 1U << 0,
  startup_particle2_null_guard_failure_primary_thread_suspended = 1U << 1,
  startup_particle2_null_guard_failure_unsupported_override = 1U << 2,
  startup_particle2_null_guard_failure_already_installed = 1U << 3,
  startup_particle2_null_guard_failure_anchor = 1U << 4,
  startup_particle2_null_guard_failure_allocation = 1U << 5,
  startup_particle2_null_guard_failure_stub_protection = 1U << 6,
  startup_particle2_null_guard_failure_target_protection = 1U << 7,
  startup_particle2_null_guard_failure_target_identity = 1U << 8,
  startup_particle2_null_guard_failure_flush = 1U << 9,
  startup_particle2_null_guard_failure_rollback = 1U << 10,
};

using StartupParticle2VirtualAllocV1 = void *(*)(
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using StartupParticle2VirtualFreeV1 = bool (*)(
    void *context, void *address, std::size_t size,
    DWORD free_type) noexcept;
using StartupParticle2VirtualProtectV1 = bool (*)(
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using StartupParticle2FlushInstructionCacheV1 = bool (*)(
    void *context, const void *address, std::size_t size) noexcept;

// Overrides are an offline-test seam only. Production must provide exactly the
// admitted module base while its newly-created primary thread is suspended.
struct StartupParticle2NullGuardV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;

  std::uintptr_t patch_target_override = 0;
  std::uintptr_t root_slot_address_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t skip_target_override = 0;

  void *memory_context = nullptr;
  StartupParticle2VirtualAllocV1 virtual_alloc_override = nullptr;
  StartupParticle2VirtualFreeV1 virtual_free_override = nullptr;
  StartupParticle2VirtualProtectV1 virtual_protect_override = nullptr;
  StartupParticle2FlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

// The state address must remain stable from installation through uninstall.
// The generated no-call stub embeds addresses of the three diagnostic atomics.
struct StartupParticle2NullGuardV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      startup_particle2_null_guard_failure_none};
  alignas(8) std::atomic<std::uint64_t> suppressed_count{0};
  alignas(4) std::atomic<std::uint32_t> suppressed_index_mask{0};
  alignas(4) std::atomic<std::uint32_t> last_suppressed_index{
      kStartupParticle2NoSuppressedIndexV1};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t root_slot_address = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t skip_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kStartupParticle2NullGuardPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kStartupParticle2NullGuardPatchBytesV1>
      installed_patch_bytes{};

  void *memory_context = nullptr;
  StartupParticle2VirtualFreeV1 virtual_free = nullptr;
  StartupParticle2VirtualProtectV1 virtual_protect = nullptr;
  StartupParticle2FlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

struct StartupParticle2NullGuardV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = startup_particle2_null_guard_failure_none;
  std::uint64_t suppressed_count = 0;
  std::uint32_t suppressed_index_mask = 0;
  std::uint32_t last_suppressed_index =
      kStartupParticle2NoSuppressedIndexV1;
};

bool InstallStartupParticle2NullGuardV1(
    StartupParticle2NullGuardV1State &state,
    const StartupParticle2NullGuardV1Environment &environment) noexcept;

// The caller must again prove quiescence externally before uninstalling. A
// failed restore retains the executable stub and reports rollback failure.
bool UninstallStartupParticle2NullGuardV1(
    StartupParticle2NullGuardV1State &state) noexcept;

StartupParticle2NullGuardV1Diagnostics
ReadStartupParticle2NullGuardV1Diagnostics(
    const StartupParticle2NullGuardV1State &state) noexcept;

} // namespace xar::bridge
