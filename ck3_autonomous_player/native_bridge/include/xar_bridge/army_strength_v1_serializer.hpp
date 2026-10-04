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
  if (strength.available && strength.regiment_strengths.has_value()) {
    result += ",\"regiment_strengths\":[";
    bool first = true;
    for (const auto &regiment : *strength.regiment_strengths) {
      if (!first) result += ',';
      first = false;
      result += "{\"army_regiment_id\":";
      result += number(regiment.army_regiment_id);
      result += ",\"current_soldiers\":";
      result += number(regiment.current_soldiers);
      result += ",\"maximum_soldiers\":";
      result += number(regiment.maximum_soldiers);
      result += ",\"scale\":1}";
    }
    result += ']';
  }
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
  if (strength.available && strength.regiment_replenishment_records_v1.has_value()) {
    result += ",\"regiment_replenishment_records_v1\":[";
    bool first_regiment = true;
    for (const auto &regiment : *strength.regiment_replenishment_records_v1) {
      if (!first_regiment) result += ',';
      first_regiment = false;
      result += "{\"army_regiment_id\":" + number(regiment.army_regiment_id);
      result += ",\"source\":\"native_all_data_records\",\"status\":\"";
      switch (regiment.status) {
      case ArmyRegimentReplenishmentRecordsStatusV1::available: result += "available"; break;
      case ArmyRegimentReplenishmentRecordsStatusV1::partial: result += "partial"; break;
      default: result += "unavailable"; break;
      }
      result += "\",\"ready\":";
      result += regiment.status == ArmyRegimentReplenishmentRecordsStatusV1::available ? "true" : "false";
      result += ",\"native_data_record_count\":";
      result += regiment.native_data_record_count.has_value() ? number(*regiment.native_data_record_count) : "null";
      result += ",\"unavailable_reason\":";
      if (regiment.unavailable_reason.empty()) result += "null";
      else append_json_string(result,regiment.unavailable_reason);
      result += ",\"records\":[";
      bool first_record=true;
      for (const auto &record : regiment.records) {
        if (!first_record) result += ',';
        first_record=false;
        result += "{\"record_index\":" + number(record.record_index);
        result += ",\"persistent_regiment_id\":" + number(record.persistent_regiment_id);
        result += ",\"chunk_index\":" + number(record.chunk_index);
        result += ",\"status\":\"";
        result += record.available ? "available" : "unavailable";
        result += "\",\"unavailable_reason\":";
        if (record.unavailable_reason.empty()) result += "null";
        else append_json_string(result,record.unavailable_reason);
        const auto optional_number=[&](std::string_view key,const auto &value) {
          result += ','; append_json_string(result,key); result += ':';
          result += value.has_value() ? number(*value) : "null";
        };
        const auto optional_bool=[&](std::string_view key,const auto &value) {
          result += ','; append_json_string(result,key); result += ':';
          result += value.has_value() ? (*value ? "true" : "false") : "null";
        };
        optional_number("current_soldiers",record.current_soldiers);
        optional_number("maximum_soldiers",record.maximum_soldiers);
        optional_number("effective_current_soldiers",record.effective_current_soldiers);
        optional_number("state_raw",record.state_raw);
        optional_bool("native_can_replenish",record.native_can_replenish);
        optional_bool("native_chunk_can_replenish",record.native_chunk_can_replenish);
        optional_number("persistent_monthly_replenishment_fraction_raw",record.persistent_monthly_replenishment_fraction_raw);
        optional_number("persistent_prepared_replenishment_fraction_raw",record.persistent_prepared_replenishment_fraction_raw);
        result += ",\"persistent_monthly_replenishment_fraction_scale\":100000";
        result += ",\"persistent_prepared_replenishment_fraction_scale\":100000}";
      }
      result += "]}";
    }
    result += ']';
  }
  if (strength.current_movement_progress.has_value()) {
    const auto &movement = *strength.current_movement_progress;
    result += ",\"current_movement_progress\":{\"status\":\"";
    switch (movement.status) {
    case ArmyMovementProgressStatus::available: result += "available"; break;
    case ArmyMovementProgressStatus::partial: result += "partial"; break;
    case ArmyMovementProgressStatus::not_applicable: result += "not_applicable"; break;
    case ArmyMovementProgressStatus::unavailable: result += "unavailable"; break;
    }
    result += "\",\"source\":\"native_current_route_edge\",\"unit_state_raw\":";
    result += movement.unit_state_raw.has_value() ? number(*movement.unit_state_raw) : "null";
    result += ",\"accumulated_movement_weight_raw\":";
    result += movement.accumulated_movement_weight_raw.has_value()
                  ? number(*movement.accumulated_movement_weight_raw) : "null";
    result += ",\"cached_edge_speed_raw\":";
    result += movement.cached_edge_speed_raw.has_value()
                  ? number(*movement.cached_edge_speed_raw) : "null";
    const auto append_fixed = [&](const std::optional<std::int64_t> &raw) {
      if (raw.has_value()) {
        result += "{\"raw\":";
        result += number(*raw);
        result += ",\"scale\":100000}";
      } else {
        result += "null";
      }
    };
    result += ",\"normalized_edge_progress\":";
    append_fixed(movement.normalized_edge_progress_raw);
    result += ",\"first_route_edge_remaining_duration\":";
    append_fixed(movement.first_route_edge_remaining_duration_raw);
    result += ",\"unavailable_reason\":";
    if (movement.unavailable_reason.empty()) result += "null";
    else append_json_string(result, movement.unavailable_reason);
    result += '}';
  }
  if (strength.army_update_clock_v1.has_value()) {
    const auto &clock = *strength.army_update_clock_v1;
    result += ",\"army_update_clock_v1\":{\"status\":";
    append_json_string(result, ArmySupplyTimingStatusName(clock.status));
    result += ",\"ready\":";
    result += clock.ready ? "true" : "false";
    const auto append_optional = [&](std::string_view key, const auto &value) {
      result += ',';
      append_json_string(result, key);
      result += ':';
      result += value.has_value() ? number(*value) : "null";
    };
    append_optional("current_date_raw", clock.current_date_raw);
    append_optional("native_day_index", clock.native_day_index);
    append_optional("selected_bucket_phase", clock.selected_bucket_phase);
    append_optional("observed_army_bucket_phase", clock.observed_army_bucket_phase);
    append_optional("last_supply_update_date_storage_raw64", clock.last_supply_update_date_storage_raw64);
    append_optional("last_supply_update_date_raw", clock.last_supply_update_date_raw);
    append_optional("grace_anchor_date_storage_raw64", clock.grace_anchor_date_storage_raw64);
    append_optional("grace_anchor_date_raw", clock.grace_anchor_date_raw);
    append_optional("loaded_grace_days", clock.loaded_grace_days);
    result += ",\"unavailable_reason\":";
    if (clock.unavailable_reason.empty()) result += "null";
    else append_json_string(result, clock.unavailable_reason);
    result += '}';
  }
  result += ",\"gathering_days_left\":";
  if (strength.gathering_days_status == ArmyGatheringDaysStatus::available &&
      strength.gathering_days_left.has_value()) {
    result += number(*strength.gathering_days_left);
  } else {
    result += "null";
  }
  result += ",\"gathering_days_status\":\"";
  switch (strength.gathering_days_status) {
  case ArmyGatheringDaysStatus::available:
    result += "available";
    break;
  case ArmyGatheringDaysStatus::not_gathering:
    result += "not_gathering";
    break;
  case ArmyGatheringDaysStatus::unavailable:
    result += "unavailable";
    break;
  }
  result += "\",\"gathering_days_ready\":";
  result += strength.gathering_days_status != ArmyGatheringDaysStatus::unavailable
                ? "true" : "false";
  result += ",\"unavailable_reason\":";
  if (strength.available) {
    result += "null";
  } else {
    append_json_string(result, strength.unavailable_reason);
  }
  result += '}';
}

template <class Number, class JsonString>
inline void AppendArmyProvinceSupplyRowV1(
    std::string &output, const ArmyProvinceSupplyRow &row,
    Number number, JsonString append_json_string) {
  output += "{\"status\":\"";
  output += row.available ? "available" : "unavailable";
  output += "\",\"unavailable_reason\":";
  if (row.available) output += "null";
  else append_json_string(output, row.unavailable_reason);
  output += ",\"role\":\"";
  output += row.role == ArmyProvinceSupplyRole::current ? "current" : "target";
  output += "\",\"province_id\":" + number(row.province_id);
  output += ",\"native_supply_limit_soldiers\":";
  output += row.native_supply_limit_soldiers.has_value()
      ? number(*row.native_supply_limit_soldiers) : "null";
  output += ",\"native_supply_usage_soldiers\":";
  output += row.native_supply_usage_soldiers.has_value()
      ? number(*row.native_supply_usage_soldiers) : "null";
  output += ",\"scale\":1}";
}

template <class Number, class JsonString>
inline void AppendArmyProvinceSupplyV1(
    std::string &output, const ArmyProvinceSupplySnapshot &supply,
    Number number, JsonString append_json_string) {
  output += "{\"status\":\"";
  switch (supply.status) {
  case ArmyProvinceSupplyStatus::available: output += "available"; break;
  case ArmyProvinceSupplyStatus::partial: output += "partial"; break;
  case ArmyProvinceSupplyStatus::unavailable: output += "unavailable"; break;
  }
  output += "\",\"unavailable_reason\":";
  if (supply.status == ArmyProvinceSupplyStatus::available) output += "null";
  else append_json_string(output, supply.unavailable_reason);
  output += ",\"army_id\":" + number(supply.army_id);
  output += ",\"native_carmy_id\":";
  output += supply.native_carmy_id.has_value() ? number(*supply.native_carmy_id) : "null";
  output += ",\"owner_character_id\":";
  output += supply.owner_character_id.has_value() ? number(*supply.owner_character_id) : "null";
  output += ",\"commander_character_id\":";
  output += supply.commander_character_id.has_value() ? number(*supply.commander_character_id) : "null";
  output += ",\"current\":";
  AppendArmyProvinceSupplyRowV1(output, supply.current, number, append_json_string);
  output += ",\"target\":";
  AppendArmyProvinceSupplyRowV1(output, supply.target, number, append_json_string);
  output += '}';
}

// The same route-preview row body is used by the real bridge and its focused
// native producer. Existing helpers preserve number/array/string semantics.
template <class Number, class Int32Array, class JsonString>
inline void AppendMoveRoutePreviewV1(
    std::string &output, const PreviewMoveArmyResult &preview,
    Number number, Int32Array append_int32_array, JsonString append_json_string) {
  output += "{\"status\":\"available\",\"army_id\":" + number(preview.army_id);
  output += ",\"origin_province_id\":" + number(preview.origin_province_id);
  output += ",\"target_province_id\":" + number(preview.target_province_id);
  output += ",\"route_province_ids\":";
  append_int32_array(output, preview.route_province_ids);
  if (preview.province_supply.has_value()) {
    output += ",\"province_supply\":";
    AppendArmyProvinceSupplyV1(output, *preview.province_supply, number,
                               append_json_string);
  }
  output += '}';
}

} // namespace xar::game
