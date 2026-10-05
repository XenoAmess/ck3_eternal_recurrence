#pragma once

#include "xar_bridge/ck3_12002_phase.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstring>

namespace xar::ck3_12002 {
namespace current_dynamic_detail {
template <typename T> T Load(const void *source, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(source) + offset, sizeof(result));
  return result;
}
} // namespace current_dynamic_detail

// Exact .3 258A470, actual resolved Combat, local output, null explanation sink.
// This does not call 258B510 or refresh commander, accolade or Entry state.
inline game::BattleCurrentDynamicAdvantageV1 ReadCurrentDynamicAdvantage12003(
    void *combat, ReadPhaseDynamic read_side_dynamic) {
  using current_dynamic_detail::Load;
  game::BattleCurrentDynamicAdvantageV1 result;
  result.base_advantage_raw = Load<std::int64_t>(combat, 0x6C8);
  result.stored_resolved_advantage_raw = Load<std::int64_t>(combat, 0x710);
  for (std::size_t index = 0; index < result.sides.size(); ++index) {
    auto &side = result.sides[index];
    side.side_index = static_cast<std::int32_t>(index);
    side.current_roll_points = Load<std::int32_t>(combat, 0x6D0 + index * 4);
    side.selected_character_id_raw = Load<std::int32_t>(combat, 0x94 + index * 0x348);
    if (!read_side_dynamic) {
      side.unavailable_reason = "current_side_dynamic_getter_258A470_unbound";
      continue;
    }
    std::int64_t total = 0;
    if (read_side_dynamic(combat, &total, side.side_index, nullptr) != &total) {
      side.unavailable_reason = "current_side_dynamic_getter_258A470_output_unavailable";
      continue;
    }
    side.side_dynamic_total_raw = total;
  }
  return result;
}
} // namespace xar::ck3_12002
