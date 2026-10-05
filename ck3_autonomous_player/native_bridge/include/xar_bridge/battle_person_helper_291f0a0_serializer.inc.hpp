// Included inside the source serializer detail namespace.
inline void HelperString(std::string &out, const std::optional<std::string> &p) {
  if (p) String(out, *p);
  else out += "null";
}
inline void HelperFamily(std::string &out, const game::ContextSourceHelperFamilyV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"selected_source\":";
  String(out, p.selected_source);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"count\":";
  Number(out, p.count);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      const auto &r = (*p.rows)[i];
      out += "{\"native_index\":" + std::to_string(r.native_index);
      out += ",\"source_identity\":";
      HelperString(out, r.source_identity);
      out += ",\"gate_raw\":";
      Number(out, r.gate_raw);
      out += ",\"admitted\":";
      Boolean(out, r.admitted);
      out += ",\"property_block\":";
      Properties(out, r.property_block);
      out += ",\"reason\":";
      Reason(out, r.reason);
      out += '}';
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void Helper291f0a0(std::string &out, const game::ContextSourceHelper291f0a0V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  out += ",\"first_selection\":";
  HelperString(out, p.first_selection);
  out += ",\"first_key_b4_raw\":";
  Number(out, p.first_key_b4_raw);
  out += ",\"manager_present\":";
  Boolean(out, p.manager_present);
  out += ",\"manager_definition_selection\":";
  HelperString(out, p.manager_definition_selection);
  out += ",\"manager_definition_identity\":";
  HelperString(out, p.manager_definition_identity);
  out += ",\"recipient_source\":";
  HelperString(out, p.recipient_source);
  out += ",\"recipient_q64\":";
  Number(out, p.recipient_q64);
  out += ",\"range_count_raw\":";
  Number(out, p.range_count_raw);
  out += ",\"range_selection\":";
  HelperString(out, p.range_selection);
  out += ",\"range_native_index\":";
  Number(out, p.range_native_index);
  out += ",\"range_lower_q64\":";
  Number(out, p.range_lower_q64);
  out += ",\"range_upper_q64\":";
  Number(out, p.range_upper_q64);
  out += ",\"default_pc_guard_raw\":";
  Number(out, p.default_pc_guard_raw);
  out += ",\"pointer_list_guard_raw\":";
  Number(out, p.pointer_list_guard_raw);
  out += ",\"predicate_character_15c_raw\":";
  Number(out, p.predicate_character_15c_raw);
  out += ",\"predicate_first_key_b4_raw\":";
  Number(out, p.predicate_first_key_b4_raw);
  out += ",\"predicate_second_key_4b8_raw\":";
  Number(out, p.predicate_second_key_4b8_raw);
  out += ",\"predicate_second_a0_raw\":";
  Number(out, p.predicate_second_a0_raw);
  out += ",\"predicate_admitted\":";
  Boolean(out, p.predicate_admitted);
  out += ",\"primary_direct\":";
  HelperFamily(out, p.primary_direct);
  out += ",\"manager_range\":";
  HelperFamily(out, p.manager_range);
  out += ",\"source_a18\":";
  HelperFamily(out, p.source_a18);
  out += ",\"conditional_direct\":";
  HelperFamily(out, p.conditional_direct);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

