#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

#include <windows.h>

namespace xar::bridge {

inline constexpr std::uintptr_t kG2TrucePreviewEntryPatchRvaV1 = 0x2E87155;
inline constexpr std::uintptr_t kG2TrucePreviewEntryContinueRvaV1 = 0x2E87165;
inline constexpr std::size_t kG2TrucePreviewEntryPatchBytesV1 = 16;
inline constexpr std::uintptr_t kG2AddTruceEffectNormalVtableRvaV1 = 0x4461CA8;
inline constexpr std::uintptr_t kG2AddTruceEffectForcedVtableRvaV1 = 0x4461D70;
inline constexpr bool kG2TrucePreviewEntryObserverInstalledByDefaultV1 = false;

enum G2TrucePreviewEntryObserverFailureV1 : std::uint32_t {
  g2_truce_preview_entry_observer_failure_none = 0,
  g2_truce_preview_entry_observer_failure_exact_build = 1U << 0,
  g2_truce_preview_entry_observer_failure_primary_thread_suspended = 1U << 1,
  g2_truce_preview_entry_observer_failure_unsupported_override = 1U << 2,
  g2_truce_preview_entry_observer_failure_already_installed = 1U << 3,
  g2_truce_preview_entry_observer_failure_anchor = 1U << 4,
  g2_truce_preview_entry_observer_failure_allocation = 1U << 5,
  g2_truce_preview_entry_observer_failure_stub_protection = 1U << 6,
  g2_truce_preview_entry_observer_failure_target_protection = 1U << 7,
  g2_truce_preview_entry_observer_failure_target_identity = 1U << 8,
  g2_truce_preview_entry_observer_failure_flush = 1U << 9,
  g2_truce_preview_entry_observer_failure_rollback = 1U << 10,
};

using G2TrucePreviewEntryVirtualAllocV1 = void *(*) (
    void *, std::size_t, DWORD, DWORD) noexcept;
using G2TrucePreviewEntryVirtualFreeV1 = bool (*) (
    void *, void *, std::size_t, DWORD) noexcept;
using G2TrucePreviewEntryVirtualProtectV1 = bool (*) (
    void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using G2TrucePreviewEntryFlushInstructionCacheV1 = bool (*) (
    void *, const void *, std::size_t) noexcept;
using G2TrucePreviewEntryCaptureV1 = void (*)(
    void *context, std::uintptr_t effect_this,
    std::uintptr_t preview_context,
    std::uintptr_t preview_collector) noexcept;

struct G2TrucePreviewEntryObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  bool primary_thread_suspended_proven = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target_override = 0;
  std::uintptr_t continue_target_override = 0;
  void *memory_context = nullptr;
  G2TrucePreviewEntryVirtualAllocV1 virtual_alloc_override = nullptr;
  G2TrucePreviewEntryVirtualFreeV1 virtual_free_override = nullptr;
  G2TrucePreviewEntryVirtualProtectV1 virtual_protect_override = nullptr;
  G2TrucePreviewEntryFlushInstructionCacheV1
      flush_instruction_cache_override = nullptr;
};

struct G2TrucePreviewEntryObserverV1State {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{
      g2_truce_preview_entry_observer_failure_none};
  std::atomic<std::uint64_t> accepted_count{0};
  std::atomic<std::uint64_t> normal_effect_count{0};
  std::atomic<std::uint64_t> forced_effect_count{0};
  std::atomic<std::uint64_t> last_effect_this{0};
  std::atomic<std::uint64_t> last_effect_vtable{0};
  std::atomic<std::uint64_t> last_preview_context{0};
  std::atomic<std::uint64_t> last_preview_collector{0};
  std::atomic<std::uintptr_t> armed_capture_context{0};
  std::atomic<std::uintptr_t> armed_capture_callback{0};

  std::uintptr_t module_base = 0;
  std::uintptr_t patch_target = 0;
  std::uintptr_t continue_target = 0;
  void *stub = nullptr;
  std::array<std::uint8_t, kG2TrucePreviewEntryPatchBytesV1> original{};
  std::array<std::uint8_t, kG2TrucePreviewEntryPatchBytesV1> installed_patch{};
  void *memory_context = nullptr;
  G2TrucePreviewEntryVirtualFreeV1 virtual_free = nullptr;
  G2TrucePreviewEntryVirtualProtectV1 virtual_protect = nullptr;
  G2TrucePreviewEntryFlushInstructionCacheV1 flush_instruction_cache = nullptr;
};

struct G2TrucePreviewEntryObserverV1Diagnostics {
  bool installed = false;
  std::uint32_t failure_flags = 0;
  std::uint64_t accepted_count = 0;
  std::uint64_t normal_effect_count = 0;
  std::uint64_t forced_effect_count = 0;
  std::uint64_t last_effect_this = 0;
  std::uint64_t last_effect_vtable = 0;
  std::uint64_t last_preview_context = 0;
  std::uint64_t last_preview_collector = 0;
};

bool InstallG2TrucePreviewEntryObserverV1(
    G2TrucePreviewEntryObserverV1State &,
    const G2TrucePreviewEntryObserverEnvironmentV1 &) noexcept;
bool UninstallG2TrucePreviewEntryObserverV1(
    G2TrucePreviewEntryObserverV1State &) noexcept;
G2TrucePreviewEntryObserverV1Diagnostics
ReadG2TrucePreviewEntryObserverV1Diagnostics(
    const G2TrucePreviewEntryObserverV1State &) noexcept;
void RecordG2TrucePreviewEntryV1(G2TrucePreviewEntryObserverV1State &,
                                 std::uintptr_t effect_this,
                                 std::uintptr_t preview_context,
                                 std::uintptr_t preview_collector) noexcept;
bool ArmG2TrucePreviewEntryCaptureV1(
    G2TrucePreviewEntryCaptureV1 callback, void *context) noexcept;
void DisarmG2TrucePreviewEntryCaptureV1() noexcept;

} // namespace xar::bridge
