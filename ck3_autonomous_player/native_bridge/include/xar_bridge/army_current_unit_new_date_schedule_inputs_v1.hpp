#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

// Raw current scheduling input from the same validated scoped Unit/CArmy row.
// Matching raw IDs do not establish successful native callback execution.
struct ArmyCurrentUnitNewDateScheduleInputsV1 {
  std::int32_t schema_version = 1;
  std::string source = "native_current_unit_new_date_schedule_inputs_12004";
  std::string capture_boundary = "current_query_before_unit_new_date_stage";
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason{};
  std::optional<std::uint32_t> subject_army_id_u32{};
  std::optional<std::uint32_t> subject_carmy_id_u32{};
  std::optional<std::int32_t> vector_header_count_i32{};
  std::optional<bool> vector_data_present{};
  std::optional<std::vector<std::int32_t>> subject_stored_id_positions{};
  std::optional<std::int32_t> subject_stored_id_occurrence_count_i32{};
  bool actual_unit_new_date_callback_observed = false;
  bool actual_movement_or_arrival_observed = false;
  bool earlier_stage_outputs_reconstructed = false;
  bool full_daily_supply_transition_ready = false;
  bool full_monthly_ready = false;

  friend bool operator==(const ArmyCurrentUnitNewDateScheduleInputsV1 &,
                         const ArmyCurrentUnitNewDateScheduleInputsV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_12004 {

// Kept dependency-free so the shared ArmyBindings can own this value.
struct CurrentUnitNewDateScheduleBindings12004 {
  bool enabled = false;
  std::uintptr_t expected_new_date_target = 0;
};

// One owned copy per whole query. No live receiver/data pointer escapes.
struct CurrentUnitNewDateScheduleInventory12004 {
  std::string status = "unavailable";
  std::optional<std::string> unavailable_reason{};
  std::optional<std::int32_t> vector_header_count_i32{};
  std::optional<bool> vector_data_present{};
  std::optional<std::vector<std::uint32_t>> stored_unit_ids{};
};

} // namespace xar::ck3_12004
