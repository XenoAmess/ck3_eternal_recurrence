#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
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

template <typename Integer>
inline void AppendOptionalNumber(std::string &result,
                                 const std::optional<Integer> &value) {
  result += value.has_value() ? std::to_string(*value) : "null";
}

inline void AppendSideModifierSource(
    std::string &result,
    const xar::game::ContextualAdvantageSideModifierSourceSnapshot &source) {
  result += "{\"side_index\":" + std::to_string(source.side_index);
  result += ",\"source_slot\":";
  AppendJsonString(result, source.source_slot);
  result += ",\"source_modifier_id\":";
  result += std::to_string(source.source_modifier_id);
  result += ",\"condition_observed\":";
  result += source.condition_observed ? "true" : "false";
  result += ",\"selected\":";
  result += source.selected ? "true" : "false";
  result += ",\"modifier_raw\":";
  AppendOptionalNumber(result, source.modifier_raw);
  result += ",\"contribution_raw\":";
  AppendOptionalNumber(result, source.contribution_raw);
  result += ",\"scale100000\":" + std::to_string(source.scale100000);
  result += ",\"skip_reason\":";
  AppendNullableString(result, source.skip_reason);
  result += ",\"opposite_side_index\":";
  AppendOptionalNumber(result, source.opposite_side_index);
  result += ",\"eligible_opposite_effects\":";
  if (!source.eligible_opposite_effects.has_value()) {
    result += "null";
  } else {
    result += '[';
    const auto &effects = *source.eligible_opposite_effects;
    for (std::size_t index = 0; index < effects.size(); ++index) {
      if (index != 0) result += ',';
      const auto &effect = effects[index];
      result += "{\"native_ledger_index\":" +
                std::to_string(effect.native_ledger_index);
      result += ",\"effect_key\":";
      AppendJsonString(result, effect.effect_key);
      result += ",\"flag88_raw\":" +
                std::to_string(static_cast<unsigned int>(effect.flag88_raw));
      result += ",\"flag89_raw\":" +
                std::to_string(static_cast<unsigned int>(effect.flag89_raw));
      result += ",\"contribution_raw\":" +
                std::to_string(effect.contribution_raw);
      result += '}';
    }
    result += ']';
  }
  result += ",\"opposite_eligible_contribution_sum_raw\":";
  AppendOptionalNumber(result, source.opposite_eligible_contribution_sum_raw);
  result += '}';
}

inline void AppendOptionalBool(std::string &result,
                               const std::optional<bool> &value) {
  result += value.has_value() ? (*value ? "true" : "false") : "null";
}

inline void AppendEntityId(std::string &result, std::int32_t value) {
  result += value == -1 ? "null" : std::to_string(value);
}

inline void AppendOptionalEntityId(
    std::string &result, const std::optional<std::int32_t> &value) {
  if (value.has_value()) AppendEntityId(result, *value);
  else result += "null";
}

inline void AppendCommanderSourceInputs(
    std::string &result,
    const xar::game::ContextualAdvantageCommanderSourceInputsSnapshot &inputs) {
  result += "{\"selected_commander_character_id\":";
  AppendEntityId(result, inputs.selected_commander_character_id);
  result += ",\"effective_martial\":" + std::to_string(inputs.effective_martial);
  result += ",\"own_primary_character_id\":";
  AppendEntityId(result, inputs.own_primary_character_id);
  result += ",\"opposing_primary_character_id\":";
  AppendEntityId(result, inputs.opposing_primary_character_id);
  result += ",\"province_context_raw32\":";
  AppendOptionalNumber(result, inputs.province_context_raw32);
  result += ",\"relation_kind_raw\":" + std::to_string(inputs.relation_kind_raw);
  result += ",\"army_gated_modifier_cache_present\":";
  AppendOptionalBool(result, inputs.army_gated_modifier_cache_present);
  result += ",\"army_gated_modifier_cached_raw\":";
  AppendOptionalNumber(result, inputs.army_gated_modifier_cached_raw);
  result += ",\"army_gated_modifier_source_army_id\":";
  AppendOptionalEntityId(result, inputs.army_gated_modifier_source_army_id);
  result += ",\"army_gated_modifier_resolved_army_id\":";
  AppendOptionalEntityId(result, inputs.army_gated_modifier_resolved_army_id);
  result += ",\"army_gated_modifier_used_null_army\":";
  AppendOptionalBool(result, inputs.army_gated_modifier_used_null_army);
  result += ",\"army_gated_modifier_gate_result\":";
  AppendOptionalBool(result, inputs.army_gated_modifier_gate_result);
  result += ",\"primary_identity_matches\":";
  result += inputs.primary_identity_matches ? "true" : "false";
  result += ",\"gathering_flag_raw\":" +
            std::to_string(static_cast<unsigned int>(inputs.gathering_flag_raw));
  result += ",\"gathering_modifier_flag_1a5\":";
  AppendOptionalBool(result, inputs.gathering_modifier_flag_1a5);
  result += ",\"gathering_rule_effect_points\":";
  AppendOptionalNumber(result, inputs.gathering_rule_effect_points);
  result += ",\"gathering_rule_source_key\":";
  if (inputs.gathering_rule_source_key.has_value()) {
    AppendJsonString(result, *inputs.gathering_rule_source_key);
  } else {
    result += "null";
  }
  result += '}';
}

inline void AppendCommanderOpposingPrimaryDetails(
    std::string &result,
    const xar::game::ContextualAdvantageCommanderOpposingPrimaryDetailsSnapshot &details) {
  result += "{";
  result += "\"selected_personal_rite_reference\":";
  AppendOptionalNumber(result, details.selected_personal_rite_reference);
  result += ",\"opposing_primary_personal_rite_reference\":";
  AppendOptionalNumber(result, details.opposing_primary_personal_rite_reference);
  result += ",\"opposing_primary_character_used_fallback\":";
  AppendOptionalBool(result, details.opposing_primary_character_used_fallback);
  result += ",\"selected_rite_used_fallback\":";
  AppendOptionalBool(result, details.selected_rite_used_fallback);
  result += ",\"opposing_primary_rite_used_fallback\":";
  AppendOptionalBool(result, details.opposing_primary_rite_used_fallback);
  result += ",\"rite_pair_valid\":";
  AppendOptionalBool(result, details.rite_pair_valid);
  result += ",\"directed_rite_hostility_level\":";
  AppendOptionalNumber(result, details.directed_rite_hostility_level);
  result += ",\"hostility_factor_count\":";
  AppendOptionalNumber(result, details.hostility_factor_count);
  result += ",\"hostility_factor_raw\":";
  AppendOptionalNumber(result, details.hostility_factor_raw);
  result += ",\"selected_personal_faith_reference\":";
  AppendOptionalNumber(result, details.selected_personal_faith_reference);
  result += ",\"opposing_primary_personal_faith_reference\":";
  AppendOptionalNumber(result, details.opposing_primary_personal_faith_reference);
  result += ",\"selected_faith_used_fallback\":";
  AppendOptionalBool(result, details.selected_faith_used_fallback);
  result += ",\"opposing_primary_faith_used_fallback\":";
  AppendOptionalBool(result, details.opposing_primary_faith_used_fallback);
  result += ",\"selected_religion_reference\":";
  AppendOptionalNumber(result, details.selected_religion_reference);
  result += ",\"opposing_primary_religion_reference\":";
  AppendOptionalNumber(result, details.opposing_primary_religion_reference);
  result += ",\"religion_references_equal\":";
  AppendOptionalBool(result, details.religion_references_equal);
  result += ",\"sources\":[";
  for (std::size_t index = 0; index < details.sources.size(); ++index) {
    if (index != 0) result += ',';
    const auto &source = details.sources[index];
    result += "{\"modifier_id\":" + std::to_string(source.modifier_id);
    result += ",\"cache_present\":";
    AppendOptionalBool(result, source.cache_present);
    result += ",\"modifier_raw\":";
    AppendOptionalNumber(result, source.modifier_raw);
    result += ",\"selected\":";
    AppendOptionalBool(result, source.selected);
    result += ",\"predicate_observed\":";
    AppendOptionalBool(result, source.predicate_observed);
    result += ",\"contribution_raw\":";
    AppendOptionalNumber(result, source.contribution_raw);
    result += ",\"skip_reason\":";
    AppendNullableString(result, source.skip_reason);
    result += '}';
  }
  result += ']';
  result += '}';
}

inline void AppendCommanderProvinceDetails(
    std::string &result,
    const xar::game::ContextualAdvantageCommanderProvinceDetailsSnapshot &details) {
  result += "{";
  result += "\"cache_present\":";
  AppendOptionalBool(result, details.cache_present);
  result += ",\"selected_culture_reference\":";
  AppendOptionalNumber(result, details.selected_culture_reference);
  result += ",\"province_culture_reference\":";
  AppendOptionalNumber(result, details.province_culture_reference);
  result += ",\"selected_culture_used_fallback\":";
  AppendOptionalBool(result, details.selected_culture_used_fallback);
  result += ",\"province_culture_used_fallback\":";
  AppendOptionalBool(result, details.province_culture_used_fallback);
  result += ",\"category1_pillar_equal\":";
  AppendOptionalBool(result, details.category1_pillar_equal);
  result += '}';
}

inline void AppendCommanderSource(
    std::string &result,
    const xar::game::ContextualAdvantageCommanderSourceSnapshot &source) {
  result += "{\"side_index\":" + std::to_string(source.side_index);
  result += ",\"stage_order\":" + std::to_string(source.stage_order);
  result += ",\"source_kind\":";
  AppendJsonString(result, source.source_kind);
  result += ",\"modifier_id\":";
  AppendOptionalNumber(result, source.modifier_id);
  result += ",\"status\":";
  AppendJsonString(result, source.status);
  result += ",\"predicate_observed\":";
  AppendOptionalBool(result, source.predicate_observed);
  result += ",\"selected\":";
  AppendOptionalBool(result, source.selected);
  result += ",\"modifier_raw\":";
  AppendOptionalNumber(result, source.modifier_raw);
  result += ",\"contribution_raw\":";
  AppendOptionalNumber(result, source.contribution_raw);
  result += ",\"scale100000\":" + std::to_string(source.scale100000);
  result += ",\"accumulator_before_raw\":";
  AppendOptionalNumber(result, source.accumulator_before_raw);
  result += ",\"accumulator_after_raw\":";
  AppendOptionalNumber(result, source.accumulator_after_raw);
  result += ",\"skip_reason\":";
  AppendNullableString(result, source.skip_reason);
  result += ",\"source_provenance\":";
  AppendJsonString(result, source.source_provenance);
  result += ",\"opposing_primary_details\":";
  if (source.opposing_primary_details)
    AppendCommanderOpposingPrimaryDetails(result, *source.opposing_primary_details);
  else result += "null";
  result += ",\"province_details\":";
  if (source.province_details)
    AppendCommanderProvinceDetails(result, *source.province_details);
  else result += "null";
  result += '}';
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
  result += ",\"commander_source_inputs\":";
  if (side.commander_source_inputs.has_value()) {
    AppendCommanderSourceInputs(result, *side.commander_source_inputs);
  } else {
    result += "null";
  }
  result += ",\"commander_sources\":";
  if (!side.commander_sources.has_value()) {
    result += "null";
  } else {
    result += '[';
    const auto &sources = *side.commander_sources;
    for (std::size_t index = 0; index < sources.size(); ++index) {
      if (index != 0) result += ',';
      AppendCommanderSource(result, sources[index]);
    }
    result += ']';
  }
  result += ",\"side_modifier_sources\":";
  if (!side.side_modifier_sources.has_value()) {
    result += "null";
  } else {
    result += '[';
    const auto &sources = *side.side_modifier_sources;
    for (std::size_t index = 0; index < sources.size(); ++index) {
      if (index != 0) result += ',';
      AppendSideModifierSource(result, sources[index]);
    }
    result += ']';
  }
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
