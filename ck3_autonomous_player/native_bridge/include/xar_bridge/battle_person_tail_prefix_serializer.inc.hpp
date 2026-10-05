// Included inside the existing source serializer detail namespace.
inline void TailPrefixRelationV1Json(std::string &out, const game::ContextSourceTailPrefixRelationV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"character_identity\":";
  HelperString(out, p.character_identity);
  out += ",\"magic_1c_raw\":";
  Number(out, p.magic_1c_raw);
  out += ",\"character_id_18_raw\":";
  Number(out, p.character_id_18_raw);
  out += ",\"accepted\":";
  Boolean(out, p.accepted);
  out += ",\"next_selection\":";
  HelperString(out, p.next_selection);
  out += ",\"next_key_c8_raw\":";
  Number(out, p.next_key_c8_raw);
  out += ",\"next_identity\":";
  HelperString(out, p.next_identity);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TailPrefix275V1Json(std::string &out, const game::ContextSourceTailPrefix275V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"first_key_158_raw\":";
  Number(out, p.first_key_158_raw);
  out += ",\"first_selection\":";
  HelperString(out, p.first_selection);
  out += ",\"first_identity\":";
  HelperString(out, p.first_identity);
  out += ",\"caller_gate_218_raw\":";
  Number(out, p.caller_gate_218_raw);
  out += ",\"caller_gate_218_recheck_raw\":";
  Number(out, p.caller_gate_218_recheck_raw);
  out += ",\"caller_admitted\":";
  Boolean(out, p.caller_admitted);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"definition_pointer_260_identity\":";
  HelperString(out, p.definition_pointer_260_identity);
  out += ",\"character_land_present\":";
  Boolean(out, p.character_land_present);
  out += ",\"land_field_1f8_raw\":";
  Number(out, p.land_field_1f8_raw);
  out += ",\"government_selection\":";
  HelperString(out, p.government_selection);
  out += ",\"government_identity\":";
  HelperString(out, p.government_identity);
  out += ",\"government_mode_80c_raw\":";
  Number(out, p.government_mode_80c_raw);
  out += ",\"predicate_pointer_selection\":";
  HelperString(out, p.predicate_pointer_selection);
  out += ",\"predicate_pointer_identity\":";
  HelperString(out, p.predicate_pointer_identity);
  out += ",\"predicate_admitted\":";
  Boolean(out, p.predicate_admitted);
  out += ",\"owner_key_1e0_raw\":";
  Number(out, p.owner_key_1e0_raw);
  out += ",\"owner_selection\":";
  HelperString(out, p.owner_selection);
  out += ",\"owner_identity\":";
  HelperString(out, p.owner_identity);
  out += ",\"owner_id_160_raw\":";
  Number(out, p.owner_id_160_raw);
  out += ",\"character_id_18_raw\":";
  Number(out, p.character_id_18_raw);
  out += ",\"initial_relation_selection\":";
  HelperString(out, p.initial_relation_selection);
  out += ",\"initial_relation_key_c8_raw\":";
  Number(out, p.initial_relation_key_c8_raw);
  out += ",\"initial_relation_identity\":";
  HelperString(out, p.initial_relation_identity);
  out += ",\"relation_rows\":";
  if (!p.relation_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.relation_rows->size(); ++i) {
      if (i) out += ',';
      TailPrefixRelationV1Json(out, p.relation_rows->at(i));
    }
    out += ']';
  }
  out += ",\"last_character_id_18_raw\":";
  Number(out, p.last_character_id_18_raw);
  out += ",\"owner_admitted\":";
  Boolean(out, p.owner_admitted);
  out += ",\"property_identity\":";
  HelperString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TailPrefix2530RowV1Json(std::string &out, const game::ContextSourceTailPrefix2530RowV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"count_214_raw\":";
  Number(out, p.count_214_raw);
  out += ",\"requested_index_228_raw\":";
  Number(out, p.requested_index_228_raw);
  out += ",\"selected_index_raw\":";
  Number(out, p.selected_index_raw);
  out += ",\"table_identity\":";
  HelperString(out, p.table_identity);
  out += ",\"property_identity\":";
  HelperString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TailPrefix2530V1Json(std::string &out, const game::ContextSourceTailPrefix2530V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"first_key_158_raw\":";
  Number(out, p.first_key_158_raw);
  out += ",\"first_selection\":";
  HelperString(out, p.first_selection);
  out += ",\"first_identity\":";
  HelperString(out, p.first_identity);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"definition_magic_38_raw\":";
  Number(out, p.definition_magic_38_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"type_280_raw\":";
  Number(out, p.type_280_raw);
  out += ",\"owner_id_160_raw\":";
  Number(out, p.owner_id_160_raw);
  out += ",\"character_id_18_raw\":";
  Number(out, p.character_id_18_raw);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      TailPrefix2530RowV1Json(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void TailPrefixV1Json(std::string &out, const game::ContextSourceTailPrefixV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"helper_2753860\":";
  TailPrefix275V1Json(out, p.helper_2753860);
  out += ",\"helper_2922530\":";
  TailPrefix2530V1Json(out, p.helper_2922530);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
