#pragma once

#include "xar_bridge/army_daily_assault_preparation_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {

enum class AssaultPlacementBaselineStage12004 {
  conditional_current_table,
  pre_date_copied_table,
};

struct AssaultPlacementBaseline12004 {
  AssaultPlacementBaselineStage12004 stage =
      AssaultPlacementBaselineStage12004::conditional_current_table;
  std::string source_provenance;
  std::string frame_identity;
  // Exact comparison of the supplied table storage with actual helper
  // 2A9E8A0's native empty-storage identity (RVA5D68C00).
  std::optional<bool> native_empty_storage_matches;
  std::size_t operation_limit = 1000000;
};

struct AssaultPlacementGroup12004 {
  game::ArmyDailyAssaultGroupV1 value{};
  // Constructed/moved canonical values are source-derived premises. They do
  // not manufacture an actual allocator read in value.*.allocator_witness.
  bool army_allocator_canonical_by_source = false;
  bool arrg_allocator_canonical_by_source = false;
};

struct AssaultPlacementGrowthRelease12004 {
  std::size_t growth_index = 0;
  std::int64_t old_physical_slot_i64 = 0;
  std::uint32_t callsite_rva = 0x2A9FE71;
  std::string stage = "growth_after_2AA2870_before_9D11F0";
  bool source_value_moved = false;
  game::ArmyDailyAssaultArmyReferencesV1 armies_after_transfer{};
  game::ArmyDailyAssaultArRgReferencesV1 arrgs_after_transfer{};
};

struct AssaultPlacementGrowth12004 {
  std::uint32_t source_rva = 0x2A9FDA0;
  std::int32_t index_i32 = 0, old_occupied_count_i32 = 0;
  std::int32_t new_mask_i32 = 0, new_end_slot_i32 = 0;
  std::uint8_t new_tail_u8 = 0;
  std::uint64_t allocated_record_count = 0, allocated_bytes = 0;
  std::string symbolic_storage_identity;
  std::vector<std::int64_t> old_reinsert_physical_order;
  std::optional<bool> old_table_release_selected;
};

struct AssaultPlacementRequestResult12004 {
  std::int32_t native_occurrence_index = 0;
  std::string status = "not_reached";
  std::string branch, unavailable_reason;
  std::optional<std::int64_t> returned_physical_slot_i64;
  std::optional<bool> inserted;
};

struct AssaultPlacementResult12004 {
  std::string source = "actual4_source_bound_assault_group_placement";
  std::string stage = "conditional_projection";
  std::string frame_identity, source_provenance;
  bool ready = false;
  std::string unavailable_reason;
  std::size_t applied_request_count = 0;
  std::optional<game::ArmyCurrentDailyAssaultTableV1> observed_current_table;
  game::ArmyDailyAssaultTableHeaderV1 projected_header{};
  std::vector<game::ArmyDailyAssaultControlV1> projected_physical_controls;
  // Growth source proves all unspecified controls [0,end) are zero. This
  // range avoids materializing up to 2^30 empty records in a pure projection.
  bool unspecified_controls_zero = false;
  std::optional<std::int64_t> zero_control_extent_end_i64;
  std::vector<AssaultPlacementGroup12004> projected_groups;
  bool projected_physical_group_order_ready = false;
  std::vector<AssaultPlacementGrowth12004> growth;
  std::vector<AssaultPlacementGrowthRelease12004> growth_release_inputs;
  std::vector<AssaultPlacementRequestResult12004> requests;
  bool normal_return_premise = true;
  bool actual_callback_execution_observed = false;
  bool full_future_table_placement_ready = false;
  bool full_daily_assault_ready = false;
  bool full_monthly_execution_ready = false;
};

// Uses copied readonly preparation and a separate explicit baseline premise.
// A pre-date stream starts at its bound original-roster occurrence; Root
// explicitly supplies that suffix, so earlier appends are never replayed.
// Executes no reader, callback, allocation, release or native write.
AssaultPlacementResult12004 ProjectAssaultGroupPlacement12004(
    const DailyAssaultPreparationInput12004 &preparation,
    const AssaultPlacementBaseline12004 &baseline);

} // namespace xar::ck3_12004
