#pragma once

#include "xar_bridge/ck3_combat_effect_reader.hpp"
#include "xar_bridge/battle_stored_effect_flags_reader.hpp"
#include "xar_bridge/game_contract.hpp"

#include <utility>

namespace xar::ck3_12002 {

// Exact .3 AppendCombatEffect: Combat-relative98/A0/A4 + side*348;
// row+8 is the retained contribution, never a scale or current effect points.
inline game::BattleStoredAdvantageSourcesV1 ReadStoredAdvantageSources12003(
    const void *combat) {
  using combat_effect_detail::Load;
  game::BattleStoredAdvantageSourcesV1 result;
  result.base_advantage_raw = Load<std::int64_t>(combat, 0x6C8);
  result.resolved_advantage_raw = Load<std::int64_t>(combat, 0x710);
  for (std::size_t index = 0; index < result.sides.size(); ++index) {
    auto &side = result.sides[index];
    side.side_index = static_cast<std::int32_t>(index);
    const auto offset = index * 0x348;
    const auto count = Load<std::int32_t>(combat, offset + 0xA4);
    const auto capacity = Load<std::int32_t>(combat, offset + 0xA0);
    const auto *data = Load<const void *>(combat, offset + 0x98);
    if (count < 0 || count > 65'536 || capacity < count ||
        (count > 0 && data == nullptr)) {
      side.unavailable_reason = "stored_advantage_source_vector_unavailable";
      continue;
    }
    side.available = true;
    side.rows.reserve(static_cast<std::size_t>(count));
    for (std::int32_t ordinal = 0; ordinal < count; ++ordinal) {
      const auto row_offset = static_cast<std::size_t>(ordinal) * 0x10;
      game::BattleStoredAdvantageRowV1 row;
      row.contribution_raw = Load<std::int64_t>(data, row_offset + 8);
      auto *effect = Load<void *>(data, row_offset);
      row.effect_flags_v1 = ReadStoredEffectFlags12003(effect);
      std::string key;
      if (combat_effect_detail::ValidEffect(effect) &&
          combat_effect_detail::ReadKey(effect, key)) {
        row.effect_key = std::move(key);
      } else {
        row.key_unavailable_reason = "stored_advantage_effect_key_unavailable";
      }
      side.rows.push_back(std::move(row));
    }
  }
  return result;
}

} // namespace xar::ck3_12002
