#pragma once

#include "xar_bridge/army_battle_casualty_observations_v1.hpp"
#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kBattleCasualtyApplicationRva12004 = 0x2652D00;
inline constexpr std::uintptr_t kBattleCasualtyWriterReturnRva12004 = 0x2652D6A;
inline constexpr std::size_t kBattleCasualtyApplicationPatchBytes12004 = 15;
using BattleCasualtyOriginal12004 = void *(__fastcall *)(
    void *side, std::int64_t soft_raw, std::int64_t hard_raw, void *entry);

struct BattleCasualtyObserverBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void **game_state_slot = nullptr;
  void **army_storage_slot = nullptr;
  void **army_fallback_slot = nullptr;
  void **unit_storage_slot = nullptr;
  void **unit_fallback_slot = nullptr;
  void *read_context = nullptr;
  ActualLossWriterReadMemoryV1 read_memory = nullptr;
};

struct BattleCasualtyObserverInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  BattleCasualtyObserverBindings12004 bindings{};
  std::uintptr_t target_override = 0;
  void *memory_context = nullptr;
  ActualLossWriterVirtualAllocV1 virtual_alloc_override = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free_override = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect_override = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache_override = nullptr;
};

struct BattleCasualtyObserverDetourState12004 {
  std::atomic<std::uint32_t> installed{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::uintptr_t target = 0;
  void *trampoline = nullptr;
  void *memory_context = nullptr;
  ActualLossWriterVirtualFreeV1 virtual_free = nullptr;
  ActualLossWriterVirtualProtectV1 virtual_protect = nullptr;
  ActualLossWriterFlushV1 flush_instruction_cache = nullptr;
};

BattleCasualtyObserverBindings12004 BindBattleCasualtyObserverImage12004(
    std::uintptr_t base, std::string_view sha) noexcept;
bool InstallBattleCasualtyObserver12004(
    BattleCasualtyObserverDetourState12004 &state,
    const BattleCasualtyObserverInstallEnvironment12004 &environment,
    std::string_view sha) noexcept;
bool UninstallBattleCasualtyObserver12004(
    BattleCasualtyObserverDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept;
bool InitializeBattleCasualtyObserverFixture12004(
    const BattleCasualtyObserverBindings12004 &bindings,
    BattleCasualtyOriginal12004 original) noexcept;

// The actual2634190 hook calls this after its original-once physical capture.
// No active same-thread application means this is a no-op.
void ObserveNestedBattleCasualtyWriter12004(
    void *actual_regiment,
    const game::ArmyActualLossWriterObservationV1 &writer_event) noexcept;

// Reads completed owned events only, never CK3 memory or a mutating callback.
std::optional<game::ArmyBattleCasualtyObservationsV1>
ReadBattleCasualtyObservations12004(
    std::span<const std::int32_t> current_full_regiment_ids) noexcept;

extern "C" void *__fastcall XarBattleCasualtyApplicationHook12004(
    void *side, std::int64_t soft_raw, std::int64_t hard_raw, void *entry) noexcept;

} // namespace xar::ck3_12004
