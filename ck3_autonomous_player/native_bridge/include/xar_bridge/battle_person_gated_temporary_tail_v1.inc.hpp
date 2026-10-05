// Included inside xar::game after ContextSourcePropertiesV1.
// FINAL-RAW-LITERAL-SCHEMA.json was sealed before these source DTOs.
struct ContextSourceGatedNamedLiteralV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t slot_offset = 0x168;
  std::optional<std::string> entry_identity;
  std::optional<bool> tree_present;
  std::optional<std::string> tree_identity;
  std::optional<std::uint8_t> fixed_flag_u8;
  std::optional<std::int64_t> raw_fixed_q64;
  std::optional<std::int64_t> value_q64;
  std::string kind = "unconsumed";
  std::string reason = "gated_named_source_unconsumed";
  explicit ContextSourceGatedNamedLiteralV1(std::int32_t slot = 0x168)
      : slot_offset(slot) {}
  friend bool operator==(const ContextSourceGatedNamedLiteralV1 &,
                         const ContextSourceGatedNamedLiteralV1 &) = default;
};
struct ContextSourceGatedRefreshV1 {
  std::string status = "partial";
  bool ready = false;
  ContextSourceGatedNamedLiteralV1 source{};
  std::optional<std::int64_t> minimum_q64;
  std::optional<std::int64_t> maximum_q64;
  std::optional<std::int64_t> clamped_q64;
  std::optional<std::int32_t> threshold_count;
  std::optional<bool> threshold_array_present;
  std::optional<std::vector<std::int64_t>> thresholds_consumed_q64;
  std::optional<std::int32_t> fresh_rank_raw;
  std::string reason = "gated_refresh_not_observed";
  friend bool operator==(const ContextSourceGatedRefreshV1 &,
                         const ContextSourceGatedRefreshV1 &) = default;
};
struct ContextSourceGatedPrefixRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> definition_identity;
  std::optional<std::uint32_t> magic_raw;
  std::optional<bool> admitted;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceGatedPrefixRowV1 &,
                         const ContextSourceGatedPrefixRowV1 &) = default;
};
struct ContextSourceGatedPrefixV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::int32_t> selector_raw;
  std::optional<std::int32_t> native_prefix_count;
  std::optional<std::int32_t> header_count;
  std::optional<bool> array_present;
  std::optional<std::vector<ContextSourceGatedPrefixRowV1>> rows;
  std::string reason = "gated_prefix_not_observed";
  friend bool operator==(const ContextSourceGatedPrefixV1 &,
                         const ContextSourceGatedPrefixV1 &) = default;
};
struct ContextSourceGatedDeltaV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::int32_t> delta_raw;
  std::optional<std::int32_t> absolute_delta_raw;
  std::optional<std::string> header_selection;
  ContextSourceGatedNamedLiteralV1 weight_source{0x170};
  ContextSourceGatedPrefixV1 prefix{};
  std::string reason = "gated_delta_not_observed";
  friend bool operator==(const ContextSourceGatedDeltaV1 &,
                         const ContextSourceGatedDeltaV1 &) = default;
};
struct ContextSourceGatedResolutionV1 {
  std::int32_t native_index = 0;
  std::optional<std::int32_t> requested_full_id_raw;
  std::optional<bool> registry_present;
  std::optional<std::uint32_t> capacity_u32;
  std::optional<bool> indexed_pointer_present;
  std::optional<std::int32_t> indexed_full_id_raw;
  std::optional<std::string> selection;
  std::optional<std::string> object_identity;
  std::optional<std::uint32_t> magic_raw;
  std::optional<std::int32_t> full_id_raw;
  std::optional<bool> admitted;
  std::string reason;
  friend bool operator==(const ContextSourceGatedResolutionV1 &,
                         const ContextSourceGatedResolutionV1 &) = default;
};
struct ContextSourceGatedRelatedV1 {
  std::optional<bool> carrier_present;
  std::vector<ContextSourceGatedResolutionV1> attempts;
  std::optional<std::int32_t> self_full_id_raw;
  std::optional<std::int32_t> helper_return_full_id_raw;
  ContextSourceGatedResolutionV1 caller{};
  std::optional<bool> land_present;
  std::optional<bool> selected_present;
  std::string reason;
  friend bool operator==(const ContextSourceGatedRelatedV1 &,
                         const ContextSourceGatedRelatedV1 &) = default;
};
struct ContextSourceGatedListRowV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> property_identity;
  std::optional<ContextSourcePropertiesV1> property_block;
  std::string reason;
  friend bool operator==(const ContextSourceGatedListRowV1 &,
                         const ContextSourceGatedListRowV1 &) = default;
};
struct ContextSourceGatedListV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::string> selection;
  ContextSourceGatedRelatedV1 related{};
  std::optional<std::int32_t> count_raw;
  std::optional<bool> array_present;
  std::optional<std::vector<ContextSourceGatedListRowV1>> rows;
  std::string reason = "gated_list_not_observed";
  friend bool operator==(const ContextSourceGatedListV1 &,
                         const ContextSourceGatedListV1 &) = default;
};
struct ContextSourceGatedTemporaryTail291c7a7V1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<std::uint8_t> global_flag_u8;
  std::optional<bool> global_bit20;
  std::optional<bool> current_land_present;
  std::optional<bool> current_selected_present;
  std::optional<bool> temporary_admitted;
  std::optional<std::int32_t> selected_ec_raw;
  std::optional<std::int32_t> selector_global_raw;
  std::optional<std::int32_t> selected_e8_raw;
  std::optional<std::int32_t> selected_f8_raw;
  ContextSourceGatedRefreshV1 refresh_168{};
  ContextSourceGatedPrefixV1 prefix_1398{};
  ContextSourceGatedDeltaV1 delta_prefix_1420_14a8{};
  ContextSourceGatedListV1 list{};
  std::string reason = "gated_temporary_tail_not_observed";
  friend bool operator==(const ContextSourceGatedTemporaryTail291c7a7V1 &,
                         const ContextSourceGatedTemporaryTail291c7a7V1 &) = default;
};
