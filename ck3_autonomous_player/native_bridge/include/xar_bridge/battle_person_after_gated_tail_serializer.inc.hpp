// Included inside the existing context-source serializer detail namespace.

inline void AfterPcJson(std::string &out, const game::ContextSourceAfterPcV1 &p) {
  out += "{\"property_identity\":";
  HelperString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterDateJson(std::string &out, const game::ContextSourceAfterDateV1 &p) {
  out += "{\"raw_i32\":";
  Number(out, p.raw_i32);
  out += ",\"day_cache_i8\":";
  Number(out, p.day_cache_i8);
  out += ",\"month_cache_i8\":";
  Number(out, p.month_cache_i8);
  out += ",\"year_cache_i16\":";
  Number(out, p.year_cache_i16);
  out += '}';
}

inline void AfterThresholdRowJson(std::string &out, const game::ContextSourceAfterThresholdRowV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"threshold_raw\":";
  Number(out, p.threshold_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"pc\":";
  AfterPcJson(out, p.pc);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterRowsetJson(std::string &out, const game::ContextSourceAfterRowsetV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      AfterThresholdRowJson(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterRelatedSelectionJson(std::string &out, const game::ContextSourceAfterRelatedSelectionV1 &p) {
  out += "{\"carrier_present\":";
  Boolean(out, p.carrier_present);
  out += ",\"attempts\":";
  out += '[';
  for (std::size_t i = 0; i < p.attempts.size(); ++i) {
    if (i) out += ',';
    GatedResolutionJson(out, p.attempts.at(i));
  }
  out += ']';
  out += ",\"self_full_id_raw\":";
  Number(out, p.self_full_id_raw);
  out += ",\"helper_return_full_id_raw\":";
  Number(out, p.helper_return_full_id_raw);
  out += ",\"caller_selection\":";
  HelperString(out, p.caller_selection);
  out += ",\"caller_identity\":";
  HelperString(out, p.caller_identity);
  out += ",\"caller_requested_full_id_raw\":";
  Number(out, p.caller_requested_full_id_raw);
  out += ",\"caller_full_id_raw\":";
  Number(out, p.caller_full_id_raw);
  out += ",\"caller_magic_raw\":";
  Number(out, p.caller_magic_raw);
  out += ",\"caller_admitted\":";
  Boolean(out, p.caller_admitted);
  out += ",\"land_present\":";
  Boolean(out, p.land_present);
  out += ",\"selected_present\":";
  Boolean(out, p.selected_present);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterCompositionJson(std::string &out, const game::ContextSourceAfterCompositionV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"global_flag_u8\":";
  Number(out, p.global_flag_u8);
  out += ",\"global_bit20\":";
  Boolean(out, p.global_bit20);
  out += ",\"current_land_present\":";
  Boolean(out, p.current_land_present);
  out += ",\"current_selected_present\":";
  Boolean(out, p.current_selected_present);
  out += ",\"receiver_selection\":";
  HelperString(out, p.receiver_selection);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"related\":";
  AfterRelatedSelectionJson(out, p.related);
  out += ",\"owner_mode\":";
  Boolean(out, p.owner_mode);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"level_raw\":";
  Number(out, p.level_raw);
  out += ",\"handle_date\":";
  AfterDateJson(out, p.handle_date);
  out += ",\"fifth_date\":";
  AfterDateJson(out, p.fifth_date);
  out += ",\"current_date\":";
  AfterDateJson(out, p.current_date);
  out += ",\"chosen_date_selection\":";
  HelperString(out, p.chosen_date_selection);
  out += ",\"completed_months_raw\":";
  Number(out, p.completed_months_raw);
  out += ",\"level_rows\":";
  AfterRowsetJson(out, p.level_rows);
  out += ",\"month_rows\":";
  AfterRowsetJson(out, p.month_rows);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterRuleJson(std::string &out, const game::ContextSourceAfterRuleV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"mode_raw\":";
  Number(out, p.mode_raw);
  out += ",\"tree_present\":";
  Boolean(out, p.tree_present);
  out += ",\"tree_identity\":";
  HelperString(out, p.tree_identity);
  out += ",\"named_present\":";
  Boolean(out, p.named_present);
  out += ",\"named\":";
  GatedNamedLiteralJson(out, p.named);
  out += ",\"target_count_raw\":";
  Number(out, p.target_count_raw);
  out += ",\"raw_98_q64\":";
  Number(out, p.raw_98_q64);
  out += ",\"value_q64\":";
  Number(out, p.value_q64);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterKindJson(std::string &out, const game::ContextSourceAfterKindV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"position_120_raw\":";
  Number(out, p.position_120_raw);
  out += ",\"position_124_raw\":";
  Number(out, p.position_124_raw);
  out += ",\"owner_selection\":";
  HelperString(out, p.owner_selection);
  out += ",\"owner_identity\":";
  HelperString(out, p.owner_identity);
  out += ",\"owner_full_id_raw\":";
  Number(out, p.owner_full_id_raw);
  out += ",\"played_count_raw\":";
  Number(out, p.played_count_raw);
  out += ",\"played_full_ids\":";
  Numbers(out, p.played_full_ids);
  out += ",\"owner_played\":";
  Boolean(out, p.owner_played);
  out += ",\"raw_a0_u8\":";
  Number(out, p.raw_a0_u8);
  out += ",\"threshold_count_raw\":";
  Number(out, p.threshold_count_raw);
  out += ",\"thresholds_i32\":";
  Numbers(out, p.thresholds_i32);
  out += ",\"rule\":";
  AfterRuleJson(out, p.rule);
  out += ",\"kind_raw\":";
  Number(out, p.kind_raw);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterPairProbeJson(std::string &out, const game::ContextSourceAfterPairProbeV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += '}';
}

inline void AfterPositionJson(std::string &out, const game::ContextSourceAfterPositionV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"requested_full_id_raw\":";
  Number(out, p.requested_full_id_raw);
  out += ",\"position_selection\":";
  HelperString(out, p.position_selection);
  out += ",\"position_identity\":";
  HelperString(out, p.position_identity);
  out += ",\"position_full_id_raw\":";
  Number(out, p.position_full_id_raw);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"other_definition_identity\":";
  HelperString(out, p.other_definition_identity);
  out += ",\"other_magic_raw\":";
  Number(out, p.other_magic_raw);
  out += ",\"other_admitted\":";
  Boolean(out, p.other_admitted);
  out += ",\"base_pc\":";
  AfterPcJson(out, p.base_pc);
  out += ",\"tier_pc\":";
  AfterPcJson(out, p.tier_pc);
  out += ",\"composite_group\":";
  if (p.composite_group) TraitGroup291d460V1Json(out, *p.composite_group); else out += "null";
  out += ",\"kind\":";
  AfterKindJson(out, p.kind);
  out += ",\"other_base_pc\":";
  AfterPcJson(out, p.other_base_pc);
  out += ",\"other_tier_pc\":";
  AfterPcJson(out, p.other_tier_pc);
  out += ",\"other_kind\":";
  AfterKindJson(out, p.other_kind);
  out += ",\"definition_pair_probes\":";
  out += '[';
  for (std::size_t i = 0; i < p.definition_pair_probes.size(); ++i) {
    if (i) out += ',';
    AfterPairProbeJson(out, p.definition_pair_probes.at(i));
  }
  out += ']';
  out += ",\"definition_pair_admitted\":";
  Boolean(out, p.definition_pair_admitted);
  out += ",\"other_pair_probes\":";
  out += '[';
  for (std::size_t i = 0; i < p.other_pair_probes.size(); ++i) {
    if (i) out += ',';
    AfterPairProbeJson(out, p.other_pair_probes.at(i));
  }
  out += ']';
  out += ",\"other_pair_admitted\":";
  Boolean(out, p.other_pair_admitted);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterCourtListJson(std::string &out, const game::ContextSourceAfterCourtListV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"owner_present\":";
  Boolean(out, p.owner_present);
  out += ",\"header_selection\":";
  HelperString(out, p.header_selection);
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += ",\"numeric_count\":";
  Number(out, p.numeric_count);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"default_init_guard_raw\":";
  Number(out, p.default_init_guard_raw);
  out += ",\"related\":";
  AfterRelatedSelectionJson(out, p.related);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      AfterPositionJson(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterSelectorInputsJson(std::string &out, const game::ContextSourceTraitStage291d460V1 &p) {
  out += "{\"selector_a_key_raw\":";
  Number(out, p.selector_a_key_raw);
  out += ",\"selector_a_selection\":";
  HelperString(out, p.selector_a_selection);
  out += ",\"selector_a_identity\":";
  HelperString(out, p.selector_a_identity);
  out += ",\"selector_b_key_raw\":";
  Number(out, p.selector_b_key_raw);
  out += ",\"selector_b_selection\":";
  HelperString(out, p.selector_b_selection);
  out += ",\"selector_b_identity\":";
  HelperString(out, p.selector_b_identity);
  out += ",\"selector_a_membership_count\":";
  Number(out, p.selector_a_membership_count);
  out += ",\"selector_a_keys_i32\":";
  Numbers(out, p.selector_a_keys_i32);
  out += ",\"selector_b_primary_count\":";
  Number(out, p.selector_b_primary_count);
  out += ",\"selector_b_primary_keys_i32\":";
  Numbers(out, p.selector_b_primary_keys_i32);
  out += ",\"selector_b_nested_count\":";
  Number(out, p.selector_b_nested_count);
  out += ",\"selector_b_nested_keys\":";
  // The sealed ledger has an occurrence list, with the nullable raw count
  // separately recording whether the nested family was demanded.
  if (!p.selector_b_nested_keys) out += "[]";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.selector_b_nested_keys->size(); ++i) {
      if (i) out += ',';
      TraitStageSignedKeySetJson(out, p.selector_b_nested_keys->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void AfterGatedTail326a8e0And2920310Json(std::string &out, const game::ContextSourceAfterGatedTail326a8e0And2920310V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"current_land_present\":";
  Boolean(out, p.current_land_present);
  out += ",\"selector_inputs\":";
  AfterSelectorInputsJson(out, p.selector_inputs);
  out += ",\"composition_326a8e0\":";
  AfterCompositionJson(out, p.composition_326a8e0);
  out += ",\"current_1b8_court_positions\":";
  AfterCourtListJson(out, p.current_1b8_court_positions);
  out += ",\"current_1c0_court_positions\":";
  AfterCourtListJson(out, p.current_1c0_court_positions);
  out += ",\"related_court_positions\":";
  AfterCourtListJson(out, p.related_court_positions);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
