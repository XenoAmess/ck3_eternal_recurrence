#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kPhase2PostCallObserverPatchRvaV1 = 0x3407DA1;
inline constexpr std::uintptr_t kPhase2PostCallObserverContinueRvaV1 = 0x3407DAF;
inline constexpr std::uintptr_t kPhase2PostCallObserverNullTargetRvaV1 = 0x3407DBD;
inline constexpr std::uintptr_t kPhase2PostCallSelectedCallbackTargetRvaV1 =
    0x88B480;
inline constexpr std::size_t kPhase2PostCallObserverPatchBytesV1 = 14;
inline constexpr std::size_t kPhase2PostCallObserverStubBytesV1 = 87;
inline constexpr std::uint32_t kPhase2PostCallObserverMaxDescriptorsV1 = 4096;
inline constexpr bool kPhase2PostCallObserverInstalledByDefaultV1 = false;

enum Phase2PostCallObserverFailureV1 : std::uint32_t {
  phase2_post_call_observer_failure_none = 0,
  phase2_post_call_observer_failure_exact_build = 1U << 0,
  phase2_post_call_observer_failure_primary_thread_suspended = 1U << 1,
  phase2_post_call_observer_failure_unsupported_override = 1U << 2,
  phase2_post_call_observer_failure_already_installed = 1U << 3,
  phase2_post_call_observer_failure_anchor = 1U << 4,
  phase2_post_call_observer_failure_allocation = 1U << 5,
  phase2_post_call_observer_failure_stub_protection = 1U << 6,
  phase2_post_call_observer_failure_target_protection = 1U << 7,
  phase2_post_call_observer_failure_target_identity = 1U << 8,
  phase2_post_call_observer_failure_flush = 1U << 9,
  phase2_post_call_observer_failure_rollback = 1U << 10,
};

using Phase2PostCallObserverVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using Phase2PostCallObserverVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using Phase2PostCallObserverVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using Phase2PostCallObserverFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct Phase2PostCallObserverV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t null_target_override = 0;
  void *memory_context = nullptr;
  Phase2PostCallObserverVirtualAllocV1 virtual_alloc_override = nullptr;
  Phase2PostCallObserverVirtualFreeV1 virtual_free_override = nullptr;
  Phase2PostCallObserverVirtualProtectV1 virtual_protect_override = nullptr;
  Phase2PostCallObserverFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

struct Phase2PostCallObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      phase2_post_call_observer_failure_none};
  std::atomic<std::uint64_t> hit_count{0};
  std::atomic<std::uint64_t> nonempty_list_count{0};
  std::atomic<std::uint64_t> descriptor_seen_count{0};
  std::atomic<std::uint64_t> selected_event_count{0};
  std::atomic<std::uint64_t> selected_state0_count{0};
  std::atomic<std::uint64_t> selected_state2_count{0};
  std::atomic<std::uint64_t> selected_state3_count{0};
  std::atomic<std::uint64_t> selected_other_state_count{0};
  std::atomic<std::uint64_t> read_failure_count{0};
  std::atomic<std::uint64_t> scan_truncated_count{0};
  std::atomic<std::uint64_t> last_producer_list{0};
  std::atomic<std::uint64_t> last_list_begin{0};
  std::atomic<std::uint32_t> last_list_count{0};
  std::atomic<std::uint64_t> raw_last_descriptor{0};
  std::atomic<std::uint64_t> raw_last_task{0};
  std::atomic<std::uint64_t> raw_last_owner{0};
  std::atomic<std::uint64_t> raw_last_callback{0};
  std::atomic<std::uint64_t> raw_last_callback_slot2_target{0};
  std::atomic<std::uint32_t> raw_last_state{0};
  std::atomic<std::uint64_t> last_descriptor{0};
  std::atomic<std::uint64_t> last_task{0};
  std::atomic<std::uint64_t> last_owner{0};
  std::atomic<std::uint64_t> last_callback{0};
  std::atomic<std::uint64_t> last_callback_slot2_target{0};
  std::atomic<std::uint32_t> last_state{0};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t null_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kPhase2PostCallObserverPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kPhase2PostCallObserverPatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  Phase2PostCallObserverVirtualFreeV1 virtual_free = nullptr;
  Phase2PostCallObserverVirtualProtectV1 virtual_protect = nullptr;
  Phase2PostCallObserverFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct Phase2PostCallObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = phase2_post_call_observer_failure_none;
  std::uint64_t hit_count = 0;
  std::uint64_t nonempty_list_count = 0;
  std::uint64_t descriptor_seen_count = 0;
  std::uint64_t selected_event_count = 0;
  std::uint64_t selected_state0_count = 0;
  std::uint64_t selected_state2_count = 0;
  std::uint64_t selected_state3_count = 0;
  std::uint64_t selected_other_state_count = 0;
  std::uint64_t read_failure_count = 0;
  std::uint64_t scan_truncated_count = 0;
  std::uint64_t last_producer_list = 0;
  std::uint64_t last_list_begin = 0;
  std::uint32_t last_list_count = 0;
  std::uint64_t raw_last_descriptor = 0;
  std::uint64_t raw_last_task = 0;
  std::uint64_t raw_last_owner = 0;
  std::uint64_t raw_last_callback = 0;
  std::uint64_t raw_last_callback_slot2_target = 0;
  std::uint32_t raw_last_state = 0;
  std::uint64_t last_descriptor = 0;
  std::uint64_t last_task = 0;
  std::uint64_t last_owner = 0;
  std::uint64_t last_callback = 0;
  std::uint64_t last_callback_slot2_target = 0;
  std::uint32_t last_state = 0;
  std::uint32_t last_thread_id = 0;
  std::uint64_t last_timestamp_qpc = 0;
};

bool InstallPhase2PostCallObserverV1(
    Phase2PostCallObserverV1State &state,
    const Phase2PostCallObserverV1Environment &environment) noexcept;
bool UninstallPhase2PostCallObserverV1(
    Phase2PostCallObserverV1State &state) noexcept;
Phase2PostCallObserverV1Diagnostics ReadPhase2PostCallObserverV1Diagnostics(
    const Phase2PostCallObserverV1State &state) noexcept;

void RecordPhase2PostCallObservationV1(
    Phase2PostCallObserverV1State &state, std::uintptr_t frame_base,
    std::uint32_t thread_id, std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
