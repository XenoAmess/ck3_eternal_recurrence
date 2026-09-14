#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t
    kStewardDevelopCountyEnumeratorObserverPatchRvaV1 = 0x1056289;
inline constexpr std::uintptr_t
    kStewardDevelopCountyEnumeratorObserverCallRvaV1 = 0x105629C;
inline constexpr std::uintptr_t
    kStewardDevelopCountyEnumeratorObserverContinueRvaV1 = 0x10562A1;
inline constexpr std::uintptr_t
    kStewardDevelopCountyEnumeratorRvaV1 = 0x105B6A0;
inline constexpr std::size_t
    kStewardDevelopCountyEnumeratorObserverPatchBytesV1 = 24;
inline constexpr std::size_t
    kStewardDevelopCountyEnumeratorObserverStubCapacityV1 = 192;
inline constexpr std::size_t
    kStewardDevelopCountyEnumeratorObserverMaxRowsV1 = 32;
inline constexpr bool
    kStewardDevelopCountyEnumeratorObserverInstalledByDefaultV1 = false;

enum StewardDevelopCountyEnumeratorObserverFailureV1 : std::uint32_t {
  steward_develop_county_enumerator_observer_failure_none = 0,
  steward_develop_county_enumerator_observer_failure_exact_build = 1U << 0,
  steward_develop_county_enumerator_observer_failure_primary_thread_suspended =
      1U << 1,
  steward_develop_county_enumerator_observer_failure_unsupported_override =
      1U << 2,
  steward_develop_county_enumerator_observer_failure_already_installed =
      1U << 3,
  steward_develop_county_enumerator_observer_failure_anchor = 1U << 4,
  steward_develop_county_enumerator_observer_failure_allocation = 1U << 5,
  steward_develop_county_enumerator_observer_failure_stub_protection = 1U << 6,
  steward_develop_county_enumerator_observer_failure_target_protection =
      1U << 7,
  steward_develop_county_enumerator_observer_failure_target_identity = 1U << 8,
  steward_develop_county_enumerator_observer_failure_flush = 1U << 9,
  steward_develop_county_enumerator_observer_failure_rollback = 1U << 10,
};

using StewardDevelopCountyEnumeratorObserverVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using StewardDevelopCountyEnumeratorObserverVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using StewardDevelopCountyEnumeratorObserverVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using StewardDevelopCountyEnumeratorObserverFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct StewardDevelopCountyEnumeratorObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t enumerator_target_override = 0;
  void *memory_context = nullptr;
  StewardDevelopCountyEnumeratorObserverVirtualAllocV1 virtual_alloc_override =
      nullptr;
  StewardDevelopCountyEnumeratorObserverVirtualFreeV1 virtual_free_override =
      nullptr;
  StewardDevelopCountyEnumeratorObserverVirtualProtectV1
      virtual_protect_override = nullptr;
  StewardDevelopCountyEnumeratorObserverFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

struct StewardDevelopCountyEnumeratorRawRowV1 {
  std::uintptr_t candidate = 0;
  std::uintptr_t task_type = 0;
  std::uintptr_t query_owner = 0;
};

struct StewardDevelopCountyEnumeratorObservationV1 {
  std::atomic<std::uint64_t> call_count{0};
  std::atomic<std::uint64_t> task_key_read_failure_count{0};
  std::atomic<std::uint64_t> capture_read_failure_count{0};
  std::atomic<std::uint64_t> develop_capture_count{0};
  std::atomic<std::uint64_t> last_task_type{0};
  std::atomic<std::uint64_t> last_gui_task_state{0};
  std::atomic<std::uint32_t> last_scope_word0{0};
  std::atomic<std::uint32_t> last_scope_word1{0};
  std::atomic<std::uint64_t> last_vector_data{0};
  std::atomic<std::int32_t> last_vector_capacity{0};
  std::atomic<std::int32_t> last_vector_count{0};
  std::atomic<std::uint32_t> last_captured_row_count{0};
  std::atomic<std::uint32_t> last_rows_truncated{0};
  std::array<std::atomic<std::uint64_t>,
             kStewardDevelopCountyEnumeratorObserverMaxRowsV1>
      last_candidate_pointers{};
  std::array<std::atomic<std::uint64_t>,
             kStewardDevelopCountyEnumeratorObserverMaxRowsV1>
      last_row_task_types{};
  std::array<std::atomic<std::uint64_t>,
             kStewardDevelopCountyEnumeratorObserverMaxRowsV1>
      last_row_query_owners{};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};
};

struct StewardDevelopCountyEnumeratorObserverStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      steward_develop_county_enumerator_observer_failure_none};
  StewardDevelopCountyEnumeratorObservationV1 observation{};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t enumerator_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t,
             kStewardDevelopCountyEnumeratorObserverPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t,
             kStewardDevelopCountyEnumeratorObserverPatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  StewardDevelopCountyEnumeratorObserverVirtualFreeV1 virtual_free = nullptr;
  StewardDevelopCountyEnumeratorObserverVirtualProtectV1 virtual_protect =
      nullptr;
  StewardDevelopCountyEnumeratorObserverFlushInstructionCacheV1
      flush_instruction_cache = nullptr;
};

struct StewardDevelopCountyEnumeratorObservationDiagnosticsV1 {
  std::uint64_t call_count = 0;
  std::uint64_t task_key_read_failure_count = 0;
  std::uint64_t capture_read_failure_count = 0;
  std::uint64_t develop_capture_count = 0;
  std::uint64_t last_task_type = 0;
  std::uint64_t last_gui_task_state = 0;
  std::uint32_t last_scope_word0 = 0;
  std::uint32_t last_scope_word1 = 0;
  std::uint64_t last_vector_data = 0;
  std::int32_t last_vector_capacity = 0;
  std::int32_t last_vector_count = 0;
  std::uint32_t last_captured_row_count = 0;
  bool last_rows_truncated = false;
  std::array<StewardDevelopCountyEnumeratorRawRowV1,
             kStewardDevelopCountyEnumeratorObserverMaxRowsV1>
      rows{};
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
};

struct StewardDevelopCountyEnumeratorObserverDiagnosticsV1 {
  bool installed = false;
  std::uint32_t failure_flags =
      steward_develop_county_enumerator_observer_failure_none;
  StewardDevelopCountyEnumeratorObservationDiagnosticsV1 observation{};
};

bool InstallStewardDevelopCountyEnumeratorObserverV1(
    StewardDevelopCountyEnumeratorObserverStateV1 &state,
    const StewardDevelopCountyEnumeratorObserverEnvironmentV1
        &environment) noexcept;
bool UninstallStewardDevelopCountyEnumeratorObserverV1(
    StewardDevelopCountyEnumeratorObserverStateV1 &state) noexcept;
StewardDevelopCountyEnumeratorObserverDiagnosticsV1
ReadStewardDevelopCountyEnumeratorObserverDiagnosticsV1(
    const StewardDevelopCountyEnumeratorObserverStateV1 &state) noexcept;

bool CaptureStewardDevelopCountyEnumeratorPostCallV1(
    StewardDevelopCountyEnumeratorObserverStateV1 &state,
    std::uintptr_t task_type, std::uintptr_t gui_task_state,
    std::uint32_t thread_id, std::uint64_t timestamp_qpc) noexcept;

void RecordStewardDevelopCountyEnumeratorObservationV1(
    StewardDevelopCountyEnumeratorObserverStateV1 &state,
    bool task_key_readable, bool task_is_develop_county,
    bool capture_readable,
    std::uintptr_t task_type, std::uintptr_t gui_task_state,
    std::uint32_t scope_word0, std::uint32_t scope_word1,
    std::uintptr_t vector_data, std::int32_t vector_capacity,
    std::int32_t vector_count,
    const StewardDevelopCountyEnumeratorRawRowV1 *rows,
    std::uint32_t captured_row_count, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
