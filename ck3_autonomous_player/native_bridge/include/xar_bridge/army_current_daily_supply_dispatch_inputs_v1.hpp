#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
// SOURCE_PREPARED: current selected-bucket raw input, not later callbacks.
struct ArmyCurrentDailySupplyDispatchInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::int32_t> subject_army_id;
  std::optional<std::int32_t> subject_carmy_id;
  std::optional<std::int32_t> current_date_raw;
  std::optional<std::int32_t> native_day_index;
  std::optional<std::int32_t> selected_bucket_phase;
  std::optional<std::int32_t> selected_bucket_capacity_raw;
  std::optional<std::int32_t> selected_bucket_count_raw;
  std::optional<bool> selected_bucket_data_present;
  std::optional<std::vector<std::int32_t>> subject_occurrence_indices;
  std::optional<std::int32_t> subject_dispatch_occurrence_count;
  friend bool operator==(const ArmyCurrentDailySupplyDispatchInputsV1 &,
                         const ArmyCurrentDailySupplyDispatchInputsV1 &) = default;
};
} // namespace xar::game

namespace xar::ck3_12003 {
// Dependency-free tail binding; all actual slots are existing ArmyBindings.
struct CurrentDailySupplyDispatchBindings12003 { bool enabled = false; };
} // namespace xar::ck3_12003
