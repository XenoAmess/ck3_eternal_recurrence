// Included inside namespace xar::game. All operands belong to one current query.
struct ContextSourceAbsentMap430EntryV1 {
  std::uint32_t bucket_index = 0;
  std::optional<std::uint32_t> hash_u32;
  std::optional<std::uint8_t> probe_u8;
  std::optional<std::uint64_t> key_object;
  std::optional<std::uint32_t> trait_id_u32;
  std::optional<std::int64_t> value_q64;
  friend bool operator==(const ContextSourceAbsentMap430EntryV1 &,
                         const ContextSourceAbsentMap430EntryV1 &) = default;
};
struct ContextSourceAbsentMap458EntryV1 {
  std::uint32_t bucket_index = 0;
  std::optional<std::uint32_t> hash_u32;
  std::optional<std::uint8_t> probe_u8;
  std::optional<std::uint64_t> key_object;
  std::optional<std::uint64_t> value_u64;
  friend bool operator==(const ContextSourceAbsentMap458EntryV1 &,
                         const ContextSourceAbsentMap458EntryV1 &) = default;
};
template <typename Entry> struct ContextSourceAbsentMapV1 {
  std::optional<std::int32_t> count;
  std::optional<std::int32_t> mask;
  std::optional<std::uint8_t> max_probe_u8;
  std::optional<std::vector<Entry>> entries;
  friend bool operator==(const ContextSourceAbsentMapV1 &,
                         const ContextSourceAbsentMapV1 &) = default;
};
struct ContextSourceAbsentTraitIdsV1 {
  std::optional<std::int32_t> count;
  std::optional<std::vector<std::uint32_t>> values_u32;
  friend bool operator==(const ContextSourceAbsentTraitIdsV1 &,
                         const ContextSourceAbsentTraitIdsV1 &) = default;
};
struct ContextSourceAbsentMembershipIdsV1 {
  std::optional<std::int32_t> count;
  std::optional<std::vector<std::uint64_t>> values_u64;
  friend bool operator==(const ContextSourceAbsentMembershipIdsV1 &,
                         const ContextSourceAbsentMembershipIdsV1 &) = default;
};
struct ContextSourceAbsentAggregateV1 {
  std::optional<std::int32_t> count;
  std::optional<std::vector<std::uint16_t>> keys_u16;
  std::optional<std::vector<std::int64_t>> values_q64;
  friend bool operator==(const ContextSourceAbsentAggregateV1 &,
                         const ContextSourceAbsentAggregateV1 &) = default;
};
struct ContextSourceAbsentRecipientInputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = 0;
  std::optional<bool> carrier_present;
  std::optional<std::uint32_t> associated_full_id;
  std::optional<std::uint32_t> associated_resolved_full_id;
  std::optional<bool> associated_used_fallback;
  std::optional<std::uint32_t> associated_cache_440;
  ContextSourceAbsentMapV1<ContextSourceAbsentMap430EntryV1> cached_map_430;
  ContextSourceAbsentMapV1<ContextSourceAbsentMap458EntryV1> cached_map_458;
  ContextSourceAbsentTraitIdsV1 trait_ids;
  ContextSourceAbsentMembershipIdsV1 membership_ids;
  std::optional<std::int32_t> membership_header_guard_raw;
  ContextSourceAbsentAggregateV1 aggregate_properties;
  std::optional<std::string> aggregate_context_selection;
  std::optional<std::int32_t> aggregate_context_guard_raw;
  std::optional<std::int64_t> member_multiplier_q64;
  std::optional<std::int64_t> clamp_lower_q64;
  std::optional<std::int64_t> clamp_upper_q64;
  std::optional<std::int64_t> calculated_recipient_q64;
  std::string reason;
  friend bool operator==(const ContextSourceAbsentRecipientInputsV1 &,
                         const ContextSourceAbsentRecipientInputsV1 &) = default;
};
