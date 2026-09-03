#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kPhase2WrapperConsumerEdgePatchRvaV1 =
    0x3B9DD50;
inline constexpr std::uintptr_t kPhase2WrapperConsumerEdgeContinueRvaV1 =
    0x3B9DD60;
inline constexpr std::uintptr_t kPhase2WrapperConsumerEdgeCallRva0V1 =
    0x3B9E10B;
inline constexpr std::uintptr_t kPhase2WrapperConsumerEdgeCallRva1V1 =
    0x3B9E175;
inline constexpr std::size_t kPhase2WrapperConsumerEdgePatchBytesV1 = 16;
inline constexpr std::size_t kPhase2WrapperConsumerEdgeStubBytesV1 = 87;
inline constexpr bool kPhase2WrapperConsumerEdgeInstalledByDefaultV1 = false;

enum Phase2WrapperConsumerEdgeFailureV1 : std::uint32_t {
  phase2_wrapper_consumer_edge_failure_none = 0,
  phase2_wrapper_consumer_edge_failure_exact_build = 1U << 0,
  phase2_wrapper_consumer_edge_failure_primary_thread_suspended = 1U << 1,
  phase2_wrapper_consumer_edge_failure_unsupported_override = 1U << 2,
  phase2_wrapper_consumer_edge_failure_already_installed = 1U << 3,
  phase2_wrapper_consumer_edge_failure_anchor = 1U << 4,
  phase2_wrapper_consumer_edge_failure_allocation = 1U << 5,
  phase2_wrapper_consumer_edge_failure_stub_protection = 1U << 6,
  phase2_wrapper_consumer_edge_failure_target_protection = 1U << 7,
  phase2_wrapper_consumer_edge_failure_target_identity = 1U << 8,
  phase2_wrapper_consumer_edge_failure_flush = 1U << 9,
  phase2_wrapper_consumer_edge_failure_rollback = 1U << 10,
};

using Phase2WrapperConsumerEdgeVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using Phase2WrapperConsumerEdgeVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using Phase2WrapperConsumerEdgeVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using Phase2WrapperConsumerEdgeFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct Phase2WrapperConsumerEdgeEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  void *memory_context = nullptr;
  Phase2WrapperConsumerEdgeVirtualAllocV1 virtual_alloc_override = nullptr;
  Phase2WrapperConsumerEdgeVirtualFreeV1 virtual_free_override = nullptr;
  Phase2WrapperConsumerEdgeVirtualProtectV1 virtual_protect_override = nullptr;
  Phase2WrapperConsumerEdgeFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
  const std::atomic<std::uint64_t> *selected_task_source = nullptr;
};

struct Phase2WrapperConsumerEdgeStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      phase2_wrapper_consumer_edge_failure_none};
  std::atomic<std::uint64_t> entry_count{0};
  std::atomic<std::uint64_t> edge_0x3B9E10B_count{0};
  std::atomic<std::uint64_t> edge_0x3B9E175_count{0};
  std::atomic<std::uint64_t> other_caller_count{0};
  std::atomic<std::uint64_t> selected_after_publish_entry_count{0};
  std::atomic<std::uint64_t> selected_after_publish_edge_0x3B9E10B_count{0};
  std::atomic<std::uint64_t> selected_after_publish_edge_0x3B9E175_count{0};
  std::atomic<std::uint64_t> selected_after_publish_other_caller_count{0};
  std::atomic<std::uint64_t> last_return_address{0};
  std::atomic<std::uint64_t> last_callsite_rva{0};
  std::atomic<std::uint64_t> last_consumer_context{0};
  std::atomic<std::uint32_t> last_item_count{0};
  std::atomic<std::uint64_t> last_selected_task{0};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kPhase2WrapperConsumerEdgePatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kPhase2WrapperConsumerEdgePatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  Phase2WrapperConsumerEdgeVirtualFreeV1 virtual_free = nullptr;
  Phase2WrapperConsumerEdgeVirtualProtectV1 virtual_protect = nullptr;
  Phase2WrapperConsumerEdgeFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
  const std::atomic<std::uint64_t> *selected_task_source = nullptr;
};

struct Phase2WrapperConsumerEdgeDiagnosticsV1 {
  bool installed = false;
  std::uint32_t failure_flags = phase2_wrapper_consumer_edge_failure_none;
  std::uint64_t entry_count = 0;
  std::uint64_t edge_0x3B9E10B_count = 0;
  std::uint64_t edge_0x3B9E175_count = 0;
  std::uint64_t other_caller_count = 0;
  std::uint64_t selected_after_publish_entry_count = 0;
  std::uint64_t selected_after_publish_edge_0x3B9E10B_count = 0;
  std::uint64_t selected_after_publish_edge_0x3B9E175_count = 0;
  std::uint64_t selected_after_publish_other_caller_count = 0;
  std::uint64_t last_return_address = 0;
  std::uint64_t last_callsite_rva = 0;
  std::uint64_t last_consumer_context = 0;
  std::uint32_t last_item_count = 0;
  std::uint64_t last_selected_task = 0;
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
};

bool InstallPhase2WrapperConsumerEdgeObserverV1(
    Phase2WrapperConsumerEdgeStateV1 &state,
    const Phase2WrapperConsumerEdgeEnvironmentV1 &environment) noexcept;
bool UninstallPhase2WrapperConsumerEdgeObserverV1(
    Phase2WrapperConsumerEdgeStateV1 &state) noexcept;
Phase2WrapperConsumerEdgeDiagnosticsV1
ReadPhase2WrapperConsumerEdgeDiagnosticsV1(
    const Phase2WrapperConsumerEdgeStateV1 &state) noexcept;
void RecordPhase2WrapperConsumerEdgeObservationV1(
    Phase2WrapperConsumerEdgeStateV1 &state, std::uintptr_t return_address,
    std::uintptr_t consumer_context, std::uint32_t item_count,
    std::uint32_t thread_id, std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
