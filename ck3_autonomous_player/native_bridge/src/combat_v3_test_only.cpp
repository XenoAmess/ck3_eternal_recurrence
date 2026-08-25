#include "xar_bridge/combat_v3_test_only.hpp"

#include <array>
#include <charconv>
#include <string>

namespace xar::game {
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
    "gathering_army_0",
    "gathering_army_1",
    "debt_0_owner_then_treasury",
    "debt_1_owner_then_treasury",
    "unreformed_faith_0",
    "unreformed_faith_1",
    "side_finalize_0",
    "side_finalize_1",
};

constexpr std::array<std::string_view, 7> kTestOnlyBlockers{
    "native_exact_phase_state_readers",
    "native_advantage_model_fixture_and_paused_live_acceptance",
    "loaded_playset_phase_effects_exact",
    "phase_effect_ast_evaluator_exact",
    "effect_local_candidate_order_exact",
    "dynamic_participant_route_exact",
    "original_participant_recompute_trace_exact",
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

std::string_view StateValueKindName(CombatPhaseStateValueKind kind) {
  switch (kind) {
  case CombatPhaseStateValueKind::boolean:
    return "bool";
  case CombatPhaseStateValueKind::signed_int32:
    return "signed_int32";
  case CombatPhaseStateValueKind::signed_int64:
    return "signed_int64";
  case CombatPhaseStateValueKind::signed_q100000:
    return "signed_q100000";
  case CombatPhaseStateValueKind::full_id:
    return "full_id";
  case CombatPhaseStateValueKind::full_id_array:
    return "full_id_array";
  case CombatPhaseStateValueKind::string:
    return "string";
  case CombatPhaseStateValueKind::not_applicable:
    return "not_applicable";
  }
  return "not_applicable";
}

void AppendStateRef(std::string &output,
                    const CombatPhaseStateRefV3TestOnly &ref) {
  output += "{\"path\":";
  AppendString(output, ref.path);
  output += ",\"value_type\":";
  AppendString(output, StateValueKindName(ref.value_kind));
  output += ",\"value\":";
  switch (ref.value_kind) {
  case CombatPhaseStateValueKind::boolean:
    output += ref.boolean_value ? "true" : "false";
    break;
  case CombatPhaseStateValueKind::signed_int32:
  case CombatPhaseStateValueKind::signed_int64:
  case CombatPhaseStateValueKind::signed_q100000:
  case CombatPhaseStateValueKind::full_id:
    AppendSigned(output, ref.signed_value);
    break;
  case CombatPhaseStateValueKind::full_id_array:
    AppendIdArray(output, ref.id_values);
    break;
  case CombatPhaseStateValueKind::string:
  case CombatPhaseStateValueKind::not_applicable:
    AppendString(output, ref.string_value);
    break;
  }
  output += '}';
}

void AppendStateRefs(
    std::string &output,
    const std::vector<CombatPhaseStateRefV3TestOnly> &refs) {
  output += '[';
  for (std::size_t index = 0; index < refs.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendStateRef(output, refs[index]);
  }
  output += ']';
}

void AppendCharacters(
    std::string &output,
    const std::vector<CombatPhaseCharacterV3TestOnly> &characters) {
  output += '[';
  for (std::size_t index = 0; index < characters.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &character = characters[index];
    output += "{\"character_id\":";
    AppendSigned(output, character.character_id);
    output += ",\"source_army_id\":";
    AppendSigned(output, character.source_army_id);
    output += ",\"source_regiment_id\":";
    if (character.source_regiment_id < 0) {
      output += "null";
    } else {
      AppendSigned(output, character.source_regiment_id);
    }
    output += ",\"encounter_role\":";
    AppendString(output, character.encounter_role);
    output += ",\"phase_roles\":";
    AppendStringArray(output, character.phase_roles);
    output += ",\"state_refs\":";
    AppendStateRefs(output, character.state_refs);
    output += '}';
  }
  output += ']';
}

void AppendArmies(std::string &output,
                  const std::vector<CombatPhaseArmyV3TestOnly> &armies) {
  output += '[';
  for (std::size_t index = 0; index < armies.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &army = armies[index];
    output += "{\"army_id\":";
    AppendSigned(output, army.army_id);
    output += ",\"encounter_role\":";
    AppendString(output, army.encounter_role);
    output += ",\"state_refs\":";
    AppendStateRefs(output, army.state_refs);
    output += '}';
  }
  output += ']';
}

void AppendSides(std::string &output,
                 const std::vector<CombatPhaseSideV3TestOnly> &sides) {
  output += '[';
  for (std::size_t index = 0; index < sides.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &side = sides[index];
    output += "{\"side_index\":";
    AppendSigned(output, side.side_index);
    output += ",\"encounter_role\":";
    AppendString(output, side.encounter_role);
    output += ",\"ordered_army_ids\":";
    AppendIdArray(output, side.ordered_army_ids);
    output += ",\"ordered_character_ids\":";
    AppendIdArray(output, side.ordered_character_ids);
    output += ",\"primary_participant_character_id\":";
    AppendSigned(output, side.primary_participant_character_id);
    output += ",\"primary_source_army_id\":";
    AppendSigned(output, side.primary_source_army_id);
    output += ",\"primary_selection_policy\":";
    AppendString(output, side.primary_selection_policy);
    output += ",\"side_strength_raw\":";
    AppendSigned(output, side.side_strength_raw);
    output += ",\"side_strength_scale\":100000";
    output += ",\"side_army_size_raw\":";
    AppendSigned(output, side.side_army_size_raw);
    output += ",\"side_army_size_scale\":100000";
    output += ",\"state_refs\":";
    AppendStateRefs(output, side.state_refs);
    output += '}';
  }
  output += ']';
}

void AppendSupplyInput(std::string &output,
                       const CombatAdvantageSupplyInputV3TestOnly &supply) {
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
    const std::vector<CombatAdvantageSideInputV3TestOnly> &sides) {
  output += '[';
  for (std::size_t index = 0; index < sides.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &side = sides[index];
    output += "{\"side\":";
    AppendString(output, side.side);
    output += ",\"primary_army_id\":";
    AppendSigned(output, side.primary_army_id);
    output += ",\"ordered_army_ids\":";
    AppendIdArray(output, side.ordered_army_ids);
    output += ",\"supply\":";
    AppendSupplyInput(output, side.supply);
    output += ",\"primary_army_gathering_raw\":";
    AppendSigned(output, side.primary_army_gathering_raw);
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
    const std::vector<CombatAdvantageConstructorSourceV3TestOnly> &sources) {
  output += '[';
  for (std::size_t index = 0; index < sources.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    const auto &source = sources[index];
    output += "{\"stage_order\":";
    AppendSigned(output, source.stage_order);
    output += ",\"append_order\":";
    if (source.append_order < 0) {
      output += "null";
    } else {
      AppendSigned(output, source.append_order);
    }
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

void AppendResolvedDynamicSide(
    std::string &output,
    const CombatResolvedDynamicSideV3TestOnly &side) {
  output += "{\"side\":";
  AppendString(output, side.side);
  output += ",\"battle_commander_character_id\":";
  if (side.battle_commander_selected) {
    AppendSigned(output, side.battle_commander_character_id);
  } else {
    output += "null";
  }
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

void AppendResolvedDynamic(std::string &output,
                           const CombatResolvedDynamicV3TestOnly &dynamic) {
  output += "{\"status\":\"available\",\"helper_status\":"
            "\"original_helpers_matched\",\"context_mode\":"
            "\"temporary_unregistered_local_context\",\"roll_policy\":"
            "\"zero_in_query_sampled_offline\",\"sides\":[";
  for (std::size_t index = 0; index < dynamic.sides.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendResolvedDynamicSide(output, dynamic.sides[index]);
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

void AppendAdvantageModel(std::string &output,
                          const CombatAdvantageModelV3TestOnly &model) {
  output += "{\"status\":";
  AppendString(output, model.available ? "available" : "unavailable");
  output += ",\"scale\":100000,\"scenario_policy\":"
            "\"explicit_hypothetical_fixed_at_contact_no_reinforcements\","
            "\"observation_origin\":";
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
  if (model.available) {
    AppendResolvedDynamic(output, model.resolved_dynamic);
  } else {
    output += "null";
  }
  output += ",\"unavailable_reason\":";
  if (model.available) {
    output += "null";
  } else {
    AppendString(output, model.unavailable_reason);
  }
  output += '}';
}

void AppendBlockers(std::string &output) {
  output += '[';
  for (std::size_t index = 0; index < kTestOnlyBlockers.size(); ++index) {
    if (index != 0) {
      output += ',';
    }
    AppendString(output, kTestOnlyBlockers[index]);
  }
  output += ']';
}

} // namespace

std::string SerializeCombatPhaseInputsV3TestOnly(
    const CombatPhaseInputsV3TestOnly &inputs) {
  std::string output;
  output.reserve(8'192);
  output += "{\"status\":";
  AppendString(output, inputs.available ? "partial" : "unavailable");
  output += ",\"rules_source\":"
            "\"stock-installation-static-manifest\",\"rules_manifest_sha256\":";
  AppendString(output, kCombatPhaseManifestSha256);
  output += ",\"required_state_refs\":{\"count\":";
  AppendSigned(output, kCombatPhaseRequiredRefCount);
  output += ",\"sha256\":";
  AppendString(output, kCombatPhaseRequiredRefsSha256);
  output += "},\"state_ref_coverage\":{"
            "\"manifest_domain_counts\":{\"character_relation\":79,"
            "\"army\":13,\"side\":10,\"global\":3,\"derived\":27},"
            "\"abi_level_counts\":{\"native_leaf_exact\":47,"
            "\"offline_derived_exact\":15,\"determinable\":62,"
            "\"remaining_unclosed\":70,\"production_live_observed\":0},"
            "\"path_set_sha256\":{\"native_leaf_exact\":"
            "\"1BB1CA55C1C7E2388B5FE2A71CB4AFBD76DAD784A9CDB825615E2AACB94D8D5E\","
            "\"offline_derived_exact\":"
            "\"7F93575CEDFE3CF1DCEBC6265A2BE867FA1BC341CDFE334DE3791B6A9AB48064\","
            "\"remaining_unclosed\":"
            "\"180FD456E591FF72CF513D5197EB927782EB813001DDAE533482B3985038A60F\"},"
            "\"native_payload_policy\":"
            "\"closed_native_leaves_only_offline_derived_not_serialized\"},"
            "\"scope_mode\":\"hypothetical_precontact_offline_ast\",";
  output += "\"characters\":";
  if (inputs.available) {
    AppendCharacters(output, inputs.characters);
  } else {
    output += "null";
  }
  output += ",\"armies\":";
  if (inputs.available) {
    AppendArmies(output, inputs.armies);
  } else {
    output += "null";
  }
  output += ",\"sides\":";
  if (inputs.available) {
    AppendSides(output, inputs.sides);
  } else {
    output += "null";
  }
  output += ",\"global_state_refs\":";
  if (inputs.available) {
    AppendStateRefs(output, inputs.global_state_refs);
  } else {
    output += "null";
  }
  output += ",\"advantage_model\":";
  if (inputs.available) {
    AppendAdvantageModel(output, inputs.advantage_model);
  } else {
    output += "null";
  }
  output += ",\"row_evaluations\":";
  if (inputs.available) {
    output += "{\"status\":\"unsupported\","
              "\"scope\":\"hypothetical_precontact\",\"reason\":"
              "\"hypothetical_precontact_has_no_real_combat_side\"}";
  } else {
    output += "null";
  }
  output += ',';
  output += "\"offline_admission\":{\"raw_state_ref_contract_complete\":true,"
            "\"advantage_model_contract_complete\":true,"
            "\"native_raw_state_refs_ready\":false,"
            "\"native_advantage_model_ready\":false,"
            "\"loaded_playset_verified\":false,"
            "\"ast_evaluator_ready\":false,\"ready\":false,"
            "\"missing_required_domains\":";
  AppendBlockers(output);
  output += "},\"unavailable_reason\":";
  if (inputs.available) {
    output += "\"v3_test_only_contract_not_production_ready\"";
  } else {
    AppendString(output, inputs.unavailable_reason);
  }
  output += '}';
  return output;
}

} // namespace xar::game
