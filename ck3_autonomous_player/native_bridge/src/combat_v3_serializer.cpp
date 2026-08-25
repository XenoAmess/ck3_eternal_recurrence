#include "xar_bridge/combat_v3.hpp"

#include <array>
#include <charconv>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {
namespace {

constexpr std::array<std::string_view, 18> kConstructorCallOrder{
    "width",
    "attacker_adjacency",
    "defender_adjacency",
    "attacker_terrain",
    "defender_terrain",
    "side_context_0",
    "side_context_1",
    "supply_0",
    "supply_1",
    "holding_defender_1",
    "recently_disembarked_0",
    "recently_disembarked_1",
    "debt_0_owner_then_treasury",
    "debt_1_owner_then_treasury",
    "unreformed_faith_0",
    "unreformed_faith_1",
    "side_finalize_0",
    "side_finalize_1",
};

void AppendSigned(std::string &output, std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto conversion =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (conversion.ec == std::errc{}) {
    output.append(buffer.data(), conversion.ptr);
  } else {
    output += '0';
  }
}

void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output += '\\';
      output += static_cast<char>(character);
    } else if (character < 0x20U) {
      output += "\\u00";
      output += hex[(character >> 4U) & 0x0FU];
      output += hex[character & 0x0FU];
    } else {
      output += static_cast<char>(character);
    }
  }
  output += '"';
}

void AppendNullableId(std::string &output, std::int32_t value) {
  if (value < 0) {
    output += "null";
  } else {
    AppendSigned(output, value);
  }
}

void AppendIdArray(std::string &output,
                   const std::vector<std::int32_t> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendSigned(output, values[index]);
  }
  output += ']';
}

void AppendStringArray(std::string &output,
                       const std::vector<std::string> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendString(output, values[index]);
  }
  output += ']';
}

void AppendNamedBools(std::string &output,
                      const std::vector<NamedBoolV3> &values) {
  output += '{';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendString(output, values[index].key);
    output += ':';
    output += values[index].value ? "true" : "false";
  }
  output += '}';
}

void AppendNamedSigned(std::string &output,
                       const std::vector<NamedSignedV3> &values) {
  output += '{';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendString(output, values[index].key);
    output += ':';
    AppendSigned(output, values[index].value);
  }
  output += '}';
}

void AppendOptionalId(std::string &output, const OptionalFullIdV3 &value) {
  output += "{\"status\":\"";
  output += value.present ? "available\",\"value\":"
                          : "absent\",\"value\":null}";
  if (value.present) {
    AppendSigned(output, value.value);
    output += '}';
  }
}

void AppendCharacter(std::string &output,
                     const CombatPhaseCharacterV3 &character) {
  output += "{\"character_id\":";
  AppendSigned(output, character.character_id);
  output += ",\"source_army_id\":";
  AppendSigned(output, character.source_army_id);
  output += ",\"source_regiment_id\":";
  AppendNullableId(output, character.source_regiment_id);
  output += ",\"encounter_role\":";
  AppendString(output, character.encounter_role);
  output += ",\"phase_roles\":";
  AppendStringArray(output, character.phase_roles);
  output += ",\"alive\":";
  output += character.alive ? "true" : "false";
  output += ",\"is_ai\":";
  output += character.is_ai ? "true" : "false";
  output += ",\"martial\":";
  AppendSigned(output, character.martial);
  output += ",\"learning\":";
  AppendSigned(output, character.learning);
  output += ",\"prowess\":";
  AppendSigned(output, character.prowess);
  output += ",\"traits_or_groups\":";
  AppendNamedBools(output, character.traits_or_groups);
  output += ",\"wounded_rank_raw\":";
  AppendSigned(output, character.wounded_rank_raw);
  output += ",\"fragile_bones_rank_raw\":";
  AppendSigned(output, character.fragile_bones_rank_raw);
  output += ",\"fragile_bones_xp_raw\":";
  AppendSigned(output, character.fragile_bones_xp_raw);
  output += ",\"lifestyle_blademaster_xp_raw\":";
  AppendSigned(output, character.lifestyle_blademaster_xp_raw);
  output += ",\"tourney_bow_xp_raw\":";
  AppendSigned(output, character.tourney_bow_xp_raw);
  output += ",\"tourney_foot_xp_raw\":";
  AppendSigned(output, character.tourney_foot_xp_raw);
  output += ",\"tourney_horse_xp_raw\":";
  AppendSigned(output, character.tourney_horse_xp_raw);
  output += ",\"house\":";
  AppendOptionalId(output, character.house);
  output += ",\"liege\":";
  AppendOptionalId(output, character.liege);
  output += ",\"liege_house\":";
  AppendOptionalId(output, character.liege_house);
  output += ",\"employer\":";
  AppendOptionalId(output, character.employer);
  output += ",\"dynasty\":";
  AppendOptionalId(output, character.dynasty);
  output += ",\"warfare_legacy_3\":";
  output += character.warfare_legacy_3 ? "true" : "false";
  output += ",\"stalwart_leader\":";
  output += character.stalwart_leader ? "true" : "false";
  output += ",\"culture\":";
  AppendOptionalId(output, character.culture);
  output += ",\"faith\":";
  AppendOptionalId(output, character.faith);
  output += ",\"religion\":";
  AppendOptionalId(output, character.religion);
  output += ",\"heritage_north_germanic\":";
  output += character.heritage_north_germanic ? "true" : "false";
  output += ",\"knights_slightly_more_prone_to_injury\":";
  output += character.knights_slightly_more_prone_to_injury ? "true"
                                                            : "false";
  output += ",\"death_is_glory\":";
  output += character.death_is_glory ? "true" : "false";
  output += ",\"tenet_warmonger\":";
  output += character.tenet_warmonger ? "true" : "false";
  output += ",\"germanic_religion\":";
  output += character.germanic_religion ? "true" : "false";
  output += ",\"blademaster_traits_more_common\":";
  output += character.blademaster_traits_more_common ? "true" : "false";
  output += ",\"innovations\":";
  AppendNamedBools(output, character.innovations);
  output += ",\"traditions\":";
  AppendNamedBools(output, character.traditions);
  output += ",\"culture_parameters\":";
  AppendNamedBools(output, character.culture_parameters);
  output += ",\"is_acclaimed\":";
  output += character.is_acclaimed ? "true" : "false";
  output += ",\"can_be_acclaimed\":";
  output += character.can_be_acclaimed ? "true" : "false";
  output += ",\"accolade\":";
  AppendOptionalId(output, character.accolade);
  output += ",\"accolade_has_men_at_arms_category\":";
  output += character.accolade_has_men_at_arms_category ? "true" : "false";
  output += ",\"accolade_parameters\":";
  AppendNamedBools(output, character.accolade_parameters);
  output += ",\"conqueror_variable_present\":";
  output += character.conqueror_variable_present ? "true" : "false";
  output += ",\"attribute_unlock_variables\":";
  AppendNamedBools(output, character.attribute_unlock_variables);
  output += ",\"hold_court_8050_knight\":";
  AppendOptionalId(output, character.hold_court_8050_knight);
  output += ",\"employer_hold_court_8050_promise\":";
  AppendOptionalId(output, character.employer_hold_court_8050_promise);
  output += ",\"liege_accolade_progress_raw\":";
  AppendSigned(output, character.liege_accolade_progress_raw);
  output += ",\"ai_extreme_conqueror_modifier\":";
  output += character.ai_extreme_conqueror_modifier ? "true" : "false";
  output += ",\"garuda_court_position\":";
  output += character.garuda_court_position ? "true" : "false";
  output += ",\"government_is_nomadic\":";
  output += character.government_is_nomadic ? "true" : "false";
  output += '}';
}

void AppendCharacters(std::string &output,
                      const std::vector<CombatPhaseCharacterV3> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendCharacter(output, values[index]);
  }
  output += ']';
}

void AppendArmies(std::string &output,
                   const std::vector<CombatPhaseArmyV3> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &army = values[index];
    output += "{\"army_id\":";
    AppendSigned(output, army.army_id);
    output += ",\"native_carmy_id\":";
    AppendSigned(output, army.native_carmy_id);
    output += ",\"encounter_role\":";
    AppendString(output, army.encounter_role);
    output += ",\"maa_regiment_count_raw\":";
    AppendSigned(output, army.maa_regiment_count_raw);
    output += ",\"maa_counts_raw\":";
    AppendNamedSigned(output, army.maa_counts_raw);
    output += '}';
  }
  output += ']';
}

void AppendCandidateSourceProof(
    std::string &output,
    const CombatPhaseCandidateSourceProofV3 &proof) {
  output += "{\"policy\":";
  AppendString(output, proof.policy);
  output += ",\"source_vector_equivalence\":";
  output += proof.source_vector_equivalence ? "true" : "false";
  output += ",\"sequence_sha256\":";
  AppendString(output, proof.sequence_sha256);
  output += ",\"ordered_sources\":[";
  for (std::size_t index = 0; index < proof.ordered_sources.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &source = proof.ordered_sources[index];
    output += "{\"role\":";
    AppendString(output, source.role);
    output += ",\"source_army_id\":";
    AppendSigned(output, source.source_army_id);
    output += ",\"source_regiment_id\":";
    AppendNullableId(output, source.source_regiment_id);
    output += ",\"character_id\":";
    AppendSigned(output, source.character_id);
    output += '}';
  }
  output += "]}";
}

void AppendSides(std::string &output,
                 const std::vector<CombatPhaseSideV3> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &side = values[index];
    output += "{\"side_index\":";
    AppendSigned(output, side.side_index);
    output += ",\"encounter_role\":";
    AppendString(output, side.encounter_role);
    output += ",\"ordered_army_ids\":";
    AppendIdArray(output, side.ordered_army_ids);
    output += ",\"ordered_character_ids\":";
    AppendIdArray(output, side.ordered_character_ids);
    output += ",\"ordered_commander_ids\":";
    AppendIdArray(output, side.ordered_commander_ids);
    output += ",\"ordered_knight_ids\":";
    AppendIdArray(output, side.ordered_knight_ids);
    output += ",\"primary_participant_character_id\":";
    AppendSigned(output, side.primary_participant_character_id);
    output += ",\"primary_source_army_id\":";
    AppendSigned(output, side.primary_source_army_id);
    output += ",\"commander_character_id\":";
    AppendNullableId(output, side.commander_character_id);
    output += ",\"side_strength_raw\":";
    AppendSigned(output, side.side_strength_raw);
    output += ",\"side_army_size_raw\":";
    AppendSigned(output, side.side_army_size_raw);
    output += ",\"participants\":[";
    for (std::size_t participant_index = 0;
         participant_index < side.participants.size(); ++participant_index) {
      if (participant_index != 0) {
        output += ',';
      }
      const auto &participant = side.participants[participant_index];
      output += "{\"source_army_id\":";
      AppendSigned(output, participant.source_army_id);
      output += ",\"owner_character_id\":";
      AppendSigned(output, participant.owner_character_id);
      output += ",\"faith_id\":";
      AppendSigned(output, participant.faith_id);
      output += '}';
    }
    output += "],\"candidate_source_proof\":";
    AppendCandidateSourceProof(output, side.candidate_source_proof);
    output += '}';
  }
  output += ']';
}

void AppendFaithHostility(
    std::string &output,
    const std::vector<CombatPhaseFaithHostilityV3> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &row = values[index];
    output += "{\"root_character_id\":";
    AppendSigned(output, row.root_character_id);
    output += ",\"enemy_side_index\":";
    AppendSigned(output, row.enemy_side_index);
    output += ",\"enemy_owner_character_id\":";
    AppendSigned(output, row.enemy_owner_character_id);
    output += ",\"enemy_faith_id\":";
    AppendSigned(output, row.enemy_faith_id);
    output += ",\"root_faith_id\":";
    AppendSigned(output, row.root_faith_id);
    output += ",\"hostility_level_raw\":";
    AppendSigned(output, row.hostility_level_raw);
    output += '}';
  }
  output += ']';
}

void AppendSupply(std::string &output,
                  const game::CombatAdvantageSupplyInputV3TestOnly &supply) {
  output += "{\"selected_key\":";
  AppendString(output, supply.selected_key);
  output += ",\"selected_effect_identity\":";
  AppendString(output, supply.selected_effect_identity);
  output += ",\"selected_effect_points\":";
  AppendSigned(output, supply.selected_effect_points);
  output += ",\"eligible_soldiers_total\":";
  AppendSigned(output, supply.eligible_soldiers_total);
  output += ",\"eligible_soldiers_supplied\":";
  AppendSigned(output, supply.eligible_soldiers_supplied);
  output += ",\"eligible_soldiers_running_low\":";
  AppendSigned(output, supply.eligible_soldiers_running_low);
  output += ",\"eligible_soldiers_starving\":";
  AppendSigned(output, supply.eligible_soldiers_starving);
  output += '}';
}

void AppendAdvantageSideInputs(
    std::string &output,
    const std::vector<game::CombatAdvantageSideInputV3TestOnly> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &side = values[index];
    output += "{\"side\":";
    AppendString(output, side.side);
    output += ",\"primary_army_id\":";
    AppendSigned(output, side.primary_army_id);
    output += ",\"ordered_army_ids\":";
    AppendIdArray(output, side.ordered_army_ids);
    output += ",\"supply\":";
    AppendSupply(output, side.supply);
    output += ",\"primary_army_recently_disembarked_raw\":";
    AppendSigned(output, side.primary_army_recently_disembarked_raw);
    output += ",\"owner_character_id\":";
    AppendSigned(output, side.owner_character_id);
    output += ",\"owner_debt_selector_raw\":";
    AppendSigned(output, side.owner_debt_selector_raw);
    output += ",\"treasury_debt_selector_raw\":";
    if (side.treasury_debt_selector_observable) {
      AppendSigned(output, side.treasury_debt_selector_raw);
    } else {
      output += "null";
    }
    output += '}';
  }
  output += ']';
}

void AppendConstructorSources(
    std::string &output,
    const std::vector<game::CombatAdvantageConstructorSourceV3TestOnly>
        &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &source = values[index];
    output += "{\"stage_order\":";
    AppendSigned(output, source.stage_order);
    output += ",\"append_order\":";
    AppendNullableId(output, source.append_order);
    output += ",\"stage\":";
    AppendString(output, source.stage);
    output += ",\"side\":";
    AppendString(output, source.side);
    output += ",\"source_key\":";
    if (source.selected) {
      AppendString(output, source.source_key);
    } else {
      output += "null";
    }
    output += ",\"effect_advantage_points\":";
    if (source.selected) {
      AppendSigned(output, source.effect_advantage_points);
    } else {
      output += "null";
    }
    output += ",\"scale_raw\":";
    AppendSigned(output, source.scale_raw);
    output += ",\"signed_contribution_raw\":";
    AppendSigned(output, source.signed_contribution_raw);
    output += ",\"accumulator_before_raw\":";
    AppendSigned(output, source.accumulator_before_raw);
    output += ",\"accumulator_after_raw\":";
    AppendSigned(output, source.accumulator_after_raw);
    output += ",\"selected\":";
    output += source.selected ? "true" : "false";
    output += ",\"applied\":";
    output += source.applied ? "true" : "false";
    output += ",\"skip_reason\":";
    if (source.applied) {
      output += "null";
    } else {
      AppendString(output, source.skip_reason);
    }
    output += '}';
  }
  output += ']';
}

void AppendResolvedSide(
    std::string &output,
    const game::CombatResolvedDynamicSideV3TestOnly &side) {
  output += "{\"side\":";
  AppendString(output, side.side);
  output += ",\"battle_commander_character_id\":";
  AppendNullableId(output, side.battle_commander_selected
                               ? side.battle_commander_character_id
                               : -1);
  output += ",\"battle_commander_selected\":";
  output += side.battle_commander_selected ? "true" : "false";
  output += ",\"battle_commander_selection\":\"native_0x23C8A60\"";
  output += ",\"primary_army_gathering_raw\":";
  AppendSigned(output, side.primary_army_gathering_raw);
  output += ",\"gathering\":";
  output += side.primary_army_gathering_raw > 0 ? "true" : "false";
  output += ",\"relation_kind_raw\":";
  AppendSigned(output, side.relation_kind_raw);
  output += ",\"roll_points\":";
  AppendSigned(output, side.roll_points);
  output += ",\"roll_raw\":";
  AppendSigned(output, side.roll_raw);
  output += ",\"target_conditionals_residual_raw\":";
  AppendSigned(output, side.target_conditionals_residual_raw);
  output += ",\"commander_dynamic_raw\":";
  AppendSigned(output, side.commander_dynamic_raw);
  output += ",\"side_dynamic_raw\":";
  AppendSigned(output, side.side_dynamic_raw);
  output += ",\"side_total_raw\":";
  AppendSigned(output, side.side_total_raw);
  output += ",\"contribution_to_resolved_raw\":";
  AppendSigned(output, side.contribution_to_resolved_raw);
  output += '}';
}

void AppendAdvantage(std::string &output,
                     const game::CombatAdvantageModelV3TestOnly &model) {
  output += "{\"status\":";
  AppendString(output, model.available ? "available" : "unavailable");
  output += ",\"scale\":100000,\"scenario_policy\":"
            "\"explicit_hypothetical_fixed_at_contact_no_reinforcements\",";
  output += "\"observation_origin\":";
  AppendString(output, model.observation_origin);
  output += ",\"side_inputs\":";
  if (model.available) {
    AppendAdvantageSideInputs(output, model.side_inputs);
  } else {
    output += "null";
  }
  output += ",\"constructor_call_order\":[";
  for (std::size_t index = 0; index < kConstructorCallOrder.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendString(output, kConstructorCallOrder[index]);
  }
  output += "],\"constructor_sources\":";
  if (model.available) {
    AppendConstructorSources(output, model.constructor_sources);
  } else {
    output += "null";
  }
  output += ",\"base_static_accumulator_raw\":";
  if (model.available) {
    AppendSigned(output, model.base_static_accumulator_raw);
  } else {
    output += "null";
  }
  output += ",\"resolved_dynamic\":";
  if (!model.available) {
    output += "null";
  } else {
    const auto &dynamic = model.resolved_dynamic;
    output += "{\"status\":\"available\",\"helper_status\":"
              "\"original_helpers_matched\",\"context_mode\":"
              "\"temporary_unregistered_local_context\",\"roll_policy\":"
              "\"zero_in_query_sampled_offline\",\"sides\":[";
    for (std::size_t index = 0; index < dynamic.sides.size(); ++index) {
      if (index != 0) {
        output += ',';
      }
      AppendResolvedSide(output, dynamic.sides[index]);
    }
    output += "],\"side_0_dynamic_raw\":";
    AppendSigned(output, dynamic.side_0_dynamic_raw);
    output += ",\"side_1_dynamic_raw\":";
    AppendSigned(output, dynamic.side_1_dynamic_raw);
    output += ",\"resolved_advantage_at_zero_roll_raw\":";
    AppendSigned(output, dynamic.resolved_advantage_at_zero_roll_raw);
    output += ",\"original_total_helper_raw\":";
    AppendSigned(output, dynamic.original_total_helper_raw);
    output += ",\"original_total_helper_match\":";
    output += dynamic.original_total_helper_match ? "true" : "false";
    output += '}';
  }
  output += ",\"unavailable_reason\":";
  if (model.available) {
    output += "null";
  } else {
    AppendString(output, model.unavailable_reason);
  }
  output += '}';
}

} // namespace

std::string SerializeCombatPhaseInputsV3(const CombatPhaseInputsV3 &inputs) {
  std::string output;
  output.reserve(32'768);
  output += "{\"status\":";
  AppendString(output, inputs.available ? "available" : "unavailable");
  output += ",\"rules_source\":\"stock-installation-static-manifest\",";
  output += "\"rules_manifest_sha256\":";
  AppendString(output, game::kCombatPhaseManifestSha256);
  output += ",\"required_state_refs\":{\"count\":132,\"sha256\":";
  AppendString(output, game::kCombatPhaseRequiredRefsSha256);
  output += "},\"state_ref_coverage\":{";
  output += "\"manifest_domain_counts\":{\"character_relation\":79,"
            "\"army\":13,\"side\":10,\"global\":3,\"derived\":27},";
  output += "\"abi_level_counts\":{\"native_leaf_exact\":81,"
            "\"offline_exact\":51,\"determinable\":132,\"missing\":0},";
  output += "\"path_set_sha256\":{\"native_leaf_exact\":";
  AppendString(output,
               "E18C26667EF5F896564B21766E145A5B63C73ACDB5DD8B21ED25853CA793119E");
  output += ",\"offline_exact\":";
  AppendString(output,
               "368924B26875C74EEA9A631CAA528086829851233A48860671140E7842FF5CA6");
  output += ",\"required\":";
  AppendString(output, game::kCombatPhaseRequiredRefsSha256);
  output += "},\"native_payload_policy\":"
            "\"81_exact_native_leaves_plus_51_offline_exact\"},";
  output += "\"scope_mode\":\"hypothetical_precontact_offline_ast\",";
  output += "\"raw\":";
  if (!inputs.available) {
    output += "null";
  } else {
    output += "{\"characters\":";
    AppendCharacters(output, inputs.characters);
    output += ",\"armies\":";
    AppendArmies(output, inputs.armies);
    output += ",\"sides\":";
    AppendSides(output, inputs.sides);
    output += ",\"faith_hostility\":";
    AppendFaithHostility(output, inputs.faith_hostility);
    output += ",\"game_rules\":{\"easy_difficulty\":";
    output += inputs.easy_difficulty ? "true" : "false";
    output += ",\"very_easy_difficulty\":";
    output += inputs.very_easy_difficulty ? "true" : "false";
    output += "}}";
  }
  output += ",\"advantage_model\":";
  if (inputs.available) {
    AppendAdvantage(output, inputs.advantage_model);
  } else {
    output += "null";
  }
  output += ",\"unavailable_reason\":";
  if (inputs.available) {
    output += "null";
  } else {
    AppendString(output, inputs.unavailable_reason);
  }
  output += '}';
  return output;
}

} // namespace xar::ck3_11906
