#pragma once
#include "xar_bridge/army_assault_consumer_parent_12004.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace xar::ck3_12004 {
inline constexpr std::size_t kAssaultConsumerMaximumSlots12004 = 512;
inline constexpr std::size_t kAssaultConsumerMaximumGroups12004 = 32;
inline constexpr std::size_t kAssaultConsumerMaximumOccurrences12004 = 128;
inline constexpr std::size_t kAssaultConsumerMaximumRegiments12004 = 256;
inline constexpr std::size_t kAssaultConsumerMaximumDataRecords12004 = 1024;
inline constexpr std::size_t kAssaultConsumerJournalEvents12004 = 8;

struct AssaultConsumerVector12004 {
  std::optional<std::uintptr_t> data_identity;
  std::optional<std::int32_t> capacity, count;
  std::optional<std::uintptr_t> allocator_identity;
  bool references_complete = false;
  std::vector<std::optional<std::uint32_t>> ordered_full_ids;
};
struct AssaultConsumerResolved12004 {
  std::optional<std::uint32_t> requested_full_id;
  std::optional<std::uintptr_t> object_identity;
  std::optional<std::uint32_t> selected_full_id;
  std::optional<bool> used_fallback;
};
struct AssaultConsumerArmy12004 {
  std::int32_t native_index = 0;
  AssaultConsumerResolved12004 resolution;
  AssaultConsumerVector12004 regiment_roster;
  // This getter is not called by passive capture.
  std::optional<std::int32_t> native_whole_current_soldiers;
};
struct AssaultConsumerGroup12004 {
  std::int32_t native_index = 0;
  std::int64_t physical_slot = 0;
  std::optional<std::uint8_t> control;
  std::optional<std::uint32_t> hash, siege_full_id;
  AssaultConsumerResolved12004 siege_resolution;
  std::optional<std::uintptr_t> province_identity;
  std::optional<std::uint32_t> province_magic, province_full_id;
  std::optional<std::int32_t> breach_level;
  // The original calls 25205A0 later at each group. No getter is invoked here.
  std::optional<std::int32_t> native_current_expected_loss;
  ArmyNaturalPhaseEvent12004 budget_entry_event, budget_returned_event;
  bool natural_budget_observed = false;
  bool besieging_dependencies_complete = false;
  AssaultConsumerVector12004 armies, arrgs;
  std::vector<AssaultConsumerArmy12004> army_occurrences;
};
struct AssaultConsumerTable12004 {
  std::optional<std::uintptr_t> entries_identity;
  std::optional<std::int32_t> occupied_count, mask, end_slot;
  std::optional<std::uint8_t> tail_distance, end_marker_control;
  std::optional<std::uint32_t> load_factor_bits;
  bool controls_complete = false, raw_references_complete = false;
  std::vector<std::optional<std::uint8_t>> physical_controls;
  std::vector<AssaultConsumerGroup12004> groups;
};
struct AssaultConsumerPhysical12004 {
  std::uintptr_t object_identity = 0;
  std::optional<std::int32_t> maximum, current, persistent_full_id,
      own_ordinal, army_regiment_full_id, state;
};
struct AssaultConsumerData12004 {
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> persistent_full_id;
  std::optional<std::int32_t> data_ordinal;
  AssaultConsumerResolved12004 persistent_resolution;
  std::optional<bool> persistent_identity_valid;
  std::optional<AssaultConsumerPhysical12004> physical;
  bool ready = false;
};
struct AssaultConsumerRegiment12004 {
  AssaultConsumerResolved12004 resolution;
  std::optional<std::uint32_t> magic;
  std::optional<bool> identity_valid, native_loss_writer_skipped;
  std::optional<std::int32_t> current, maximum, definition_type;
  std::optional<std::uintptr_t> data_identity;
  std::optional<std::int32_t> data_capacity, data_count;
  bool data_complete = false;
  std::optional<bool> same_instance_after, same_data_header_after;
  std::vector<AssaultConsumerData12004> data_records;
};
struct ArmyActualAssaultConsumerObservationV1 {
  std::uint64_t journal_sequence = 0;
  ArmyAssaultConsumerParent12004 parent;
  ArmyNaturalPhaseEvent12004 returned_event;
  bool original_called = false, original_returned = false;
  bool current_session_guard = false;
  std::uintptr_t raw_return_bits = 0;
  std::uint32_t capture_failure_flags = 0;
  AssaultConsumerTable12004 entry_table, returned_table;
  AssaultConsumerVector12004 entry_pending_queue, returned_pending_queue;
  std::vector<AssaultConsumerRegiment12004> entry_regiments, returned_regiments;
  bool entry_dependencies_complete = false;
  bool returned_dependencies_complete = false;
  // Full B, statistics and lifecycle context are not guessed from later queries.
  bool conditional_stage_binding_ready = false;
};
struct ArmyActualAssaultConsumerObservationsV1 {
  bool observer_installed = false;
  bool current_session_guard = false;
  std::uint64_t latest_journal_sequence = 0, overwritten_events = 0;
  std::vector<ArmyActualAssaultConsumerObservationV1> events;
};
} // namespace xar::ck3_12004
