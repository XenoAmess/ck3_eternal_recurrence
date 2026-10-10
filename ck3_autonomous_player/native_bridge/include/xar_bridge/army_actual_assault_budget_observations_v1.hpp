#pragma once
#include "xar_bridge/army_assault_consumer_parent_12004.hpp"
#include <cstdint>
#include <optional>
#include <vector>

namespace xar::ck3_12004 {
inline constexpr std::size_t kActualAssaultBudgetJournalEvents12004 = 64;
struct ActualAssaultBudgetReceiver12004 {
  std::optional<std::uint32_t> siege_full_id;
  std::optional<std::uintptr_t> province_identity;
  std::optional<std::uint32_t> province_full_id, province_magic;
  std::optional<std::int32_t> breach_level;
  bool identity_complete = false;
};
struct ArmyActualAssaultBudgetObservationV1 {
  std::uint64_t journal_sequence = 0;
  ArmyAssaultConsumerParent12004 parent;
  ArmyNaturalPhaseEvent12004 entry_event, returned_event;
  std::uint32_t observed_thread_id = 0;
  std::uintptr_t getter_entry_rva = 0, actual_caller_return_rva = 0;
  std::uintptr_t selected_siege_identity = 0;
  ActualAssaultBudgetReceiver12004 entry_receiver, returned_receiver;
  bool original_called = false, original_returned = false;
  std::uintptr_t raw_return_bits = 0;
  std::uint32_t consumed_eax_u32 = 0;
  std::int32_t native_expected_loss_i32 = 0;
  bool parent_still_active = false, same_clock_thread_order = false;
  bool receiver_identity_unchanged = false;
  bool parent_group_budget_recorded = false;
  // The scalar was naturally returned. No B contributor family or stage
  // completeness is inferred from it, even when the parent accepted it.
  bool full_besieging_dependencies_captured = false;
};
struct ArmyActualAssaultBudgetObservationsV1 {
  bool observer_installed = false;
  std::uint64_t latest_journal_sequence = 0, overwritten_events = 0;
  std::vector<ArmyActualAssaultBudgetObservationV1> events;
};
} // namespace xar::ck3_12004
