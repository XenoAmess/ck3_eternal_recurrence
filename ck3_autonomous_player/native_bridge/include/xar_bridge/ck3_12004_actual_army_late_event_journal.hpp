#pragma once

#include "xar_bridge/actual_army_late_event_observations_v1.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kActualArmyLateEventRva12004 = 0x37CCC39;
inline constexpr std::size_t kActualArmyLateEventPatchBytes12004 = 14;
inline constexpr std::size_t kActualArmyLateEventAbsoluteJumpBytes12004 = 14;

using ActualArmyLateEventOriginalV1 = void(__fastcall *)(void *, const void *, void *, void *, void *, void *);
using ActualArmyLateEventReadMemoryV1 = bool (*)(void *context, const void *address,
                                                void *output, std::size_t size) noexcept;
using ActualArmyLateEventVirtualAllocV1 = void *(*)(void *context, std::size_t size,
                                                    DWORD allocation_type,
                                                    DWORD protection) noexcept;
using ActualArmyLateEventVirtualFreeV1 = bool (*)(void *context, void *address,
                                                  std::size_t size, DWORD type) noexcept;
using ActualArmyLateEventVirtualProtectV1 = bool (*)(void *context, void *address,
                                                     std::size_t size, DWORD protection,
                                                     DWORD &old) noexcept;
using ActualArmyLateEventFlushV1 = bool (*)(void *context, const void *address,
                                            std::size_t size) noexcept;

struct ActualArmyLateEventJournalBindingsV1 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  // Reads only the genuine incoming scope, loaded definition and manager table.
  void *read_context = nullptr;
  ActualArmyLateEventReadMemoryV1 read_memory = nullptr;
};

struct ActualArmyLateEventJournalInstallEnvironmentV1 {
  bool primary_thread_suspended_proven = false;
  ActualArmyLateEventJournalBindingsV1 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ActualArmyLateEventVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualArmyLateEventVirtualFreeV1 virtual_free_override = nullptr;
  ActualArmyLateEventVirtualProtectV1 virtual_protect_override = nullptr;
  ActualArmyLateEventFlushV1 flush_instruction_cache_override = nullptr;
};

struct ActualArmyLateEventJournalDetourStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kActualArmyLateEventPatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualArmyLateEventVirtualFreeV1 virtual_free = nullptr;
  ActualArmyLateEventVirtualProtectV1 virtual_protect = nullptr;
  ActualArmyLateEventFlushV1 flush_instruction_cache = nullptr;
};

enum ActualArmyLateEventJournalInstallFailureV1 : std::uint32_t {
  actual_army_late_event_install_none = 0,
  actual_army_late_event_install_exact_build = 1U << 0,
  actual_army_late_event_install_quiescence = 1U << 1,
  actual_army_late_event_install_already_installed = 1U << 2,
  actual_army_late_event_install_anchor = 1U << 3,
  actual_army_late_event_install_allocation = 1U << 4,
  actual_army_late_event_install_protection = 1U << 5,
  actual_army_late_event_install_flush = 1U << 6,
  actual_army_late_event_install_rollback = 1U << 7,
};

enum ActualArmyLateEventCaptureFailureV1 : std::uint32_t {
  actual_army_late_event_capture_before = 1U << 0,
  actual_army_late_event_capture_definition = 1U << 1,
  actual_army_late_event_capture_after = 1U << 2,
  actual_army_late_event_capture_identity_changed = 1U << 3,
};

ActualArmyLateEventJournalBindingsV1 BindActualArmyLateEventJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallActualArmyLateEventJournal12004(
    ActualArmyLateEventJournalDetourStateV1 &state,
    const ActualArmyLateEventJournalInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept;
bool UninstallActualArmyLateEventJournal12004(
    ActualArmyLateEventJournalDetourStateV1 &state,
    bool primary_thread_suspended_proven) noexcept;

// Own-storage/typed-local seam only. No patch, executable read, CK3 call or query.
bool InitializeActualArmyLateEventJournalFixture12004(
    const ActualArmyLateEventJournalBindingsV1 &bindings,
    ActualArmyLateEventOriginalV1 original) noexcept;

// The argument is the complete CArmy generation ID. No native object is resolved or
// read here; the query joins only retained owned invocation observations.
std::optional<game::ArmyActualLateEventObservationsV1>
ReadActualArmyLateEventObservations12004(
    std::int32_t native_carmy_id) noexcept;

extern "C" void __fastcall XarActualArmyLateEventHook12004V1(
    void *manager, const void *definition, void *scope, void *extra,
    void *effect_callback, void *event_callback) noexcept;

// Synthetic test seam; no wire setter and never used by current query.
void InvokeActualArmyLateEventJournalFixture12004(
    std::uint64_t caller_return_rva, void *manager, const void *definition,
    void *scope, void *extra, void *effect_callback, void *event_callback) noexcept;

} // namespace xar::ck3_12004
