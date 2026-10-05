#pragma once

#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/ck3_combat_effect_reader.hpp"

namespace xar::ck3_12002 {
inline game::BattleRetainedRuleEffectsV1 ReadRetainedConstructorRuleEffects(
    GetCombatRules get_rules, std::int32_t kind) {
  using combat_effect_detail::Load;
  using combat_effect_detail::ReadKey;
  using combat_effect_detail::ValidEffect;
  game::BattleRetainedRuleEffectsV1 out;
  if (kind < 0 || kind > 3) {
    out.unavailable_reason = "unsupported_retained_constructor_kind";
    return out;
  }
  auto *rules = get_rules ? get_rules() : nullptr;
  if (!rules) {
    out.unavailable_reason = "loaded_phase_effect_rules_unavailable";
    return out;
  }
  const char *stages[]{"attacker_adjacency", "defender_adjacency", "holding_defender"};
  const std::uint32_t offsets[]{0xF70U + 8U * static_cast<std::uint32_t>(kind),
                              0xFA0U + 8U * static_cast<std::uint32_t>(kind), 0xF10U};
  for (std::size_t i = 0; i < 3; ++i) {
    game::BattleRetainedRuleEffectV1 row;
    row.stage = stages[i];
    row.side_index = i == 0 ? 0 : 1;
    row.rules_pointer_offset = offsets[i];
    auto *effect = Load<void *>(rules, offsets[i]);
    if (!ValidEffect(effect)) {
      if (i < 2) row.status = "not_selected";
      else row.unavailable_reason = "holding_defender_effect_unavailable";
    } else {
      std::string key;
      if (!ReadKey(effect, key)) row.unavailable_reason = "loaded_effect_key_unavailable";
      else if (i == 2 && key != "holding_defender_advantage")
        row.unavailable_reason = "holding_defender_effect_key_mismatch";
      else {
        row.status = "available";
        row.key = std::move(key);
        row.advantage_points = Load<std::int32_t>(effect, 0x40);
      }
    }
    if (row.status == "unavailable" && out.unavailable_reason.empty())
      out.unavailable_reason = row.unavailable_reason;
    out.rows.push_back(std::move(row));
  }
  out.available = out.unavailable_reason.empty();
  return out;
}
} // namespace xar::ck3_12002
