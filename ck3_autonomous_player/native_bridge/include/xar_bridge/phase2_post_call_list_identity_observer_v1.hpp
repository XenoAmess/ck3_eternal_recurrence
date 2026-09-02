#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kPhase2PostCallListIdentityPatchRvaV1 =
    0x3407DA1;
inline constexpr std::uintptr_t kPhase2PostCallListIdentityContinueRvaV1 =
    0x3407DAF;
inline constexpr std::uintptr_t kPhase2PostCallListIdentityNullTargetRvaV1 =
    0x3407DBD;
inline constexpr std::uintptr_t kPhase2PostCallListIdentitySelectedTargetRvaV1 =
    0x88B480;
inline constexpr std::size_t kPhase2PostCallListIdentityPatchBytesV1 = 14;
inline constexpr std::size_t kPhase2PostCallListIdentityStubBytesV1 = 87;
inline constexpr std::uint32_t kPhase2PostCallListIdentityMaxDescriptorsV1 =
    4096;
inline constexpr std::size_t kPhase2PostCallListIdentitySampleCapacityV1 = 64;
inline constexpr std::size_t kPhase2PostCallListIdentityHistogramCapacityV1 =
    64;
inline constexpr bool kPhase2PostCallListIdentityInstalledByDefaultV1 = false;

enum Phase2PostCallListIdentityFailureV1 : std::uint32_t {
  phase2_post_call_list_identity_failure_none = 0,
  phase2_post_call_list_identity_failure_exact_build = 1U << 0,
  phase2_post_call_list_identity_failure_primary_thread_suspended = 1U << 1,
  phase2_post_call_list_identity_failure_unsupported_override = 1U << 2,
  phase2_post_call_list_identity_failure_already_installed = 1U << 3,
  phase2_post_call_list_identity_failure_anchor = 1U << 4,
  phase2_post_call_list_identity_failure_allocation = 1U << 5,
  phase2_post_call_list_identity_failure_stub_protection = 1U << 6,
  phase2_post_call_list_identity_failure_target_protection = 1U << 7,
  phase2_post_call_list_identity_failure_target_identity = 1U << 8,
  phase2_post_call_list_identity_failure_flush = 1U << 9,
  phase2_post_call_list_identity_failure_rollback = 1U << 10,
};

using Phase2PostCallListIdentityVirtualAllocV1 = void *(*) (
    void *, std::size_t, DWORD, DWORD) noexcept;
using Phase2PostCallListIdentityVirtualFreeV1 = bool (*) (
    void *, void *, std::size_t, DWORD) noexcept;
using Phase2PostCallListIdentityVirtualProtectV1 = bool (*) (
    void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using Phase2PostCallListIdentityFlushV1 = bool (*) (
    void *, const void *, std::size_t) noexcept;

struct Phase2PostCallListIdentityEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t null_target_override = 0;
  void *memory_context = nullptr;
  Phase2PostCallListIdentityVirtualAllocV1 virtual_alloc_override = nullptr;
  Phase2PostCallListIdentityVirtualFreeV1 virtual_free_override = nullptr;
  Phase2PostCallListIdentityVirtualProtectV1 virtual_protect_override = nullptr;
  Phase2PostCallListIdentityFlushV1 flush_instruction_cache_override = nullptr;
};

struct Phase2PostCallListIdentitySampleV1 {
  std::uint32_t descriptor_index = 0;
  bool read_complete = false;
  std::uint64_t descriptor = 0;
  std::uint64_t task = 0;
  std::uint64_t owner = 0;
  std::uint64_t callback = 0;
  std::uint64_t callback_slot2_target = 0;
  std::uint64_t callback_slot2_rva = 0;
  std::uint32_t state = 0;
};

struct Phase2PostCallListIdentityHistogramBinV1 {
  std::uint64_t callback_slot2_target = 0;
  std::uint64_t callback_slot2_rva = 0;
  std::uint32_t count = 0;
  std::uint64_t first_task = 0;
  std::uint64_t first_owner = 0;
  std::uint64_t last_task = 0;
  std::uint64_t last_owner = 0;
};

struct Phase2PostCallListIdentityAtomicSampleV1 {
  std::atomic<std::uint32_t> descriptor_index{0};
  std::atomic<std::uint32_t> read_complete{0};
  std::atomic<std::uint64_t> descriptor{0};
  std::atomic<std::uint64_t> task{0};
  std::atomic<std::uint64_t> owner{0};
  std::atomic<std::uint64_t> callback{0};
  std::atomic<std::uint64_t> callback_slot2_target{0};
  std::atomic<std::uint64_t> callback_slot2_rva{0};
  std::atomic<std::uint32_t> state{0};
};

struct Phase2PostCallListIdentityAtomicHistogramBinV1 {
  std::atomic<std::uint64_t> callback_slot2_target{0};
  std::atomic<std::uint64_t> callback_slot2_rva{0};
  std::atomic<std::uint32_t> count{0};
  std::atomic<std::uint64_t> first_task{0};
  std::atomic<std::uint64_t> first_owner{0};
  std::atomic<std::uint64_t> last_task{0};
  std::atomic<std::uint64_t> last_owner{0};
};

struct Phase2PostCallListIdentityStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      phase2_post_call_list_identity_failure_none};
  std::atomic<std::uint64_t> hit_count{0};
  std::atomic<std::uint64_t> capture_count{0};
  std::atomic<std::uint64_t> capture_contention_count{0};
  std::atomic<std::uint64_t> snapshot_sequence{0};
  std::atomic_flag capture_lock = ATOMIC_FLAG_INIT;
  std::atomic<std::uint64_t> last_producer_list{0};
  std::atomic<std::uint64_t> last_list_begin{0};
  std::atomic<std::uint32_t> last_list_count{0};
  std::atomic<std::uint32_t> last_scan_count{0};
  std::atomic<std::uint32_t> last_read_failure_count{0};
  std::atomic<std::uint32_t> last_scan_truncated_count{0};
  std::atomic<std::uint32_t> last_sample_count{0};
  std::atomic<std::uint32_t> last_sample_overflow_count{0};
  std::atomic<std::uint32_t> last_histogram_bin_count{0};
  std::atomic<std::uint32_t> last_histogram_overflow_count{0};
  std::atomic<std::uint32_t> last_selected_target_count{0};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};
  std::array<Phase2PostCallListIdentityAtomicSampleV1,
             kPhase2PostCallListIdentitySampleCapacityV1>
      samples{};
  std::array<Phase2PostCallListIdentityAtomicHistogramBinV1,
             kPhase2PostCallListIdentityHistogramCapacityV1>
      histogram{};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t null_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kPhase2PostCallListIdentityPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kPhase2PostCallListIdentityPatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  Phase2PostCallListIdentityVirtualFreeV1 virtual_free = nullptr;
  Phase2PostCallListIdentityVirtualProtectV1 virtual_protect = nullptr;
  Phase2PostCallListIdentityFlushV1 flush_instruction_cache = nullptr;
};

struct Phase2PostCallListIdentityDiagnosticsV1 {
  bool installed = false;
  std::uint32_t failure_flags = 0;
  bool snapshot_consistent = false;
  std::uint64_t hit_count = 0;
  std::uint64_t capture_count = 0;
  std::uint64_t capture_contention_count = 0;
  std::uint64_t snapshot_sequence = 0;
  std::uint64_t last_producer_list = 0;
  std::uint64_t last_list_begin = 0;
  std::uint32_t last_list_count = 0;
  std::uint32_t last_scan_count = 0;
  std::uint32_t last_read_failure_count = 0;
  std::uint32_t last_scan_truncated_count = 0;
  std::uint32_t last_sample_count = 0;
  std::uint32_t last_sample_overflow_count = 0;
  std::uint32_t last_histogram_bin_count = 0;
  std::uint32_t last_histogram_overflow_count = 0;
  std::uint32_t last_selected_target_count = 0;
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
  std::array<Phase2PostCallListIdentitySampleV1,
             kPhase2PostCallListIdentitySampleCapacityV1>
      samples{};
  std::array<Phase2PostCallListIdentityHistogramBinV1,
             kPhase2PostCallListIdentityHistogramCapacityV1>
      histogram{};
};

bool InstallPhase2PostCallListIdentityObserverV1(
    Phase2PostCallListIdentityStateV1 &state,
    const Phase2PostCallListIdentityEnvironmentV1 &environment) noexcept;
bool UninstallPhase2PostCallListIdentityObserverV1(
    Phase2PostCallListIdentityStateV1 &state) noexcept;
void RecordPhase2PostCallListIdentityObservationV1(
    Phase2PostCallListIdentityStateV1 &state, std::uintptr_t frame_base,
    std::uint32_t thread_id, std::uint64_t timestamp_qpc) noexcept;
Phase2PostCallListIdentityDiagnosticsV1
ReadPhase2PostCallListIdentityDiagnosticsV1(
    const Phase2PostCallListIdentityStateV1 &state) noexcept;

} // namespace xar::bridge
