#pragma once

#include "xar_bridge/army_daily_assault_preparation_12004.hpp"
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>
#include <windows.h>

#define XAR_HAS_ACTUAL_ARMY_DAILY_ASSAULT_PREPARATION_12004 1

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kActualArmyDailyAssaultPreparationRva12004 = 0x2A99B20;
inline constexpr std::uintptr_t kActualArmyDailyAssaultPreparationReturnRva12004 = 0x2A9A086;
inline constexpr std::size_t kActualArmyDailyAssaultPreparationPatchBytes12004 = 16;
inline constexpr std::size_t kActualArmyDailyAssaultPreparationAbsoluteJumpBytes12004 = 14;
inline constexpr std::size_t kActualArmyDailyAssaultPreparationEntryThunkBytes12004 = 20;
inline constexpr std::size_t kActualArmyDailyAssaultPreparationJournalCapacity12004 = 64;

// Only RCX/RDX have source-defined input meanings. The unused return register is
// preserved as opaque bits, including when observation is incomplete.
using ActualArmyDailyAssaultPreparationOriginal12004 = std::uint64_t(__fastcall *)(const void *, const void *);
using ActualArmyDailyAssaultPreparationRead12004 = bool (*)(void *, const void *, void *, std::size_t) noexcept;
using ActualArmyDailyAssaultPreparationVirtualAlloc12004 = void *(*)(void *, std::size_t, DWORD, DWORD) noexcept;
using ActualArmyDailyAssaultPreparationVirtualFree12004 = bool (*)(void *, void *, std::size_t, DWORD) noexcept;
using ActualArmyDailyAssaultPreparationVirtualProtect12004 = bool (*)(void *, void *, std::size_t, DWORD, DWORD &) noexcept;
using ActualArmyDailyAssaultPreparationFlush12004 = bool (*)(void *, const void *, std::size_t) noexcept;

struct ActualArmyDailyAssaultPreparationBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ActualArmyDailyAssaultPreparationRead12004 read_memory = nullptr;
};
struct ActualArmyDailyAssaultPreparationInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ActualArmyDailyAssaultPreparationBindings12004 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ActualArmyDailyAssaultPreparationVirtualAlloc12004 virtual_alloc_override = nullptr;
  ActualArmyDailyAssaultPreparationVirtualFree12004 virtual_free_override = nullptr;
  ActualArmyDailyAssaultPreparationVirtualProtect12004 virtual_protect_override = nullptr;
  ActualArmyDailyAssaultPreparationFlush12004 flush_instruction_cache_override = nullptr;
};
struct ActualArmyDailyAssaultPreparationDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kActualArmyDailyAssaultPreparationPatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualArmyDailyAssaultPreparationVirtualFree12004 virtual_free = nullptr;
  ActualArmyDailyAssaultPreparationVirtualProtect12004 virtual_protect = nullptr;
  ActualArmyDailyAssaultPreparationFlush12004 flush_instruction_cache = nullptr;
};
enum ActualArmyDailyAssaultPreparationInstallFailure12004 : std::uint32_t {
  actual_army_preparation_install_none = 0,
  actual_army_preparation_install_exact_build = 1U << 0,
  actual_army_preparation_install_quiescence = 1U << 1,
  actual_army_preparation_install_already_installed = 1U << 2,
  actual_army_preparation_install_anchor = 1U << 3,
  actual_army_preparation_install_allocation = 1U << 4,
  actual_army_preparation_install_protection = 1U << 5,
  actual_army_preparation_install_flush = 1U << 6,
  actual_army_preparation_install_rollback = 1U << 7,
};
enum ActualArmyDailyAssaultPreparationCaptureFailure12004 : std::uint32_t {
  actual_army_preparation_capture_before = 1U << 0,
  actual_army_preparation_capture_after = 1U << 1,
  actual_army_preparation_capture_parent = 1U << 2,
  actual_army_preparation_capture_roster = 1U << 3,
  actual_army_preparation_capture_identity_changed = 1U << 4,
  actual_army_preparation_capture_exception = 1U << 5,
};

struct ActualArmyDailyAssaultPreparationSnapshot12004 {
  std::optional<std::uint32_t> selected_army_full_id_raw_u32;
  std::optional<std::uintptr_t> game_state_identity_raw;
  std::optional<bool> game_state_matches_parent;
  std::optional<std::uint64_t> game_date_raw_u64;
  std::optional<std::uint32_t> absolute_day_raw_u32;
  std::optional<std::uint8_t> calendar_flags_raw_u8;
  // Reads use the original RDX instance. This is a source-derived conditional
  // request, independent of the fact that the native callback returned.
  game::ArmyDailyAssaultRosterAdmissionOccurrenceV1 selected_occurrence{};
  game::ArmyDailyAssaultRawReferencesV1 removal_queue{};
  std::optional<DailyAssaultPreparationInput12004> copied_stage_input;
  bool source_inputs_ready = false;
};
struct ActualArmyDailyAssaultPreparationActive12004 {
  bool observed = false, parent_bound = false, original_occurrence_bound = false;
  ArmyNaturalPhaseScope12004 parent{};
  ArmyNaturalPhaseEvent12004 entry_event{};
  std::uintptr_t incoming_primary_manager = 0, incoming_selected_army = 0;
  std::uintptr_t caller_return_rva = 0, callsite_rva = 0;
  std::uintptr_t actual_caller_iterator = 0, actual_caller_end = 0;
  std::optional<std::int32_t> native_occurrence_index, local_start_index;
  std::optional<std::uint32_t> requested_army_full_id_u32;
  std::optional<std::uint32_t> iterator_entry_full_id_u32;
  std::optional<std::uint32_t> selected_army_full_id_raw_u32;
};
struct ActualArmyDailyAssaultPreparationObservation12004 {
  std::uint64_t sequence = 0;
  ActualArmyDailyAssaultPreparationActive12004 active{};
  ActualArmyDailyAssaultPreparationSnapshot12004 before{}, after{};
  ArmyNaturalPhaseEvent12004 returned_event{};
  bool original_called = false, original_returned = false;
  std::uint64_t original_rax_raw_u64 = 0;
  std::optional<bool> same_selected_army_generation_after;
  std::uint32_t capture_failure_flags = 0;
};
struct ActualArmyDailyAssaultPreparationObservations12004 {
  bool observer_installed = false, current_session_guard = false;
  std::uint64_t oldest_available_sequence = 0, latest_sequence = 0;
  std::uint64_t overwritten_events = 0, unattributed_capture_failures = 0;
  std::uint64_t dropped_owned_copy_events = 0;
  std::vector<ActualArmyDailyAssaultPreparationObservation12004> events;
};

ActualArmyDailyAssaultPreparationBindings12004 BindActualArmyDailyAssaultPreparationImage12004(
    std::uintptr_t, std::string_view) noexcept;
bool InstallActualArmyDailyAssaultPreparationObserver12004(
    ActualArmyDailyAssaultPreparationDetourState12004 &,
    const ActualArmyDailyAssaultPreparationInstallEnvironment12004 &, std::string_view) noexcept;
ActualArmyDailyAssaultPreparationActive12004 CopyActiveActualArmyDailyAssaultPreparation12004() noexcept;
// Query join is exact before-entry CArmy FullID, including generation bits. It
// returns owned past observations and never resolves or calls a native callback.
std::optional<ActualArmyDailyAssaultPreparationObservations12004>
ReadActualArmyDailyAssaultPreparationObservations12004(std::uint32_t exact_full_carmy_id) noexcept;
extern "C" std::uint64_t __fastcall XarActualArmyDailyAssaultPreparationHook12004(
    const void *, const void *, std::uintptr_t actual_r15, std::uintptr_t actual_r12) noexcept;
// Owned fixture uses the same observation path; it does not patch or execute the
// game. Production reaches the entry thunk with the actual native R15/R12.
bool InitializeActualArmyDailyAssaultPreparationFixture12004(
    const ActualArmyDailyAssaultPreparationBindings12004 &,
    ActualArmyDailyAssaultPreparationOriginal12004) noexcept;
std::uint64_t InvokeActualArmyDailyAssaultPreparationFixture12004(
    std::uintptr_t caller_return_rva, const void *, const void *,
    std::uintptr_t actual_r15, std::uintptr_t actual_r12) noexcept;
} // namespace xar::ck3_12004
