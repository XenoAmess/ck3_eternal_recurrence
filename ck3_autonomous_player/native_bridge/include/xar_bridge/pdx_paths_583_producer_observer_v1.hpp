#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kPdxPaths583TaskPatchRvaV1 = 0x3B96A2E;
inline constexpr std::uintptr_t kPdxPaths583TaskContinueRvaV1 = 0x3B96A33;
inline constexpr std::uintptr_t kPdxPaths583PathsLookupCallRvaV1 = 0x3B96A4E;
inline constexpr std::uintptr_t kPdxPaths583ChecksummedLookupCallRvaV1 =
    0x3B96B62;
inline constexpr std::uintptr_t kPdxPaths583LookupTargetRvaV1 = 0x3BE2340;
inline constexpr std::uintptr_t kPdxPaths583ParserPatchRvaV1 = 0x3B96531;
inline constexpr std::uintptr_t kPdxPaths583ParserContinueRvaV1 = 0x3B96536;
inline constexpr std::uintptr_t kPdxPaths583InsertCallRvaV1 = 0x3B96897;
inline constexpr std::uintptr_t kPdxPaths583InsertTargetRvaV1 = 0x253A9F0;
inline constexpr std::uintptr_t kPdxPaths583MapRvaV1 = 0x5764698;
inline constexpr std::uintptr_t kPdxPaths583PathsLiteralRvaV1 = 0x4558570;
inline constexpr std::uintptr_t kPdxPaths583ChecksummedLiteralRvaV1 =
    0x45584B0;
inline constexpr std::uint32_t kPdxPaths583NamedPathIdV1 = 0x583;
inline constexpr std::uint32_t kPdxPaths583NamedPathHashV1 = 0xC0242C1D;
inline constexpr std::size_t kPdxPaths583HookCountV1 = 5;
inline constexpr std::size_t kPdxPaths583PatchBytesV1 = 5;
inline constexpr std::size_t kPdxPaths583StubAllocationBytesV1 = 4096;
inline constexpr bool kPdxPaths583ProducerObserverInstalledByDefaultV1 = false;

enum PdxPaths583SourceV1 : std::uint32_t {
  pdx_paths_583_source_unknown = 0,
  pdx_paths_583_source_paths = 1,
  pdx_paths_583_source_checksummed = 2,
};

enum PdxPaths583ProducerObserverFailureV1 : std::uint32_t {
  pdx_paths_583_producer_observer_failure_none = 0,
  pdx_paths_583_producer_observer_failure_exact_build = 1U << 0,
  pdx_paths_583_producer_observer_failure_primary_thread_suspended = 1U << 1,
  pdx_paths_583_producer_observer_failure_unsupported_override = 1U << 2,
  pdx_paths_583_producer_observer_failure_already_installed = 1U << 3,
  pdx_paths_583_producer_observer_failure_anchor = 1U << 4,
  pdx_paths_583_producer_observer_failure_allocation = 1U << 5,
  pdx_paths_583_producer_observer_failure_stub_range = 1U << 6,
  pdx_paths_583_producer_observer_failure_stub_protection = 1U << 7,
  pdx_paths_583_producer_observer_failure_target_protection = 1U << 8,
  pdx_paths_583_producer_observer_failure_target_identity = 1U << 9,
  pdx_paths_583_producer_observer_failure_flush = 1U << 10,
  pdx_paths_583_producer_observer_failure_rollback = 1U << 11,
};

using PdxPaths583VirtualAllocNearV1 = void *(*) (
    void *context, std::uintptr_t lower_bound, std::uintptr_t upper_bound,
    std::size_t size, DWORD allocation_type, DWORD protection) noexcept;
using PdxPaths583VirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using PdxPaths583VirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using PdxPaths583FlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct PdxPaths583ProducerObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::array<std::uintptr_t, kPdxPaths583HookCountV1>
      patch_target_overrides{};
  std::uintptr_t task_continue_target_override = 0;
  std::uintptr_t parser_continue_target_override = 0;
  std::uintptr_t lookup_target_override = 0;
  std::uintptr_t insert_target_override = 0;
  std::uintptr_t map_address_override = 0;
  void *memory_context = nullptr;
  PdxPaths583VirtualAllocNearV1 virtual_alloc_near_override = nullptr;
  PdxPaths583VirtualFreeV1 virtual_free_override = nullptr;
  PdxPaths583VirtualProtectV1 virtual_protect_override = nullptr;
  PdxPaths583FlushInstructionCacheV1 flush_instruction_cache_override =
      nullptr;
};

struct PdxPaths583TableObservationV1 {
  std::atomic<std::uint64_t> map{0};
  std::atomic<std::uint64_t> rows{0};
  std::atomic<std::uint64_t> count{0};
  std::atomic<std::uint32_t> mask{0};
  std::atomic<std::uint32_t> max_probe{0};
  std::atomic<std::uint32_t> id_583_present{0};
  std::atomic<std::uint64_t> id_583_row{0};
  std::atomic<std::uint32_t> read_fault{0};
};

struct PdxPaths583LookupObservationV1 {
  std::atomic<std::uint64_t> pre_count{0};
  std::atomic<std::uint64_t> return_count{0};
  std::atomic<std::uint64_t> raw_result{0};
  std::atomic<std::uint32_t> null_result{0};
  std::atomic<std::uint32_t> thread_id{0};
  std::atomic<std::uint64_t> sequence{0};
};

struct PdxPaths583HookStateV1 {
  std::uintptr_t patch_target = 0;
  std::array<std::uint8_t, kPdxPaths583PatchBytesV1> original{};
  std::array<std::uint8_t, kPdxPaths583PatchBytesV1> installed_patch{};
};

struct PdxPaths583ProducerObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> installed_mask{0};
  std::atomic<std::uint32_t> failure_flags{
      pdx_paths_583_producer_observer_failure_none};
  std::atomic<std::uint64_t> next_sequence{0};
  std::atomic<std::uint64_t> task_enter_count{0};
  std::atomic<std::uint32_t> task_thread_id{0};
  std::atomic<std::uint64_t> task_sequence{0};
  PdxPaths583TableObservationV1 task_table{};
  PdxPaths583LookupObservationV1 paths_lookup{};
  PdxPaths583LookupObservationV1 checksummed_lookup{};
  std::atomic<std::uint64_t> paths_parser_enter_count{0};
  std::atomic<std::uint64_t> checksummed_parser_enter_count{0};
  std::atomic<std::uint64_t> other_parser_enter_count{0};
  std::atomic<std::uint64_t> parser_source{0};
  std::atomic<std::uint32_t> parser_thread_id{0};
  std::atomic<std::uint64_t> parser_sequence{0};
  std::atomic<std::uint64_t> insert_call_count{0};
  std::atomic<std::uint64_t> key_583_insert_pre_count{0};
  std::atomic<std::uint64_t> key_583_insert_post_count{0};
  std::atomic<std::uint64_t> key_read_fault_count{0};
  std::atomic<std::uint32_t> last_key{0};
  std::atomic<std::uint32_t> last_hash{0};
  std::atomic<std::uint32_t> insert_thread_id{0};
  std::atomic<std::uint64_t> insert_sequence{0};
  std::atomic<std::uint64_t> rhs_string{0};
  std::atomic<std::uint64_t> result_pair{0};
  std::atomic<std::uint64_t> native_result{0};
  std::atomic<std::uint64_t> result_row{0};
  std::atomic<std::uint32_t> result_inserted{0};
  std::atomic<std::uint32_t> result_pair_null{0};
  std::atomic<std::uint32_t> result_read_fault{0};
  PdxPaths583TableObservationV1 table_before{};
  PdxPaths583TableObservationV1 table_after{};

  std::uintptr_t module_base = 0;
  std::uintptr_t task_continue_target = 0;
  std::uintptr_t parser_continue_target = 0;
  std::uintptr_t lookup_target = 0;
  std::uintptr_t insert_target = 0;
  std::uintptr_t map_address = 0;
  std::array<PdxPaths583HookStateV1, kPdxPaths583HookCountV1> hooks{};
  void *stub_allocation = nullptr;
  void *memory_context = nullptr;
  PdxPaths583VirtualFreeV1 virtual_free = nullptr;
  PdxPaths583VirtualProtectV1 virtual_protect = nullptr;
  PdxPaths583FlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

struct PdxPaths583TableDiagnosticsV1 {
  std::uint64_t map = 0;
  std::uint64_t rows = 0;
  std::uint64_t count = 0;
  std::uint32_t mask = 0;
  std::uint32_t max_probe = 0;
  bool id_583_present = false;
  std::uint64_t id_583_row = 0;
  bool read_fault = false;
};

struct PdxPaths583LookupDiagnosticsV1 {
  std::uint64_t pre_count = 0;
  std::uint64_t return_count = 0;
  std::uint64_t raw_result = 0;
  bool null_result = false;
  std::uint32_t thread_id = 0;
  std::uint64_t sequence = 0;
};

struct PdxPaths583ProducerObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t installed_mask = 0;
  std::uint32_t failure_flags = 0;
  std::uint64_t task_enter_count = 0;
  std::uint32_t task_thread_id = 0;
  std::uint64_t task_sequence = 0;
  PdxPaths583TableDiagnosticsV1 task_table{};
  PdxPaths583LookupDiagnosticsV1 paths_lookup{};
  PdxPaths583LookupDiagnosticsV1 checksummed_lookup{};
  std::uint64_t paths_parser_enter_count = 0;
  std::uint64_t checksummed_parser_enter_count = 0;
  std::uint64_t other_parser_enter_count = 0;
  std::uint64_t parser_source = 0;
  std::uint32_t parser_thread_id = 0;
  std::uint64_t parser_sequence = 0;
  std::uint64_t insert_call_count = 0;
  std::uint64_t key_583_insert_pre_count = 0;
  std::uint64_t key_583_insert_post_count = 0;
  std::uint64_t key_read_fault_count = 0;
  std::uint32_t last_key = 0;
  std::uint32_t last_hash = 0;
  std::uint32_t insert_thread_id = 0;
  std::uint64_t insert_sequence = 0;
  std::uint64_t rhs_string = 0;
  std::uint64_t result_pair = 0;
  std::uint64_t native_result = 0;
  std::uint64_t result_row = 0;
  bool result_inserted = false;
  bool result_pair_null = false;
  bool result_read_fault = false;
  PdxPaths583TableDiagnosticsV1 table_before{};
  PdxPaths583TableDiagnosticsV1 table_after{};
};

bool InstallPdxPaths583ProducerObserverV1(
    PdxPaths583ProducerObserverV1State &state,
    const PdxPaths583ProducerObserverEnvironmentV1 &environment) noexcept;
bool UninstallPdxPaths583ProducerObserverV1(
    PdxPaths583ProducerObserverV1State &state) noexcept;
PdxPaths583ProducerObserverV1Diagnostics
ReadPdxPaths583ProducerObserverV1Diagnostics(
    const PdxPaths583ProducerObserverV1State &state) noexcept;

void RecordPdxPaths583TaskEnterV1(
    PdxPaths583ProducerObserverV1State &state,
    std::uint32_t thread_id) noexcept;
void RecordPdxPaths583LookupPreV1(
    PdxPaths583ProducerObserverV1State &state, PdxPaths583SourceV1 source,
    std::uint32_t thread_id) noexcept;
void RecordPdxPaths583LookupPostV1(
    PdxPaths583ProducerObserverV1State &state, PdxPaths583SourceV1 source,
    std::uintptr_t result, std::uint32_t thread_id) noexcept;
void RecordPdxPaths583ParserEnterV1(
    PdxPaths583ProducerObserverV1State &state, std::uintptr_t source,
    std::uint32_t thread_id) noexcept;
void RecordPdxPaths583InsertPreV1(
    PdxPaths583ProducerObserverV1State &state, std::uintptr_t map,
    std::uintptr_t result_pair, std::uint32_t hash,
    std::uintptr_t key_pointer, std::uintptr_t rhs_string,
    std::uint32_t thread_id) noexcept;
void RecordPdxPaths583InsertPostV1(
    PdxPaths583ProducerObserverV1State &state, std::uintptr_t map,
    std::uintptr_t result_pair, std::uint32_t hash,
    std::uintptr_t key_pointer, std::uintptr_t native_result,
    std::uint32_t thread_id) noexcept;

} // namespace xar::bridge
