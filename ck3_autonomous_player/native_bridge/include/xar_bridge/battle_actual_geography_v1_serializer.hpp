#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/battle_current_dynamic_components_serializer.hpp"
#include "xar_bridge/battle_stored_effect_flags_serializer.hpp"

#include <string>
#include <string_view>

namespace xar::bridge {
namespace battle_actual_geography_v1_detail {

inline void String(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  out += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') {
      out += '\\';
      out += static_cast<char>(c);
    } else if (c < 0x20U) {
      out += "\\u00";
      out += hex[(c >> 4U) & 0x0FU];
      out += hex[c & 0x0FU];
    } else {
      out += static_cast<char>(c);
    }
  }
  out += '"';
}

} // namespace battle_actual_geography_v1_detail

inline std::string SerializeBattleActualGeographyV1(
    const game::BattleActualGeographyInputsV1 &inputs) {
  using battle_actual_geography_v1_detail::String;
  const auto &terrain = inputs.terrain;
  if (terrain.scale != 100'000 ||
      (terrain.available &&
       (terrain.key.empty() || !terrain.unavailable_reason.empty())) ||
      (!terrain.available && terrain.unavailable_reason.empty())) {
    return {};
  }
  std::string out = "{\"terrain\":{\"status\":";
  String(out, terrain.available ? "available" : "unavailable");
  out += ",\"key\":";
  if (terrain.available) String(out, terrain.key);
  else out += "null";
  out += ",\"combat_width_multiplier_raw\":";
  out += terrain.available
      ? std::to_string(terrain.combat_width_multiplier_raw) : "null";
  out += ",\"scale\":100000,\"unavailable_reason\":";
  if (terrain.available) out += "null";
  else String(out, terrain.unavailable_reason);
  out += "},\"constructor_adjacency_kind_raw\":";
  out += inputs.constructor_adjacency_kind_raw
      ? std::to_string(*inputs.constructor_adjacency_kind_raw) : "null";
  out += ",\"holding_defender\":";
  out += !inputs.holding_defender ? "null"
      : (*inputs.holding_defender ? "true" : "false");
  if (inputs.constructor_rule_effects_v1) {
    const auto &effects = *inputs.constructor_rule_effects_v1;
    out += ",\"constructor_rule_effects_v1\":{\"status\":";
    String(out, effects.available ? "available" : "unavailable");
    out += ",\"points_scale\":1,\"unavailable_reason\":";
    if (effects.available) out += "null";
    else String(out, effects.unavailable_reason);
    out += ",\"rows\":[";
    for (std::size_t i = 0; i < effects.rows.size(); ++i) {
      if (i) out += ',';
      const auto &row = effects.rows[i];
      out += "{\"stage\":";
      String(out, row.stage);
      out += ",\"side_index\":" + std::to_string(row.side_index);
      out += ",\"rules_pointer_offset\":" + std::to_string(row.rules_pointer_offset);
      out += ",\"status\":";
      String(out, row.status);
      out += ",\"key\":";
      if (row.key) String(out, *row.key);
      else out += "null";
      out += ",\"advantage_points\":";
      out += row.advantage_points ? std::to_string(*row.advantage_points) : "null";
      out += ",\"unavailable_reason\":";
      if (row.unavailable_reason.empty()) out += "null";
      else String(out, row.unavailable_reason);
      out += '}';
    }
    out += "]}";
  }
  if (inputs.current_rule_context_v1) {
    const auto &holding = inputs.current_rule_context_v1->holding_multiplier;
    const auto &commander = inputs.current_rule_context_v1->commander_exclusion;
    out += ",\"current_rule_context_v1\":{\"holding_multiplier\":{\"status\":";
    String(out, holding.status);
    out += ",\"scale\":100000,\"province_multiplier_raw\":";
    out += holding.province_multiplier_raw ? std::to_string(*holding.province_multiplier_raw) : "null";
    out += ",\"province_has_holding\":";
    out += !holding.province_has_holding ? "null" : (*holding.province_has_holding ? "true" : "false");
    out += ",\"holding_modifier_raw\":";
    out += holding.holding_modifier_raw ? std::to_string(*holding.holding_modifier_raw) : "null";
    out += ",\"unavailable_reason\":";
    if (holding.unavailable_reason.empty()) out += "null";
    else String(out, holding.unavailable_reason);
    out += "},\"commander_exclusion\":{\"status\":";
    String(out, commander.status);
    out += ",\"selected_character_id_raw\":" + std::to_string(commander.selected_character_id_raw);
    out += ",\"used_native_fallback\":";
    out += !commander.used_native_fallback ? "null" : (*commander.used_native_fallback ? "true" : "false");
    out += ",\"defender_adjacency_excluded\":";
    out += !commander.defender_adjacency_excluded ? "null" : (*commander.defender_adjacency_excluded ? "true" : "false");
    out += ",\"unavailable_reason\":";
    if (commander.unavailable_reason.empty()) out += "null";
    else String(out, commander.unavailable_reason);
    out += "}}";
  }
  if (inputs.stored_advantage_sources_v1) {
    const auto &stored = *inputs.stored_advantage_sources_v1;
    out += ",\"stored_advantage_sources_v1\":{\"scale\":100000,\"base_advantage_raw\":";
    out += std::to_string(stored.base_advantage_raw);
    out += ",\"resolved_advantage_raw\":" + std::to_string(stored.resolved_advantage_raw);
    out += ",\"sides\":[";
    for (std::size_t index = 0; index < stored.sides.size(); ++index) {
      if (index) out += ',';
      const auto &side = stored.sides[index];
      out += "{\"side_index\":" + std::to_string(side.side_index) + ",\"status\":";
      String(out, side.available ? "available" : "unavailable");
      out += ",\"unavailable_reason\":";
      if (side.available) out += "null";
      else String(out, side.unavailable_reason);
      out += ",\"rows\":";
      if (!side.available) out += "null";
      else {
        out += '[';
        for (std::size_t ordinal = 0; ordinal < side.rows.size(); ++ordinal) {
          if (ordinal) out += ',';
          const auto &row = side.rows[ordinal];
          out += "{\"effect_key\":";
          if (row.effect_key) String(out, *row.effect_key);
          else out += "null";
          out += ",\"key_unavailable_reason\":";
          if (row.effect_key) out += "null";
          else String(out, row.key_unavailable_reason);
          out += ",\"contribution_raw\":" + std::to_string(row.contribution_raw);
          if (row.effect_flags_v1)
            out += ",\"effect_flags_v1\":" + SerializeStoredEffectFlagsV1(*row.effect_flags_v1);
          out += '}';
        }
        out += ']';
      }
      out += '}';
    }
    out += "]}";
  }
  if (inputs.current_dynamic_advantage_v1) {
    const auto &current = *inputs.current_dynamic_advantage_v1;
    out += ",\"current_dynamic_advantage_v1\":{\"scale\":100000,\"base_advantage_raw\":";
    out += std::to_string(current.base_advantage_raw);
    out += ",\"stored_resolved_advantage_raw\":" + std::to_string(current.stored_resolved_advantage_raw);
    out += ",\"sides\":[";
    for (std::size_t index = 0; index < current.sides.size(); ++index) {
      if (index) out += ',';
      const auto &side = current.sides[index];
      out += "{\"side_index\":" + std::to_string(side.side_index) + ",\"status\":";
      String(out, side.side_dynamic_total_raw ? "available" : "unavailable");
      out += ",\"current_roll_points\":" + std::to_string(side.current_roll_points);
      out += ",\"selected_character_id_raw\":" + std::to_string(side.selected_character_id_raw);
      out += ",\"side_dynamic_total_raw\":";
      out += side.side_dynamic_total_raw ? std::to_string(*side.side_dynamic_total_raw) : "null";
      out += ",\"unavailable_reason\":";
      if (side.side_dynamic_total_raw) out += "null";
      else String(out, side.unavailable_reason);
      out += '}';
    }
    out += "]}";
  }
  if (inputs.current_dynamic_components_v1) {
    out += ",\"current_dynamic_components_v1\":";
    out += SerializeCurrentDynamicComponentsV1(*inputs.current_dynamic_components_v1);
  }
  out += '}';
  return out;
}

} // namespace xar::bridge
