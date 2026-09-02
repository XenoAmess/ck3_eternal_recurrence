#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::size_t kG2TruceNativeCallsiteCountV1 = 2;
inline constexpr std::size_t kG2TruceNativeCallsiteMaxPatchBytesV1 = 20;
inline constexpr std::size_t kG2TruceNativeCallsiteStubCapacityV1 = 160;
inline constexpr std::uintptr_t kG2TruceEvaluatorRvaV1 = 0x3373000;
inline constexpr std::array<std::uintptr_t, kG2TruceNativeCallsiteCountV1>
    kG2TruceNativeCallsitePatchRvasV1{0x2EDAF01, 0x2EDB58F};
inline constexpr std::array<std::uintptr_t, kG2TruceNativeCallsiteCountV1>
    kG2TruceNativeCallsiteInstructionRvasV1{0x2EDAF0F, 0x2EDB59E};
inline constexpr std::array<std::uintptr_t, kG2TruceNativeCallsiteCountV1>
    kG2TruceNativeCallsiteContinueRvasV1{0x2EDAF14, 0x2EDB5A3};
inline constexpr std::array<std::size_t, kG2TruceNativeCallsiteCountV1>
    kG2TruceNativeCallsitePatchSizesV1{19, 20};
inline constexpr bool kG2TruceNativeCallsiteObserverInstalledByDefaultV1 =
    false;

enum G2TruceNativeCallsiteObserverFailureV1 : std::uint32_t {
  g2_truce_native_callsite_observer_failure_none = 0,
  g2_truce_native_callsite_observer_failure_exact_build = 1U << 0,
  g2_truce_native_callsite_observer_failure_primary_thread_suspended = 1U << 1,
  g2_truce_native_callsite_observer_failure_unsupported_override = 1U << 2,
  g2_truce_native_callsite_observer_failure_already_installed = 1U << 3,
  g2_truce_native_callsite_observer_failure_anchor = 1U << 4,
  g2_truce_native_callsite_observer_failure_allocation = 1U << 5,
  g2_truce_native_callsite_observer_failure_stub_protection = 1U << 6,
  g2_truce_native_callsite_observer_failure_target_protection = 1U << 7,
  g2_truce_native_callsite_observer_failure_target_identity = 1U << 8,
  g2_truce_native_callsite_observer_failure_flush = 1U << 9,
  g2_truce_native_callsite_observer_failure_rollback = 1U << 10,
};

using G2TruceNativeCallsiteObserverVirtualAllocV1 = void *(*) (
    void *context, std::size_t size, DWORD allocation_type,
    DWORD protection) noexcept;
using G2TruceNativeCallsiteObserverVirtualFreeV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD free_type) noexcept;
using G2TruceNativeCallsiteObserverVirtualProtectV1 = bool (*) (
    void *context, void *address, std::size_t size, DWORD new_protection,
    DWORD &old_protection) noexcept;
using G2TruceNativeCallsiteObserverFlushInstructionCacheV1 = bool (*) (
    void *context, const void *address, std::size_t size) noexcept;

struct G2TruceNativeCallsiteObserverV1Environment {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::array<std::uintptr_t, kG2TruceNativeCallsiteCountV1>
      patch_target_overrides{};
  std::array<std::uintptr_t, kG2TruceNativeCallsiteCountV1>
      continue_target_overrides{};
  std::uintptr_t evaluator_target_override = 0;
  void *memory_context = nullptr;
  G2TruceNativeCallsiteObserverVirtualAllocV1 virtual_alloc_override = nullptr;
  G2TruceNativeCallsiteObserverVirtualFreeV1 virtual_free_override = nullptr;
  G2TruceNativeCallsiteObserverVirtualProtectV1 virtual_protect_override =
      nullptr;
  G2TruceNativeCallsiteObserverFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

struct G2TruceNativeCallsiteObservationV1 {
  std::atomic<std::uint64_t> pre_call_count{0};
  std::atomic<std::uint64_t> post_call_count{0};
  std::atomic<std::uint64_t> last_script_value{0};
  std::atomic<std::uint64_t> last_effect_context{0};
  std::atomic<std::uint64_t> last_evaluation_context{0};
  std::atomic<std::uint32_t> last_pre_thread_id{0};
  std::atomic<std::uint64_t> last_pre_timestamp_qpc{0};
  std::atomic<std::int32_t> last_return_eax{0};
  std::atomic<std::uint32_t> last_post_thread_id{0};
  std::atomic<std::uint64_t> last_post_timestamp_qpc{0};
};

struct G2TruceNativeCallsiteObserverV1State {
  std::atomic<std::uint32_t> installed_mask{0};
  std::atomic<std::uint32_t> failure_flags{
      g2_truce_native_callsite_observer_failure_none};
  std::array<G2TruceNativeCallsiteObservationV1,
             kG2TruceNativeCallsiteCountV1>
      observations{};

  std::uintptr_t module_base = 0;
  std::uintptr_t evaluator_target = 0;
  std::array<std::uintptr_t, kG2TruceNativeCallsiteCountV1> patch_targets{};
  std::array<std::uintptr_t, kG2TruceNativeCallsiteCountV1> continue_targets{};
  std::array<void *, kG2TruceNativeCallsiteCountV1> stubs{};
  std::array<std::array<std::uint8_t,
                        kG2TruceNativeCallsiteMaxPatchBytesV1>,
             kG2TruceNativeCallsiteCountV1>
      original_patch_bytes{};
  std::array<std::array<std::uint8_t,
                        kG2TruceNativeCallsiteMaxPatchBytesV1>,
             kG2TruceNativeCallsiteCountV1>
      installed_patch_bytes{};
  void *memory_context = nullptr;
  G2TruceNativeCallsiteObserverVirtualFreeV1 virtual_free = nullptr;
  G2TruceNativeCallsiteObserverVirtualProtectV1 virtual_protect = nullptr;
  G2TruceNativeCallsiteObserverFlushInstructionCacheV1
      flush_instruction_cache = nullptr;
};

struct G2TruceNativeCallsiteObservationV1Diagnostics {
  std::uint64_t pre_call_count = 0;
  std::uint64_t post_call_count = 0;
  std::uint64_t last_script_value = 0;
  std::uint64_t last_effect_context = 0;
  std::uint64_t last_evaluation_context = 0;
  std::uint32_t last_pre_thread_id = 0;
  std::uint64_t last_pre_timestamp_qpc = 0;
  std::int32_t last_return_eax = 0;
  std::uint32_t last_post_thread_id = 0;
  std::uint64_t last_post_timestamp_qpc = 0;
};

struct G2TruceNativeCallsiteObserverV1Diagnostics {
  std::uint32_t installed_mask = 0;
  std::uint32_t failure_flags =
      g2_truce_native_callsite_observer_failure_none;
  std::array<G2TruceNativeCallsiteObservationV1Diagnostics,
             kG2TruceNativeCallsiteCountV1>
      callsites{};
};

bool InstallG2TruceNativeCallsiteObserverV1(
    G2TruceNativeCallsiteObserverV1State &state,
    const G2TruceNativeCallsiteObserverV1Environment &environment) noexcept;
bool UninstallG2TruceNativeCallsiteObserverV1(
    G2TruceNativeCallsiteObserverV1State &state) noexcept;
G2TruceNativeCallsiteObserverV1Diagnostics
ReadG2TruceNativeCallsiteObserverV1Diagnostics(
    const G2TruceNativeCallsiteObserverV1State &state) noexcept;

void RecordG2TruceNativeCallsitePreV1(
    G2TruceNativeCallsiteObserverV1State &state, std::uint32_t site_index,
    std::uintptr_t script_value, std::uintptr_t effect_context,
    std::uintptr_t evaluation_context, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept;
void RecordG2TruceNativeCallsitePostV1(
    G2TruceNativeCallsiteObserverV1State &state, std::uint32_t site_index,
    std::int32_t return_eax, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept;

} // namespace xar::bridge
