// Included inside battle_context_source_inputs_v1_detail.
template <typename Entry, typename Append>
inline void AbsentMapV1Json(std::string &out,
    const game::ContextSourceAbsentMapV1<Entry> &p, Append append) {
  out += "{\"count\":";
  Number(out, p.count);
  out += ",\"mask\":";
  Number(out, p.mask);
  out += ",\"max_probe_u8\":";
  Number(out, p.max_probe_u8);
  out += ",\"entries\":";
  Rows(out, p.entries, append);
  out += '}';
}
inline void Absent430EntryV1Json(std::string &out,
    const game::ContextSourceAbsentMap430EntryV1 &p) {
  out += "{\"bucket_index\":" + std::to_string(p.bucket_index);
  out += ",\"hash_u32\":";
  Number(out, p.hash_u32);
  out += ",\"probe_u8\":";
  Number(out, p.probe_u8);
  out += ",\"key_object\":";
  Number(out, p.key_object);
  out += ",\"trait_id_u32\":";
  Number(out, p.trait_id_u32);
  out += ",\"value_q64\":";
  Number(out, p.value_q64);
  out += '}';
}
inline void Absent458EntryV1Json(std::string &out,
    const game::ContextSourceAbsentMap458EntryV1 &p) {
  out += "{\"bucket_index\":" + std::to_string(p.bucket_index);
  out += ",\"hash_u32\":";
  Number(out, p.hash_u32);
  out += ",\"probe_u8\":";
  Number(out, p.probe_u8);
  out += ",\"key_object\":";
  Number(out, p.key_object);
  out += ",\"value_u64\":";
  Number(out, p.value_u64);
  out += '}';
}
inline void AbsentRecipientV1Json(std::string &out,
    const game::ContextSourceAbsentRecipientInputsV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  out += ",\"carrier_present\":";
  Boolean(out, p.carrier_present);
  out += ",\"associated_full_id\":";
  Number(out, p.associated_full_id);
  out += ",\"associated_resolved_full_id\":";
  Number(out, p.associated_resolved_full_id);
  out += ",\"associated_used_fallback\":";
  Boolean(out, p.associated_used_fallback);
  out += ",\"associated_cache_440\":";
  Number(out, p.associated_cache_440);
  out += ",\"cached_map_430\":";
  AbsentMapV1Json(out, p.cached_map_430, Absent430EntryV1Json);
  out += ",\"cached_map_458\":";
  AbsentMapV1Json(out, p.cached_map_458, Absent458EntryV1Json);
  out += ",\"trait_ids\":{\"count\":";
  Number(out, p.trait_ids.count);
  out += ",\"values_u32\":";
  Numbers(out, p.trait_ids.values_u32);
  out += "},\"membership_ids\":{\"count\":";
  Number(out, p.membership_ids.count);
  out += ",\"values_u64\":";
  Numbers(out, p.membership_ids.values_u64);
  out += "},\"membership_header_guard_raw\":";
  Number(out, p.membership_header_guard_raw);
  out += ",\"aggregate_properties\":{\"count\":";
  Number(out, p.aggregate_properties.count);
  out += ",\"keys_u16\":";
  Numbers(out, p.aggregate_properties.keys_u16);
  out += ",\"values_q64\":";
  Numbers(out, p.aggregate_properties.values_q64);
  out += "},\"aggregate_context_selection\":";
  Identity(out, p.aggregate_context_selection);
  out += ",\"aggregate_context_guard_raw\":";
  Number(out, p.aggregate_context_guard_raw);
  out += ",\"member_multiplier_q64\":";
  Number(out, p.member_multiplier_q64);
  out += ",\"clamp_lower_q64\":";
  Number(out, p.clamp_lower_q64);
  out += ",\"clamp_upper_q64\":";
  Number(out, p.clamp_upper_q64);
  out += ",\"calculated_recipient_q64\":";
  Number(out, p.calculated_recipient_q64);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
