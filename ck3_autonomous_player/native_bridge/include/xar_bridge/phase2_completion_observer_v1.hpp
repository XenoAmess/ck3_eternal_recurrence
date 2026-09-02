#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kPhase2CompletionObserverPatchRvaV1 =
    0x3B9DEA7;
inline constexpr std::uintptr_t kPhase2CompletionObserverContinueRvaV1 =
    0x3B9DEB6;
inline constexpr std::uintptr_t kPhase2CompletionObserverRetireRvaV1 =
    0x3B9DF63;
inline constexpr std::uintptr_t kPhase2SelectedCallbackTargetRvaV1 =
    0x88B480;
inline constexpr std::size_t kPhase2CompletionObserverPatchBytesV1 = 15;
inline constexpr std::size_t kPhase2CompletionObserverStubBytesV1 = 85;
inline constexpr bool kPhase2CompletionObserverInstalledByDefaultV1 = false;

enum Phase2CompletionObserverFailureV1 : std::uint32_t {
  phase2_completion_observer_failure_none = 0,
  phase2_completion_observer_failure_exact_build = 1U << 0,
  phase2_completion_observer_failure_primary_thread_suspended = 1U << 1,
  phase2_completion_observer_failure_unsupported_override = 1U << 2,
  phase2_completion_observer_failure_already_installed = 1U << 3,
  phase2_completion_observer_failure_anchor = 1U << 4,
  phase2_completion_observer_failure_allocation = 1U << 5,
  phase2_completion_observer_failure_stub_protection = 1U << 6,
  phase2_completion_observer_failure_target_protection = 1U << 7,
  phase2_completion_observer_failure_target_identity = 1U << 8,
  phase2_completion_observer_failure_flush = 1U << 9,
  phase2_completion_observer_failure_rollback = 1U << 10,
};

using Phase2CompletionObserverVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using Phase2CompletionObserverVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using Phase2CompletionObserverVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using Phase2CompletionObserverFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct Phase2CompletionObserverV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  std::uintptr_t retire_target_override = 0;
  void *memory_context = nullptr;
  Phase2CompletionObserverVirtualAllocV1 virtual_alloc_override = nullptr;
  Phase2CompletionObserverVirtualFreeV1 virtual_free_override = nullptr;
  Phase2CompletionObserverVirtualProtectV1 virtual_protect_override = nullptr;
  Phase2CompletionObserverFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

struct Phase2CompletionObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      phase2_completion_observer_failure_none};
  std::atomic<std::uint64_t> selected_event_count{0};
  std::atomic<std::uint64_t> state2_count{0};
  std::atomic<std::uint64_t> state3_count{0};
  std::atomic<std::uint64_t> last_timestamp_qpc{0};
  std::atomic<std::uint64_t> last_task{0};
  std::atomic<std::uint64_t> last_callback{0};
  std::atomic<std::uint64_t> last_callback_slot2_target{0};
  std::atomic<std::uint32_t> last_state{0};
  std::atomic<std::uint32_t> last_thread_id{0};
  std::atomic<std::uint32_t> last_reference_count{0};
  std::atomic<std::uint32_t> last_observed_retired{0};
  std::atomic<std::uint32_t> last_will_retire{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  std::uintptr_t retire_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kPhase2CompletionObserverPatchBytesV1>
      original_patch_bytes{};
  std::array<std::uint8_t, kPhase2CompletionObserverPatchBytesV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  Phase2CompletionObserverVirtualFreeV1 virtual_free = nullptr;
  Phase2CompletionObserverVirtualProtectV1 virtual_protect = nullptr;
  Phase2CompletionObserverFlushInstructionCacheV1 flush_instruction_cache =
      nullptr;
};

struct Phase2CompletionObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = phase2_completion_observer_failure_none;
  std::uint64_t selected_event_count = 0;
  std::uint64_t state2_count = 0;
  std::uint64_t state3_count = 0;
  std::uint64_t last_timestamp_qpc = 0;
  std::uint64_t last_task = 0;
  std::uint64_t last_callback = 0;
  std::uint64_t last_callback_slot2_target = 0;
  std::uint32_t last_state = 0;
  std::uint32_t last_thread_id = 0;
  std::uint32_t last_reference_count = 0;
  bool last_observed_retired = false;
  bool last_will_retire = false;
};

bool InstallPhase2CompletionObserverV1(
    Phase2CompletionObserverV1State &state,
    const Phase2CompletionObserverV1Environment &environment) noexcept;
bool UninstallPhase2CompletionObserverV1(
    Phase2CompletionObserverV1State &state) noexcept;
Phase2CompletionObserverV1Diagnostics ReadPhase2CompletionObserverV1Diagnostics(
    const Phase2CompletionObserverV1State &state) noexcept;

// Internal fixture seam used by the generated stub and focused tests. It only
// reads the task/callback identity and publishes private atomic telemetry.
void RecordPhase2CompletionObservationV1(
    Phase2CompletionObserverV1State &state, std::uintptr_t task,
    std::uint32_t observed_state, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
