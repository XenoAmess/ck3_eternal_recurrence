// Included inside the existing context-source serializer detail namespace.

inline void Following2920b50AttributeJson(std::string &out, const game::ContextSourceFollowing2920b50AttributeV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"definition_present\":";
  Boolean(out, p.definition_present);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"definition_magic_u32\":";
  Number(out, p.definition_magic_u32);
  out += ",\"preflight_valid\":";
  Boolean(out, p.preflight_valid);
  out += ",\"rank_raw_i32\":";
  Number(out, p.rank_raw_i32);
  out += ",\"index_raw_i32\":";
  Number(out, p.index_raw_i32);
  out += ",\"ranked_header_identity\":";
  HelperString(out, p.ranked_header_identity);
  out += ",\"ranked_count_raw\":";
  Number(out, p.ranked_count_raw);
  out += ",\"ranked_array_present\":";
  Boolean(out, p.ranked_array_present);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"selected_row_identity\":";
  HelperString(out, p.selected_row_identity);
  out += ",\"ranked_default_init_guard_raw\":";
  Number(out, p.ranked_default_init_guard_raw);
  out += ",\"pc\":";
  AfterPcJson(out, p.pc);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2920b50OccurrenceJson(std::string &out, const game::ContextSourceFollowing2920b50OccurrenceV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"requested_full_id_raw\":";
  Number(out, p.requested_full_id_raw);
  out += ",\"resolution_selection\":";
  HelperString(out, p.resolution_selection);
  out += ",\"selected_full_id_raw\":";
  Number(out, p.selected_full_id_raw);
  out += ",\"object_identity\":";
  HelperString(out, p.object_identity);
  out += ",\"accolade_magic_u32\":";
  Number(out, p.accolade_magic_u32);
  out += ",\"accolade_full_id_raw\":";
  Number(out, p.accolade_full_id_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"attribute_count_raw\":";
  Number(out, p.attribute_count_raw);
  out += ",\"attribute_array_present\":";
  Boolean(out, p.attribute_array_present);
  out += ",\"preflight_ready\":";
  out += p.preflight_ready ? "true" : "false";
  out += ",\"preflight_all_valid\":";
  Boolean(out, p.preflight_all_valid);
  out += ",\"attributes\":";
  if (!p.attributes) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.attributes->size(); ++i) {
      if (i) out += ',';
      Following2920b50AttributeJson(out, p.attributes->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2920b50ListJson(std::string &out, const game::ContextSourceFollowing2920b50ListV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"component_present\":";
  Boolean(out, p.component_present);
  out += ",\"header_selection\":";
  HelperString(out, p.header_selection);
  out += ",\"default_init_guard_raw\":";
  Number(out, p.default_init_guard_raw);
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += ",\"numeric_count\":";
  Number(out, p.numeric_count);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      Following2920b50OccurrenceJson(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2920b50OwnJson(std::string &out, const game::ContextSourceFollowing2920b50OwnV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"component_present\":";
  Boolean(out, p.component_present);
  out += ",\"occurrence\":";
  Following2920b50OccurrenceJson(out, p.occurrence);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2920b50Json(std::string &out, const game::ContextSourceFollowing2920b50InputsV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"list_1c8_50\":";
  Following2920b50ListJson(out, p.list_1c8_50);
  out += ",\"own_1b0_570\":";
  Following2920b50OwnJson(out, p.own_1b0_570);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
