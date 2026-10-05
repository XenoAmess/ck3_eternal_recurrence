#pragma once

#include "xar_bridge/battle_current_dynamic_components_serializer.hpp"

#include <utility>

namespace xar::bridge {
inline std::string SerializeCurrentOwnNestedModifierV1(
    const game::BattleCurrentOwnNestedModifierV1 &inputs) {
  using current_components_wire_detail::Status;
  using current_components_wire_detail::Value;
  std::string out = "{\"scale\":100000,\"modifier_id\":415,\"sides\":[";
  for (std::size_t index = 0; index < inputs.sides.size(); ++index) {
    if (index) out += ',';
    const auto &side = inputs.sides[index];
    out += "{\"side_index\":" + std::to_string(side.side_index);
    out += ",\"selected_character_id_raw\":" + std::to_string(side.selected_character_id_raw);
    out += ",\"selection\":{";
    Status(out, side.resolved_character_id_raw.has_value(), side.selection_unavailable_reason);
    out += ",\"resolved_character_id_raw\":";
    Value(out, side.resolved_character_id_raw);
    out += ",\"used_native_fallback\":";
    out += !side.used_native_fallback ? "null" : (*side.used_native_fallback ? "true" : "false");
    out += '}';
    const std::array<std::pair<const char *, const game::BattleCurrentOwnModifierAmountV1 *>, 2> scopes{{
        {"combat_side_aggregate", &side.combat_side_aggregate},
        {"selected_character_aggregate", &side.selected_character_aggregate}}};
    for (const auto &[scope, amount] : scopes) {
      out += ",\"";
      out += scope;
      out += "\":{";
      Status(out, amount->amount_raw.has_value(), amount->unavailable_reason);
      out += ",\"amount_raw\":";
      Value(out, amount->amount_raw);
      out += '}';
    }
    out += '}';
  }
  out += "]}";
  return out;
}
} // namespace xar::bridge
