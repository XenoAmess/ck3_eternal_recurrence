// Included inside namespace xar::game after the cached absent DTO.
struct ContextSourceUncachedIntrinsicRecordV1 {
  std::uint32_t native_index = 0;
  std::optional<std::uint8_t> marker_u8;
  std::optional<std::uint64_t> key_object;
  std::optional<std::int32_t> key_id_i32;
  std::optional<std::int64_t> value_q64;
  bool operator==(const ContextSourceUncachedIntrinsicRecordV1 &) const = default;
};
struct ContextSourceUncachedIntrinsicVectorV1 {
  std::optional<std::int32_t> count;
  std::optional<std::vector<ContextSourceUncachedIntrinsicRecordV1>> records;
  bool operator==(const ContextSourceUncachedIntrinsicVectorV1 &) const = default;
};
struct ContextSourceUncachedIntrinsicFamilyV1 {
  bool ready = false;
  ContextSourceUncachedIntrinsicVectorV1 first, second;
  bool operator==(const ContextSourceUncachedIntrinsicFamilyV1 &) const = default;
};
struct ContextSourceUncachedObjectV1 {
  std::uint32_t native_index = 0;
  std::optional<std::uint64_t> object;
  std::optional<std::uint32_t> magic_u32;
  ContextSourceUncachedIntrinsicFamilyV1 intrinsic_family;
  bool operator==(const ContextSourceUncachedObjectV1 &) const = default;
};
struct ContextSourceUncachedObjectVectorV1 {
  std::optional<std::int32_t> count;
  std::optional<std::vector<ContextSourceUncachedObjectV1>> entries;
  bool operator==(const ContextSourceUncachedObjectVectorV1 &) const = default;
};
struct ContextSourceUncachedContextRecordV1 {
  std::uint32_t native_index = 0;
  std::optional<std::uint64_t> object;
  std::optional<std::uint8_t> flag_u8;
  bool operator==(const ContextSourceUncachedContextRecordV1 &) const = default;
};
struct ContextSourceUncachedContextVectorV1 {
  std::optional<std::int32_t> count;
  std::optional<std::vector<ContextSourceUncachedContextRecordV1>> entries;
  bool operator==(const ContextSourceUncachedContextVectorV1 &) const = default;
};
struct ContextSourceUncachedSeedReceiverV1 {
  std::optional<std::uint32_t> first_full_id, first_resolved_full_id;
  std::optional<bool> first_used_fallback;
  std::optional<std::uint32_t> second_full_id, second_resolved_full_id;
  std::optional<bool> second_used_fallback;
  std::optional<std::uint64_t> definition_object;
  bool operator==(const ContextSourceUncachedSeedReceiverV1 &) const = default;
};
struct ContextSourceUncachedRecipientInputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = 0;
  std::optional<bool> carrier_present;
  std::optional<std::uint32_t> associated_full_id, associated_resolved_full_id;
  std::optional<bool> associated_used_fallback;
  std::optional<std::uint32_t> associated_cache_440;
  ContextSourceUncachedSeedReceiverV1 seed_receiver;
  ContextSourceUncachedIntrinsicFamilyV1 seed_family;
  std::optional<std::uint64_t> fallback_key_object;
  std::optional<std::int32_t> fallback_key_id_i32;
  ContextSourceUncachedObjectVectorV1 active_objects, removed_objects;
  ContextSourceUncachedContextVectorV1 active_context;
  std::optional<std::int32_t> cap_i32;
  std::optional<std::int64_t> active_flag4_multiplier_q64,
      active_other_multiplier_q64, seed_boost_multiplier_q64;
  std::optional<std::uint64_t> positive_fallback_object, negative_fallback_object;
  std::optional<std::uint32_t> positive_fallback_magic_u32, negative_fallback_magic_u32;
  // Local storage reuses the physical downstream types; cached maps and status
  // are never serialized as part of this nested raw input family.
  ContextSourceAbsentRecipientInputsV1 downstream_inputs;
  std::optional<std::int64_t> calculated_recipient_q64;
  std::string reason;
  bool operator==(const ContextSourceUncachedRecipientInputsV1 &) const = default;
};
