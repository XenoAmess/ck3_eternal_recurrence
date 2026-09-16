#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kPhysfsMountedDataCallRvaV1 = 0x3B5CE1D;
inline constexpr std::uintptr_t kPhysfsMountedDataPublisherRvaV1 = 0x3BE18C0;
inline constexpr std::uintptr_t kPhysfsMountedDataLogLiteralRvaV1 = 0x4556E50;
inline constexpr std::size_t kPhysfsMountedDataPatchBytesV1 = 5;
inline constexpr std::size_t kPhysfsMountedDataStubBytesV1 = 4096;
inline constexpr std::size_t kPhysfsMountedDataSlotsV1 = 128;
inline constexpr std::size_t kPhysfsMountedDataPathBytesV1 = 256;
inline constexpr bool kPhysfsMountedDataObserverInstalledByDefaultV1 = false;

enum PhysfsMountedDataObserverFailureV1 : std::uint32_t {
  physfs_mounted_data_observer_failure_none = 0,
  physfs_mounted_data_observer_failure_exact_build = 1U << 0,
  physfs_mounted_data_observer_failure_primary_thread_suspended = 1U << 1,
  physfs_mounted_data_observer_failure_unsupported_override = 1U << 2,
  physfs_mounted_data_observer_failure_already_installed = 1U << 3,
  physfs_mounted_data_observer_failure_anchor = 1U << 4,
  physfs_mounted_data_observer_failure_allocation = 1U << 5,
  physfs_mounted_data_observer_failure_stub_range = 1U << 6,
  physfs_mounted_data_observer_failure_stub_protection = 1U << 7,
  physfs_mounted_data_observer_failure_target_protection = 1U << 8,
  physfs_mounted_data_observer_failure_target_identity = 1U << 9,
  physfs_mounted_data_observer_failure_flush = 1U << 10,
  physfs_mounted_data_observer_failure_rollback = 1U << 11,
};

using PhysfsMountedDataVirtualAllocNearV1 = void *(*) (
    void *context, std::uintptr_t lower_bound, std::uintptr_t upper_bound,
    std::size_t size, DWORD allocation_type, DWORD protection) noexcept;
using PhysfsMountedDataVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using PhysfsMountedDataVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using PhysfsMountedDataFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct PhysfsMountedDataObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t publisher_target_override = 0;
  void *memory_context = nullptr;
  PhysfsMountedDataVirtualAllocNearV1 virtual_alloc_near_override = nullptr;
  PhysfsMountedDataVirtualFreeV1 virtual_free_override = nullptr;
  PhysfsMountedDataVirtualProtectV1 virtual_protect_override = nullptr;
  PhysfsMountedDataFlushInstructionCacheV1 flush_instruction_cache_override =
      nullptr;
};

struct PhysfsMountedDataSlotV1 {
  std::atomic<std::uint64_t> published_ordinal{0};
  std::atomic<std::uint32_t> thread_id{0};
  std::atomic<std::uint32_t> raw_result{0};
  std::atomic<std::uint32_t> preview_length{0};
  std::atomic<std::uint32_t> terminated{0};
  std::atomic<std::uint32_t> null_pointer{0};
  std::atomic<std::uint32_t> read_fault{0};
  std::array<std::atomic<std::uint64_t>,
             kPhysfsMountedDataPathBytesV1 / sizeof(std::uint64_t)>
      preview{};
};

struct PhysfsMountedDataObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      physfs_mounted_data_observer_failure_none};
  std::atomic<std::uint64_t> call_count{0};
  std::atomic<std::uint64_t> success_count{0};
  std::atomic<std::uint64_t> failure_count{0};
  std::atomic<std::uint64_t> slot_overwrite_count{0};
  std::array<PhysfsMountedDataSlotV1, kPhysfsMountedDataSlotsV1> slots{};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t publisher_target = 0;
  std::array<std::uint8_t, kPhysfsMountedDataPatchBytesV1> original{};
  std::array<std::uint8_t, kPhysfsMountedDataPatchBytesV1> installed_patch{};
  void *stub_allocation = nullptr;
  void *memory_context = nullptr;
  PhysfsMountedDataVirtualFreeV1 virtual_free = nullptr;
  PhysfsMountedDataVirtualProtectV1 virtual_protect = nullptr;
  PhysfsMountedDataFlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

struct PhysfsMountedDataRowDiagnosticsV1 {
  std::uint64_t ordinal = 0;
  std::uint32_t thread_id = 0;
  std::uint32_t raw_result = 0;
  bool success = false;
  std::uint32_t preview_length = 0;
  bool terminated = false;
  bool null_pointer = false;
  bool read_fault = false;
  std::array<std::uint8_t, kPhysfsMountedDataPathBytesV1> preview{};
};

struct PhysfsMountedDataObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = 0;
  std::uint64_t call_count = 0;
  std::uint64_t success_count = 0;
  std::uint64_t failure_count = 0;
  std::uint64_t slot_overwrite_count = 0;
  std::size_t row_count = 0;
  std::array<PhysfsMountedDataRowDiagnosticsV1, kPhysfsMountedDataSlotsV1>
      rows{};
};

bool InstallPhysfsMountedDataObserverV1(
    PhysfsMountedDataObserverV1State &state,
    const PhysfsMountedDataObserverEnvironmentV1 &environment) noexcept;
bool UninstallPhysfsMountedDataObserverV1(
    PhysfsMountedDataObserverV1State &state) noexcept;
PhysfsMountedDataObserverV1Diagnostics
ReadPhysfsMountedDataObserverV1Diagnostics(
    const PhysfsMountedDataObserverV1State &state) noexcept;
void RecordPhysfsMountedDataV1(PhysfsMountedDataObserverV1State &state,
                               std::uintptr_t path,
                               std::uint32_t raw_result,
                               std::uint32_t thread_id) noexcept;

} // namespace xar::bridge
