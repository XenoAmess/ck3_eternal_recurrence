// Included inside the existing context-source serializer detail namespace.

inline void Provider192FamilyJson(std::string &out, const game::ContextSourceProvider192V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"provider_loaded\":";
  Boolean(out, p.provider_loaded);
  out += ",\"provider_identity\":";
  HelperString(out, p.provider_identity);
  out += ",\"character_192_i16\":";
  Number(out, p.character_192_i16);
  out += ",\"upper_i32\":";
  Number(out, p.upper_i32);
  out += ",\"lower_i32\":";
  Number(out, p.lower_i32);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"selected_identity\":";
  HelperString(out, p.selected_identity);
  out += ",\"magic_u32\":";
  Number(out, p.magic_u32);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"pc\":";
  AfterPcJson(out, p.pc);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Provider2920850DirectJson(std::string &out, const game::ContextSourceProvider2920850DirectV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"pc\":";
  AfterPcJson(out, p.pc);
  out += '}';
}

inline void Provider2920850NestedJson(std::string &out, const game::ContextSourceProvider2920850NestedV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"mapped_family\":";
  RemainingFamilyV1Json(out, p.mapped_family);
  out += '}';
}

inline void Provider2920850OccurrenceJson(std::string &out, const game::ContextSourceProvider2920850OccurrenceV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"requested_full_id_raw\":";
  Number(out, p.requested_full_id_raw);
  out += ",\"resolution_selection\":";
  HelperString(out, p.resolution_selection);
  out += ",\"selected_full_id_raw\":";
  Number(out, p.selected_full_id_raw);
  out += ",\"object_identity\":";
  HelperString(out, p.object_identity);
  out += ",\"table_identity\":";
  HelperString(out, p.table_identity);
  out += ",\"direct_rows\":";
  if (!p.direct_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.direct_rows->size(); ++i) {
      if (i) out += ',';
      Provider2920850DirectJson(out, p.direct_rows->at(i));
    }
    out += ']';
  }
  out += ",\"nested_rows\":";
  if (!p.nested_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.nested_rows->size(); ++i) {
      if (i) out += ',';
      Provider2920850NestedJson(out, p.nested_rows->at(i));
    }
    out += ']';
  }
  out += ",\"direct_ready\":";
  out += p.direct_ready ? "true" : "false";
  out += ",\"mapped_ready\":";
  out += p.mapped_ready ? "true" : "false";
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Provider2920850ListJson(std::string &out, const game::ContextSourceProvider2920850ListV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"direct_ready\":";
  out += p.direct_ready ? "true" : "false";
  out += ",\"mapped_ready\":";
  out += p.mapped_ready ? "true" : "false";
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
      Provider2920850OccurrenceJson(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Provider192And2920850Json(std::string &out, const game::ContextSourceProvider192And2920850InputsV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"current_land_present\":";
  Boolean(out, p.current_land_present);
  out += ",\"current_death_present\":";
  Boolean(out, p.current_death_present);
  out += ",\"rite\":";
  RemainingRiteV1Json(out, p.rite);
  out += ",\"mapped_default_guard_raw\":";
  Number(out, p.mapped_default_guard_raw);
  out += ",\"provider_192\":";
  Provider192FamilyJson(out, p.provider_192);
  out += ",\"list_168\":";
  Provider2920850ListJson(out, p.list_168);
  out += ",\"list_180\":";
  Provider2920850ListJson(out, p.list_180);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
