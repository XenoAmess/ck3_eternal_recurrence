#pragma once

#include "xar_bridge/actual_army_daily_assault_preparation_observer_12004.hpp"
#include "xar_bridge/army_assault_group_placement_12004.hpp"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
#include <windows.h>

#define XAR_HAS_ACTUAL_ARMY_ASSAULT_PLACEMENT_12004 1
namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kActualArmyAssaultPlacementRva12004 = 0x2AA2010;
inline constexpr std::uintptr_t kActualArmyAssaultPlacementDirectReturnRva12004 = 0x2A99C7F;
inline constexpr std::uintptr_t kActualArmyAssaultPlacementRecursiveReturnRva12004 = 0x2AA226D;
inline constexpr std::uintptr_t kActualArmyAssaultEmptyStorageRva12004 = 0x5D68C00;
inline constexpr std::size_t kActualArmyAssaultPlacementPatchBytes12004 = 19;
inline constexpr std::size_t kActualArmyAssaultPlacementAbsoluteJumpBytes12004 = 14;
inline constexpr std::size_t kActualArmyAssaultPlacementJournalCapacity12004 = 16;
using ActualArmyAssaultPlacementOriginal12004 = std::uint64_t(__fastcall *)(const void *, void *, std::uint32_t, const std::uint32_t *);
using ActualArmyAssaultPlacementRead12004 = ActualArmyDailyAssaultPreparationRead12004;
struct ActualArmyAssaultPlacementBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void *read_context = nullptr;
  ActualArmyAssaultPlacementRead12004 read_memory = nullptr;
};
struct ActualArmyAssaultPlacementInstallEnvironment12004 {
  bool primary_thread_suspended_proven = false;
  ActualArmyAssaultPlacementBindings12004 bindings{};
  std::uintptr_t callback_target_override = 0;
  void *memory_context = nullptr;
  ActualArmyDailyAssaultPreparationVirtualAlloc12004 virtual_alloc_override = nullptr;
  ActualArmyDailyAssaultPreparationVirtualFree12004 virtual_free_override = nullptr;
  ActualArmyDailyAssaultPreparationVirtualProtect12004 virtual_protect_override = nullptr;
  ActualArmyDailyAssaultPreparationFlush12004 flush_instruction_cache_override = nullptr;
};
struct ActualArmyAssaultPlacementDetourState12004 {
  std::atomic<std::uint32_t> installed{0}, failure_flags{0};
  std::uintptr_t callback_target = 0;
  void *trampoline = nullptr;
  std::array<std::uint8_t, kActualArmyAssaultPlacementPatchBytes12004> original{};
  void *memory_context = nullptr;
  ActualArmyDailyAssaultPreparationVirtualFree12004 virtual_free = nullptr;
  ActualArmyDailyAssaultPreparationVirtualProtect12004 virtual_protect = nullptr;
  ActualArmyDailyAssaultPreparationFlush12004 flush_instruction_cache = nullptr;
};
enum ActualArmyAssaultPlacementInstallFailure12004 : std::uint32_t {
  actual_army_placement_install_none = 0,
  actual_army_placement_install_exact_build = 1U << 0,
  actual_army_placement_install_quiescence = 1U << 1,
  actual_army_placement_install_already_installed = 1U << 2,
  actual_army_placement_install_anchor = 1U << 3,
  actual_army_placement_install_allocation = 1U << 4,
  actual_army_placement_install_protection = 1U << 5,
  actual_army_placement_install_flush = 1U << 6,
  actual_army_placement_install_rollback = 1U << 7,
};
enum ActualArmyAssaultPlacementCaptureFailure12004 : std::uint32_t {
  actual_army_placement_capture_parent = 1U << 0,
  actual_army_placement_capture_receiver = 1U << 1,
  actual_army_placement_capture_before = 1U << 2,
  actual_army_placement_capture_after = 1U << 3,
  actual_army_placement_capture_request = 1U << 4,
  actual_army_placement_capture_output = 1U << 5,
  actual_army_placement_capture_exception = 1U << 6,
};
struct ActualArmyAssaultPlacementVectorBound12004 {
  std::int64_t physical_slot_i64 = 0;
  bool arrg = false;
  std::int32_t actual_count_raw_i32 = 0;
};
struct ActualArmyAssaultPlacementSnapshot12004 {
  std::string stage;
  ArmyNaturalPhaseEvent12004 capture_event{};
  std::uintptr_t receiver_table_identity = 0;
  std::optional<std::uintptr_t> entries_identity;
  std::optional<bool> native_empty_storage_matches;
  std::optional<std::int32_t> occupied_count_raw_i32, mask_raw_i32;
  std::optional<std::uint8_t> tail_distance_raw_u8;
  std::optional<std::uint32_t> load_factor_f32_bits_u32;
  std::optional<std::uintptr_t> table_allocator_identity;
  std::optional<bool> current_primary_table_matches_receiver;
  game::ArmyCurrentDailyAssaultTableV1 physical_table{};
  bool capture_complete = false, budget_exhausted = false;
  std::size_t read_calls = 0, read_bytes = 0, admitted_reference_count = 0;
  // Counts refused by the bounded collector remain actual raw evidence here.
  std::vector<ActualArmyAssaultPlacementVectorBound12004> denied_vector_counts;
};
struct ActualArmyAssaultPlacementObservation12004 {
  std::uint64_t sequence = 0;
  ActualArmyDailyAssaultPreparationActive12004 preparation{};
  ArmyNaturalPhaseEvent12004 entry_event{}, returned_event{};
  std::uintptr_t caller_return_rva = 0, incoming_table_identity = 0;
  std::uintptr_t incoming_output_identity = 0, incoming_key_identity = 0;
  std::uint32_t incoming_hash_raw_u32 = 0;
  std::optional<std::uint32_t> incoming_key_raw_u32;
  std::optional<std::uint32_t> selected_army_full_id_at_placement_u32;
  std::optional<bool> entries_identity_changed;
  bool parent_bound = false, recursive = false;
  ActualArmyAssaultPlacementSnapshot12004 before{}, after{};
  bool original_called = false, original_returned = false;
  std::uint64_t original_rax_raw_u64 = 0;
  std::optional<std::uintptr_t> returned_entry_identity;
  std::optional<std::uint8_t> returned_inserted_raw_u8;
  std::optional<std::int64_t> returned_physical_slot_i64;
  std::uint32_t capture_failure_flags = 0;
};
struct ActualArmyAssaultPlacementObservations12004 {
  bool observer_installed = false, current_session_guard = false;
  std::uint64_t oldest_available_sequence = 0, latest_sequence = 0;
  std::uint64_t overwritten_events = 0, unattributed_capture_failures = 0;
  std::vector<ActualArmyAssaultPlacementObservation12004> events;
};
struct ActualArmyAssaultPlacementProjection12004 {
  bool mapping_ready = false;
  std::string unavailable_reason;
  // Source projection includes the later preparation append. Actual aftertable
  // above is immediate-after-placement, before that append occurs.
  std::string projected_stage = "conditional_after_preparation_append";
  std::optional<AssaultPlacementResult12004> projection;
};
ActualArmyAssaultPlacementBindings12004 BindActualArmyAssaultPlacementImage12004(std::uintptr_t, std::string_view) noexcept;
bool InstallActualArmyAssaultPlacementObserver12004(ActualArmyAssaultPlacementDetourState12004 &,
    const ActualArmyAssaultPlacementInstallEnvironment12004 &, std::string_view) noexcept;
std::optional<ActualArmyAssaultPlacementObservations12004>
ReadActualArmyAssaultPlacementObservations12004(std::uint32_t exact_full_carmy_id) noexcept;
ActualArmyAssaultPlacementProjection12004 ProjectActualArmyAssaultPlacementObservation12004(
    const ActualArmyAssaultPlacementObservation12004 &,
    const ActualArmyDailyAssaultPreparationObservation12004 &);
extern "C" std::uint64_t __fastcall XarActualArmyAssaultPlacementHook12004(
    const void *, void *, std::uint32_t, const std::uint32_t *) noexcept;
bool InitializeActualArmyAssaultPlacementFixture12004(const ActualArmyAssaultPlacementBindings12004 &,
    ActualArmyAssaultPlacementOriginal12004) noexcept;
std::uint64_t InvokeActualArmyAssaultPlacementFixture12004(std::uintptr_t caller_return_rva,
    const void *, void *, std::uint32_t, const std::uint32_t *) noexcept;
} // namespace xar::ck3_12004
