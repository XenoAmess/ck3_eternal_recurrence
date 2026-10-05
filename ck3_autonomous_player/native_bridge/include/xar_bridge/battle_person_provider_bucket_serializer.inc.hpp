// Included inside the existing source serializer detail namespace.
inline void ProviderBucket291c5b2(
    std::string &out, const game::ContextSourceProviderBucket291c5b2V1 &p) {
  out += "{\"status\":"; String(out, p.status);
  out += ",\"ready\":"; out += p.ready ? "true" : "false";
  out += ",\"character_id\":"; out += std::to_string(p.character_id);
  out += ",\"provider_present\":"; Boolean(out, p.provider_present);
  out += ",\"provider_identity\":"; HelperString(out, p.provider_identity);
  out += ",\"carrier_present\":"; Boolean(out, p.carrier_present);
  out += ",\"key_2f8_raw\":"; Number(out, p.key_2f8_raw);
  out += ",\"denominator_5c68ce8_raw\":"; Number(out, p.denominator_5c68ce8_raw);
  out += ",\"bucket_index_raw\":"; Number(out, p.bucket_index_raw);
  out += ",\"provider_count_1204_raw\":"; Number(out, p.provider_count_1204_raw);
  out += ",\"provider_array_present\":"; Boolean(out, p.provider_array_present);
  out += ",\"selection\":"; HelperString(out, p.selection);
  out += ",\"selected_definition_identity\":"; HelperString(out, p.selected_definition_identity);
  out += ",\"selected_magic_raw\":"; Number(out, p.selected_magic_raw);
  out += ",\"admitted\":"; Boolean(out, p.admitted);
  out += ",\"property_identity\":"; HelperString(out, p.property_identity);
  out += ",\"property_block\":"; Properties(out, p.property_block);
  out += ",\"reason\":"; Reason(out, p.reason);
  out += '}';
}
