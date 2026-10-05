// Included inside the existing source serializer detail namespace.
inline void TraitStageOptionalString(std::string &out, const std::optional<std::string> &value) {
  if (value) String(out, *value); else out += "null";
}
inline void TraitStageSignedKeySetJson(std::string &out, const game::ContextSourceSignedKeySetV1 &p) {
  out += "{\"native_index\":" + std::to_string(p.native_index);
  out += ",\"count\":"; Number(out, p.count);
  out += ",\"keys_i32\":"; Numbers(out, p.keys_i32);
  out += ",\"reason\":"; Reason(out, p.reason); out += '}';
}
inline void TraitCondition291d460V1Json(std::string &out, const game::ContextSourceTraitCondition291d460V1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"key_i32\":";
  Number(out, p.key_i32);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"property_identity\":";
  TraitStageOptionalString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TraitGroup291d460V1Json(std::string &out, const game::ContextSourceTraitGroup291d460V1 &p) {
  out += "{\"role\":";
  String(out, p.role);
  out += ",\"track_index\":";
  Number(out, p.track_index);
  out += ",\"level_index\":";
  Number(out, p.level_index);
  out += ",\"property_identity\":";
  TraitStageOptionalString(out, p.property_identity);
  out += ",\"base_property_block\":";
  Properties(out, p.base_property_block);
  out += ",\"conditional_b_count\":";
  Number(out, p.conditional_b_count);
  out += ",\"conditional_b_rows\":";
  if (!p.conditional_b_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.conditional_b_rows->size(); ++i) {
      if (i) out += ',';
      TraitCondition291d460V1Json(out, p.conditional_b_rows->at(i));
    }
    out += ']';
  }
  out += ",\"conditional_a_count\":";
  Number(out, p.conditional_a_count);
  out += ",\"conditional_a_rows\":";
  if (!p.conditional_a_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.conditional_a_rows->size(); ++i) {
      if (i) out += ',';
      TraitCondition291d460V1Json(out, p.conditional_a_rows->at(i));
    }
    out += ']';
  }
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TraitTrack291d460V1Json(std::string &out, const game::ContextSourceTraitTrack291d460V1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"current_value_raw\":";
  Number(out, p.current_value_raw);
  out += ",\"level_count\":";
  Number(out, p.level_count);
  out += ",\"thresholds_read\":";
  Numbers(out, p.thresholds_read);
  out += ",\"admitted_prefix_count\":";
  Number(out, p.admitted_prefix_count);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TraitProbe291d460V1Json(std::string &out, const game::ContextSourceTraitProbe291d460V1 &p) {
  out += "{\"row_index\":";
  out += std::to_string(p.row_index);
  out += ",\"distance_u8\":";
  out += std::to_string(p.distance_u8);
  out += ",\"control_u8\":";
  Number(out, p.control_u8);
  out += ",\"key_pointer_raw\":";
  Number(out, p.key_pointer_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TraitSide291d460V1Json(std::string &out, const game::ContextSourceTraitSide291d460V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"map_mask_raw\":";
  Number(out, p.map_mask_raw);
  out += ",\"map_overflow_raw\":";
  Number(out, p.map_overflow_raw);
  out += ",\"hash_u32\":";
  Number(out, p.hash_u32);
  out += ",\"first_row_index\":";
  Number(out, p.first_row_index);
  out += ",\"probes\":";
  out += '[';
  for (std::size_t i = 0; i < p.probes.size(); ++i) {
    if (i) out += ',';
    TraitProbe291d460V1Json(out, p.probes[i]);
  }
  out += ']';
  out += ",\"kind_raw\":";
  Number(out, p.kind_raw);
  out += ",\"owner_selection\":";
  TraitStageOptionalString(out, p.owner_selection);
  out += ",\"property_identity\":";
  TraitStageOptionalString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TraitRow291d460V1Json(std::string &out, const game::ContextSourceTraitRow291d460V1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"trait_id_raw\":";
  out += std::to_string(p.trait_id_raw);
  out += ",\"definition_selection\":";
  TraitStageOptionalString(out, p.definition_selection);
  out += ",\"definition_identity\":";
  TraitStageOptionalString(out, p.definition_identity);
  out += ",\"definition_pointer_raw\":";
  Number(out, p.definition_pointer_raw);
  out += ",\"definition_id_raw\":";
  Number(out, p.definition_id_raw);
  out += ",\"composite_ready\":";
  out += p.composite_ready ? "true" : "false";
  out += ",\"composite_groups\":";
  out += '[';
  for (std::size_t i = 0; i < p.composite_groups.size(); ++i) {
    if (i) out += ',';
    TraitGroup291d460V1Json(out, p.composite_groups[i]);
  }
  out += ']';
  out += ",\"growth_flag_raw\":";
  Number(out, p.growth_flag_raw);
  out += ",\"track_count_raw\":";
  Number(out, p.track_count_raw);
  out += ",\"growth_trait_match_index\":";
  Number(out, p.growth_trait_match_index);
  out += ",\"growth_prefix_track_counts\":";
  Numbers(out, p.growth_prefix_track_counts);
  out += ",\"growth_prefix_offset_raw\":";
  Number(out, p.growth_prefix_offset_raw);
  out += ",\"growth_aux_count_raw\":";
  Number(out, p.growth_aux_count_raw);
  out += ",\"growth_output_count_raw\":";
  Number(out, p.growth_output_count_raw);
  out += ",\"growth_tracks\":";
  out += '[';
  for (std::size_t i = 0; i < p.growth_tracks.size(); ++i) {
    if (i) out += ',';
    TraitTrack291d460V1Json(out, p.growth_tracks[i]);
  }
  out += ']';
  out += ",\"growth_selection\":";
  String(out, p.growth_selection);
  out += ",\"composite_reason\":";
  Reason(out, p.composite_reason);
  out += ",\"side\":";
  TraitSide291d460V1Json(out, p.side);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TraitStage291d460V1Json(std::string &out, const game::ContextSourceTraitStage291d460V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"trait_count\":";
  Number(out, p.trait_count);
  out += ",\"trait_array_present\":";
  Boolean(out, p.trait_array_present);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      TraitRow291d460V1Json(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"selector_a_key_raw\":";
  Number(out, p.selector_a_key_raw);
  out += ",\"selector_a_selection\":";
  TraitStageOptionalString(out, p.selector_a_selection);
  out += ",\"selector_a_identity\":";
  TraitStageOptionalString(out, p.selector_a_identity);
  out += ",\"selector_b_key_raw\":";
  Number(out, p.selector_b_key_raw);
  out += ",\"selector_b_selection\":";
  TraitStageOptionalString(out, p.selector_b_selection);
  out += ",\"selector_b_identity\":";
  TraitStageOptionalString(out, p.selector_b_identity);
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
  if (!p.selector_b_nested_keys) out += "null";
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
