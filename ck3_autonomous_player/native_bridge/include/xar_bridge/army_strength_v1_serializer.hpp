#pragma once

#include "xar_bridge/game_contract.hpp"

#include <string>

namespace xar::game {

// One row implementation shared by the bridge and its production-reader fixture.
// The bridge supplies its existing number, array, and string-escaping helpers.
template <class Number, class Int32Array, class JsonString>
inline void AppendArmyStrengthV1(
    std::string &result,
    const ArmyStrengthSnapshot &strength, Number number,
    Int32Array append_int32_array, JsonString append_json_string) {
  result += "{\"status\":\"";
  result += strength.available ? "available" : "unavailable";
  result += "\",\"army_id\":";
  result += number(strength.army_id);
  result += ",\"native_carmy_id\":";
  if (strength.native_carmy_id_observable) {
    result += number(strength.native_carmy_id);
  } else {
    result += "null";
  }
  result += ",\"scope_role\":\"";
  switch (strength.scope_role) {
  case ArmyStrengthScopeRole::player:
    result += "player";
    break;
  case ArmyStrengthScopeRole::active_war_ally:
    result += "active_war_ally";
    break;
  case ArmyStrengthScopeRole::active_war_enemy:
    result += "active_war_enemy";
    break;
  }
  result += "\",\"war_ids\":";
  append_int32_array(result, strength.war_ids);
  result += ",\"regiment_count\":";
  if (strength.available) {
    result += number(strength.regiment_count);
  } else {
    result += "null";
  }
  result += ",\"current_soldiers\":";
  if (strength.available) {
    result += number(strength.current_soldiers);
  } else {
    result += "null";
  }
  result += ",\"maximum_soldiers\":";
  if (strength.available) {
    result += number(strength.maximum_soldiers);
  } else {
    result += "null";
  }
  result += ",\"ai_base_power_raw\":";
  if (strength.available) {
    result += number(strength.ai_base_power_raw);
  } else {
    result += "null";
  }
  result += ",\"ai_base_power_scale\":";
  result += number(strength.ai_base_power_scale);
  if (strength.available && strength.current_supply_raw.has_value()) {
    result += ",\"current_supply_raw\":";
    result += number(*strength.current_supply_raw);
    result += ",\"current_supply_scale\":100000";
  }
  if (strength.available && strength.current_supply_capacity_raw.has_value()) {
    result += ",\"current_supply_capacity_raw\":";
    result += number(*strength.current_supply_capacity_raw);
    result += ",\"current_supply_capacity_scale\":100000";
  }
  if (strength.available && strength.current_supply_change_monthly_raw.has_value()) {
    result += ",\"current_supply_change_monthly_raw\":";
    result += number(*strength.current_supply_change_monthly_raw);
    result += ",\"current_supply_change_monthly_scale\":100000";
  }
  if (strength.available && strength.current_attrition_fraction_raw.has_value()) {
    result += ",\"current_attrition_fraction_raw\":";
    result += number(*strength.current_attrition_fraction_raw);
    result += ",\"current_attrition_fraction_scale\":100000";
  }
  if (strength.available && strength.regiment_replenishment.has_value()) {
    result += ",\"regiment_replenishment\":[";
    bool first_regiment = true;
    for (const auto &regiment : *strength.regiment_replenishment) {
      if (!first_regiment) {
        result += ',';
      }
      first_regiment = false;
      result += "{\"army_regiment_id\":";
      result += number(regiment.army_regiment_id);
      result += ",\"native_data_record_count\":";
      if (regiment.native_data_record_count.has_value()) {
        result += number(*regiment.native_data_record_count);
      } else {
        result += "null";
      }
      result += ",\"status\":\"";
      result += regiment.available ? "available" : "unavailable";
      result += "\",\"source\":\"native_first_record\",\"unavailable_reason\":";
      if (regiment.available) {
        result += "null";
      } else {
        append_json_string(result, regiment.unavailable_reason);
      }
      result += ",\"chunks\":[";
      bool first_chunk = true;
      if (regiment.available) {
        for (const auto &chunk : regiment.chunks) {
          if (!first_chunk) {
            result += ',';
          }
          first_chunk = false;
          result += "{\"persistent_regiment_id\":";
          result += number(chunk.persistent_regiment_id);
          result += ",\"chunk_index\":";
          result += number(chunk.chunk_index);
          result += ",\"current_soldiers\":";
          result += number(chunk.current_soldiers);
          result += ",\"maximum_soldiers\":";
          result += number(chunk.maximum_soldiers);
          result += ",\"state_raw\":";
          result += number(chunk.state_raw);
          result += ",\"native_can_replenish\":";
          result += chunk.native_can_replenish ? "true" : "false";
          result += ",\"native_chunk_can_replenish\":";
          result += chunk.native_chunk_can_replenish ? "true" : "false";
          result += ",\"persistent_monthly_replenishment_fraction_raw\":";
          result += number(chunk.persistent_monthly_replenishment_fraction_raw);
          result += ",\"persistent_monthly_replenishment_fraction_scale\":100000}";
        }
      }
      result += "]}";
    }
    result += ']';
  }
  result += ",\"unavailable_reason\":";
  if (strength.available) {
    result += "null";
  } else {
    append_json_string(result, strength.unavailable_reason);
  }
  result += '}';
}

} // namespace xar::game
