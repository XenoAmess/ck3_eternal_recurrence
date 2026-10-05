// Included inside the existing source serializer detail namespace.
inline void TailGovernmentV1Json(std::string &out, const game::ContextSourceTailGovernmentV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"land_present\":";
  Boolean(out, p.land_present);
  out += ",\"government_selection\":";
  HelperString(out, p.government_selection);
  out += ",\"government_identity\":";
  HelperString(out, p.government_identity);
  out += ",\"government_magic_raw\":";
  Number(out, p.government_magic_raw);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"property_870_identity\":";
  HelperString(out, p.property_870_identity);
  out += ",\"property_870\":";
  Properties(out, p.property_870);
  out += ",\"second_land_present\":";
  Boolean(out, p.second_land_present);
  out += ",\"subcarrier_magic_raw\":";
  Number(out, p.subcarrier_magic_raw);
  out += ",\"subcarrier_full_id_raw\":";
  Number(out, p.subcarrier_full_id_raw);
  out += ",\"additional_a30_admitted\":";
  Boolean(out, p.additional_a30_admitted);
  out += ",\"property_a30_identity\":";
  HelperString(out, p.property_a30_identity);
  out += ",\"property_a30\":";
  Properties(out, p.property_a30);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void TailWeightedRowV1Json(std::string &out, const game::ContextSourceTailWeightedRowV1 &p) {
  out += "{\"native_index\":";
  out += std::to_string(p.native_index);
  out += ",\"property_identity\":";
  HelperString(out, p.property_identity);
  out += ",\"property_block\":";
  Properties(out, p.property_block);
  out += ",\"weight_q64\":";
  Number(out, p.weight_q64);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void TailWeightedV1Json(std::string &out, const game::ContextSourceTailWeightedV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"carrier_present\":";
  Boolean(out, p.carrier_present);
  out += ",\"key_274_raw\":";
  Number(out, p.key_274_raw);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"selected_identity\":";
  HelperString(out, p.selected_identity);
  out += ",\"count_63c\":";
  Number(out, p.count_63c);
  out += ",\"array_present\":";
  Boolean(out, p.array_present);
  out += ",\"rows\":";
  if (!p.rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.rows->size(); ++i) {
      if (i) out += ',';
      TailWeightedRowV1Json(out, p.rows->at(i));
    }
    out += ']';
  }
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void TailDirectV1Json(std::string &out, const game::ContextSourceTailDirectV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"government_870_a30\":";
  TailGovernmentV1Json(out, p.government_870_a30);
  out += ",\"carrier_weighted630\":";
  TailWeightedV1Json(out, p.carrier_weighted630);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
