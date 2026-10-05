// Included inside the existing source serializer detail namespace.
inline void RemainingRowV1Json(std::string &out, const game::ContextSourceRemainingRowV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"source_identity\":";
  HelperString(out, p.source_identity);
  out += ",\"key_identity\":";
  HelperString(out, p.key_identity);
  out += ",\"key_magic_raw\":";
  Number(out, p.key_magic_raw);
  out += ",\"key_full_id_raw\":";
  Number(out, p.key_full_id_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"property_selection\":";
  HelperString(out, p.property_selection);
  out += ",\"mapping_native_index\":";
  Number(out, p.mapping_native_index);
  out += ",\"property_identity\":";
  HelperString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void RemainingFamilyV1Json(std::string &out, const game::ContextSourceRemainingFamilyV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
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
      RemainingRowV1Json(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void RemainingRiteV1Json(std::string &out, const game::ContextSourceRemainingRiteV1 &p) {
  out += "{\"first_key_b4_raw\":";
  Number(out, p.first_key_b4_raw);
  out += ",\"first_selection\":";
  HelperString(out, p.first_selection);
  out += ",\"second_key_4b8_raw\":";
  Number(out, p.second_key_4b8_raw);
  out += ",\"second_selection\":";
  HelperString(out, p.second_selection);
  out += ",\"third_key_98_raw\":";
  Number(out, p.third_key_98_raw);
  out += ",\"third_selection\":";
  HelperString(out, p.third_selection);
  out += ",\"selected_identity\":";
  HelperString(out, p.selected_identity);
  out += ",\"membership_count\":";
  Number(out, p.membership_count);
  out += ",\"membership_array_present\":";
  Boolean(out, p.membership_array_present);
  out += ",\"membership_identities\":";
  if (!p.membership_identities) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.membership_identities->size(); ++i) {
      if (i) out += ',';
      String(out, p.membership_identities->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void Remaining550V1Json(std::string &out, const game::ContextSourceRemaining550V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"culture_key_b0_raw\":";
  Number(out, p.culture_key_b0_raw);
  out += ",\"culture_selection\":";
  HelperString(out, p.culture_selection);
  out += ",\"culture_identity\":";
  HelperString(out, p.culture_identity);
  out += ",\"culture_magic_raw\":";
  Number(out, p.culture_magic_raw);
  out += ",\"culture_full_id_raw\":";
  Number(out, p.culture_full_id_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"government_selection\":";
  HelperString(out, p.government_selection);
  out += ",\"government_identity\":";
  HelperString(out, p.government_identity);
  out += ",\"government_magic_raw\":";
  Number(out, p.government_magic_raw);
  out += ",\"government_full_id_raw\":";
  Number(out, p.government_full_id_raw);
  out += ",\"government_default_guard_raw\":";
  Number(out, p.government_default_guard_raw);
  out += ",\"mapped_default_guard_raw\":";
  Number(out, p.mapped_default_guard_raw);
  out += ",\"rite\":";
  RemainingRiteV1Json(out, p.rite);
  out += ",\"government_indexed\":";
  RemainingFamilyV1Json(out, p.government_indexed);
  out += ",\"culture_direct\":";
  RemainingFamilyV1Json(out, p.culture_direct);
  out += ",\"culture_mapped\":";
  RemainingFamilyV1Json(out, p.culture_mapped);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void RemainingOuterV1Json(std::string &out, const game::ContextSourceRemainingOuterV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"source_identity\":";
  HelperString(out, p.source_identity);
  out += ",\"direct_gate_raw\":";
  Number(out, p.direct_gate_raw);
  out += ",\"direct_admitted\":";
  Boolean(out, p.direct_admitted);
  out += ",\"direct_property_identity\":";
  HelperString(out, p.direct_property_identity);
  out += ",\"direct_property_block\":";
  Properties(out, p.direct_property_block);
  out += ",\"direct_reason\":";
  Reason(out, p.direct_reason);
  out += ",\"inner_mapped\":";
  RemainingFamilyV1Json(out, p.inner_mapped);
  out += '}';
}
inline void Remaining940V1Json(std::string &out, const game::ContextSourceRemaining940V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"direct_ready\":";
  out += p.direct_ready ? "true" : "false";
  out += ",\"mapped_ready\":";
  out += p.mapped_ready ? "true" : "false";
  out += ",\"first_key_158_raw\":";
  Number(out, p.first_key_158_raw);
  out += ",\"first_selection\":";
  HelperString(out, p.first_selection);
  out += ",\"second_key_2c_raw\":";
  Number(out, p.second_key_2c_raw);
  out += ",\"second_selection\":";
  HelperString(out, p.second_selection);
  out += ",\"selected_identity\":";
  HelperString(out, p.selected_identity);
  out += ",\"outer_count\":";
  Number(out, p.outer_count);
  out += ",\"outer_array_present\":";
  Boolean(out, p.outer_array_present);
  out += ",\"outer_rows\":";
  if (!p.outer_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.outer_rows->size(); ++i) {
      if (i) out += ',';
      RemainingOuterV1Json(out, p.outer_rows->at(i));
    }
    out += ']';
  }
  out += ",\"mapped_default_guard_raw\":";
  Number(out, p.mapped_default_guard_raw);
  out += ",\"rite\":";
  RemainingRiteV1Json(out, p.rite);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
inline void RemainingHelpersV1Json(std::string &out, const game::ContextSourceRemainingHelpersV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"helper_291f550\":";
  Remaining550V1Json(out, p.helper_291f550);
  out += ",\"helper_291f940\":";
  Remaining940V1Json(out, p.helper_291f940);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
