#pragma once

#include "xar_bridge/battle_current_dynamic_components_reader.hpp"
#include "xar_bridge/ck3_12002_combat.hpp"

namespace xar::ck3_12002 {
struct BattleCurrentOwnModifierBindings12003 {
  bool enabled = false;
  GetCharacterModifierAggregator character_aggregate = nullptr;
  ReadCharacterModifier modifier = nullptr;
};
namespace own_nested_modifier_detail {
inline game::BattleCurrentOwnModifierAmountV1 Amount(
    void *aggregate, const BattleCurrentOwnModifierBindings12003 &b) {
  game::BattleCurrentOwnModifierAmountV1 out;
  if (!aggregate) out.unavailable_reason = "own_character_aggregate_28C3AE0_output_unavailable";
  else if (!b.modifier) out.unavailable_reason = "own_modifier_getter_2303700_unbound";
  else {
    std::int64_t raw = 0;
    // 2303700 consumes sparse component aggregate+68, not whole aggregate.
    if (b.modifier(static_cast<std::byte *>(aggregate) + 0x68, &raw, 0x19F) != &raw)
      out.unavailable_reason = "own_modifier_getter_2303700_output_unavailable";
    else out.amount_raw = raw; // Native missing-key zero remains available.
  }
  return out;
}
} // namespace own_nested_modifier_detail
inline game::BattleCurrentOwnNestedModifierV1 ReadCurrentOwnNestedModifier12003(
    void *combat, const BattleCurrentOwnModifierBindings12003 &b,
    const BattleCurrentDynamicComponentBindings12003 &selection) {
  using current_components_detail::Load;
  game::BattleCurrentOwnNestedModifierV1 result;
  for (std::size_t index = 0; index < result.sides.size(); ++index) {
    auto &side = result.sides[index];
    side.side_index = static_cast<std::int32_t>(index);
    side.selected_character_id_raw = Load<std::int32_t>(combat, 0x94 + index * 0x348);
    game::BattleCurrentDynamicComponentSideV1 selected;
    selected.selected_character_id_raw = side.selected_character_id_raw;
    void *character = current_components_detail::Selected(selection, selected);
    side.resolved_character_id_raw = selected.resolved_character_id_raw;
    side.used_native_fallback = selected.used_native_fallback;
    side.selection_unavailable_reason = selected.selection_unavailable_reason;
    side.combat_side_aggregate = own_nested_modifier_detail::Amount(
        static_cast<std::byte *>(combat) + 0x130 + index * 0x348, b);
    if (!character)
      side.selected_character_aggregate.unavailable_reason = side.selection_unavailable_reason;
    else if (!b.character_aggregate)
      side.selected_character_aggregate.unavailable_reason = "own_character_aggregate_28C3AE0_unbound";
    else side.selected_character_aggregate =
        own_nested_modifier_detail::Amount(b.character_aggregate(character), b);
  }
  return result;
}
} // namespace xar::ck3_12002
