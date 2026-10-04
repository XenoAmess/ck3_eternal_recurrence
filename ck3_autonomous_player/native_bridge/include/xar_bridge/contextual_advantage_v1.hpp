#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

namespace xar::bridge {

namespace contextual_advantage_v1_detail {

inline void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}

inline void AppendNullableString(std::string &result, std::string_view value) {
  if (value.empty()) {
    result += "null";
  } else {
    AppendJsonString(result, value);
  }
}

inline void AppendDatabaseId(std::string &result, std::uint32_t value) {
  result += value == std::numeric_limits<std::uint32_t>::max()
                ? "null"
                : std::to_string(value);
}

inline void AppendSide(
    std::string &result,
    const xar::game::ContextualAdvantageSideSnapshot &side) {
  result += "{\"side_index\":" + std::to_string(side.side_index);
  result += ",\"ordered_public_cunit_ids\":[";
  for (std::size_t index = 0; index < side.ordered_public_cunit_ids.size();
       ++index) {
    if (index != 0) result += ',';
    result += std::to_string(side.ordered_public_cunit_ids[index]);
  }
  result += "],\"selected_commander_character_id\":";
  result += side.selected_commander_character_id == -1
                ? "null"
                : std::to_string(side.selected_commander_character_id);
  result += ",\"relation_kind_raw\":" + std::to_string(side.relation_kind_raw);
  result += ",\"commander_dynamic_raw\":" +
            std::to_string(side.commander_dynamic_raw);
  result += ",\"side_dynamic_raw\":" + std::to_string(side.side_dynamic_raw);
  result += ",\"target_conditionals_residual_raw\":" +
            std::to_string(side.target_conditionals_residual_raw);
  result += ",\"side_total_raw\":" + std::to_string(side.side_total_raw);
  result += '}';
}

inline void AppendNonreligiousConstructorSource(
    std::string &result,
    const xar::game::ContextualAdvantageConstructorSourceSnapshot &source) {
  result += "{\"stage_order\":" + std::to_string(source.stage_order);
  result += ",\"append_order\":";
  result += source.append_order == -1 ? "null" : std::to_string(source.append_order);
  result += ",\"stage\":";
  AppendJsonString(result, source.stage);
  result += ",\"side\":";
  AppendJsonString(result, source.side);
  result += ",\"source_key\":";
  if (source.selected) AppendJsonString(result, source.source_key);
  else result += "null";
  result += ",\"effect_advantage_points\":";
  result += source.selected ? std::to_string(source.effect_advantage_points) : "null";
  result += ",\"scale_raw\":" + std::to_string(source.scale_raw);
  result += ",\"signed_contribution_raw\":" + std::to_string(source.signed_contribution_raw);
  result += ",\"accumulator_before_raw\":" + std::to_string(source.accumulator_before_raw);
  result += ",\"accumulator_after_raw\":" + std::to_string(source.accumulator_after_raw);
  result += ",\"selected\":";
  result += source.selected ? "true" : "false";
  result += ",\"applied\":";
  result += source.applied ? "true" : "false";
  result += ",\"skip_reason\":";
  if (source.applied) result += "null";
  else AppendJsonString(result, source.skip_reason);
  result += '}';
}

inline void AppendReligionSource(
    std::string &result,
    const xar::game::ContextualAdvantageReligionSourceSnapshot &source) {
  result += "{\"side_index\":" + std::to_string(source.side_index);
  result += ",\"primary_public_cunit_id\":" +
            std::to_string(source.primary_public_cunit_id);
  result += ",\"owner_character_id\":" +
            std::to_string(source.owner_character_id);
  result += ",\"target_rite_id\":";
  AppendDatabaseId(result, source.target_rite_id);
  result += ",\"target_faith_id\":";
  AppendDatabaseId(result, source.target_faith_id);
  result += ",\"target_main_rite_id\":";
  AppendDatabaseId(result, source.target_main_rite_id);
  result += ",\"owner_rite_id\":";
  AppendDatabaseId(result, source.owner_rite_id);
  result += ",\"owner_faith_id\":";
  AppendDatabaseId(result, source.owner_faith_id);
  result += ",\"owner_rite_observed\":";
  result += source.owner_rite_observed ? "true" : "false";
  result += ",\"target_faith_unreformed\":";
  result += source.target_faith_unreformed ? "true" : "false";
  result += ",\"owner_faith_matches_target\":";
  result += source.owner_faith_matches_target.has_value()
                ? (*source.owner_faith_matches_target ? "true" : "false")
                : "null";
  result += ",\"selected\":";
  result += source.selected ? "true" : "false";
  result += ",\"applied\":";
  result += source.applied ? "true" : "false";
  result += ",\"source_key\":";
  AppendNullableString(result, source.source_key);
  result += ",\"effect_advantage_points\":";
  result += source.selected ? std::to_string(source.effect_advantage_points)
                            : "null";
  result += ",\"scale_raw\":" + std::to_string(source.scale_raw);
  result += ",\"signed_contribution_raw\":" +
            std::to_string(source.signed_contribution_raw);
  result += ",\"accumulator_before_raw\":" +
            std::to_string(source.accumulator_before_raw);
  result += ",\"accumulator_after_raw\":" +
            std::to_string(source.accumulator_after_raw);
  result += ",\"append_order\":" + std::to_string(source.append_order);
  result += ",\"skip_reason\":";
  AppendNullableString(result, source.skip_reason);
  result += '}';
}

}  // namespace contextual_advantage_v1_detail

// Typed synthetic constructor context. A religion attempt publishes schema 2
// even when unavailable; neither revision grants full encounter readiness.
inline std::string SerializeContextualAdvantageV1(
    const xar::game::ContextualAdvantageSnapshot &snapshot) {
  const bool religious = snapshot.religion_constructor_attempted;
  std::string result = religious ? "{\"schema_version\":2,\"status\":"
                                 : "{\"schema_version\":1,\"status\":";
  result += snapshot.available ? "\"available\"" : "\"unavailable\"";
  result += religious
                ? ",\"scope\":\"hypothetical_constructor_context\","
                : ",\"scope\":\"hypothetical_nonreligious_constructor_context\",";
  result += "\"scale\":100000,\"target_province_id\":";
  result += std::to_string(snapshot.target_province_id);
  result += ",\"sides\":";
  if (snapshot.available) {
    result += '[';
    for (std::size_t index = 0; index < snapshot.sides.size(); ++index) {
      if (index != 0) result += ',';
      contextual_advantage_v1_detail::AppendSide(result, snapshot.sides[index]);
    }
    result += ']';
    result += ",\"base_nonreligious_accumulator_raw\":" +
              std::to_string(snapshot.base_nonreligious_accumulator_raw);
    result += ",\"synthetic_zero_roll_total_raw\":" +
              std::to_string(snapshot.synthetic_zero_roll_total_raw);
    result += ",\"synthetic_helper_total_match\":";
    result += snapshot.synthetic_helper_total_match ? "true" : "false";
  } else {
    result += "null,\"base_nonreligious_accumulator_raw\":null,"
              "\"synthetic_zero_roll_total_raw\":null,"
              "\"synthetic_helper_total_match\":null";
  }
  result += ",\"nonreligious_constructor_sources\":";
  if (snapshot.available) {
    result += '[';
    for (std::size_t index = 0;
         index < snapshot.nonreligious_constructor_sources.size(); ++index) {
      if (index != 0) result += ',';
      contextual_advantage_v1_detail::AppendNonreligiousConstructorSource(
          result, snapshot.nonreligious_constructor_sources[index]);
    }
    result += ']';
  } else {
    result += "null";
  }
  if (religious) {
    result += ",\"religion_constructor_sources_ready\":";
    result += snapshot.religion_constructor_sources_ready ? "true" : "false";
    result += ",\"base_constructor_accumulator_raw\":";
    if (snapshot.available) {
      result += std::to_string(snapshot.base_constructor_accumulator_raw);
      result += ",\"religion_constructor_sources\":[";
      for (std::size_t index = 0;
           index < snapshot.religion_constructor_sources.size(); ++index) {
        if (index != 0) result += ',';
        contextual_advantage_v1_detail::AppendReligionSource(
            result, snapshot.religion_constructor_sources[index]);
      }
      result += ']';
    } else {
      result += "null,\"religion_constructor_sources\":null";
    }
  }
  result += ",\"partial_context_observation_ready\":";
  result += snapshot.available ? "true" : "false";
  result += ",\"complete_encounter_advantage_ready\":false,"
            "\"missing_domains\":";
  result += religious && snapshot.religion_constructor_sources_ready
                ? "[]"
                : "[\"religion_constructor_sources\"]";
  result += ",\"unavailable_reason\":";
  if (snapshot.available) {
    result += "null";
  } else {
    contextual_advantage_v1_detail::AppendJsonString(
        result, snapshot.unavailable_reason.empty()
                    ? std::string_view("contextual_advantage_read_unavailable")
                    : std::string_view(snapshot.unavailable_reason));
  }
  result += '}';
  return result;
}

}  // namespace xar::bridge
