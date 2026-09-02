#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kPhase2WrapperEntryObserverPatchRvaV1 =
    0x3B9E030;
inline constexpr std::uintptr_t kPhase2WrapperEntryObserverContinueRvaV1 =
    0x3B9E03F;
inline constexpr std::size_t kPhase2WrapperEntryObserverPatchBytesV1 = 15;
inline constexpr std::size_t kPhase2WrapperEntryObserverStubBytesV1 = 89;
inline constexpr bool kPhase2WrapperEntryObserverInstalledByDefaultV1 = false;

enum Phase2WrapperEntryObserverFailureV1 : std::uint32_t {
  phase2_wrapper_entry_observer_failure_none = 0,
  phase2_wrapper_entry_observer_failure_exact_build = 1U << 0,
  phase2_wrapper_entry_observer_failure_primary_thread_suspended = 1U << 1,
  phase2_wrapper_entry_observer_failure_unsupported_override = 1U << 2,
  phase2_wrapper_entry_observer_failure_already_installed = 1U << 3,
  phase2_wrapper_entry_observer_failure_anchor = 1U << 4,
  phase2_wrapper_entry_observer_failure_allocation = 1U << 5,
  phase2_wrapper_entry_observer_failure_stub_protection = 1U << 6,
  phase2_wrapper_entry_observer_failure_target_protection = 1U << 7,
  phase2_wrapper_entry_observer_failure_target_identity = 1U << 8,
  phase2_wrapper_entry_observer_failure_flush = 1U << 9,
  phase2_wrapper_entry_observer_failure_rollback = 1U << 10,
};

using Phase2WrapperEntryObserverVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using Phase2WrapperEntryObserverVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using Phase2WrapperEntryObserverVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using Phase2WrapperEntryObserverFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct Phase2WrapperEntryObserverV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  void *memory_context = nullptr;
  Phase2WrapperEntryObserverVirtualAllocV1 virtual_alloc_override = nullptr;
  Phase2WrapperEntryObserverVirtualFreeV1 virtual_free_override = nullptr;
  Phase2WrapperEntryObserverVirtualProtectV1 virtual_protect_override = nullptr;
  Phase2WrapperEntryObserverFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

struct Phase2WrapperEntryObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      phase2_wrapper_entry_observer_failure_none};
  std::atomic<std::uint64_t> entry_count{0};
  std::atomic<std::uint64_t> last_return_address{0};
  std::atomic<std::uint64_t> last_callsite_rva{0};
  std::atomic<std::uint64_t> last_scheduler_owner{0};
  std::atomic<std::uint64_t> last_producer_list{0};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kPhase2WrapperEntryObserverPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kPhase2WrapperEntryObserverPatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  Phase2WrapperEntryObserverVirtualFreeV1 virtual_free = nullptr;
  Phase2WrapperEntryObserverVirtualProtectV1 virtual_protect = nullptr;
  Phase2WrapperEntryObserverFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct Phase2WrapperEntryObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = phase2_wrapper_entry_observer_failure_none;
  std::uint64_t entry_count = 0;
  std::uint64_t last_return_address = 0;
  std::uint64_t last_callsite_rva = 0;
  std::uint64_t last_scheduler_owner = 0;
  std::uint64_t last_producer_list = 0;
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
};

bool InstallPhase2WrapperEntryObserverV1(
    Phase2WrapperEntryObserverV1State &state,
    const Phase2WrapperEntryObserverV1Environment &environment) noexcept;
bool UninstallPhase2WrapperEntryObserverV1(
    Phase2WrapperEntryObserverV1State &state) noexcept;
Phase2WrapperEntryObserverV1Diagnostics
ReadPhase2WrapperEntryObserverV1Diagnostics(
    const Phase2WrapperEntryObserverV1State &state) noexcept;

void RecordPhase2WrapperEntryObservationV1(
    Phase2WrapperEntryObserverV1State &state, std::uintptr_t return_address,
    std::uintptr_t scheduler_owner, std::uintptr_t producer_list,
    std::uint32_t thread_id, std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
