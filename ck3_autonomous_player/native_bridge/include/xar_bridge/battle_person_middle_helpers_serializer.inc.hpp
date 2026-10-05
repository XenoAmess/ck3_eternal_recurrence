// Included inside the existing source serializer detail namespace.
template <typename T> inline void MiddleJsonStart(std::string &out, const T &p) {
  out += "{\"status\":"; String(out, p.status);
  out += ",\"ready\":"; out += p.ready ? "true" : "false";
}
template <typename T> inline void MiddleJsonEnd(std::string &out, const T &p) {
  out += ",\"reason\":"; Reason(out, p.reason); out += '}';
}
inline void MiddleRankFamilyV1Json(std::string &out, const game::ContextSourceMiddleRankFamilyV1 &p) {
  MiddleJsonStart(out, p);
  out += ",\"native_index\":"; out += std::to_string(p.native_index);
  out += ",\"score_q64\":"; Number(out, p.score_q64);
  out += ",\"override_raw\":"; Number(out, p.override_raw);
  out += ",\"threshold_count\":"; Number(out, p.threshold_count);
  out += ",\"threshold_array_present\":"; Boolean(out, p.threshold_array_present);
  out += ",\"thresholds_consumed_q64\":";
  if (!p.thresholds_consumed_q64) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.thresholds_consumed_q64->size(); ++i) {
      if (i) out += ',';
      out += std::to_string(p.thresholds_consumed_q64->at(i));
    }
    out += ']';
  }
  out += ",\"rank_raw\":"; Number(out, p.rank_raw);
  out += ",\"manager_count_raw\":"; Number(out, p.manager_count_raw);
  out += ",\"definition_selection\":"; HelperString(out, p.definition_selection);
  out += ",\"definition_identity\":"; HelperString(out, p.definition_identity);
  out += ",\"definition_gate_raw\":"; Number(out, p.definition_gate_raw);
  out += ",\"admitted\":"; Boolean(out, p.admitted);
  out += ",\"weight_key_u16\":"; out += std::to_string(p.weight_key_u16);
  out += ",\"weight_carrier_present\":"; Boolean(out, p.weight_carrier_present);
  out += ",\"weight_owner_matches\":"; Boolean(out, p.weight_owner_matches);
  out += ",\"weight_source_selection\":"; HelperString(out, p.weight_source_selection);
  out += ",\"weight_source_identity\":"; HelperString(out, p.weight_source_identity);
  out += ",\"weight_default_guard_raw\":"; Number(out, p.weight_default_guard_raw);
  out += ",\"weight_keys_count_raw\":"; Number(out, p.weight_keys_count_raw);
  out += ",\"weight_key_probes\":";
  if (!p.weight_key_probes) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.weight_key_probes->size(); ++i) {
      if (i) out += ',';
      const auto &probe = p.weight_key_probes->at(i);
      out += "{\"native_index\":"; out += std::to_string(probe.native_index);
      out += ",\"key_u16\":"; out += std::to_string(probe.key_u16); out += '}';
    }
    out += ']';
  }
  out += ",\"weight_found\":"; Boolean(out, p.weight_found);
  out += ",\"weight_native_index\":"; Number(out, p.weight_native_index);
  out += ",\"weight_value_q64\":"; Number(out, p.weight_value_q64);
  out += ",\"weight_q64\":"; Number(out, p.weight_q64);
  out += ",\"property_identity\":"; HelperString(out, p.property_identity);
  out += ",\"property_block\":"; Properties(out, p.property_block);
  MiddleJsonEnd(out, p);
}
inline void Middle260V1Json(std::string &out, const game::ContextSourceMiddle260V1 &p) {
  MiddleJsonStart(out, p);
  out += ",\"component_present\":"; Boolean(out, p.component_present);
  out += ",\"families\":[";
  for (std::size_t i = 0; i < p.families.size(); ++i) {
    if (i) out += ',';
    MiddleRankFamilyV1Json(out, p.families[i]);
  }
  out += ']'; MiddleJsonEnd(out, p);
}
inline void MiddleModifierV1Json(std::string &out, const game::ContextSourceMiddleModifierV1 &p) {
  out += "{\"native_index\":"; out += std::to_string(p.native_index);
  out += ",\"modifier_identity\":"; HelperString(out, p.modifier_identity);
  out += ",\"token_u8\":"; Number(out, p.token_u8);
  out += ",\"modifier_count_u8\":"; Number(out, p.modifier_count_u8);
  out += ",\"base_selection\":"; HelperString(out, p.base_selection);
  out += ",\"property_identity\":"; HelperString(out, p.property_identity);
  out += ",\"gate_raw\":"; Number(out, p.gate_raw);
  out += ",\"admitted\":"; Boolean(out, p.admitted);
  out += ",\"property_block\":"; Properties(out, p.property_block);
  MiddleJsonEnd(out, p);
}
inline void MiddleContextV1Json(std::string &out, const game::ContextSourceMiddleContextV1 &p) {
  MiddleJsonStart(out, p);
  out += ",\"native_index\":"; out += std::to_string(p.native_index);
  out += ",\"requested_full_id_raw\":"; Number(out, p.requested_full_id_raw);
  out += ",\"selection\":"; HelperString(out, p.selection);
  out += ",\"context_identity\":"; HelperString(out, p.context_identity);
  out += ",\"magic_raw\":"; Number(out, p.magic_raw);
  out += ",\"full_id_raw\":"; Number(out, p.full_id_raw);
  out += ",\"admitted\":"; Boolean(out, p.admitted);
  out += ",\"owner_full_id_raw\":"; Number(out, p.owner_full_id_raw);
  out += ",\"character_full_id_raw\":"; Number(out, p.character_full_id_raw);
  out += ",\"owner_matches\":"; Boolean(out, p.owner_matches);
  out += ",\"modifier_count\":"; Number(out, p.modifier_count);
  out += ",\"modifier_array_present\":"; Boolean(out, p.modifier_array_present);
  out += ",\"token_array_present\":"; Boolean(out, p.token_array_present);
  out += ",\"modifier_rows\":";
  if (!p.modifier_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.modifier_rows->size(); ++i) {
      if (i) out += ',';
      MiddleModifierV1Json(out, p.modifier_rows->at(i));
    }
    out += ']';
  }
  out += ",\"terminal_property_identity\":"; HelperString(out, p.terminal_property_identity);
  out += ",\"terminal_property_block\":"; Properties(out, p.terminal_property_block);
  MiddleJsonEnd(out, p);
}
inline void MiddleContextFamilyV1Json(std::string &out, const game::ContextSourceMiddleContextFamilyV1 &p) {
  MiddleJsonStart(out, p);
  out += ",\"header_selection\":"; HelperString(out, p.header_selection);
  out += ",\"count\":"; Number(out, p.count);
  out += ",\"array_present\":"; Boolean(out, p.array_present);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      MiddleContextV1Json(out, p.rows->at(i));
    }
    out += ']';
  }
  MiddleJsonEnd(out, p);
}
inline void MiddleFb10V1Json(std::string &out, const game::ContextSourceMiddleFb10V1 &p) {
  MiddleJsonStart(out, p);
  out += ",\"land_present\":"; Boolean(out, p.land_present);
  out += ",\"preferred\":"; MiddleContextFamilyV1Json(out, p.preferred);
  out += ",\"list_218\":"; MiddleContextFamilyV1Json(out, p.list_218);
  out += ",\"list_248\":"; MiddleContextFamilyV1Json(out, p.list_248);
  MiddleJsonEnd(out, p);
}
inline void MiddleHelpersV1Json(std::string &out, const game::ContextSourceMiddleHelpersV1 &p) {
  MiddleJsonStart(out, p);
  out += ",\"character_id\":"; out += std::to_string(p.character_id);
  out += ",\"helper_291f260\":"; Middle260V1Json(out, p.helper_291f260);
  out += ",\"helper_291fb10\":"; MiddleFb10V1Json(out, p.helper_291fb10);
  MiddleJsonEnd(out, p);
}
