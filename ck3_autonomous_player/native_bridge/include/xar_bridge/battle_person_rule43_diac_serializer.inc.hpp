// Included inside the existing context-source serializer detail namespace.
inline void Rule43NodeJson(std::string &out, const game::Rule43NodeV1 &p) {
  out += "{\"path\":";
  String(out, p.path);
  out += ",\"identity\":";
  HelperString(out, p.identity);
  out += ",\"slot58_rva\":";
  Number(out, p.slot58_rva);
  out += ",\"slot60_rva\":";
  Number(out, p.slot60_rva);
  out += ",\"slotc8_rva\":";
  Number(out, p.slotc8_rva);
  out += ",\"children_count_raw\":";
  Number(out, p.children_count_raw);
  out += ",\"children_array_present\":";
  Boolean(out, p.children_array_present);
  out += ",\"reference_arguments_count_raw\":";
  Number(out, p.reference_arguments_count_raw);
  out += ",\"reference_compare_raw\":";
  Number(out, p.reference_compare_raw);
  out += ",\"nested_present\":";
  Boolean(out, p.nested_present);
  out += ",\"children\":";
  out += "[";
  for (std::size_t i = 0; i < p.children.size(); ++i) {
    if (i) out += ',';
    Rule43NodeJson(out, p.children[i]);
  }
  out += ']';
  out += ",\"result\":";
  Boolean(out, p.result);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Rule43AdmissionJson(std::string &out, const game::Rule43AdmissionV1 &p) {
  out += "{\"input_character_full_id\":";
  out += std::to_string(p.input_character_full_id);
  out += ",\"source_constructed_root_kind\":";
  out += std::to_string(p.source_constructed_root_kind);
  out += ",\"expected_validator_rva\":";
  out += std::to_string(p.expected_validator_rva);
  out += ",\"mode_raw\":";
  Number(out, p.mode_raw);
  out += ",\"provider_identity\":";
  HelperString(out, p.provider_identity);
  out += ",\"rule_identity\":";
  HelperString(out, p.rule_identity);
  out += ",\"registry_count_raw\":";
  Number(out, p.registry_count_raw);
  out += ",\"descriptor_selection\":";
  HelperString(out, p.descriptor_selection);
  out += ",\"loaded_validator_rva\":";
  Number(out, p.loaded_validator_rva);
  out += ",\"root_lookup_selection\":";
  HelperString(out, p.root_lookup_selection);
  out += ",\"root_object_identity\":";
  HelperString(out, p.root_object_identity);
  out += ",\"root_tag_raw\":";
  Number(out, p.root_tag_raw);
  out += ",\"root_full_id_raw\":";
  Number(out, p.root_full_id_raw);
  out += ",\"root_valid\":";
  Boolean(out, p.root_valid);
  out += ",\"nodes\":";
  out += "[";
  for (std::size_t i = 0; i < p.nodes.size(); ++i) {
    if (i) out += ',';
    Rule43NodeJson(out, p.nodes[i]);
  }
  out += ']';
  out += ",\"result\":";
  Boolean(out, p.result);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void DiacSelectionJson(std::string &out, const game::DiacSelectionV1 &p) {
  out += "{\"source_character_identity\":";
  HelperString(out, p.source_character_identity);
  out += ",\"requested_diac_id_raw\":";
  Number(out, p.requested_diac_id_raw);
  out += ",\"lookup_selection\":";
  HelperString(out, p.lookup_selection);
  out += ",\"diac_identity\":";
  HelperString(out, p.diac_identity);
  out += ",\"diac_tag_raw\":";
  Number(out, p.diac_tag_raw);
  out += ",\"diac_full_id_raw\":";
  Number(out, p.diac_full_id_raw);
  out += ",\"diac_owner_full_id_raw\":";
  Number(out, p.diac_owner_full_id_raw);
  out += ",\"early_character_lookup_selection\":";
  HelperString(out, p.early_character_lookup_selection);
  out += ",\"rule_character_full_id_raw\":";
  Number(out, p.rule_character_full_id_raw);
  out += ",\"diac_valid\":";
  Boolean(out, p.diac_valid);
  out += ",\"owner_matches\":";
  Boolean(out, p.owner_matches);
  out += ",\"rule\":";
  if (p.rule) Rule43AdmissionJson(out, *p.rule);
  else out += "null";
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void FollowingDiac2920d60Json(std::string &out, const game::FollowingDiac2920d60V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"current_character_full_id_raw\":";
  Number(out, p.current_character_full_id_raw);
  out += ",\"primary\":";
  DiacSelectionJson(out, p.primary);
  out += ",\"secondary\":";
  if (p.secondary) DiacSelectionJson(out, *p.secondary);
  else out += "null";
  out += ",\"selected_family\":";
  HelperString(out, p.selected_family);
  out += ",\"numeric_inputs\":";
  if (p.numeric_inputs) out += ck3_12003::SerializeDiacLiteralNumericInputs12003(*p.numeric_inputs);
  else out += "null";
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
