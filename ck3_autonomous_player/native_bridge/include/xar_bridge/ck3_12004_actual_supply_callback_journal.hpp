#pragma once

#include "xar_bridge/army_actual_supply_callback_observations_v1.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <windows.h>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kActualSupplyCallbackRva12004 = 0x24E3410;
inline constexpr std::size_t kActualSupplyCallbackPatchBytes12004 = 19;
inline constexpr std::size_t kActualSupplyCallbackAbsoluteJumpBytes12004 = 14;

using ActualSupplyCallbackOriginalV1 = void(__fastcall *)(void *, const void *);
using ActualSupplyCallbackReadMemoryV1 = bool (*)(void *context, const void *address,
                                                void *output, std::size_t size) noexcept;
using ActualSupplyCallbackVirtualAllocV1 = void *(*)(void *context, std::size_t size,
                                                    DWORD allocation_type,
                                                    DWORD protection) noexcept;
using ActualSupplyCallbackVirtualFreeV1 = bool (*)(void *context, void *address,
                                                  std::size_t size, DWORD type) noexcept;
using ActualSupplyCallbackVirtualProtectV1 = bool (*)(void *context, void *address,
                                                     std::size_t size, DWORD protection,
                                                     DWORD &old) noexcept;
using ActualSupplyCallbackFlushV1 = bool (*)(void *context, const void *address,
                                            std::size_t size) noexcept;

struct ActualSupplyCallbackJournalBindingsV1 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  // Fixture readers only read a declared local Army/date object, never a world.
  void *read_context = nullptr;
  ActualSupplyCallbackReadMemoryV1 read_memory = nullptr;
};

struct ActualSupplyCallbackJournalInstallEnvironmentV1 {
  bool primary_thread_suspended_proven = false;
  ActualSupplyCallbackJournalBindingsV1 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ActualSupplyCallbackVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualSupplyCallbackVirtualFreeV1 virtual_free_override = nullptr;
  ActualSupplyCallbackVirtualProtectV1 virtual_protect_override = nullptr;
  ActualSupplyCallbackFlushV1 flush_instruction_cache_override = nullptr;
};

struct ActualSupplyCallbackJournalDetourStateV1 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kActualSupplyCallbackPatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualSupplyCallbackVirtualFreeV1 virtual_free = nullptr;
  ActualSupplyCallbackVirtualProtectV1 virtual_protect = nullptr;
  ActualSupplyCallbackFlushV1 flush_instruction_cache = nullptr;
};

enum ActualSupplyCallbackJournalInstallFailureV1 : std::uint32_t {
  actual_supply_callback_install_none = 0,
  actual_supply_callback_install_exact_build = 1U << 0,
  actual_supply_callback_install_quiescence = 1U << 1,
  actual_supply_callback_install_already_installed = 1U << 2,
  actual_supply_callback_install_anchor = 1U << 3,
  actual_supply_callback_install_allocation = 1U << 4,
  actual_supply_callback_install_protection = 1U << 5,
  actual_supply_callback_install_flush = 1U << 6,
  actual_supply_callback_install_rollback = 1U << 7,
};

enum ActualSupplyCallbackCaptureFailureV1 : std::uint32_t {
  actual_supply_callback_capture_before = 1U << 0,
  actual_supply_callback_capture_after = 1U << 1,
  actual_supply_callback_capture_date = 1U << 2,
  actual_supply_callback_capture_identity_changed = 1U << 3,
};

ActualSupplyCallbackJournalBindingsV1 BindActualSupplyCallbackJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool InstallActualSupplyCallbackJournal12004(
    ActualSupplyCallbackJournalDetourStateV1 &state,
    const ActualSupplyCallbackJournalInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept;
bool UninstallActualSupplyCallbackJournal12004(
    ActualSupplyCallbackJournalDetourStateV1 &state,
    bool primary_thread_suspended_proven) noexcept;

// Own-storage/typed-local seam only. No patch, executable read, CK3 call or query.
bool InitializeActualSupplyCallbackJournalFixture12004(
    const ActualSupplyCallbackJournalBindingsV1 &bindings,
    ActualSupplyCallbackOriginalV1 original) noexcept;

// Both arguments are complete generation IDs. No native object is resolved or
// read here; the query joins only retained owned invocation observations.
std::optional<game::ArmyActualSupplyCallbackObservationsV1>
ReadActualSupplyCallbackObservations12004(
    std::int32_t army_id, std::int32_t native_carmy_id) noexcept;

extern "C" void __fastcall XarActualSupplyCallbackHook12004V1(
    void *army, const void *date) noexcept;

} // namespace xar::ck3_12004
