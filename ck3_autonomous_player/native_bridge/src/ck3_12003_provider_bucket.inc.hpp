// Included in the existing read-only source-query anonymous namespace.
// Actual integral signed32 operand domain of 28BC5A0; low EAX is consumed.
std::int32_t ProviderBucketIndex291c5b2(std::int32_t numerator,
                                      std::int32_t denominator) noexcept {
  if (denominator == 0) return 42949;
  const auto quotient = static_cast<std::int64_t>(numerator) /
                        static_cast<std::int64_t>(denominator);
  const auto low = static_cast<std::uint32_t>(quotient);
  std::int32_t result = 0;
  std::memcpy(&result, &low, sizeof(result));
  return result;
}

game::ContextSourceProviderBucket291c5b2V1 ReadProviderBucket291c5b2(
    const ContextSourceBindingsV1 &b, const void *character,
    std::int32_t character_id) {
  game::ContextSourceProviderBucket291c5b2V1 out{};
  out.character_id = character_id;
  const auto fail = [&](const char *reason) { out.reason = reason; return out; };
  const auto &binding = b.provider_bucket_291c5b2;
  const auto provider = Read<const void *>(b, binding.provider_slot);
  if (!provider) return fail("provider_bucket_provider_slot_unavailable");
  out.provider_present = *provider != nullptr;
  if (!*provider)
    return fail("provider_bucket_provider_initializer_required");
  std::vector<const void *> identities;
  out.provider_identity = Identity(identities, *provider, "provider");

  const auto carrier = Read<const void *>(b, character, 0x1B0);
  if (!carrier) return fail("provider_bucket_carrier_unavailable");
  out.carrier_present = *carrier != nullptr;
  if (!*carrier) {
    // 291C70C MOV EAX,R12D=0. This is bucket0, not a skipped family.
    out.bucket_index_raw = 0;
  } else {
    out.key_2f8_raw = Read<std::int32_t>(b, *carrier, 0x2F8);
    if (!out.key_2f8_raw) return fail("provider_bucket_key_2f8_unavailable");
    out.denominator_5c68ce8_raw =
        Read<std::int32_t>(b, binding.factor_denominator_slot);
    if (!out.denominator_5c68ce8_raw)
      return fail("provider_bucket_denominator_unavailable");
    out.bucket_index_raw = ProviderBucketIndex291c5b2(
        *out.key_2f8_raw, *out.denominator_5c68ce8_raw);
  }

  bool use_fallback = *out.bucket_index_raw < 0;
  const void *definition = nullptr;
  if (!use_fallback) {
    out.provider_count_1204_raw = Read<std::int32_t>(b, *provider, 0x1204);
    if (!out.provider_count_1204_raw)
      return fail("provider_bucket_count_unavailable");
    // 291C715 is a signed JGE BACK to C595, including native negative counts.
    use_fallback = *out.bucket_index_raw >= *out.provider_count_1204_raw;
    if (!use_fallback) {
      out.selection = "provider_bucket_11f8";
      const auto array = Read<const void *>(b, *provider, 0x11F8);
      if (!array) return fail("provider_bucket_array_unavailable");
      out.provider_array_present = *array != nullptr;
      if (!*array) return fail("provider_bucket_array_null");
      const auto selected = Read<const void *>(b, *array,
          static_cast<std::size_t>(*out.bucket_index_raw) * 8);
      if (!selected)
        return fail("provider_bucket_selected_definition_unavailable");
      if (!*selected)
        return fail("provider_bucket_selected_definition_null");
      definition = *selected;
      // 291C728 jumps BACK to C59C, then the same C5B2/C5B7 path.
    }
  }
  if (use_fallback) {
    out.selection = "native_fallback_5d1e0b0";
    const auto fallback = Read<const void *>(b, binding.native_fallback_slot);
    if (!fallback) return fail("provider_bucket_fallback_unavailable");
    if (!*fallback) return fail("provider_bucket_fallback_null");
    definition = *fallback;
  }
  out.selected_definition_identity = Identity(identities, definition, "provider");
  out.selected_magic_raw = Read<std::uint32_t>(b, definition, 0x38);
  if (!out.selected_magic_raw)
    return fail("provider_bucket_selected_magic_unavailable");
  out.admitted = *out.selected_magic_raw == 0x4744624FU;
  if (!*out.admitted) return PostReady(std::move(out));
  const void *pc = Offset(definition, 0x40);
  out.property_identity = Identity(identities, pc, "provider");
  out.property_block = Properties(b, pc);
  if (!PropertiesReady(*out.property_block))
    return fail("provider_bucket_properties_unavailable");
  return PostReady(std::move(out));
}
