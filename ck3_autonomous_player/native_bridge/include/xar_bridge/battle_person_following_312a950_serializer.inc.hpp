// Included inside the existing context-source serializer detail namespace.

inline void Following312a950GovernmentJson(std::string &out, const game::ContextSourceFollowing312a950GovernmentV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"selected_character_identity\":";
  HelperString(out, p.selected_character_identity);
  out += ",\"selection_native_index\":";
  Number(out, p.selection_native_index);
  out += ",\"government_identity\":";
  HelperString(out, p.government_identity);
  out += ",\"flags_raw_u32\":";
  Number(out, p.flags_raw_u32);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following312a950FirstLandJson(std::string &out, const game::ContextSourceFollowing312a950FirstLandV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"living_present\":";
  Boolean(out, p.living_present);
  out += ",\"death_present\":";
  Boolean(out, p.death_present);
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"full_id_raw\":";
  Number(out, p.full_id_raw);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following312a950LandJson(std::string &out, const game::ContextSourceFollowing312a950LandResolutionV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"requested_full_id_raw\":";
  Number(out, p.requested_full_id_raw);
  out += ",\"selected_full_id_raw\":";
  Number(out, p.selected_full_id_raw);
  out += ",\"object_identity\":";
  HelperString(out, p.object_identity);
  out += ",\"magic_u32\":";
  Number(out, p.magic_u32);
  out += ",\"full_id_raw\":";
  Number(out, p.full_id_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"balance_raw_q64\":";
  Number(out, p.balance_raw_q64);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following312a950Mode3Json(std::string &out, const game::ContextSourceFollowing312a950Mode3V1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"income_q64\":";
  Number(out, p.income_q64);
  out += ",\"index_raw_i32\":";
  Number(out, p.index_raw_i32);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following312a950ProviderJson(std::string &out, const game::ContextSourceFollowing312a950ProviderV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"provider_loaded\":";
  Boolean(out, p.provider_loaded);
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"definition_magic_u32\":";
  Number(out, p.definition_magic_u32);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"pc\":";
  AfterPcJson(out, p.pc);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following312a950Json(std::string &out, const game::ContextSourceFollowing312a950InputsV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"government_source\":";
  Following312a950GovernmentJson(out, p.government_source);
  out += ",\"character_state_present\":";
  Boolean(out, p.character_state_present);
  out += ",\"first_land_source\":";
  if (p.first_land_source) Following312a950FirstLandJson(out, *p.first_land_source); else out += "null";
  out += ",\"land_resolution\":";
  if (p.land_resolution) Following312a950LandJson(out, *p.land_resolution); else out += "null";
  out += ",\"mode3_classifier\":";
  if (p.mode3_classifier) Following312a950Mode3Json(out, *p.mode3_classifier); else out += "null";
  out += ",\"provider_selection\":";
  if (p.provider_selection) Following312a950ProviderJson(out, *p.provider_selection); else out += "null";
  out += ",\"stage_selection\":";
  HelperString(out, p.stage_selection);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
