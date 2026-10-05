#pragma once

#include "xar_bridge/ck3_combat_effect_reader.hpp"
#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_12002 {
// Exact2589663/258966C: raw loaded eligibility bytes, independent of key decode.
inline game::BattleStoredEffectFlagsV1 ReadStoredEffectFlags12003(const void *effect) {
  game::BattleStoredEffectFlagsV1 result;
  if (!effect) {
    result.unavailable_reason = "stored_effect_flags_88_89_effect_pointer_unavailable";
    return result;
  }
  result.flag88_raw = combat_effect_detail::Load<std::uint8_t>(effect, 0x88);
  result.flag89_raw = combat_effect_detail::Load<std::uint8_t>(effect, 0x89);
  return result;
}
} // namespace xar::ck3_12002
