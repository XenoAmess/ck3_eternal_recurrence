#pragma once

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12003 {

// Current total skill cache for the actual CArmy+120 role holder. This is
// independent of candidate quality and any actual/hypothetical side selection.
struct CurrentCommanderTotalMartialSnapshot {
  std::string_view status = "unavailable";
  std::string_view source = "native_current_assigned_commander_total_skill_cache";
  std::optional<std::int32_t> source_character_id;
  std::int32_t skill_index = 1;
  std::optional<std::int32_t> value;
  std::string_view unavailable_reason = "current_commander_skill_not_read";
};

} // namespace xar::ck3_12003
