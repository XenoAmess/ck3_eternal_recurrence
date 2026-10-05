#pragma once

#include "xar_bridge/game_contract.hpp"

#include <string>

namespace xar::bridge {
namespace current_components_wire_detail {
inline void Status(std::string &out, bool available, const std::string &reason) {
  out += available ? "\"status\":\"available\",\"unavailable_reason\":null"
                   : "\"status\":\"unavailable\",\"unavailable_reason\":\"" + reason + '"';
}
template <typename T>
void Value(std::string &out, const std::optional<T> &value) {
  out += value ? std::to_string(*value) : "null";
}
} // namespace current_components_wire_detail
inline std::string SerializeCurrentDynamicComponentsV1(
    const game::BattleCurrentDynamicComponentsV1 &inputs) {
  using current_components_wire_detail::Status;
  using current_components_wire_detail::Value;
  std::string out = "{\"scale\":100000,\"sides\":[";
  for (std::size_t index = 0; index < inputs.sides.size(); ++index) {
    if (index) out += ',';
    const auto &side = inputs.sides[index];
    out += "{\"side_index\":" + std::to_string(side.side_index);
    out += ",\"current_roll_points\":" + std::to_string(side.current_roll_points);
    out += ",\"selected_character_id_raw\":" + std::to_string(side.selected_character_id_raw);
    out += ",\"selection\":{";
    Status(out, side.resolved_character_id_raw.has_value(), side.selection_unavailable_reason);
    out += ",\"resolved_character_id_raw\":";
    Value(out, side.resolved_character_id_raw);
    out += ",\"used_native_fallback\":";
    out += !side.used_native_fallback ? "null" : (*side.used_native_fallback ? "true" : "false");
    out += "},\"relation\":{";
    Status(out, side.relation_kind_raw.has_value(), side.relation_unavailable_reason);
    out += ",\"kind_raw\":";
    Value(out, side.relation_kind_raw);
    out += "},\"commander\":{";
    Status(out, side.commander_dynamic_raw.has_value(), side.commander_unavailable_reason);
    out += ",\"total_raw\":";
    Value(out, side.commander_dynamic_raw);
    out += "},\"side_aggregate\":{";
    Status(out, side.side_aggregate_dynamic_raw.has_value(), side.side_aggregate_unavailable_reason);
    out += ",\"total_raw\":";
    Value(out, side.side_aggregate_dynamic_raw);
    out += "}}";
  }
  out += "]}";
  return out;
}
} // namespace xar::bridge
