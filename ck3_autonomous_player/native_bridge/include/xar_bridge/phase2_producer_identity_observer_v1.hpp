#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kPhase2ProducerIdentityPreRvaV1 = 0x3B9CFD2;
inline constexpr std::uintptr_t kPhase2ProducerIdentityPublishRvaV1 = 0x3B9CFD7;
inline constexpr std::uintptr_t kPhase2ProducerIdentityContinueRvaV1 = 0x3B9CFE2;
inline constexpr std::uintptr_t kPhase2ProducerIdentityOriginalCallRvaV1 = 0x3E24040;
inline constexpr std::size_t kPhase2ProducerIdentityPatchBytesV1 = 16;
inline constexpr std::size_t kPhase2ProducerIdentityStubBytesV1 = 133;
inline constexpr bool kPhase2ProducerIdentityInstalledByDefaultV1 = false;
inline constexpr std::uintptr_t kPhase2ProducerIdentitySelectedSlot2RvaV1 =
    0x88B480;
inline constexpr std::size_t kPhase2ProducerIdentityHistogramCapacityV1 = 64;

enum Phase2ProducerIdentityFailureV1 : std::uint32_t {
  phase2_producer_identity_failure_none = 0,
  phase2_producer_identity_failure_exact_build = 1U << 0,
  phase2_producer_identity_failure_primary_thread_suspended = 1U << 1,
  phase2_producer_identity_failure_unsupported_override = 1U << 2,
  phase2_producer_identity_failure_already_installed = 1U << 3,
  phase2_producer_identity_failure_anchor = 1U << 4,
  phase2_producer_identity_failure_allocation = 1U << 5,
  phase2_producer_identity_failure_stub_protection = 1U << 6,
  phase2_producer_identity_failure_target_protection = 1U << 7,
  phase2_producer_identity_failure_target_identity = 1U << 8,
  phase2_producer_identity_failure_flush = 1U << 9,
  phase2_producer_identity_failure_rollback = 1U << 10,
};

using Phase2ProducerIdentityVirtualAllocV1 = void *(*) (
    void *, std::size_t, DWORD, DWORD) noexcept;
using Phase2ProducerIdentityVirtualFreeV1 = bool (*) (
    void *, void *, std::size_t, DWORD) noexcept;
using Phase2ProducerIdentityVirtualProtectV1 = bool (*) (
    void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using Phase2ProducerIdentityFlushV1 = bool (*) (
    void *, const void *, std::size_t) noexcept;

struct Phase2ProducerIdentityEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t original_call_target_override = 0;
  void *memory_context = nullptr;
  Phase2ProducerIdentityVirtualAllocV1 virtual_alloc_override = nullptr;
  Phase2ProducerIdentityVirtualFreeV1 virtual_free_override = nullptr;
  Phase2ProducerIdentityVirtualProtectV1 virtual_protect_override = nullptr;
  Phase2ProducerIdentityFlushV1 flush_instruction_cache_override = nullptr;
};

struct Phase2ProducerIdentityStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{phase2_producer_identity_failure_none};
  std::atomic<std::uint64_t> producer_0x3B9CFD2_entry_count{0};
  std::atomic<std::uint64_t> producer_0x3B9CFD7_entry_count{0};
  std::atomic<std::uint64_t> read_failure_count{0};
  std::atomic<std::uint64_t> last_task_pointer{0};
  std::atomic<std::uint64_t> last_callback_pointer{0};
  std::atomic<std::uint64_t> last_callback_vptr{0};
  std::atomic<std::uint64_t> last_callback_slot2{0};
  std::atomic<std::uint64_t> last_callback_slot2_rva{0};
  std::atomic<std::uint64_t> last_owner_pointer{0};
  std::atomic<std::uint32_t> last_state_before_publish{0};
  std::atomic<std::uint32_t> last_state_after_publish{0};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};
  std::atomic<std::uint32_t> histogram_bin_count{0};
  std::atomic<std::uint64_t> histogram_overflow_count{0};
  std::atomic<std::uint64_t> histogram_read_failure_count{0};
  struct HistogramBin {
    std::atomic<std::uint64_t> callback_slot2_rva{0};
    std::atomic<std::uint64_t> count{0};
  };
  std::array<HistogramBin, kPhase2ProducerIdentityHistogramCapacityV1>
      callback_slot2_rva_histogram{};
  std::atomic<std::uint64_t> selected_0x88B480_match_count{0};
  std::atomic<std::uint64_t> selected_first_task_pointer{0};
  std::atomic<std::uint64_t> selected_first_callback_pointer{0};
  std::atomic<std::uint64_t> selected_first_callback_vptr{0};
  std::atomic<std::uint64_t> selected_first_callback_slot2{0};
  std::atomic<std::uint64_t> selected_first_callback_slot2_rva{0};
  std::atomic<std::uint64_t> selected_first_owner_pointer{0};
  std::atomic<std::uint32_t> selected_first_state{0};
  std::atomic<std::uint32_t> selected_first_thread_id{0};
  std::atomic<std::uint64_t> selected_first_timestamp_qpc{0};
  std::atomic<std::uint64_t> selected_last_task_pointer{0};
  std::atomic<std::uint64_t> selected_last_callback_pointer{0};
  std::atomic<std::uint64_t> selected_last_callback_vptr{0};
  std::atomic<std::uint64_t> selected_last_callback_slot2{0};
  std::atomic<std::uint64_t> selected_last_callback_slot2_rva{0};
  std::atomic<std::uint64_t> selected_last_owner_pointer{0};
  std::atomic<std::uint32_t> selected_last_state{0};
  std::atomic<std::uint32_t> selected_last_thread_id{0};
  std::atomic<std::uint64_t> selected_last_timestamp_qpc{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t original_call_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kPhase2ProducerIdentityPatchBytesV1> original_patch_bytes{};
  std::array<std::uint8_t, kPhase2ProducerIdentityPatchBytesV1> installed_patch_bytes{};
  void *memory_context = nullptr;
  Phase2ProducerIdentityVirtualFreeV1 virtual_free = nullptr;
  Phase2ProducerIdentityVirtualProtectV1 virtual_protect = nullptr;
  Phase2ProducerIdentityFlushV1 flush_instruction_cache = nullptr;
};

struct Phase2ProducerIdentityHistogramBinDiagnosticsV1 {
  std::uint64_t callback_slot2_rva = 0;
  std::uint64_t count = 0;
};

struct Phase2ProducerIdentityDiagnosticsV1 {
  bool installed = false;
  std::uint32_t failure_flags = 0;
  std::uint64_t producer_0x3B9CFD2_entry_count = 0;
  std::uint64_t producer_0x3B9CFD7_entry_count = 0;
  std::uint64_t read_failure_count = 0;
  std::uint64_t last_task_pointer = 0;
  std::uint64_t last_callback_pointer = 0;
  std::uint64_t last_callback_vptr = 0;
  std::uint64_t last_callback_slot2 = 0;
  std::uint64_t last_callback_slot2_rva = 0;
  std::uint64_t last_owner_pointer = 0;
  std::uint32_t last_state_before_publish = 0;
  std::uint32_t last_state_after_publish = 0;
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
  std::uint32_t histogram_bin_count = 0;
  std::uint64_t histogram_overflow_count = 0;
  std::uint64_t histogram_read_failure_count = 0;
  std::array<Phase2ProducerIdentityHistogramBinDiagnosticsV1,
             kPhase2ProducerIdentityHistogramCapacityV1>
      callback_slot2_rva_histogram{};
  std::uint64_t selected_0x88B480_match_count = 0;
  std::uint64_t selected_first_task_pointer = 0;
  std::uint64_t selected_first_callback_pointer = 0;
  std::uint64_t selected_first_callback_vptr = 0;
  std::uint64_t selected_first_callback_slot2 = 0;
  std::uint64_t selected_first_callback_slot2_rva = 0;
  std::uint64_t selected_first_owner_pointer = 0;
  std::uint32_t selected_first_state = 0;
  std::uint32_t selected_first_thread_id = 0;
  std::uint64_t selected_first_timestamp_qpc = 0;
  std::uint64_t selected_last_task_pointer = 0;
  std::uint64_t selected_last_callback_pointer = 0;
  std::uint64_t selected_last_callback_vptr = 0;
  std::uint64_t selected_last_callback_slot2 = 0;
  std::uint64_t selected_last_callback_slot2_rva = 0;
  std::uint64_t selected_last_owner_pointer = 0;
  std::uint32_t selected_last_state = 0;
  std::uint32_t selected_last_thread_id = 0;
  std::uint64_t selected_last_timestamp_qpc = 0;
};

bool InstallPhase2ProducerIdentityObserverV1(
    Phase2ProducerIdentityStateV1 &state,
    const Phase2ProducerIdentityEnvironmentV1 &environment) noexcept;
bool UninstallPhase2ProducerIdentityObserverV1(
    Phase2ProducerIdentityStateV1 &state) noexcept;
Phase2ProducerIdentityDiagnosticsV1 ReadPhase2ProducerIdentityDiagnosticsV1(
    const Phase2ProducerIdentityStateV1 &state) noexcept;

// stage 0 is the logical 0x3B9CFD2 pre-publish edge; stage 1 is the logical
// 0x3B9CFD7 post-xchg edge. The physical detour is one non-overlapping exact
// transaction covering both adjacent instructions.
void RecordPhase2ProducerIdentityObservationV1(
    Phase2ProducerIdentityStateV1 &state, std::uintptr_t task,
    std::uint32_t stage, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
