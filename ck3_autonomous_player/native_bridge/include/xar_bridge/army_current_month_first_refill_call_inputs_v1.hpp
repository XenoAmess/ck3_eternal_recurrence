#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
struct ArmyCurrentMonthFirstRefillCallInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::int32_t> subject_army_id;
  std::optional<std::int32_t> subject_carmy_id;
  std::optional<std::uint8_t> game_state_calendar_flags_raw_u8;
  // Native mask0x02, mathematical bit index1; never mask0x04.
  std::optional<bool> month_first_mask_2_set;
  friend bool operator==(const ArmyCurrentMonthFirstRefillCallInputsV1 &,
                         const ArmyCurrentMonthFirstRefillCallInputsV1 &) = default;
};
} // namespace xar::game

namespace xar::ck3_12003 {
struct CurrentMonthFirstRefillCallBindings12003 {
  bool enabled = false;
};
} // namespace xar::ck3_12003
