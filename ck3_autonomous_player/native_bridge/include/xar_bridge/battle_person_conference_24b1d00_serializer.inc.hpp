template <typename T> inline void ConferenceJsonStart(std::string &out, const T &p) {
  out += "{\"status\":"; String(out, p.status);
  out += ",\"ready\":"; out += p.ready ? "true" : "false";
}
template <typename T> inline void ConferenceJsonEnd(std::string &out, const T &p) {
  out += ",\"reason\":"; Reason(out, p.reason); out += '}';
}
inline void ConferenceObjectV1Json(std::string &out, const game::ContextSourceConferenceObjectV1 &p) {
  out += "{\"requested_full_id_raw\":"; Number(out, p.requested_full_id_raw);
  out += ",\"selection\":"; HelperString(out, p.selection);
  out += ",\"identity\":"; HelperString(out, p.identity);
  out += ",\"full_id_raw\":"; Number(out, p.full_id_raw);
  ConferenceJsonEnd(out, p);
}
inline void ConferencePackV1Json(std::string &out, const game::ContextSourceConferencePackV1 &p) {
  ConferenceJsonStart(out, p);
  out += ",\"configuration_identity\":"; HelperString(out, p.configuration_identity);
  out += ",\"target_q64\":"; Number(out, p.target_q64);
  out += ",\"enabled_u8\":"; Number(out, p.enabled_u8);
  out += ",\"count_raw\":"; Number(out, p.count_raw);
  out += ",\"array_present\":"; Boolean(out, p.array_present);
  out += ",\"probes\":";
  if (!p.probes) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.probes->size(); ++i) {
      if (i) out += ',';
      const auto &probe = p.probes->at(i);
      out += "{\"native_index\":"; out += std::to_string(probe.native_index);
      out += ",\"timestamp_q64\":"; out += std::to_string(probe.timestamp_q64); out += '}';
    }
    out += ']';
  }
  out += ",\"selection\":"; HelperString(out, p.selection);
  out += ",\"selected_native_index\":"; Number(out, p.selected_native_index);
  out += ",\"pack_identity\":"; HelperString(out, p.pack_identity);
  out += ",\"default_guard_raw\":"; Number(out, p.default_guard_raw);
  ConferenceJsonEnd(out, p);
}
inline void ConferenceFamilyV1Json(std::string &out, const game::ContextSourceConferenceFamilyV1 &p) {
  ConferenceJsonStart(out, p);
  out += ",\"native_index\":"; out += std::to_string(p.native_index);
  out += ",\"admitted\":"; Boolean(out, p.admitted);
  out += ",\"pc_offset\":"; Number(out, p.pc_offset);
  out += ",\"property_identity\":"; HelperString(out, p.property_identity);
  out += ",\"property_block\":"; Properties(out, p.property_block);
  ConferenceJsonEnd(out, p);
}
inline void Conference24b1d00V1Json(std::string &out, const game::ContextSourceConference24b1d00V1 &p) {
  ConferenceJsonStart(out, p);
  out += ",\"character_id\":"; out += std::to_string(p.character_id);
  out += ",\"carrier_present\":"; Boolean(out, p.carrier_present);
  out += ",\"conference\":"; ConferenceObjectV1Json(out, p.conference);
  out += ",\"conference_magic_raw\":"; Number(out, p.conference_magic_raw);
  out += ",\"conference_admitted\":"; Boolean(out, p.conference_admitted);
  out += ",\"character_magic_raw\":"; Number(out, p.character_magic_raw);
  out += ",\"character_full_id_raw\":"; Number(out, p.character_full_id_raw);
  out += ",\"character_admitted\":"; Boolean(out, p.character_admitted);
  out += ",\"admitted\":"; Boolean(out, p.admitted);
  out += ",\"pack\":"; ConferencePackV1Json(out, p.pack);
  out += ",\"relation_registry_present\":"; Boolean(out, p.relation_registry_present);
  out += ",\"first\":"; ConferenceObjectV1Json(out, p.first);
  out += ",\"second\":"; ConferenceObjectV1Json(out, p.second);
  out += ",\"owner_full_id_raw\":"; Number(out, p.owner_full_id_raw);
  out += ",\"owner_matches\":"; Boolean(out, p.owner_matches);
  out += ",\"first_group_identity\":"; HelperString(out, p.first_group_identity);
  out += ",\"second_group_identity\":"; HelperString(out, p.second_group_identity);
  out += ",\"category\":"; HelperString(out, p.category);
  out += ",\"families\":[";
  for (std::size_t i = 0; i < p.families.size(); ++i) {
    if (i) out += ',';
    ConferenceFamilyV1Json(out, p.families[i]);
  }
  out += ']'; ConferenceJsonEnd(out, p);
}
