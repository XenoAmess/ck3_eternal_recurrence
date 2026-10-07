#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {

// Source-derived clock and calendar values from the current capture.
// Future GameState, executed date stages and effects remain independent.
struct ArmySourceDerivedNextDailySupplyFrameInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::uint32_t> subject_army_id_u32;
  std::optional<std::uint32_t> subject_carmy_id_u32;
  std::optional<std::int64_t> current_date_storage_raw64;
  std::optional<std::int32_t> current_date_raw_i32;
  std::optional<std::int32_t> current_native_day_index_raw_i32;
  std::optional<std::int32_t> source_derived_next_date_raw_i32;
  std::optional<std::int32_t> source_derived_next_native_day_index_raw_i32;
  std::optional<std::int64_t> source_derived_next_date_storage_raw64;
  std::optional<std::uint8_t> source_derived_next_calendar_day_u8;
  std::optional<std::uint8_t> source_derived_next_calendar_month_u8;
  bool source_derived_full_cdate64_ready = false;

  friend bool operator==(const ArmySourceDerivedNextDailySupplyFrameInputsV1 &,
                         const ArmySourceDerivedNextDailySupplyFrameInputsV1 &) = default;
};

} // namespace xar::game

namespace xar::ck3_12004 {
struct SourceDerivedNextDailySupplyFrameBindings12004 {
  bool enabled = false;
  const std::uint8_t *calendar_day_table = nullptr;
  const std::uint8_t *calendar_month_table = nullptr;
};
} // namespace xar::ck3_12004
