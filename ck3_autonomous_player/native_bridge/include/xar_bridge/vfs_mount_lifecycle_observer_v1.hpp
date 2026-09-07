#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kVfsMountLifecycleCoreInitCallRvaV1 =
    0x07E7136;
inline constexpr std::uintptr_t kVfsMountLifecycleCoreInitTargetRvaV1 =
    0x3B5C410;
inline constexpr std::uintptr_t kVfsMountLifecyclePublisherEntryRvaV1 =
    0x3BE18C0;
inline constexpr std::uintptr_t kVfsMountLifecyclePublisherEntryContinueRvaV1 =
    0x3BE18C5;
inline constexpr std::uintptr_t kVfsMountLifecyclePublisherReturnRvaV1 =
    0x3BE1A07;
inline constexpr std::uintptr_t kVfsMountLifecyclePublisherReturnContinueRvaV1 =
    0x3BE1A0C;
inline constexpr std::uintptr_t kVfsMountLifecycleSettingsLookupRvaV1 =
    0x3BE239C;
inline constexpr std::uintptr_t kVfsMountLifecycleSettingsLookupContinueRvaV1 =
    0x3BE23A4;
inline constexpr std::uintptr_t kVfsMountLifecycleManagerRvaV1 = 0x585FA30;
inline constexpr std::size_t kVfsMountLifecycleHookCountV1 = 4;
inline constexpr std::size_t kVfsMountLifecycleMaximumPatchBytesV1 = 8;
inline constexpr std::size_t kVfsMountLifecycleStubAllocationBytesV1 = 4096;
inline constexpr std::size_t kVfsMountLifecyclePublisherSlotsV1 = 64;
inline constexpr std::size_t kVfsMountLifecyclePathPreviewBytesV1 = 64;
inline constexpr bool kVfsMountLifecycleObserverInstalledByDefaultV1 = false;

enum VfsSettingsPathV1 : std::uint32_t {
  vfs_settings_path_unknown = 0,
  vfs_settings_path_paths = 1,
  vfs_settings_path_checksummed = 2,
};

enum VfsMountLifecycleObserverFailureV1 : std::uint32_t {
  vfs_mount_lifecycle_observer_failure_none = 0,
  vfs_mount_lifecycle_observer_failure_exact_build = 1U << 0,
  vfs_mount_lifecycle_observer_failure_primary_thread_suspended = 1U << 1,
  vfs_mount_lifecycle_observer_failure_unsupported_override = 1U << 2,
  vfs_mount_lifecycle_observer_failure_already_installed = 1U << 3,
  vfs_mount_lifecycle_observer_failure_anchor = 1U << 4,
  vfs_mount_lifecycle_observer_failure_allocation = 1U << 5,
  vfs_mount_lifecycle_observer_failure_stub_range = 1U << 6,
  vfs_mount_lifecycle_observer_failure_stub_protection = 1U << 7,
  vfs_mount_lifecycle_observer_failure_target_protection = 1U << 8,
  vfs_mount_lifecycle_observer_failure_target_identity = 1U << 9,
  vfs_mount_lifecycle_observer_failure_flush = 1U << 10,
  vfs_mount_lifecycle_observer_failure_rollback = 1U << 11,
};

using VfsMountLifecycleVirtualAllocNearV1 = void *(*) (
    void *context, std::uintptr_t lower_bound, std::uintptr_t upper_bound,
    std::size_t size, DWORD allocation_type, DWORD protection) noexcept;
using VfsMountLifecycleVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using VfsMountLifecycleVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using VfsMountLifecycleFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct VfsMountLifecycleObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::array<std::uintptr_t, kVfsMountLifecycleHookCountV1>
      patch_target_overrides{};
  std::uintptr_t core_init_target_override = 0;
  std::uintptr_t publisher_entry_continue_override = 0;
  std::uintptr_t publisher_return_continue_override = 0;
  std::uintptr_t settings_lookup_continue_override = 0;
  std::uintptr_t manager_address_override = 0;
  void *memory_context = nullptr;
  VfsMountLifecycleVirtualAllocNearV1 virtual_alloc_near_override = nullptr;
  VfsMountLifecycleVirtualFreeV1 virtual_free_override = nullptr;
  VfsMountLifecycleVirtualProtectV1 virtual_protect_override = nullptr;
  VfsMountLifecycleFlushInstructionCacheV1 flush_instruction_cache_override =
      nullptr;
};

struct VfsMountManagerObservationV1 {
  std::atomic<std::uint64_t> manager{0};
  std::atomic<std::uint64_t> head{0};
  std::atomic<std::uint32_t> ready_flag{0};
  std::atomic<std::uint32_t> read_fault{0};
};

struct VfsMountPathObservationV1 {
  std::atomic<std::uint64_t> pointer{0};
  std::atomic<std::uint32_t> preview_length{0};
  std::atomic<std::uint32_t> terminated{0};
  std::atomic<std::uint32_t> null_pointer{0};
  std::atomic<std::uint32_t> read_fault{0};
  std::array<std::atomic<std::uint64_t>,
             kVfsMountLifecyclePathPreviewBytesV1 / sizeof(std::uint64_t)>
      preview{};
};

struct VfsCoreInitObservationV1 {
  std::atomic<std::uint64_t> count{0};
  std::atomic<std::uint32_t> raw_al{0};
  std::atomic<std::uint32_t> thread_id{0};
  std::atomic<std::uint64_t> sequence{0};
  VfsMountManagerObservationV1 manager{};
};

struct VfsMountPublisherSlotV1 {
  std::atomic<std::uint64_t> published_ordinal{0};
  std::atomic<std::uint64_t> entry_sequence{0};
  std::atomic<std::uint64_t> return_sequence{0};
  std::atomic<std::uint32_t> entry_thread_id{0};
  std::atomic<std::uint32_t> return_thread_id{0};
  std::atomic<std::uint32_t> return_seen{0};
  std::atomic<std::uint32_t> raw_result{0};
  std::atomic<std::uint64_t> raw_rcx{0};
  std::atomic<std::uint64_t> backend{0};
  std::atomic<std::uint32_t> insert_mode{0};
  VfsMountPathObservationV1 path{};
  VfsMountManagerObservationV1 manager_before{};
  VfsMountManagerObservationV1 manager_after{};
};

struct VfsSettingsLookupObservationV1 {
  std::atomic<std::uint64_t> count{0};
  std::atomic<std::uint64_t> path_view{0};
  std::atomic<std::uint64_t> path_data{0};
  std::atomic<std::uint32_t> path_length{0};
  std::atomic<std::uint32_t> path_flag{0};
  std::atomic<std::uint32_t> thread_id{0};
  std::atomic<std::uint32_t> read_fault{0};
  std::atomic<std::uint64_t> sequence{0};
  VfsMountManagerObservationV1 manager{};
};

struct VfsMountLifecycleHookStateV1 {
  std::uintptr_t patch_target = 0;
  std::size_t patch_size = 0;
  std::array<std::uint8_t, kVfsMountLifecycleMaximumPatchBytesV1> original{};
  std::array<std::uint8_t, kVfsMountLifecycleMaximumPatchBytesV1>
      installed_patch{};
};

struct VfsMountLifecycleObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> installed_mask{0};
  std::atomic<std::uint32_t> failure_flags{
      vfs_mount_lifecycle_observer_failure_none};
  std::atomic<std::uint64_t> next_sequence{0};
  VfsCoreInitObservationV1 core_init{};
  std::atomic<std::uint64_t> publisher_entry_count{0};
  std::atomic<std::uint64_t> publisher_return_count{0};
  std::atomic<std::uint64_t> publisher_success_count{0};
  std::atomic<std::uint64_t> publisher_failure_count{0};
  std::atomic<std::uint64_t> publisher_correlation_miss_count{0};
  std::atomic<std::uint64_t> publisher_slot_overwrite_count{0};
  std::atomic<std::uint64_t> last_publisher_entry_sequence{0};
  std::atomic<std::uint64_t> last_publisher_return_sequence{0};
  std::array<VfsMountPublisherSlotV1, kVfsMountLifecyclePublisherSlotsV1>
      publisher_slots{};
  VfsSettingsLookupObservationV1 paths_lookup{};
  VfsSettingsLookupObservationV1 checksummed_lookup{};
  std::atomic<std::uint64_t> lookup_classification_fault_count{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t core_init_target = 0;
  std::uintptr_t publisher_entry_continue = 0;
  std::uintptr_t publisher_return_continue = 0;
  std::uintptr_t settings_lookup_continue = 0;
  std::uintptr_t manager_address = 0;
  std::array<VfsMountLifecycleHookStateV1,
             kVfsMountLifecycleHookCountV1>
      hooks{};
  void *stub_allocation = nullptr;
  void *memory_context = nullptr;
  VfsMountLifecycleVirtualFreeV1 virtual_free = nullptr;
  VfsMountLifecycleVirtualProtectV1 virtual_protect = nullptr;
  VfsMountLifecycleFlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

struct VfsMountManagerDiagnosticsV1 {
  std::uint64_t manager = 0;
  std::uint64_t head = 0;
  std::uint32_t ready_flag = 0;
  bool read_fault = false;
};

struct VfsMountPathDiagnosticsV1 {
  std::uint64_t pointer = 0;
  std::uint32_t preview_length = 0;
  bool terminated = false;
  bool null_pointer = false;
  bool read_fault = false;
  std::array<std::uint8_t, kVfsMountLifecyclePathPreviewBytesV1> preview{};
};

struct VfsMountPublisherDiagnosticsV1 {
  std::uint64_t ordinal = 0;
  std::uint64_t entry_sequence = 0;
  std::uint64_t return_sequence = 0;
  std::uint32_t entry_thread_id = 0;
  std::uint32_t return_thread_id = 0;
  bool return_seen = false;
  std::uint32_t raw_result = 0;
  std::uint64_t raw_rcx = 0;
  std::uint64_t backend = 0;
  std::uint32_t insert_mode = 0;
  VfsMountPathDiagnosticsV1 path{};
  VfsMountManagerDiagnosticsV1 manager_before{};
  VfsMountManagerDiagnosticsV1 manager_after{};
};

struct VfsSettingsLookupDiagnosticsV1 {
  std::uint64_t count = 0;
  std::uint64_t path_view = 0;
  std::uint64_t path_data = 0;
  std::uint32_t path_length = 0;
  std::uint32_t path_flag = 0;
  std::uint32_t thread_id = 0;
  bool read_fault = false;
  std::uint64_t sequence = 0;
  VfsMountManagerDiagnosticsV1 manager{};
};

struct VfsMountLifecycleObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t installed_mask = 0;
  std::uint32_t failure_flags = 0;
  std::uint64_t next_sequence = 0;
  std::uint64_t core_init_count = 0;
  std::uint32_t core_init_raw_al = 0;
  std::uint32_t core_init_thread_id = 0;
  std::uint64_t core_init_sequence = 0;
  VfsMountManagerDiagnosticsV1 core_init_manager{};
  std::uint64_t publisher_entry_count = 0;
  std::uint64_t publisher_return_count = 0;
  std::uint64_t publisher_success_count = 0;
  std::uint64_t publisher_failure_count = 0;
  std::uint64_t publisher_correlation_miss_count = 0;
  std::uint64_t publisher_slot_overwrite_count = 0;
  VfsMountPublisherDiagnosticsV1 latest_publisher{};
  VfsSettingsLookupDiagnosticsV1 paths_lookup{};
  VfsSettingsLookupDiagnosticsV1 checksummed_lookup{};
  std::uint64_t lookup_classification_fault_count = 0;
};

bool InstallVfsMountLifecycleObserverV1(
    VfsMountLifecycleObserverV1State &state,
    const VfsMountLifecycleObserverEnvironmentV1 &environment) noexcept;
bool UninstallVfsMountLifecycleObserverV1(
    VfsMountLifecycleObserverV1State &state) noexcept;
VfsMountLifecycleObserverV1Diagnostics
ReadVfsMountLifecycleObserverV1Diagnostics(
    const VfsMountLifecycleObserverV1State &state) noexcept;

void RecordVfsCoreInitReturnV1(VfsMountLifecycleObserverV1State &state,
                               std::uintptr_t raw_result,
                               std::uint32_t thread_id) noexcept;
void RecordVfsMountPublisherEnterV1(
    VfsMountLifecycleObserverV1State &state, std::uintptr_t raw_rcx,
    std::uintptr_t path, std::uintptr_t backend, std::uint32_t insert_mode,
    std::uint32_t thread_id) noexcept;
void RecordVfsMountPublisherReturnV1(
    VfsMountLifecycleObserverV1State &state, std::uint32_t raw_result,
    std::uint32_t thread_id) noexcept;
void RecordVfsSettingsLookupV1(VfsMountLifecycleObserverV1State &state,
                               std::uintptr_t path_view,
                               std::uintptr_t manager,
                               std::uint32_t thread_id) noexcept;

} // namespace xar::bridge
