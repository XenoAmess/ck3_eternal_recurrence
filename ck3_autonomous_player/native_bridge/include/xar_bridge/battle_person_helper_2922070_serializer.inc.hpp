// Included inside the existing source serializer detail namespace.
inline void Helper2922070EdgeV1Json(std::string &out, const game::ContextSource2922070EdgeV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"requested_id_raw\":";
  Number(out, p.requested_id_raw);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"object_identity\":";
  HelperString(out, p.object_identity);
  out += ",\"holder_identity\":";
  HelperString(out, p.holder_identity);
  out += ",\"holder_id_18_raw\":";
  Number(out, p.holder_id_18_raw);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void Helper2922070WalkV1Json(std::string &out, const game::ContextSource2922070WalkV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"character_identity\":";
  String(out, p.character_identity);
  out += ",\"header_selection\":";
  HelperString(out, p.header_selection);
  out += ",\"count_c_raw\":";
  Number(out, p.count_c_raw);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"edges\":";
  {
    out += '[';
    for (std::size_t i = 0; i < p.edges.size(); ++i) {
      if (i) out += ',';
      Helper2922070EdgeV1Json(out, p.edges.at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void Helper2922070CharacterV1Json(std::string &out, const game::ContextSource2922070CharacterV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"include_self\":";
  out += p.include_self ? "true" : "false";
  out += ",\"input_id_raw\":";
  Number(out, p.input_id_raw);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"character_identity\":";
  HelperString(out, p.character_identity);
  out += ",\"character_id_18_raw\":";
  Number(out, p.character_id_18_raw);
  out += ",\"first_key_158_raw\":";
  Number(out, p.first_key_158_raw);
  out += ",\"first_selection\":";
  HelperString(out, p.first_selection);
  out += ",\"first_identity\":";
  HelperString(out, p.first_identity);
  out += ",\"owner_id_160_raw\":";
  Number(out, p.owner_id_160_raw);
  out += ",\"owner_selection\":";
  HelperString(out, p.owner_selection);
  out += ",\"owner_identity\":";
  HelperString(out, p.owner_identity);
  out += ",\"government_selection\":";
  HelperString(out, p.government_selection);
  out += ",\"government_identity\":";
  HelperString(out, p.government_identity);
  out += ",\"government_mask_40_raw\":";
  Number(out, p.government_mask_40_raw);
  out += ",\"top_character_identity\":";
  HelperString(out, p.top_character_identity);
  out += ",\"top_government_selection\":";
  HelperString(out, p.top_government_selection);
  out += ",\"top_government_identity\":";
  HelperString(out, p.top_government_identity);
  out += ",\"top_government_mask_40_raw\":";
  Number(out, p.top_government_mask_40_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void Helper2922070KeyV1Json(std::string &out, const game::ContextSource2922070KeyV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"requested_id_raw\":";
  Number(out, p.requested_id_raw);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"object_identity\":";
  HelperString(out, p.object_identity);
  out += ",\"gate_32_raw\":";
  Number(out, p.gate_32_raw);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void Helper2922070MembershipV1Json(std::string &out, const game::ContextSource2922070MembershipV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"character_index\":";
  out += std::to_string(p.character_index);
  out += ",\"first_key_158_raw\":";
  Number(out, p.first_key_158_raw);
  out += ",\"first_selection\":";
  HelperString(out, p.first_selection);
  out += ",\"first_identity\":";
  HelperString(out, p.first_identity);
  out += ",\"header_selection\":";
  HelperString(out, p.header_selection);
  out += ",\"count_c_raw\":";
  Number(out, p.count_c_raw);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"scans\":";
  {
    out += '[';
    for (std::size_t i = 0; i < p.scans.size(); ++i) {
      if (i) out += ',';
      Helper2922070KeyV1Json(out, p.scans.at(i));
    }
    out += ']';
  }
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"first_id_10_raw\":";
  Number(out, p.first_id_10_raw);
  out += ",\"appended\":";
  Boolean(out, p.appended);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void Helper2922070RowV1Json(std::string &out, const game::ContextSource2922070RowV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"input_index\":";
  out += std::to_string(p.input_index);
  out += ",\"requested_id_raw\":";
  out += std::to_string(p.requested_id_raw);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"source_identity\":";
  HelperString(out, p.source_identity);
  out += ",\"selected_id_10_raw\":";
  Number(out, p.selected_id_10_raw);
  out += ",\"type_280_raw\":";
  Number(out, p.type_280_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"definition_magic_38_raw\":";
  Number(out, p.definition_magic_38_raw);
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
inline void Helper2922070V1Json(std::string &out, const game::ContextSourceHelper2922070V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"gate_ready\":";
  out += p.gate_ready ? "true" : "false";
  out += ",\"collection_ready\":";
  out += p.collection_ready ? "true" : "false";
  out += ",\"rows_ready\":";
  out += p.rows_ready ? "true" : "false";
  out += ",\"government_selection\":";
  HelperString(out, p.government_selection);
  out += ",\"government_identity\":";
  HelperString(out, p.government_identity);
  out += ",\"government_mode_4d6_raw\":";
  Number(out, p.government_mode_4d6_raw);
  out += ",\"character_land_present\":";
  Boolean(out, p.character_land_present);
  out += ",\"subject_identity\":";
  HelperString(out, p.subject_identity);
  out += ",\"subject_magic_c_raw\":";
  Number(out, p.subject_magic_c_raw);
  out += ",\"subject_id_8_raw\":";
  Number(out, p.subject_id_8_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"walk_nodes\":";
  if (!p.walk_nodes) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.walk_nodes->size(); ++i) {
      if (i) out += ',';
      Helper2922070WalkV1Json(out, p.walk_nodes->at(i));
    }
    out += ']';
  }
  out += ",\"characters\":";
  if (!p.characters) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.characters->size(); ++i) {
      if (i) out += ',';
      Helper2922070CharacterV1Json(out, p.characters->at(i));
    }
    out += ']';
  }
  out += ",\"character_order\":";
  if (!p.character_order) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.character_order->size(); ++i) {
      if (i) out += ',';
      out += std::to_string(p.character_order->at(i));
    }
    out += ']';
  }
  out += ",\"membership_rows\":";
  if (!p.membership_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.membership_rows->size(); ++i) {
      if (i) out += ',';
      Helper2922070MembershipV1Json(out, p.membership_rows->at(i));
    }
    out += ']';
  }
  out += ",\"output_ids\":";
  if (!p.output_ids) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.output_ids->size(); ++i) {
      if (i) out += ',';
      out += std::to_string(p.output_ids->at(i));
    }
    out += ']';
  }
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      Helper2922070RowV1Json(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
