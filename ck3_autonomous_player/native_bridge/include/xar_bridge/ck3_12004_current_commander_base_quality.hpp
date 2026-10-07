#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

// Actual CArmy+120 role; a candidate row or CombatSide+74 is independent.
struct CurrentCommanderNativeBaseQualitySnapshot {
  std::string_view status = "unavailable";
  std::string_view source =
      "native_current_assigned_commander_ai_base_quality";
  std::optional<std::int32_t> source_character_id;
  std::optional<std::int32_t> value;
  std::string_view unavailable_reason = "current_commander_quality_not_read";
};

using CurrentCommanderNativeBaseQualityReader = std::int32_t (*)(void *);

// The existing owning-thread query supplies its generation-checked role pointer
// only after GetArmyCommander agrees with the Character full-ID resolution.
CurrentCommanderNativeBaseQualitySnapshot
ReadCurrentCommanderNativeBaseQuality(
    std::int32_t actual_character_id, void *validated_current_character,
    CurrentCommanderNativeBaseQualityReader get_native_ai_base_quality) noexcept;

std::string SerializeCurrentCommanderNativeBaseQuality(
    const CurrentCommanderNativeBaseQualitySnapshot &quality);

} // namespace xar::ck3_12004
