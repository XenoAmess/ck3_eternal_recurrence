// Included inside bridge::battle_context_source_inputs_v1_detail after the
// cached absent serializer. No derived map is serialized as a cached source.
template <typename T>
inline void UncachedNumberField(std::string &out, const char *name,
                               const std::optional<T> &value) {
  out += ",\"";
  out += name;
  out += "\":";
  Number(out, value);
}
inline void UncachedBoolField(std::string &out, const char *name,
                             const std::optional<bool> &value) {
  out += ",\"";
  out += name;
  out += "\":";
  Boolean(out, value);
}
inline void UncachedIntrinsicRecordV1Json(std::string &out,
    const game::ContextSourceUncachedIntrinsicRecordV1 &p) {
  out += "{\"native_index\":" + std::to_string(p.native_index);
  UncachedNumberField(out, "marker_u8", p.marker_u8);
  UncachedNumberField(out, "key_object", p.key_object);
  UncachedNumberField(out, "key_id_i32", p.key_id_i32);
  UncachedNumberField(out, "value_q64", p.value_q64);
  out += '}';
}
inline void UncachedIntrinsicVectorV1Json(std::string &out,
    const game::ContextSourceUncachedIntrinsicVectorV1 &p) {
  out += "{\"count\":";
  Number(out, p.count);
  out += ",\"records\":";
  Rows(out, p.records, UncachedIntrinsicRecordV1Json);
  out += '}';
}
inline void UncachedIntrinsicFamilyV1Json(std::string &out,
    const game::ContextSourceUncachedIntrinsicFamilyV1 &p) {
  out += "{\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"first\":";
  UncachedIntrinsicVectorV1Json(out, p.first);
  out += ",\"second\":";
  UncachedIntrinsicVectorV1Json(out, p.second);
  out += '}';
}
inline void UncachedObjectV1Json(std::string &out,
    const game::ContextSourceUncachedObjectV1 &p) {
  out += "{\"native_index\":" + std::to_string(p.native_index);
  UncachedNumberField(out, "object", p.object);
  UncachedNumberField(out, "magic_u32", p.magic_u32);
  out += ",\"intrinsic_family\":";
  UncachedIntrinsicFamilyV1Json(out, p.intrinsic_family);
  out += '}';
}
inline void UncachedObjectVectorV1Json(std::string &out,
    const game::ContextSourceUncachedObjectVectorV1 &p) {
  out += "{\"count\":";
  Number(out, p.count);
  out += ",\"entries\":";
  Rows(out, p.entries, UncachedObjectV1Json);
  out += '}';
}
inline void UncachedContextRecordV1Json(std::string &out,
    const game::ContextSourceUncachedContextRecordV1 &p) {
  out += "{\"native_index\":" + std::to_string(p.native_index);
  UncachedNumberField(out, "object", p.object);
  UncachedNumberField(out, "flag_u8", p.flag_u8);
  out += '}';
}
inline void UncachedContextVectorV1Json(std::string &out,
    const game::ContextSourceUncachedContextVectorV1 &p) {
  out += "{\"count\":";
  Number(out, p.count);
  out += ",\"entries\":";
  Rows(out, p.entries, UncachedContextRecordV1Json);
  out += '}';
}
inline void UncachedSeedReceiverV1Json(std::string &out,
    const game::ContextSourceUncachedSeedReceiverV1 &p) {
  out += "{\"first_full_id\":";
  Number(out, p.first_full_id);
  UncachedNumberField(out, "first_resolved_full_id", p.first_resolved_full_id);
  UncachedBoolField(out, "first_used_fallback", p.first_used_fallback);
  UncachedNumberField(out, "second_full_id", p.second_full_id);
  UncachedNumberField(out, "second_resolved_full_id", p.second_resolved_full_id);
  UncachedBoolField(out, "second_used_fallback", p.second_used_fallback);
  UncachedNumberField(out, "definition_object", p.definition_object);
  out += '}';
}
inline void UncachedDownstreamV1Json(std::string &out,
    const game::ContextSourceAbsentRecipientInputsV1 &p) {
  out += "{\"trait_ids\":{\"count\":";
  Number(out, p.trait_ids.count);
  out += ",\"values_u32\":";
  Numbers(out, p.trait_ids.values_u32);
  out += "},\"membership_ids\":{\"count\":";
  Number(out, p.membership_ids.count);
  out += ",\"values_u64\":";
  Numbers(out, p.membership_ids.values_u64);
  out += '}';
  UncachedNumberField(out, "membership_header_guard_raw", p.membership_header_guard_raw);
  out += ",\"aggregate_properties\":{\"count\":";
  Number(out, p.aggregate_properties.count);
  out += ",\"keys_u16\":";
  Numbers(out, p.aggregate_properties.keys_u16);
  out += ",\"values_q64\":";
  Numbers(out, p.aggregate_properties.values_q64);
  out += "},\"aggregate_context_selection\":";
  Identity(out, p.aggregate_context_selection);
  UncachedNumberField(out, "aggregate_context_guard_raw", p.aggregate_context_guard_raw);
  UncachedNumberField(out, "member_multiplier_q64", p.member_multiplier_q64);
  UncachedNumberField(out, "clamp_lower_q64", p.clamp_lower_q64);
  UncachedNumberField(out, "clamp_upper_q64", p.clamp_upper_q64);
  out += '}';
}
inline void UncachedRecipientV1Json(std::string &out,
    const game::ContextSourceUncachedRecipientInputsV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  UncachedBoolField(out, "carrier_present", p.carrier_present);
  UncachedNumberField(out, "associated_full_id", p.associated_full_id);
  UncachedNumberField(out, "associated_resolved_full_id", p.associated_resolved_full_id);
  UncachedBoolField(out, "associated_used_fallback", p.associated_used_fallback);
  UncachedNumberField(out, "associated_cache_440", p.associated_cache_440);
  out += ",\"seed_receiver\":";
  UncachedSeedReceiverV1Json(out, p.seed_receiver);
  out += ",\"seed_family\":";
  UncachedIntrinsicFamilyV1Json(out, p.seed_family);
  UncachedNumberField(out, "fallback_key_object", p.fallback_key_object);
  UncachedNumberField(out, "fallback_key_id_i32", p.fallback_key_id_i32);
  out += ",\"active_objects\":";
  UncachedObjectVectorV1Json(out, p.active_objects);
  out += ",\"active_context\":";
  UncachedContextVectorV1Json(out, p.active_context);
  out += ",\"removed_objects\":";
  UncachedObjectVectorV1Json(out, p.removed_objects);
  UncachedNumberField(out, "cap_i32", p.cap_i32);
  UncachedNumberField(out, "active_flag4_multiplier_q64", p.active_flag4_multiplier_q64);
  UncachedNumberField(out, "active_other_multiplier_q64", p.active_other_multiplier_q64);
  UncachedNumberField(out, "seed_boost_multiplier_q64", p.seed_boost_multiplier_q64);
  UncachedNumberField(out, "positive_fallback_object", p.positive_fallback_object);
  UncachedNumberField(out, "negative_fallback_object", p.negative_fallback_object);
  UncachedNumberField(out, "positive_fallback_magic_u32", p.positive_fallback_magic_u32);
  UncachedNumberField(out, "negative_fallback_magic_u32", p.negative_fallback_magic_u32);
  out += ",\"downstream_inputs\":";
  UncachedDownstreamV1Json(out, p.downstream_inputs);
  UncachedNumberField(out, "calculated_recipient_q64", p.calculated_recipient_q64);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
