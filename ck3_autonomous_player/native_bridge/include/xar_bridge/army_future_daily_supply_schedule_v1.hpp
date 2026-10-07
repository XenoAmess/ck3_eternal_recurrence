#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

// Current native pointer-bucket inputs. Prospective date selection does not
// make any future callback, stock update or manager mutation an observation.
struct ArmyFutureDailySupplySchedulePhaseV1 {
  std::int32_t phase_index_i32 = 0;
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::int32_t> capacity_raw_i32;
  std::optional<std::int32_t> count_raw_i32;
  std::optional<bool> data_pointer_present;
  std::optional<std::vector<std::int32_t>> matching_positions;
  std::optional<std::int32_t> subject_occurrence_count_i32;

  friend bool operator==(const ArmyFutureDailySupplySchedulePhaseV1 &,
                         const ArmyFutureDailySupplySchedulePhaseV1 &) = default;
};

struct ArmyFutureDailySupplyScheduleInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::uint32_t> subject_army_id_u32;
  std::optional<std::uint32_t> subject_carmy_id_u32;
  std::optional<std::int64_t> current_date_storage_raw64;
  std::optional<std::int32_t> current_date_raw_i32;
  std::optional<std::int32_t> native_day_index_raw_i32;
  std::optional<std::int32_t> selected_phase_index_i32;
  std::vector<ArmyFutureDailySupplySchedulePhaseV1> phases;

  friend bool operator==(const ArmyFutureDailySupplyScheduleInputsV1 &,
                         const ArmyFutureDailySupplyScheduleInputsV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_12004 {
struct FutureDailySupplyScheduleBindings12004 {
  bool enabled = false;
};
} // namespace xar::ck3_12004
